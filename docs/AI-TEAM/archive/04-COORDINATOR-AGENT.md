# Coordinator Agent Specification

**Date**: 2026-01-09
**Status**: Design Phase

---

## Overview

The Coordinator is the **autonomous orchestration agent** that bridges decisions and execution. It reads ADRs, breaks them into tasks, assigns to Builders, maintains PROJECT_HQ.md, and creates session handoffs—all automatically.

---

## Identity

```yaml
name: coordinator
mode: autonomous
domain: project orchestration
autonomy_level: L2
```

---

## Core Responsibilities

| Responsibility | Trigger | Output |
|----------------|---------|--------|
| Task breakdown | ADR approved | tasks/work_queue.json |
| Task assignment | Task ready | Builder activated |
| Status tracking | Any task change | PROJECT_HQ.md updated |
| Session handoffs | Session end | sessions/*.md created |
| Dependency management | Task with deps | Correct ordering |
| Blocker escalation | BLOCKED verdict | Blocker in PROJECT_HQ |

---

## Auto-Behaviors

### On ADR Approved

```python
def on_adr_approved(self, adr_path):
    """
    Triggered automatically when Advisor creates an ADR.
    """
    # 1. Parse the ADR
    adr = self.parse_adr(adr_path)

    # 2. Extract implementation notes
    impl_notes = adr.get('implementation_notes')

    # 3. Generate task breakdown
    tasks = self.break_into_tasks(impl_notes)

    # 4. Identify dependencies
    tasks = self.resolve_dependencies(tasks)

    # 5. Add to work queue
    self.add_to_queue(tasks)

    # 6. Update PROJECT_HQ
    self.update_project_hq({
        'new_tasks': tasks,
        'from_adr': adr.id,
        'status': 'queued'
    })

    # 7. Assign first task (if no blockers)
    self.assign_next_task()
```

### On Task Complete

```python
def on_task_complete(self, task_id, result):
    """
    Triggered when a Builder finishes a task.
    """
    # 1. Mark task complete
    self.mark_complete(task_id)

    # 2. Update PROJECT_HQ
    self.update_project_hq({
        'task': task_id,
        'status': 'completed',
        'result': result.summary
    })

    # 3. Check for dependent tasks
    unblocked = self.check_dependencies(task_id)

    # 4. Assign next task
    if unblocked:
        self.assign_next_task()
```

### On Session End

```python
def on_session_end(self):
    """
    Triggered automatically when session is ending.
    """
    # 1. Gather session state
    state = {
        'completed': self.get_completed_tasks(),
        'in_progress': self.get_active_tasks(),
        'blocked': self.get_blocked_tasks(),
        'queue': self.get_pending_tasks()
    }

    # 2. Create handoff document
    handoff = self.create_handoff(state)

    # 3. Update PROJECT_HQ
    self.update_project_hq({
        'session_ended': True,
        'handoff': handoff.path
    })

    # 4. Persist work queue
    self.save_queue()
```

### On BLOCKED Verdict

```python
def on_blocked(self, task_id, verdict):
    """
    Triggered when Ralph returns BLOCKED.
    """
    # 1. Add to blockers section
    self.update_project_hq({
        'blocker': {
            'task': task_id,
            'reason': verdict.reason,
            'details': verdict.evidence
        }
    })

    # 2. Pause task
    self.pause_task(task_id)

    # 3. Continue with other tasks if available
    self.assign_next_task(exclude=task_id)
```

---

## Task Breakdown Strategy

### From ADR to Tasks

```
ADR-023: Certification Tracking
├── Implementation Notes:
│   - Create certification_completions table
│   - Add API endpoint for completion
│   - Build completion form UI
│   - Write tests
│
└── Generated Tasks:
    1. TASK-023-001: Create migration for certification_completions
       Type: feature, Agent: FeatureBuilder, Deps: none

    2. TASK-023-002: Implement completion API endpoint
       Type: feature, Agent: FeatureBuilder, Deps: [001]

    3. TASK-023-003: Build completion form component
       Type: feature, Agent: FeatureBuilder, Deps: [002]

    4. TASK-023-004: Write tests for completion flow
       Type: test, Agent: TestWriter, Deps: [001, 002, 003]
```

### Task Structure

```yaml
task:
  id: "TASK-023-001"
  adr: "ADR-023"
  title: "Create migration for certification_completions"
  description: |
    Create database migration adding certification_completions table
    with columns: id, user_id, certification_id, completed_at, notes
  type: feature  # feature, bugfix, test, quality
  agent: FeatureBuilder
  dependencies: []
  status: pending  # pending, in_progress, completed, blocked
  priority: P1
  estimated_iterations: 5
  completion_promise: "FEATURE_COMPLETE"
  files:
    - "alembic/versions/*_add_certification_completions.py"
  tests:
    - "tests/test_certification_completions.py"
```

---

## PROJECT_HQ.md Management

### Update Triggers

| Event | Section Updated |
|-------|-----------------|
| ADR approved | Roadmap, Recent Decisions |
| Task created | Status Dashboard |
| Task started | Status Dashboard, Current Focus |
| Task completed | Status Dashboard |
| Task blocked | Blockers |
| Session end | Session History |

### Update Format

```python
def update_project_hq(self, update):
    """
    Atomic update to PROJECT_HQ.md
    """
    hq = self.load_project_hq()

    # Update timestamp
    hq.last_updated = now()
    hq.updated_by = self.name

    # Apply specific updates
    if 'new_tasks' in update:
        hq.dashboard.extend(update['new_tasks'])

    if 'task_status' in update:
        hq.update_task(update['task'], update['status'])

    if 'blocker' in update:
        hq.blockers.append(update['blocker'])

    if 'decision' in update:
        hq.decisions.append(update['decision'])

    # Save atomically
    self.save_project_hq(hq)
```

---

## Work Queue Management

### Queue File: `tasks/work_queue.json`

```json
{
  "project": "credentialmate",
  "last_updated": "2026-01-09T15:30:00Z",
  "tasks": [
    {
      "id": "TASK-023-001",
      "adr": "ADR-023",
      "title": "Create migration for certification_completions",
      "type": "feature",
      "agent": "FeatureBuilder",
      "status": "completed",
      "dependencies": [],
      "completed_at": "2026-01-09T14:00:00Z"
    },
    {
      "id": "TASK-023-002",
      "adr": "ADR-023",
      "title": "Implement completion API endpoint",
      "type": "feature",
      "agent": "FeatureBuilder",
      "status": "in_progress",
      "dependencies": ["TASK-023-001"],
      "started_at": "2026-01-09T14:05:00Z"
    },
    {
      "id": "TASK-023-003",
      "adr": "ADR-023",
      "title": "Build completion form component",
      "type": "feature",
      "agent": "FeatureBuilder",
      "status": "pending",
      "dependencies": ["TASK-023-002"]
    }
  ]
}
```

### Assignment Logic

```python
def assign_next_task(self, exclude=None):
    """
    Assign the next ready task to appropriate Builder.
    """
    # Get pending tasks
    pending = [t for t in self.queue if t.status == 'pending']

    # Filter by dependencies satisfied
    ready = [t for t in pending if self.deps_satisfied(t)]

    # Exclude if specified
    if exclude:
        ready = [t for t in ready if t.id != exclude]

    if not ready:
        return None

    # Sort by priority
    ready.sort(key=lambda t: t.priority)

    # Assign first ready task
    task = ready[0]
    task.status = 'in_progress'
    task.started_at = now()

    # Activate appropriate Builder
    builder = self.get_builder(task.agent)
    builder.execute(task)

    return task
```

---

## Session Handoff Generation

### Handoff Template

```markdown
# Session Handoff: [YYYY-MM-DD]-[SEQ]

**Project**: [name]
**Created**: [timestamp]
**Created By**: Coordinator

## Session Summary

**Duration**: [X hours/minutes]
**Tasks Completed**: [N]
**Tasks In Progress**: [N]
**Blockers**: [N]

## Completed This Session

| Task | Description | Agent |
|------|-------------|-------|
| [Auto-populated] |

## Still In Progress

| Task | Status | Notes |
|------|--------|-------|
| [Auto-populated] |

## Blocked (Need Human)

| Task | Blocker | Details |
|------|---------|---------|
| [Auto-populated] |

## Next Session Should

1. [First priority task]
2. [Second priority task]
3. [Continue from X]

## Files Changed

| File | +/- | Agent |
|------|-----|-------|
| [Auto-populated] |

## ADRs Referenced

- [ADR links]

## Notes

[Any context for next session]
```

---

## Contract

```yaml
# governance/contracts/coordinator.yaml

name: coordinator
version: "1.0"
mode: autonomous
autonomy_level: L2

triggers:
  - adr_approved
  - task_complete
  - task_blocked
  - session_end
  - resume_session

allowed_actions:
  - read_adr
  - create_task
  - assign_task
  - update_project_hq
  - create_handoff
  - manage_queue
  - read_codebase

forbidden_actions:
  - write_code              # That's Builders' job
  - make_decisions          # That's Advisors' job
  - modify_adr              # ADRs are immutable
  - bypass_ralph            # Never bypass verification
  - delete_without_approval # Destructive actions need approval

requires_approval:
  - delete_task
  - change_priority
  - reassign_task
  - skip_task

limits:
  max_concurrent_tasks: 3
  max_queue_size: 50

behaviors:
  auto_update_project_hq: true
  auto_create_handoff: true
  auto_assign_tasks: true
  respect_dependencies: true
```

---

## Integration with Builders

### Builder Notification

```python
def notify_builder(self, builder_type, task):
    """
    Activate a Builder for a task.
    """
    builder = BuilderFactory.create(builder_type)

    # Configure for task
    builder.configure({
        'task_id': task.id,
        'completion_promise': task.completion_promise,
        'max_iterations': task.estimated_iterations * 2,
        'files': task.files,
        'tests': task.tests
    })

    # Start execution
    result = builder.execute(task.id)

    # Handle result
    if result.status == 'COMPLETED':
        self.on_task_complete(task.id, result)
    elif result.status == 'BLOCKED':
        self.on_blocked(task.id, result.verdict)
```

### Result Handling

```yaml
builder_results:
  COMPLETED:
    - Mark task complete
    - Update PROJECT_HQ
    - Assign next task

  BLOCKED:
    - Add to blockers
    - Update PROJECT_HQ
    - Continue with other tasks

  FAILED:
    - Check if regression
    - If regression: retry within budget
    - If pre-existing: mark complete anyway
```

---

## Example Flow

```
1. Advisor creates ADR-023 (certification tracking)
   ↓
2. Coordinator detects ADR-023 approved
   ↓
3. Coordinator parses implementation notes
   ↓
4. Coordinator creates 4 tasks:
   - TASK-023-001: Migration (no deps)
   - TASK-023-002: API (deps: 001)
   - TASK-023-003: UI (deps: 002)
   - TASK-023-004: Tests (deps: 001,002,003)
   ↓
5. Coordinator updates PROJECT_HQ.md
   ↓
6. Coordinator assigns TASK-023-001 to FeatureBuilder
   ↓
7. FeatureBuilder completes, Ralph PASS
   ↓
8. Coordinator marks 001 complete, assigns 002
   ↓
9. [Continues until all done or blocked]
   ↓
10. Session ends → Handoff auto-created
```
