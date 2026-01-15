# Real Ralph Loop Documentation

This document explains the Real Ralph loop implementation in this repository.

---

## What is Real Ralph?

Real Ralph is a **bash-based iteration controller** that spawns **fresh Claude Code sessions** for each attempt at a task. This is distinct from plugin-based approaches that run in a single long-lived session.

### Key Characteristics

| Aspect | Real Ralph | Plugin Ralph |
|--------|-----------|--------------|
| **Session Model** | Fresh process per iteration | Single long-lived session |
| **Context** | Clean slate + files only | Accumulating with compaction |
| **Memory** | PRD.md + progress.md | In-session context |
| **Predictability** | High (no context drift) | Variable (context pollution possible) |
| **Implementation** | Bash script (external) | Claude Code plugin (internal) |

### Why Fresh Sessions Matter

1. **No Context Pollution**: Each iteration starts clean. Failed approaches don't confuse subsequent attempts.
2. **Explicit Memory**: All knowledge passes through files (PRD.md, progress.md). Nothing hidden in compacted context.
3. **Reproducibility**: Same PRD + progress yields consistent behavior.
4. **Debuggability**: Humans can inspect progress.md to see exactly what each iteration tried.

---

## Files

| File | Purpose |
|------|---------|
| `ralph.sh` | Main loop script (spawns fresh sessions) |
| `.ralph/PRD.md` | Task definitions with acceptance criteria |
| `.ralph/progress.md` | Iteration history and failure patterns |

---

## Quick Start

### 1. Install Prerequisites

Ensure Claude CLI is installed:

```bash
# Verify installation
claude --version

# If not installed, see:
# https://docs.anthropic.com/en/docs/claude-code
```

### 2. Make Script Executable

```bash
chmod +x ralph.sh
```

### 3. Configure PRD.md

Edit `.ralph/PRD.md` to define your tasks:

```markdown
## Tasks

- [ ] Fix the authentication timeout bug
  - **Acceptance Criteria**: Login works after 30 minutes idle
  - **Files**: `src/auth/session.ts`

- [ ] Add unit tests for the session manager
  - **Acceptance Criteria**: `npm test` passes with 80%+ coverage
  - **Files**: `tests/auth/session.test.ts`
```

### 4. Run Ralph

```bash
# Default: 10 iterations
./ralph.sh

# Custom iteration limit
./ralph.sh 50

# Verbose mode (see full Claude output)
./ralph.sh 10 --verbose
```

### 5. Monitor Progress

```bash
# Check progress between runs
cat .ralph/progress.md

# Watch for task completion
watch -n 5 'grep -c "- \[x\]" .ralph/PRD.md'
```

---

## PRD.md Format

The PRD uses GitHub-flavored markdown with checkboxes:

```markdown
# Product Requirements Document (PRD)

## Tasks

### Section: Bug Fixes

- [ ] Task description here
  - **Acceptance Criteria**: What defines "done"
  - **Files**: Which files to modify

- [ ] Another task
  - **Acceptance Criteria**: Testable condition
  - **Files**: `path/to/file.ts`

## Completed Tasks

- [x] Previously completed task
  - **Completed**: 2024-01-15
```

### Task Guidelines

1. **Atomic Tasks**: One clear deliverable per checkbox
2. **Measurable Criteria**: Include commands or conditions to verify completion
3. **File Hints**: List relevant files to help Claude navigate
4. **Priority Order**: Ralph works top-to-bottom

---

## progress.md Format

Progress is logged automatically:

```markdown
# Ralph Progress Log

## Iteration Log

### Iteration 1
**Timestamp**: 2024-01-15T10:30:00Z
**Task**: Fix unused imports
**Status**: Session completed (exit 0)
**Result**: COMPLETED

### Iteration 2
**Timestamp**: 2024-01-15T10:32:00Z
**Task**: Add type hints
**Status**: Session completed (exit 0)
**Result**: INCOMPLETE - will retry

**What was attempted**:
- Added hints to main function
- Encountered mypy error

**Hypothesis for next attempt**:
- Need to import Optional from typing
```

### Human Intervention

Between runs, you can:

1. **Add notes**: Edit progress.md to guide the next attempt
2. **Skip tasks**: Mark tasks as `- [x]` manually to skip them
3. **Reorder tasks**: Move high-priority items to the top of PRD.md
4. **Reset retries**: Clear progress.md to start fresh

