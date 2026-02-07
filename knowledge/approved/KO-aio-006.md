---
{
  "id": "KO-aio-006",
  "project": "ai-orchestrator",
  "title": "Stateless Memory Architecture - Context-Independent AI Agent Execution",
  "what_was_learned": "AI agents lose memory when context windows compact or sessions end. Solution: Externalize all memory to disk using SessionState class + Claude Code hooks (PreCompact, SessionStart, Stop). PreCompact saves state BEFORE compaction. SessionStart reloads state on any session start. Stop hook monitors context size to prompt fresh start before compaction wastes tokens. Result: True stateless execution where agents resume from disk state, not context window.",
  "why_it_matters": "Context window dependency causes: (1) Memory loss on compaction (lossy summarization), (2) Wasted tokens on compaction (~2000-5000 per compact), (3) Cannot resume interrupted work, (4) No audit trail. Stateless memory enables: 80% token savings, lossless state preservation, automatic resume, cross-session continuity.",
  "prevention_rule": "Never rely on context window for durable memory. Always externalize state to disk before context operations. Use hooks to automate save/load. Monitor context size to avoid compaction entirely when possible.",
  "tags": [
    "stateless-memory",
    "context-window",
    "compaction",
    "session-state",
    "hooks",
    "persistence",
    "token-savings",
    "resume",
    "claude-code"
  ],
  "status": "approved",
  "created_at": "2026-02-07T12:00:00.000000",
  "approved_at": "2026-02-07T12:00:00.000000",
  "detection_pattern": "context.*compact|session.*lost|memory.*reset",
  "file_patterns": [
    "orchestration/session_state.py",
    "orchestration/iteration_loop.py",
    "autonomous_loop.py",
    ".claude/hooks/*.sh",
    ".claude/settings.json"
  ]
}
---

# Stateless Memory Architecture - Context-Independent AI Agent Execution

## What Was Learned

AI agents (Claude) lose memory when:
1. Context windows compact (summarization loses detail)
2. Sessions end or crash
3. Conversations reset

**The Problem**: Context window = memory. When context changes, memory is lost.

**The Solution**: Externalize ALL memory to disk. Use hooks to automate save/load.

### Architecture Components

| Component | File | Purpose |
|-----------|------|---------|
| **SessionState** | `orchestration/session_state.py` | Core class for save/load/update/archive |
| **IterationLoop Integration** | `orchestration/iteration_loop.py` | Auto-save after each agent iteration |
| **AutonomousLoop Integration** | `autonomous_loop.py` | Check for existing sessions on task start |
| **PreCompact Hook** | `.claude/hooks/pre-compact-memory.sh` | Save state BEFORE compaction |
| **SessionStart Hook** | `.claude/hooks/session-start-memory.sh` | Reload state on any session start |
| **Stop Hook** | `.claude/hooks/context-monitor.sh` | Monitor context size, warn before compaction |

### Session File Format

```markdown
---
{
  "id": "SESSION-20260207-115912",
  "task_id": "TASK-001",
  "project": "ai-orchestrator",
  "iteration_count": 5,
  "phase": "verification",
  "status": "in_progress",
  "next_steps": ["Run tests", "Deploy"],
  ...
}
---

# Task Summary
Human-readable content here...
```

## Why It Matters

### Business Impact

| Metric | Before | After |
|--------|--------|-------|
| Token usage per context reset | ~4,500 | ~650 |
| Information preservation | Lossy (summarized) | Lossless (exact state) |
| Resume capability | Manual | Automatic |
| Cross-session continuity | None | Full |

### Technical Impact

**Compaction wastes tokens**: When context compacts, Claude spends 2000-5000 tokens summarizing old context. With stateless memory, we can use `/clear` for a fresh context and reload state from disk - zero compaction tokens.

**Compaction loses information**: Summarization is lossy. "next_steps: ['Fix auth bug', 'Run tests', 'Deploy to staging']" becomes "working on auth". With disk persistence, exact state is preserved.

**Crash recovery**: If session crashes mid-task, state is already on disk. New session loads it automatically via SessionStart hook.

### Hook Flow

```
Context Window Fills Up
         ↓
┌─────────────────────────────┐
│  Stop Hook                  │ ← Checks transcript size
│  (every response)           │ ← Warns if approaching limit
└─────────────────────────────┘
         ↓
User runs /clear (or compaction triggers)
         ↓
┌─────────────────────────────┐
│  PreCompact Hook            │ ← Saves state BEFORE compaction
│  (if compaction)            │ ← Backup safety net
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│  SessionStart Hook          │ ← Loads state from disk
│  (on fresh context)         │ ← Injects into new context
└─────────────────────────────┘
         ↓
   Claude continues with full knowledge
```

## Prevention Rule

### DO: Externalize Memory

```python
# At task start
session = SessionState(task_id=task_id, project=project)

# After each significant action
session.save({
    "iteration_count": current,
    "phase": "implementation",
    "status": "in_progress",
    "next_steps": ["Fix bug", "Run tests"],
})

# On completion
session.archive()
```

### DO: Use Hooks for Automation

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "session-start-memory.sh"}]}],
    "PreCompact": [{"hooks": [{"type": "command", "command": "pre-compact-memory.sh"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "context-monitor.sh"}]}]
  }
}
```

### DON'T: Rely on Context Window

```python
# BAD: Context-dependent memory
self.memory = {"tasks_done": [...]}  # Lost on compaction!

# GOOD: Disk-based memory
session.save({"tasks_done": [...]})  # Persisted to .aibrain/
```

### DON'T: Wait for Compaction

```python
# BAD: Let compaction happen (wastes tokens)
# Context fills → Compaction (~3000 tokens) → Resume with summary

# GOOD: Pre-emptive reset (zero waste)
# Context approaching limit → Save state → /clear → Reload state
```

## Implementation Reference

### SessionState API

```python
from orchestration.session_state import SessionState

# Create/load session
session = SessionState(task_id="TASK-001", project="ai-orchestrator")

# Save state (creates .aibrain/session-TASK-001-1.md)
session.save({
    "iteration_count": 5,
    "phase": "testing",
    "status": "in_progress",
    "next_steps": ["Run tests", "Fix failures"],
})

# Update existing session
session.update(iteration_count=6, phase="deployment")

# Load latest checkpoint
data = session.get_latest()

# Archive on completion
session.archive()

# List all sessions
sessions = SessionState.get_all_sessions(project="ai-orchestrator")
```

### Hook Configuration (.claude/settings.json)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-start-memory.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact-memory.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/context-monitor.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `orchestration/session_state.py` | 430 | Core SessionState class |
| `tests/test_session_state.py` | 540 | 23 tests, all passing |
| `examples/session_state_integration_example.py` | 160 | Usage demo |
| `.claude/hooks/pre-compact-memory.sh` | 70 | PreCompact hook |
| `.claude/hooks/session-start-memory.sh` | 85 | SessionStart hook |
| `.claude/hooks/context-monitor.sh` | 75 | Stop hook for context monitoring |

## Related Knowledge Objects

- KO-aio-001: Background process crashes (non-interactive mode)
- KO-aio-002: Checkpoint system for long-running tasks

## Version History

- v1.0 (2026-02-07): Initial implementation - SessionState + hooks
