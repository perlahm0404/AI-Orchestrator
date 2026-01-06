# Wiggum + Autonomous Loop Integration Plan

**Date**: 2026-01-06
**Status**: 📋 Ready for Implementation
**Goal**: Integrate Wiggum iteration control into autonomous_loop.py for fully autonomous, long-running sessions

---

## Executive Summary

**Problem**: Current autonomous_loop.py has limited self-correction (3 retries) and no robust session persistence. Wiggum loop has powerful iteration control but no work queue discovery.

**Solution**: Integrate Wiggum's iteration control into autonomous_loop.py to create a fully autonomous system that:
- Pulls tasks from work queue (autonomous_loop)
- Retries with iteration budgets per agent type (Wiggum)
- Detects completion via `<promise>` tags (Wiggum)
- Handles BLOCKED verdicts with human override (Wiggum)
- Persists state for session resume (Wiggum)

**Expected Outcome**:
- Autonomy: 60% → **85%**
- Retries per task: 3 → **15-50** (agent-specific)
- Session resume: Manual → **Automatic**
- Completion detection: Files only → **Promise tags + verification**

---

## Current Architecture

### autonomous_loop.py (Current)

```
while tasks_remaining:
    task = queue.get_next_pending()
    result = claude_cli.execute_task(task)

    # Phase 2: Fast verification with retry
    for retry in range(3):  # Hard-coded 3 retries
        verify_result = fast_verify(changed_files)
        if verify_result.status == "PASS":
            break

        # Basic lint auto-fix
        if verify_result.has_lint_errors:
            run_lint_fix()

    if verification_passed:
        queue.mark_complete(task.id)
        git_commit()
    else:
        queue.mark_blocked(task.id)  # Just blocks and moves on
```

**Limitations**:
1. ❌ Only 3 retries (hard-coded)
2. ❌ No completion signal detection
3. ❌ No human override on BLOCKED
4. ❌ No iteration tracking
5. ❌ Weak session persistence

### Wiggum IterationLoop (Current)

```
while not task_complete:
    result = agent.execute(task)

    # Stop hook decision logic
    stop_result = agent_stop_hook(
        agent, session_id, changes, output, app_context
    )

    if stop_result.decision == ALLOW:
        # Completion signal OR Ralph PASS OR safe_to_merge
        return completed
    elif stop_result.decision == ASK_HUMAN:
        # BLOCKED verdict → interactive R/O/A prompt
        human_override = ask_human()
    elif stop_result.decision == BLOCK:
        # Ralph FAIL (regression) → retry
        continue

    agent.record_iteration(verdict, changes)
```

**Strengths**:
1. ✅ 15-50 retries per agent type
2. ✅ Completion signal detection
3. ✅ Human override on BLOCKED
4. ✅ Full iteration tracking
5. ✅ Robust state files

---

## Target Architecture: Integrated System

