---
name: restart-beacon
description: Maintains a per-session JSON snapshot of current work state. Overwrites on every prompt-response. Used for fast recovery after /clear, /compact, crash, or new session. Always runs with insight-scribe.
disable-model-invocation: false
user-invokable: false
---

# Restart Beacon — Session State Snapshot

## PURPOSE

Maintain a lightweight JSON file that captures the CURRENT state of this conversation session.
The beacon is **overwritten** (not appended) on every prompt-response cycle, so it always
reflects the latest state. On session restart (/clear, crash, new window), Claude reads the
beacon FIRST to instantly recover context without parsing the full session log.

---

## BEACON STRUCTURE

```json
{
  "session_id": "S1",
  "session_label": "short-descriptor",
  "started": "YYYY-MM-DDTHH:MM:SS",
  "last_updated": "YYYY-MM-DDTHH:MM:SS",
  "log_file": "path/to/session_log.md",

  "focus": {
    "current_task": "What Claude is working on right now",
    "priority": "Q1"
  },

  "last_completed": {
    "what": "Description of the last completed task",
    "when": "YYYY-MM-DDTHH:MM:SS",
    "files_touched": ["path/to/file1.py", "path/to/file2.py"]
  },

  "pending_immediate": [
    "Next task 1",
    "Next task 2"
  ],

  "context_decisions": [
    "Active decisions that affect current work"
  ],

  "modes_active": [],

  "session_history_today": [
    "Sub-1: Brief description of first sub-session"
  ]
}
```

---

## RULES

1. **OVERWRITE completely** — never append. The beacon is a snapshot, not a log.
2. **One beacon per active session** — if S1 exists from a different conversation, create S2.
3. **Update conjointly with insight-scribe** — every prompt-response cycle.
4. **Keep compact** — max ~40 lines of JSON. No narrative paragraphs.
5. **pending_immediate** — max 5 items, ordered by priority.
6. **Timestamps from OS** — NEVER use the model's internal date.

---

## LIFECYCLE

| Event | Action |
|-------|--------|
| Session start | Create `RESTART_BEACON_S{N}.json` |
| Every prompt-response | Overwrite beacon with current state |
| Session end | Delete the beacon (session log has the permanent record) |
| `/clear` or crash | Beacon survives — next session reads it for recovery |

---

## RECOVERY FLOW (on restart)

1. Check for `RESTART_BEACON_S*.json` files
2. If ONE beacon found → read it, resume from `pending_immediate[0]`
3. If MULTIPLE beacons → present choices to user
4. If NO beacon found → normal start
5. Beacons with `last_updated` > 24h → flag as stale, suggest cleanup
