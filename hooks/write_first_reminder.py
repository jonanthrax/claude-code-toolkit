"""
UserPromptSubmit Hook: Write-First Reminder
============================================
Injects a reminder into Claude's context before every prompt.
Claude sees this as <user-prompt-submit-hook> (treated as user input priority).
The user does NOT see this output.

Provides:
  - Session ID (from active beacon)
  - Prompt counter with health indicator (green/yellow/red)
  - Write-First trigger + entry format template

INSTALLATION:
  Add to .claude/settings.json:
  {
    "hooks": {
      "UserPromptSubmit": [{
        "hooks": [{
          "type": "command",
          "command": "python .claude/hooks/write_first_reminder.py"
        }]
      }]
    }
  }
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================================
# CONFIGURATION — Customize these for your project
# ============================================================================

# Your timezone (UTC offset)
TZ_OFFSET_HOURS = -5
TZ_LOCAL = timezone(timedelta(hours=TZ_OFFSET_HOURS))

# Directory where session beacons live
SESSIONS_DIR = Path("docs/sessions")

# Directory for counter files
COUNTER_DIR = Path(".claude/hooks")


def get_session_id() -> str:
    """Read active beacon to get session ID."""
    beacons = sorted(SESSIONS_DIR.rglob("RESTART_BEACON_S*.json"))
    if not beacons:
        return "S?"
    try:
        data = json.loads(beacons[-1].read_text(encoding="utf-8"))
        return data.get("session_id", "S?")
    except Exception:
        return "S?"


def get_and_increment_counter(session_id: str) -> int:
    """File-based prompt counter. One file per session."""
    counter_file = COUNTER_DIR / f"prompt_counter_{session_id}.txt"
    try:
        count = int(counter_file.read_text().strip()) + 1
    except Exception:
        count = 1
    counter_file.write_text(str(count))
    return count


def health_indicator(prompt_num: int) -> str:
    """Context health based on prompt count."""
    if prompt_num <= 10:
        return "green"
    elif prompt_num <= 20:
        return "yellow"
    else:
        return "red — consider restart"


def main():
    try:
        # Read stdin (UserPromptSubmit sends JSON with user prompt)
        raw = sys.stdin.read()
        # We don't need the prompt content, just the event trigger

        session_id = get_session_id()
        prompt_num = get_and_increment_counter(session_id)
        health = health_indicator(prompt_num)

        now = datetime.now(TZ_LOCAL)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        # Output injected into Claude's context as <user-prompt-submit-hook>
        # Use ASCII only to avoid Windows CP1252 pipe corruption
        print(f"[{session_id} | P{prompt_num} | {health} | Write-First ACTIVE]")
        print(f"If response contains relevant insight/output -> write to session log FIRST (Edit before SESSION_STATUS).")
        print(f"Format: ### [{session_id}/CLAUDE] {date_str} {time_str} -- Title")

    except Exception:
        # Fail-safe: never crash, never block. Empty stdout = no reminder.
        pass


if __name__ == "__main__":
    main()