```
┌─────────────────────────────────────────────────────────────────┐
│                   autonomous_loop.py (Orchestrator)              │
│                                                                  │
│  while tasks_remaining and iteration < max_global_iterations:   │
│      ┌──────────────────────────────────────────────┐           │
│      │  1. Pull next task from work_queue.json     │           │
│      └──────────────────────────────────────────────┘           │
│                          ▼                                       │
│      ┌──────────────────────────────────────────────┐           │
│      │  2. IterationLoop.run(task, max_iterations)  │           │
│      │                                               │           │
│      │  • Stop hook integration                     │           │
│      │  • Completion signal detection               │           │
│      │  • 15-50 retries per task                    │           │
│      │  • Human override on BLOCKED                 │           │
│      │  • State file persistence                    │           │
│      └──────────────────────────────────────────────┘           │
│                          ▼                                       │
│      ┌──────────────────────────────────────────────┐           │
│      │  3. Handle result                            │           │
│      │  • COMPLETED → mark_complete + git_commit   │           │
│      │  • BLOCKED → mark_blocked + continue        │           │
│      │  • ABORTED → mark_blocked + stop loop       │           │
│      └──────────────────────────────────────────────┘           │
│                                                                  │
│  Next task (loop continues)                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan: 6 Steps

### Step 1: Enhance Task Schema (30 minutes)

**File**: `tasks/work_queue.json`

**Add completion promises to tasks**:

```json
{
  "project": "karematch",
  "features": [
    {
      "id": "BUG-001",
      "description": "Fix authentication timeout",
      "file": "src/auth/session.ts",
      "status": "pending",
      "tests": ["tests/auth/session.test.ts"],
      "completion_promise": "BUGFIX_COMPLETE",  // NEW
      "max_iterations": 15                       // NEW (optional override)
    }
  ]
}
```

**Changes**:
- Add `completion_promise` field (default by task type)
- Add optional `max_iterations` override per task
- Update WorkQueue class to handle new fields

**Files to modify**:
- [tasks/work_queue.py](../../tasks/work_queue.py) - Add fields to Task dataclass
- [tasks/work_queue.json](../../tasks/work_queue.json) - Update task definitions

---

### Step 2: Create Agent Factories (45 minutes)

**File**: `agents/factory.py` (NEW)

**Purpose**: Create agents with proper AgentConfig for Wiggum integration

```python
from dataclasses import dataclass
from pathlib import Path
from agents.base import AgentConfig
from agents.bugfix import BugFixAgent
from agents.codequality import CodeQualityAgent
from adapters import get_adapter

# Default completion promises by agent type
COMPLETION_PROMISES = {
    "bugfix": "BUGFIX_COMPLETE",
    "codequality": "CODEQUALITY_COMPLETE",
    "feature": "FEATURE_COMPLETE",
    "test": "TESTS_COMPLETE"
}

# Default iteration budgets by agent type
ITERATION_BUDGETS = {
    "bugfix": 15,
    "codequality": 20,
    "feature": 50,
    "test": 15
}

def create_agent(
    task_type: str,
    project_name: str,
    completion_promise: str = None,
    max_iterations: int = None
):
    """
    Create agent instance with proper configuration.

    Args:
        task_type: Agent type (bugfix, codequality, etc.)
        project_name: Project name (karematch, credentialmate)
        completion_promise: Override default completion promise
        max_iterations: Override default iteration budget

    Returns:
        Configured agent instance
    """
    # Load adapter
    adapter = get_adapter(project_name)

    # Create config
    config = AgentConfig(
        project_name=project_name,
        agent_name=task_type,
        expected_completion_signal=completion_promise or COMPLETION_PROMISES.get(task_type, "COMPLETE"),
        max_iterations=max_iterations or ITERATION_BUDGETS.get(task_type, 10)
    )

    # Create agent
    if task_type == "bugfix":
        return BugFixAgent(adapter, config)
    elif task_type == "codequality":
        return CodeQualityAgent(adapter, config)
    else:
        raise ValueError(f"Unknown agent type: {task_type}")
```

**Files to create**:
- [agents/factory.py](../../agents/factory.py) (NEW)

---

### Step 3: Integrate IterationLoop into autonomous_loop.py (2 hours)

**File**: `autonomous_loop.py`

**Replace lines 163-305** (Claude CLI execution + fast verify) with IterationLoop integration:

```python
# OLD (lines 163-305): Direct Claude CLI + 3 retries
wrapper = ClaudeCliWrapper(actual_project_dir)
result = wrapper.execute_task(...)
for retry in range(3):  # Limited retries
    verify_result = fast_verify(...)
    # ...

# NEW: IterationLoop integration
from orchestration.iteration_loop import IterationLoop
from agents.factory import create_agent

# Determine agent type from task ID
task_type = task.id.split('-')[0].lower()  # e.g., "BUG-001" → "bug" → "bugfix"
if task_type == "bug":
    task_type = "bugfix"

