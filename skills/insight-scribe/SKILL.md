---
name: insight-scribe
description: Auto-evaluates each prompt-response for insights and appends findings to the active session log. Use after every prompt-response cycle to decide if there is a loggable insight.
disable-model-invocation: false
user-invokable: false
---

# Insight Scribe — Post-Prompt Insight Logger

## PURPOSE

Automatically evaluate each prompt-response cycle and determine if a **loggable insight**
was produced. If YES, append a structured entry to the active session log.
If NO, do nothing. This skill runs silently — the user should never need to ask for it.

---

## EVALUATION CRITERIA

After each prompt-response, ask: **"Did this exchange produce an insight?"**

### What IS an insight (APPEND — short entry, 4-5 lines)

| Type | Example |
|------|---------|
| **Decision** | Architecture choice, library selection, design pattern adopted |
| **Discovery** | Bug discovered, unexpected behavior, performance finding |
| **Bug** | Bug found AND/OR fixed (include root cause) |
| **Pattern** | Code pattern, visual pattern, narrative pattern discovered |
| **State-Change** | Priority shift, task completed, blocker resolved |
| **Doctrine** | New rule, convention, or protocol established |

### What IS an output (WRITE-FIRST — complete response, no line limit)

| Type | Example |
|------|---------|
| **Output** | Full architectural analysis, diagnostic tables, options comparison, implementation plan |

**WRITE-FIRST RULE**: When the response IS the deliverable (analysis, diagnostic, comparison),
write it COMPLETE to the session log FIRST, then show only a short reference in chat.
Chat shows: title + 3-5 bullets + "Full output: session log [HH:MM]"
No truncation. No duplication. One place only (session log).

### What is NOT an insight (SKIP)

- Simple confirmations ("ok", "done", "go")
- Questions without technical resolution
- File reads without discoveries
- Conversational exchanges
- Repetition of known information

---

## ENTRY FORMAT

When an insight is detected, APPEND to the active session log file
(insert BEFORE the `## SESSION_STATUS` line):

```markdown
### [S{N}/CLAUDE] YYYY-MM-DD HH:MM — Concise insight title

**Type:** Decision | Discovery | Bug | Pattern | State-Change | Doctrine
**Context:** [1 line — what was being done]
**Insight:** [2-3 lines max — the concrete finding]
**Impact:** [what changes in the project, which file/module affected]
```

Where:
- `S{N}` = session ID from the active RESTART_BEACON (e.g., S1, S2)
- `YYYY-MM-DD HH:MM` = obtained from system OS (NEVER from model's internal clock)

---

## RULES

1. **APPEND only** — never overwrite, never delete existing content. Use Edit tool (not Write).
2. **Timestamp from OS** — execute `date` command to get local date+time. NEVER use model's internal date.
3. **Session ID** — use `S{N}` from the active RESTART_BEACON. Format: `[S1/CLAUDE]`, `[S2/CLAUDE]`, etc.
4. **Insert position** — append BEFORE the `## SESSION_STATUS` line.
5. **Brevity** — insights are concise. 4-5 lines max per entry. Not a narrative.
6. **No duplicates** — if the same insight was already logged (check last 5 entries), skip.
7. **Conjoint with restart-beacon** — when insight-scribe runs, restart-beacon should also update.
