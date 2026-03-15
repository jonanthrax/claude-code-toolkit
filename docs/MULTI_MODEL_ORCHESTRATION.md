# Multi-Model Orchestration in Claude Code

## The Idea

Claude Code supports `model:` in agent and command frontmatter. This means you can assign different models to different tasks based on their requirements — not just capability, but cost and speed.

## Haiku-as-Scout Pattern

**Golden rule: Haiku filters by FORM (structure), never by CONTENT (meaning).**

| Task type | Haiku | Sonnet/Opus |
|-----------|-------|-------------|
| File discovery by pattern | GOOD | Overkill |
| Syntax validation | GOOD | Overkill |
| Count lines/classes | GOOD | Overkill |
| Semantic code review | BAD | Necessary |
| Architectural decisions | BAD | Necessary |
| Statistical interpretation | BAD | Necessary |

### Cascading Pipeline

```
Haiku (scout) → scans 50 files, filters to 8 by structure
    ↓
Sonnet (analyst) → reads 8 files, evaluates semantically
    ↓
Opus (reviewer) → validates critical decisions
```

Result: ~6x cheaper than Sonnet scanning everything, same quality.

## Model Capability Matrix (Empirical)

Discovered through testing — NOT in official docs as of March 2026:

| Capability | Haiku | Sonnet | Opus |
|-----------|-------|--------|------|
| Context window | **200k** | 1M | 1M |
| effortLevel support | **NO** | YES | YES |
| Extended thinking | **NO** | YES | YES |
| Tool use | YES | YES | YES |
| tool_reference blocks | **NO** | YES | YES |

## 3-Tier Depth Protocol

| Tier | Command | Model | Use case |
|------|---------|-------|----------|
| QUICK | `/quick` | Sonnet | Factual questions, config, lookups |
| STANDARD | (default) | Sonnet | Normal implementation |
| DEEP | `/deep` | Opus | Architecture, math, planning |

### Implementation

```yaml
# .claude/commands/deep.md (model switching works in commands/)
---
model: opus
---
Apply maximum analytical depth to the following task.
$ARGUMENTS
```

```yaml
# .claude/commands/quick.md
---
model: sonnet
---
Respond concisely. No analysis, no proposals.
$ARGUMENTS
```

**Note:** As of March 2026, `model:` in skill frontmatter (`skills/<name>/SKILL.md`) may be silently ignored. Use `commands/<name>.md` for reliable model switching. See [GitHub issue #34538](https://github.com/anthropics/claude-code/issues/34538).

## Agent Examples

```yaml
# .claude/agents/code-scout.md — structural filtering
---
model: haiku
description: Fast structural search — finds files by pattern, counts, validates syntax
tools: [Read, Grep, Glob]
---
```

```yaml
# .claude/agents/code-reviewer.md — semantic analysis
---
model: sonnet
description: Semantic code review — evaluates correctness, architecture, edge cases
tools: [Read, Grep, Glob]
---
```

## Anti-Token-Overflow Protocol

For agents that explore large codebases, include these rules:

```
R1: NEVER return full file contents to main context
R2: Write findings directly to output file
R3: Return ONLY summary to main: "Found N patterns in M files"
R4: Max 4 simultaneous file reads
R5: Max 15 lines if data MUST return to main
R6: Never read files >50 LOC verbatim — summarize
```

This prevents agent results from overwhelming the parent's context window.

## Cost Implications

| Model | Relative cost | When to use |
|-------|---------------|-------------|
| Haiku | 1x (baseline) | Structural filtering, data generation |
| Sonnet | ~4x | Implementation, analysis, most tasks |
| Opus | ~19x | Architecture, critical decisions, deep math |

Assign models deliberately. Don't use Opus for file discovery. Don't use Haiku for code review.