# Create agent with task-specific config
agent = create_agent(
    task_type=task_type,
    project_name=project_name,
    completion_promise=task.completion_promise if hasattr(task, 'completion_promise') else None,
    max_iterations=task.max_iterations if hasattr(task, 'max_iterations') else None
)

# Set task description for agent to access
agent.task_description = task.description
agent.task_file = task.file
agent.task_tests = task.tests if hasattr(task, 'tests') else []

# Run iteration loop
loop = IterationLoop(
    agent=agent,
    app_context=app_context,
    state_dir=actual_project_dir / ".aibrain"
)

try:
    result = loop.run(
        task_id=task.id,
        task_description=task.description,
        max_iterations=None,  # Use agent's default
        resume=True  # Enable session resume
    )

    # Handle result
    if result.status == "completed":
        queue.mark_complete(task.id)
        queue.save(queue_path)

        # Git commit
        commit_msg = f"{task_type}: {task.description}\n\nTask ID: {task.id}\nIterations: {result.iterations}"
        if git_commit(commit_msg, actual_project_dir):
            print("✅ Changes committed to git\n")

        update_progress_file(
            actual_project_dir,
            task,
            "complete",
            f"Completed after {result.iterations} iteration(s)"
        )

    elif result.status == "blocked":
        queue.mark_blocked(task.id, result.reason)
        queue.save(queue_path)
        update_progress_file(
            actual_project_dir,
            task,
            "blocked",
            result.reason
        )

    elif result.status == "aborted":
        # User aborted - stop the entire loop
        print("\n🛑 User aborted session - stopping autonomous loop")
        queue.mark_blocked(task.id, "Session aborted by user")
        queue.save(queue_path)
        break

    else:  # "failed"
        queue.mark_blocked(task.id, result.reason or "Task failed")
        queue.save(queue_path)
        update_progress_file(
            actual_project_dir,
            task,
            "blocked",
            result.reason or "Task failed"
        )

except Exception as e:
    print(f"❌ Exception during iteration loop: {e}\n")
    queue.mark_blocked(task.id, str(e))
    queue.save(queue_path)
    update_progress_file(actual_project_dir, task, "blocked", str(e))
    continue
```

**Key changes**:
1. Replace direct Claude CLI calls with IterationLoop.run()
2. Use agent factory to create properly configured agents
3. Handle all IterationLoop result statuses (completed/blocked/aborted/failed)
4. Pass state_dir for persistence
5. Enable resume=True for automatic session resume
6. Remove hard-coded 3-retry logic (IterationLoop handles this)

**Files to modify**:
- [autonomous_loop.py](../../autonomous_loop.py) - Lines 163-305

---

### Step 4: Update BugFixAgent.execute() for Autonomous Mode (1 hour)

**File**: `agents/bugfix.py`

**Current**: BugFixAgent.execute() uses Claude CLI wrapper but doesn't output completion promises.

**Enhancement**: Add completion promise output when task is complete.

```python
# In BugFixAgent.execute()

def execute(self, task_id: str) -> dict:
    """Execute bug fix task with Claude CLI"""

    # ... existing Claude CLI execution ...

    result = wrapper.execute_task(smart_prompt, ...)

    if result.success:
        # Check if fix was successful by examining output
        output = result.output

        # If tests pass and no errors in output, add completion promise
        if "error" not in output.lower() and "fail" not in output.lower():
            # Add completion promise to output
            promise_text = self.config.expected_completion_signal
            output += f"\n\n<promise>{promise_text}</promise>\n"

            return {
                "status": "success",
                "output": output,  # Now includes completion promise
                "files_changed": result.files_changed,
                "duration_ms": result.duration_ms
            }

    # If failed, don't output promise
    return {
        "status": "failed",
        "output": result.output,
        "error": result.error
    }
