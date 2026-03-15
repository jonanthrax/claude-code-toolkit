# Claude Code Toolkit

Production-tested skills, agents, and hooks for Claude Code — built from months of daily use on a real scientific analysis platform.

## What's Inside

### Hooks (System-Enforced)

| Hook | Event | Purpose |
|------|-------|---------|
| [`insight_logger.py`](hooks/insight_logger.py) | `Stop` | Safety-net that captures important outputs Claude forgets to log |
| [`write_first_reminder.py`](hooks/write_first_reminder.py) | `UserPromptSubmit` | Injects a reminder before every response to follow Write-First doctrine |

### Skills (Auto-Invoked)

| Skill | Purpose |
|-------|---------|
| [`insight-scribe`](skills/insight-scribe/SKILL.md) | Auto-evaluates each prompt-response for loggable insights |
| [`restart-beacon`](skills/restart-beacon/SKILL.md) | Maintains a JSON snapshot for fast crash recovery |

### Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| [`web-archaeologist`](agents/web-archaeologist.md) | Sonnet | Three-phase web research with credibility ranking |

### Patterns (Documented)

| Pattern | Description |
|---------|-------------|
| [Write-First Doctrine](docs/WRITE_FIRST_PATTERN.md) | 2-layer defense against losing AI outputs |
| [Multi-Model Orchestration](docs/MULTI_MODEL_ORCHESTRATION.md) | Haiku-as-Scout, cascading pipelines, capability matrix |

---

## Key Innovations

### 1. Write-First Doctrine

**Problem:** Claude produces valuable analysis, then "forgets" to save it — especially after `/compact` or long sessions.

**Solution:** A 2-layer defense system:
- **Layer 1 (Proactive):** Claude evaluates relevance → writes to log file FIRST → shows summary in chat
- **Layer 2 (Safety net):** Stop hook detects keywords → auto-appends if Layer 1 missed

```
Layer 1: Claude → Edit log → Chat shows summary
Layer 2: Stop hook → Keyword detection → Append [HOOK] entry as backup
```

### 2. Multi-Model Orchestration

**Pattern:** Use the right model for the right task:

```
Haiku (scout) → scans 50 files, filters to 8 by STRUCTURE
    ↓
Sonnet (analyst) → reads 8 files, evaluates SEMANTICALLY
    ↓
Opus (reviewer) → validates critical decisions
```

**Golden rule:** Haiku filters by FORM (structure), never by CONTENT (meaning).

Result: ~6x cost reduction with same quality.

### 3. Prompt Counter as Health Indicator

The `UserPromptSubmit` hook tracks prompts per session:
- **P1-P10:** Green — fresh context, full coherence
- **P11-P20:** Yellow — context filling, watch for drift
- **P20+:** Red — context saturated, recommend new session

### 4. Non-blocking Soft Prompt Pattern

When Claude must make a decision without full information, auto-classify using the best heuristic + append a soft correction prompt:

```
S2 started. Beacon S1 found (3h old).
ASSUMING: continuation of S1 (pending tasks inherited).
If you prefer a fresh session or parallel session, let me know.
```

1 round-trip. No interruption. User auto-corrects the ~5% residual.

---

## Installation

### 1. Copy files to your project

```bash
# Skills (directory format required!)
cp -r skills/insight-scribe/ .claude/skills/insight-scribe/
cp -r skills/restart-beacon/ .claude/skills/restart-beacon/

# Agents (flat file format)
cp agents/web-archaeologist.md .claude/agents/

# Hooks
cp hooks/insight_logger.py .claude/hooks/
cp hooks/write_first_reminder.py .claude/hooks/
```

### 2. Configure hooks in `.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/insight_logger.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/write_first_reminder.py"
          }
        ]
      }
    ]
  }
}
```

### 3. Customize for your project

Edit the hooks to match your project structure:
- **`insight_logger.py`**: Update `SESSIONS_DIR` and bitacora path pattern
- **`write_first_reminder.py`**: Update `SESSIONS_DIR` and `COUNTER_DIR`
- **Timezone**: Change `TZ_LIMA` to your local timezone

---

## Gotchas We Discovered (So You Don't Have To)

| # | Gotcha | Impact |
|---|--------|--------|
| 1 | Flat `.md` files in `.claude/skills/` are **silently ignored** | Skills require `skills/<name>/SKILL.md` (directory format) |
| 2 | `skill.md` (lowercase) is **silently ignored** | Must be `SKILL.md` (uppercase) |
| 3 | `user-invocable` (with C) is **silently ignored** | Must be `user-invokable` (with K) |
| 4 | Multi-line YAML `description:` is **silently dropped** | Use single-line descriptions only |
| 5 | `model:` in skill frontmatter may be **silently ignored** | Use `commands/<name>.md` for model switching |
| 6 | UTF-8 on Windows hooks: CP1252 pipe corruption | Force UTF-8 stdin (see `insight_logger.py` line 26-27) |
| 7 | `disable-model-invocation: false` = permission, NOT execution | Skills are hints, not triggers. Hooks are guaranteed. |

Related GitHub issues we filed:
- [#34538](https://github.com/anthropics/claude-code/issues/34538) — Silent skill format failure (BUG)
- [#34553](https://github.com/anthropics/claude-code/issues/34553) — effortLevel in frontmatter (FEATURE)
- [#34558](https://github.com/anthropics/claude-code/issues/34558) — Multi-model orchestration (FEATURE)

---

## Context

Built during daily use on a production scientific analysis platform. These patterns emerged from real pain points — lost outputs, encoding bugs, model confusion — and were validated empirically over weeks of intensive Claude Code usage.

## License

MIT — see [LICENSE](LICENSE)
