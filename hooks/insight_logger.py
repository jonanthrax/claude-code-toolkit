"""
Stop Hook: Insight Logger
=========================
Async post-response hook that evaluates Claude's last response for loggable
insights/outputs and appends them to an active session log file.

This is Layer 2 (safety net) of the Write-First Doctrine. Layer 1 is Claude
proactively writing to the log. This hook catches what Layer 1 misses.

Receives JSON on stdin from Claude Code Stop event:
  {
    "session_id": "...",
    "last_assistant_message": "...",
    "transcript_path": "...",
    "stop_hook_active": true/false,
    "cwd": "..."
  }

Runs async (fire-and-forget) — zero latency for the user.

INSTALLATION:
  Add to .claude/settings.json:
  {
    "hooks": {
      "Stop": [{
        "hooks": [{
          "type": "command",
          "command": "python .claude/hooks/insight_logger.py"
        }]
      }]
    }
  }
"""

import json
import sys
import io
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Force UTF-8 stdin on Windows (prevents CP1252 mojibake)
# CRITICAL: Without this, multi-byte UTF-8 chars (em-dash, accented letters)
# get re-interpreted as CP1252 on Windows, producing garbage like "Ã¡" for "á"
if hasattr(sys.stdin, 'buffer'):
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

# ============================================================================
# CONFIGURATION — Customize these for your project
# ============================================================================

# Your timezone (UTC offset). Examples: -5 for Lima/Bogota, -8 for PST, +1 for CET
TZ_OFFSET_HOURS = -5
TZ_LOCAL = timezone(timedelta(hours=TZ_OFFSET_HOURS))

# Directory where your session logs live (relative to project root)
SESSIONS_DIR = Path("docs/sessions")

# Session log filename pattern. {date} will be replaced with YYYY_MM_DD
LOG_FILENAME_PATTERN = "{date}_SESSION_LOG.md"

# Beacon filename glob pattern
BEACON_GLOB = "RESTART_BEACON_S*.json"

# Marker in the log file where new entries are inserted BEFORE
SESSION_STATUS_MARKER = "## SESSION_STATUS: ACTIVE"

# ============================================================================
# Keywords that signal a loggable insight in Claude's response
# ============================================================================

INSIGHT_KEYWORDS = [
    # Explicit insight markers
    "**Type:** Decision",
    "**Type:** Discovery",
    "**Type:** Bug",
    "**Type:** Pattern",
    "**Type:** State-Change",
    "**Type:** Doctrine",
    "**Type:** Output",
    "**Tipo:** Decision",
    "**Tipo:** Hallazgo",
    "**Tipo:** Bug",
    "**Tipo:** Cambio-de-Estado",
    "**Tipo:** Output",
    # Structural markers
    "[Depth: DEEP]",
    "## Proposal",
    "## Analysis",
    "#### IMPLEMENTATION PLAN",
]

# Keywords that signal this is NOT worth logging (already saved elsewhere)
SKIP_KEYWORDS = [
    "Full output: bitacora",
    "Full output: session log",
    "Full output:",
]

# Minimum response length to even consider (short responses = not insights)
MIN_RESPONSE_LENGTH = 200


def get_log_path(cwd: str) -> Path | None:
    """Find today's active session log file."""
    today = datetime.now(TZ_LOCAL).strftime("%Y_%m_%d")
    filename = LOG_FILENAME_PATTERN.format(date=today)
    sessions_dir = Path(cwd) / SESSIONS_DIR
    log_file = sessions_dir / filename
    if log_file.exists():
        return log_file
    # Also search one level deeper (e.g., sessions/username/)
    for subdir in sessions_dir.iterdir():
        if subdir.is_dir():
            candidate = subdir / filename
            if candidate.exists():
                return candidate
    return None


def should_log(message: str) -> bool:
    """Heuristic: does this response contain a loggable insight?"""
    if len(message) < MIN_RESPONSE_LENGTH:
        return False

    # Skip if already written via Write-First
    for skip in SKIP_KEYWORDS:
        if skip in message:
            return False

    # Check for insight keywords
    for keyword in INSIGHT_KEYWORDS:
        if keyword in message:
            return True

    return False