```

**Alternative**: Modify Claude CLI prompts to instruct Claude to output `<promise>TEXT</promise>` on completion.

**Files to modify**:
- [agents/bugfix.py](../../agents/bugfix.py) - execute() method
- [agents/codequality.py](../../agents/codequality.py) - execute() method
- [claude/prompts.py](../../claude/prompts.py) - Add promise instruction to prompts

---

### Step 5: Enhance Progress Tracking (30 minutes)

**File**: `autonomous_loop.py`

**Update progress file format** to include iteration details:

```python
def update_progress_file(project_dir: Path, task: Task, status: str, details: str, iterations: int = 0) -> None:
    """Update claude-progress.txt with iteration details"""
    progress_file = project_dir / "claude-progress.txt"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {timestamp}\n\n"

    if status == "complete":
        entry += f"- [x] {task.id}: {task.description}\n"
        entry += f"  - Files: {task.file}\n"
        entry += f"  - Iterations: {iterations}\n"  # NEW
        entry += f"  - Status: ✅ Complete\n"
        entry += f"  - {details}\n"
    elif status == "in_progress":
        entry += f"- [ ] {task.id}: {task.description}\n"
        entry += f"  - Status: 🔄 In Progress (iteration {iterations}/{task.max_iterations if hasattr(task, 'max_iterations') else 'N/A'})\n"  # NEW
        entry += f"  - {details}\n"
    elif status == "blocked":
        entry += f"- [ ] {task.id}: {task.description}\n"
        entry += f"  - Iterations attempted: {iterations}\n"  # NEW
        entry += f"  - Status: 🛑 Blocked\n"
        entry += f"  - Reason: {details}\n"

    with progress_file.open("a") as f:
        f.write(entry)
```

**Files to modify**:
- [autonomous_loop.py](../../autonomous_loop.py) - update_progress_file() function

---

### Step 6: Update CLI and Documentation (45 minutes)

**Files to update**:

1. **CLI Help** - [autonomous_loop.py](../../autonomous_loop.py)
   - Update argparse description
   - Add note about Wiggum integration

2. **Work Queue Tool** - [tasks/work_queue.py](../../tasks/work_queue.py)
   - Add Task schema validation
   - Document new fields

3. **Session Handoff** - [orchestration/reflection.py](../../orchestration/reflection.py)
   - Include iteration summary in handoff
   - Add Wiggum-specific metadata

**CLI Help Text**:
```python
parser = argparse.ArgumentParser(
    description="""
    Autonomous Agent Loop - Fully autonomous task execution with Wiggum iteration control

    This system combines:
    - Work queue discovery (autonomous_loop)
    - Wiggum iteration control (self-correction with budgets)
    - Completion signal detection (<promise> tags)
    - Human override on BLOCKED verdicts
    - Session persistence and resume

    Features:
    - 15-50 retries per task (agent-specific)
    - Automatic lint/type/test error correction
    - Resume from interruption
    - Full iteration audit trail

    Example:
        python autonomous_loop.py --project karematch --max-iterations 100
    """
)
```

---

## File Modification Summary

| File | Action | Lines | Effort |
|------|--------|-------|--------|
| [docs/planning/wiggum-autonomous-integration-plan.md](wiggum-autonomous-integration-plan.md) | CREATE | ~800 | This file |
| [agents/factory.py](../../agents/factory.py) | CREATE | ~80 | 45min |
| [tasks/work_queue.py](../../tasks/work_queue.py) | MODIFY | +30 | 15min |
| [tasks/work_queue.json](../../tasks/work_queue.json) | MODIFY | +2 fields per task | 15min |
| [autonomous_loop.py](../../autonomous_loop.py) | MODIFY | ~150 lines replaced | 2hr |
| [agents/bugfix.py](../../agents/bugfix.py) | MODIFY | +15 | 30min |
| [agents/codequality.py](../../agents/codequality.py) | MODIFY | +15 | 30min |
| [claude/prompts.py](../../claude/prompts.py) | MODIFY | +20 | 15min |
| [STATE.md](../../STATE.md) | UPDATE | +50 | 15min |
| [DECISIONS.md](../../DECISIONS.md) | UPDATE | +30 | 15min |
| [CLAUDE.md](../../CLAUDE.md) | UPDATE | +100 | 30min |
| [docs/planning/autonomous-implementation-plan.md](autonomous-implementation-plan.md) | UPDATE | +50 | 15min |

**Total Effort**: ~6 hours
**Total New Code**: ~400 lines
**Total Modified Code**: ~200 lines

---

## Testing Plan

### Phase 1: Unit Testing (1 hour)

Test each component in isolation:

```bash
# Test agent factory
python -m pytest tests/agents/test_factory.py -v

