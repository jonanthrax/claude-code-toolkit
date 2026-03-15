# Write-First Doctrine

## The Problem

Claude produces valuable analysis — architectural decisions, diagnostic tables, multi-option comparisons — then shows it in chat. After `/compact`, crash, or context overflow, that analysis is **gone forever**. The chat is ephemeral. Your session log is permanent.

Even with `disable-model-invocation: false` on an auto-skill like `insight-scribe`, Claude "forgets" to follow the instruction after ~15-20 prompts or post-compact. This is not a bug — it's a fundamental limitation of LLMs with finite context windows.

**Key insight:** `disable-model-invocation: false` makes a skill ELIGIBLE for invocation, not EXECUTED. Permission ≠ execution.

## The Solution: 2-Layer Defense

```
Layer 1 (Proactive — Claude writes):
  Claude evaluates: "Is this response relevant?"
  YES → Edit session log FIRST → Chat shows only summary
  NO  → Respond normally in chat

Layer 2 (Safety net — Hook writes):
  Stop hook fires after EVERY response
  Detects insight keywords in Claude's response
  If Layer 1 missed → Hook appends [HOOK] entry to log
```

### Layer 1: Write-First (Behavioral)

When Claude's response is a deliverable (analysis, diagnostic, comparison):

1. **Evaluate:** Is this relevant? (Decision, Discovery, Output, State-Change)
2. **YES** → Write COMPLETE to session log via Edit tool
3. **Chat shows:** title + 3-5 bullets + "Full output: session log [HH:MM]"
4. **NO** → Respond normally

### Layer 2: Stop Hook (System-Enforced)

The `insight_logger.py` script runs after every Claude response:

1. Receives `last_assistant_message` via stdin JSON
2. Checks for keyword patterns (e.g., `**Type:** Decision`, `[Depth: DEEP]`)
3. If keywords found AND no "Full output:" skip marker → appends to log
4. Non-blocking, async, zero latency

### Layer 3: UserPromptSubmit Reminder (Reinforcement)

The `write_first_reminder.py` hook injects a reminder before every prompt:

```
[S1 | P12 | green | Write-First ACTIVE]
If response contains relevant insight → write to session log FIRST.
```

Claude treats this as user-priority input (via `<user-prompt-submit-hook>`), which is stronger than CLAUDE.md instructions that can be deprioritized.

## Why This Works

| Mechanism | Type | Reliable? | Why |
|-----------|------|-----------|-----|
| Skill instruction | Behavioral | NO | Permission ≠ execution. Claude can forget. |
| CLAUDE.md instruction | Behavioral | PARTIAL | Reloaded post-compact, but can be ignored |
| **UserPromptSubmit hook** | **System + behavioral** | **YES** | Fresh every turn, treated as user input |
| **Stop hook** | **System-enforced** | **YES** | OS-level, runs regardless of Claude's behavior |

## Observed Failure Mode

In practice (observed 2024-2026), Claude wrote analysis directly to chat despite Write-First being active. The Stop hook captured it as a `[HOOK]` safety-net entry — proving that Layer 2 works. But hook entries have lower quality (keyword-based title extraction, potential encoding issues on Windows).

**Lesson:** Layer 1 (Claude proactive) produces better entries. Layer 2 (hook) is the safety net, not the primary mechanism.

## Prompt Counter as Health Indicator

The `UserPromptSubmit` hook maintains a per-session prompt counter:

| Range | Color | Meaning |
|-------|-------|---------|
| P1-P10 | green | Fresh context, full Write-First adherence |
| P11-P20 | yellow | Context filling, adherence may drift |
| P20+ | red | Context saturated, recommend new session |

This is a proxy for context window utilization — not exact, but correlates with quality degradation.