---

## How It Works

### Loop Flow

```
┌─────────────────────────────────────────────────────┐
│                    ralph.sh                         │
│                                                     │
│  1. Read PRD.md → Find first incomplete task        │
│  2. Build prompt with task + context                │
│  3. Spawn: claude --print -p "$PROMPT"              │
│     └─→ Fresh Claude Code process                   │
│         └─→ Reads PRD.md, progress.md               │
│         └─→ Attempts task                           │
│         └─→ Updates files                           │
│         └─→ Exits (context discarded)               │
│  4. Check if task checkbox changed                  │
│  5. Log result to progress.md                       │
│  6. Repeat until done or budget exhausted           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Fresh Session Mechanism

Each iteration runs:

```bash
claude --print -p "$PROMPT"
```

This spawns a **new Claude Code process** that:
- Has zero memory of previous iterations
- Reads only what's in PRD.md and progress.md
- Writes changes to disk before exiting
- Terminates completely (context destroyed)

The next iteration starts from scratch, with updated file contents as its only memory.

---

## Comparison with Existing Systems

### This Repo's Systems

| System | Purpose | Session Model |
|--------|---------|--------------|
| `ralph/` | Code verification (PASS/FAIL/BLOCKED) | N/A (library) |
| `autonomous_loop.py` | Task automation | Single Python process |
| `ralph.sh` (Real Ralph) | Fresh session iteration | New process per iteration |

### When to Use Each

- **ralph.sh**: General-purpose task iteration with fresh contexts
- **autonomous_loop.py**: Deep integration with governance, Ralph verification, Knowledge Objects
- **Direct Claude**: One-off tasks that don't need iteration

---

## Troubleshooting

### "Claude CLI not found"

```bash
# Install Claude Code CLI
# See: https://docs.anthropic.com/en/docs/claude-code
```

### "PRD.md not found"

```bash
# Create the .ralph directory and PRD file
mkdir -p .ralph
# Copy from template or create manually
```

### Tasks Not Getting Marked Complete

1. Check if Claude has write access to PRD.md
2. Verify the checkbox format: `- [ ]` with a space
3. Check progress.md for error details

### Session Hangs

```bash
# Add timeout (example: 5 minutes per iteration)
timeout 300 claude --print -p "$PROMPT"
```

### Context Too Large

If PRD.md or progress.md grows too large:

```bash
# Archive old progress
mv progress.md progress-archive-$(date +%Y%m%d).md
touch progress.md

# Or summarize progress.md manually
```

---

## Integration with AI Orchestrator

Real Ralph (`ralph.sh`) is **independent** of the AI Orchestrator's existing systems:

- It does NOT use `autonomous_loop.py`
- It does NOT invoke Ralph verification (`ralph/`)
- It does NOT use Wiggum stop hooks
- It does NOT require the virtual environment

This makes it a lightweight, portable alternative for simple task iteration.

To integrate with governance if needed:

```bash
# Run with verification (requires venv)
source .venv/bin/activate
export AI_ORCHESTRATOR_HARNESS_ACTIVE=1
./ralph.sh
```

---

## Verification Checklist

Use this to confirm Real Ralph is working:

- [ ] `ralph.sh` is executable (`chmod +x ralph.sh`)
- [ ] `claude --version` returns a version number
- [ ] `.ralph/PRD.md` exists with at least one unchecked task
- [ ] `./ralph.sh` starts and shows iteration output
- [ ] After completion, `.ralph/progress.md` contains iteration logs
- [ ] Completed tasks show `- [x]` in .ralph/PRD.md

---

## FAQ

**Q: Does this replace the Ralph Wiggum plugin?**
A: No. This is an independent implementation. Use whichever approach fits your needs.

**Q: Can I use both ralph.sh and autonomous_loop.py?**
A: Yes, they're independent. Use ralph.sh for simple task iteration, autonomous_loop.py for governed automation.

**Q: Why bash instead of Python?**
A: Bash ensures true process isolation. Each `claude` invocation is a subprocess with no shared memory.

**Q: How do I increase the iteration budget for a specific task?**
A: Either increase the global budget (`./ralph.sh 100`) or manually retry by running ralph.sh again after it stops.