# Test work queue with new fields
python -m pytest tests/tasks/test_work_queue.py -v

# Test iteration loop integration
python -m pytest tests/integration/test_autonomous_wiggum.py -v
```

### Phase 2: Integration Testing (2 hours)

Run autonomous loop with controlled test tasks:

```bash
# Create test work queue with 3 simple tasks
cat > tasks/test_work_queue.json <<EOF
{
  "project": "karematch",
  "features": [
    {
      "id": "TEST-001",
      "description": "Add console.log to test file",
      "file": "test-file.ts",
      "completion_promise": "BUGFIX_COMPLETE",
      "max_iterations": 5
    }
  ]
}
EOF

# Run autonomous loop
python autonomous_loop.py --project karematch --max-iterations 10
```

**Expected behavior**:
1. Pull TEST-001 from queue
2. Create agent with completion_promise="BUGFIX_COMPLETE"
3. Execute via IterationLoop
4. Retry up to 5 times if needed
5. Detect completion promise in output
6. Mark complete and commit
7. Move to next task

### Phase 3: Production Testing (4 hours)

Run on real KareMatch bugs:

```bash
# Load real work queue
python autonomous_loop.py --project karematch --max-iterations 50
```

**Monitor**:
- Iteration counts per task
- Completion signal detection rate
- BLOCKED verdict handling
- Session resume after interruption

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Autonomy level** | 60% | - | **85%** |
| **Retries per task** | 3 (fixed) | - | **15-50** (agent-specific) |
| **Completion detection** | File changes only | - | **Promise tags + verification** |
| **BLOCKED handling** | Skip task | - | **Human R/O/A** |
| **Session resume** | Manual | - | **Automatic** |
| **Iteration tracking** | None | - | **Full audit trail** |
| **Tasks per session** | ~10-15 | - | **30-50** |

---

## Rollback Plan

If integration causes issues:

1. **Immediate rollback**: Revert autonomous_loop.py to previous version
2. **Keep Wiggum separate**: Can still use `aibrain wiggum` CLI for manual iteration
3. **Partial rollback**: Keep agent factory, revert IterationLoop integration

**Rollback commit**:
```bash
git revert HEAD  # Revert integration commit
git checkout main -- autonomous_loop.py  # Restore old version
```

---

## Next Steps

1. ✅ Create this plan document
2. ⏳ Review and approve plan
3. ⏳ Implement Step 1-6 in order
4. ⏳ Run testing phases
5. ⏳ Deploy to production
6. ⏳ Monitor autonomy metrics

---

## References

- [Wiggum Implementation Plan](../../.claude/plans/jaunty-humming-hartmanis.md)
- [Autonomous Implementation Plan](autonomous-implementation-plan.md)
- [RALPH-COMPARISON.md](../../RALPH-COMPARISON.md)
- [Anthropic Autonomous Coding Quickstart](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)

---

**Status**: 📋 **READY FOR IMPLEMENTATION**
**Expected Completion**: 1-2 days
**Risk Level**: LOW (both systems already working, minimal integration surface)
**Impact**: HIGH (60% → 85% autonomy improvement)