def extract_title(message: str) -> str:
    """Extract a title from the response for the log entry."""
    SKIP_HEADERS = {
        "Scope", "Analysis", "Proposal", "Risks",
        "Summary", "Output format:",
    }

    # Look for markdown headers (skip generic ones)
    headers = re.findall(r'^#{1,4}\s+(.+)$', message, re.MULTILINE)
    for h in headers:
        clean = h.strip().rstrip(':')
        if clean not in SKIP_HEADERS and len(clean) > 5:
            return clean[:80]

    # Look for **Type:** or **Tipo:** line
    tipo = re.search(r'\*\*(?:Type|Tipo):\*\*\s*(.+)', message)
    if tipo:
        return tipo.group(1).strip()[:80]

    # Fallback: first substantive line
    for line in message.split('\n'):
        line = line.strip()
        if line and not line.startswith('[') and not line.startswith('#') and len(line) > 10:
            return line[:80]

    return "Insight detected by Stop hook"


def get_session_id(cwd: str) -> str:
    """Read active beacon to get session ID."""
    sessions_dir = Path(cwd) / SESSIONS_DIR
    # Search in sessions dir and subdirs
    beacons = sorted(sessions_dir.rglob(BEACON_GLOB))
    if not beacons:
        return "S?"
    try:
        data = json.loads(beacons[-1].read_text(encoding="utf-8"))
        return data.get("session_id", "S?")
    except Exception:
        return "S?"


def sanitize_encoding(text: str) -> str:
    """Fix common UTF-8 mojibake from Windows CP1252 pipe corruption.

    When Claude's response passes through stdin on Windows, multi-byte
    UTF-8 characters sometimes get re-interpreted as CP1252, producing
    mojibake like 'Ã¡' instead of 'á', or 'â€"' instead of '—'.

    Strategy: re-encode as CP1252 bytes, then decode as UTF-8.
    Must use CP1252 (NOT latin-1) because CP1252 has characters in the
    0x80-0x9F range (euro, smart quotes, em-dash) that latin-1 does not.
    """
    try:
        return text.encode("cp1252").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def append_to_log(log_file: Path, message: str, cwd: str) -> None:
    """Append a hook-detected insight entry to the session log."""
    now_date = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d")
    now_time = datetime.now(TZ_LOCAL).strftime("%H:%M")
    title = extract_title(message)
    session_id = get_session_id(cwd)

    # Full content, sanitized encoding
    clean_message = sanitize_encoding(message.strip())

    # Cap at 80 lines to prevent massive entries
    lines = clean_message.split('\n')
    if len(lines) > 80:
        content_body = '\n'.join(lines[:80])
        content_body += f"\n\n... [{len(lines) - 80} more lines truncated by safety-net]"
    else:
        content_body = clean_message

    entry = f"""
### [{session_id}/HOOK] {now_date} {now_time} — Safety-net: {title}

**Type:** Hook-detected (insight-scribe safety net)
**Note:** Claude did not write this output via Write-First. The Stop hook captured it.

{content_body}

---
"""

    file_content = log_file.read_text(encoding="utf-8")
    if SESSION_STATUS_MARKER in file_content:
        file_content = file_content.replace(SESSION_STATUS_MARKER, entry + SESSION_STATUS_MARKER)
        log_file.write_text(file_content, encoding="utf-8")


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return

        data = json.loads(raw)

        # Guard: prevent infinite loops
        if data.get("stop_hook_active", False):
            return

        message = data.get("last_assistant_message", "")
        cwd = data.get("cwd", ".")

        if not message or not should_log(message):
            return

        log_file = get_log_path(cwd)
        if not log_file:
            return

        append_to_log(log_file, message, cwd)

    except Exception:
        # Fire-and-forget: never crash, never block
        pass


if __name__ == "__main__":
    main()
