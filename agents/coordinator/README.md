# Coordinator Agent

**Version**: 3.0
**Part of**: AI Team (AI-TEAM-SPEC-V3)

---

## Overview

The Coordinator is the **autonomous orchestration agent** that bridges decisions and execution. It sits at Tier 2 of the AI Team hierarchy:

```
Tier 1: Advisors (user-invoked, recommend)
    ↓
Tier 2: Coordinator (autonomous, orchestrate)  ← This module
    ↓
Tier 3: Builders (autonomous, execute code)
```

## Responsibilities

| Responsibility | Trigger | Output |
|----------------|---------|--------|
| Task breakdown | ADR approved | `work_queue.json` updated |
| Task assignment | Task ready | Builder activated |
| Status tracking | Any task change | `PROJECT_HQ.md` updated |
| Session handoffs | Session end | `sessions/*.md` created |
| Dependency management | Task with deps | Correct ordering |
| Blocker escalation | BLOCKED verdict | Blocker in PROJECT_HQ |
| Task discovery (ADR-003) | Advisor decision | New tasks registered |

---

## Module Components

### 1. `coordinator.py` - Main Coordinator Agent

The central orchestration engine.

```python
from agents.coordinator import Coordinator, CoordinatorConfig

config = CoordinatorConfig(
    project_root=Path("/path/to/project"),
    max_concurrent_tasks=3,
    max_queue_size=50,
    auto_assign=True,
)
coordinator = Coordinator(config)

# Handle ADR approval
tasks = coordinator.on_adr_approved(Path("AI-Team-Plans/decisions/ADR-001.md"))

# Handle task completion
next_task = coordinator.on_task_completed("TASK-001-001", {"iterations": 5})

# Create session handoff
handoff_path = coordinator.on_session_end()
```

**Key Methods**:

| Method | Description |
|--------|-------------|
| `on_adr_approved(path)` | Parse ADR, create tasks, add to queue |
| `on_adr_closed(path)` | Close out ADR when all tasks complete |
| `on_task_completed(id, result)` | Mark complete, assign next task |
| `on_task_blocked(id, reason, details)` | Add to blockers, continue others |
| `on_session_end()` | Create handoff document |
| `on_scope_escalation(task, files, callback)` | Trigger Advisor for 5+ files |
| `on_advisor_decision(decision, queue)` | Register discovered tasks (ADR-003) |
| `resume_session()` | Resume from previous session |

### 2. `task_manager.py` - Task Lifecycle Management

Manages the work queue and task state transitions.

```python
from agents.coordinator import TaskManager, Task, TaskStatus, TaskType

manager = TaskManager(Path("AI-Team-Plans/tasks/work_queue.json"))

# Create a task
task = Task(
    id="TASK-001-001",
    title="Implement user authentication",
    type=TaskType.FEATURE,
    agent="FeatureBuilder",
    priority="P1",
)
manager.add_task(task)

# Transition task state
manager.start_task("TASK-001-001")
manager.complete_task("TASK-001-001", iterations=10)

# Query tasks
pending = manager.get_tasks_by_status(TaskStatus.PENDING)
summary = manager.get_summary()
```

**Task Status Flow**:
```
PENDING → IN_PROGRESS → COMPLETED
              ↓
          BLOCKED → (human resolves) → PENDING
              ↓
          CANCELLED
```

**Task Types**:
- `FEATURE` - New functionality (→ FeatureBuilder)
- `BUGFIX` - Bug fixes (→ BugFixer)
- `REFACTOR` - Code restructuring (→ CodeQuality)
- `TEST` - Test writing (→ TestWriter)
- `DOCUMENTATION` - Docs updates (→ manual)
- `INFRASTRUCTURE` - Infra changes (→ manual)
- `MIGRATION` - Schema changes (→ manual)

### 3. `handoff.py` - Session Handoff Generation

Creates session handoff documents and phase retrospectives.

```python
from agents.coordinator import HandoffGenerator

generator = HandoffGenerator(Path("AI-Team-Plans/sessions"))

# Create session handoff
handoff_path = generator.create_handoff({
    "session_id": "session-2026-01-10-001",
    "completed_tasks": [...],
    "in_progress_tasks": [...],
    "blocked_tasks": [...],
})

# Generate phase retrospective
retro_path = generator.generate_retrospective(
    phase_id=1,
    phase_name="Foundation",
    stats={...},
    patterns=[...],
)
```

### 4. `project_hq.py` - PROJECT_HQ.md Dashboard Manager

Maintains the single source of truth for project status.

```python
from agents.coordinator import ProjectHQManager

hq = ProjectHQManager(Path("AI-Team-Plans/PROJECT_HQ.md"))

# Update dashboard
hq.update_dashboard(tasks)
hq.set_current_focus(task)

# Manage blockers
hq.add_blocker("TASK-001-001", "RALPH_BLOCKED", "Test failure")
hq.resolve_blocker("TASK-001-001")

# Phase management
hq.start_phase(1, "Foundation")
hq.complete_phase(1)

# Add milestone
hq.add_milestone("v1.0", "First release")
```

---

## ADR-003: Autonomous Task Registration

The Coordinator integrates with the WorkQueue to register tasks discovered by Advisors during their analysis.

```python
# In agents/advisor/base_advisor.py
@dataclass
class DiscoveredTask:
    source: str        # "ADR-002", "consultation"
    description: str   # Human-readable
    file: str          # Target file path
    priority: Optional[int] = None
    task_type: Optional[str] = None

@dataclass
class AdvisorDecision:
    # ... other fields ...
    discovered_tasks: List[DiscoveredTask] = field(default_factory=list)
```

```python
# Coordinator handling discovered tasks
from tasks.work_queue import WorkQueue

def process_advisor_decision(coordinator, decision, work_queue):
    result = coordinator.on_advisor_decision(decision, work_queue)

    print(f"Tasks registered: {len(result['tasks_registered'])}")
    print(f"Duplicates skipped: {len(result['duplicates_skipped'])}")

    # Save the queue
    work_queue.save(Path("tasks/work_queue_project.json"))
```

**Event Types**:
- `TASK_DISCOVERED` - New task was registered
- `TASK_DUPLICATE_SKIPPED` - Task fingerprint already exists

---

## ADR Close-Out Process

When all tasks from an ADR are complete, use `on_adr_closed()` to formally close the ADR:

```python
from agents.coordinator import Coordinator, CoordinatorConfig
from pathlib import Path

coordinator = Coordinator(CoordinatorConfig(project_root=Path(".")))

# Close out ADR when all tasks complete
result = coordinator.on_adr_closed(
    Path("AI-Team-Plans/decisions/ADR-003-lambda-cost-controls.md")
)

print(f"ADR closed: {result['adr_id']}")
print(f"Tasks completed: {result['tasks_completed']}")
```

**Close-Out Actions**:

| Step | Action | Target File |
|------|--------|-------------|
| 1 | Verify all tasks complete | `work_queue.json` |
| 2 | Update ADR status | `ADR-XXX.md`: `Approved` → `Complete ✅` |
| 3 | Add completion date | `ADR-XXX.md`: `**Completed**: YYYY-MM-DD` |
| 4 | Check acceptance criteria | `ADR-XXX.md`: `[ ]` → `[x]` |
| 5 | Add completion summary | `ADR-XXX.md`: tasks table |
| 6 | Update ADR index | `ADR-INDEX.md`: status column |
| 7 | Log ADR_CLOSED event | Event logger |

**Error Handling**:
- Raises `ValueError` if any tasks are incomplete
- Skips completion summary if already present (idempotent)
- Safe to call multiple times on same ADR

---

## Configuration

```python
@dataclass
class CoordinatorConfig:
    project_root: Path              # Required: project directory
    max_concurrent_tasks: int = 3   # Max tasks in progress
    max_queue_size: int = 50        # Max pending tasks
    max_tasks_per_adr: int = 20     # Max tasks from single ADR
    scope_escalation_threshold: int = 5  # Files before Advisor escalation
    auto_assign: bool = True        # Auto-assign tasks to Builders
    auto_update_hq: bool = True     # Auto-update PROJECT_HQ.md
    auto_handoff: bool = True       # Auto-create session handoffs
```

---

## Event Types

The Coordinator emits these events (integrate with `orchestration/event_logger.py`):

| Event | Description |
|-------|-------------|
| `ADR_APPROVED` | ADR was approved, triggering task breakdown |
| `ADR_CLOSED` | ADR fully implemented and closed out |
| `TASK_COMPLETED` | Builder finished a task |
| `TASK_BLOCKED` | Task hit a blocker (Ralph BLOCKED) |
| `SESSION_END` | Session ending, handoff created |
| `SCOPE_ESCALATION` | Task touches 5+ files |
| `PHASE_COMPLETE` | All phase tasks done |
| `SESSION_START` | Session resumed/started |
| `TASK_DISCOVERED` | New task from Advisor (ADR-003) |
| `TASK_DUPLICATE_SKIPPED` | Duplicate task fingerprint (ADR-003) |

---

## Governance Contract

See `governance/contracts/coordinator.yaml`:

```yaml
name: coordinator
version: "3.0"
mode: autonomous
autonomy_level: L2.5

allowed_actions:
  - read_adr, read_codebase, read_project_hq
  - create_task, update_task_status, assign_task
  - update_project_hq, update_work_queue
  - create_handoff, create_retrospective
  - log_event, trigger_advisor, notify_builder

forbidden_actions:
  - write_code                    # Builders' job
  - modify_application_files      # Builders' job
  - make_architectural_decisions  # Advisors' job
  - modify_adr                    # ADRs are immutable
  - bypass_dependencies           # Must respect ordering
  - skip_logging                  # All events must be logged
```

---

## Integration with Autonomous Loop

The Coordinator is used by `autonomous_loop.py` for task orchestration:

```python
# In autonomous_loop.py
coordinator = create_coordinator(project_root)

# Resume previous session
summary = coordinator.resume_session()

# Process tasks
for task in work_queue.features:
    if task.status == "pending":
        # Coordinator assigns to Builder
        assigned = coordinator._assign_next_task()

        # Builder executes...

        # On completion
        coordinator.on_task_completed(task.id, result)
```

---

## File Structure

```
agents/coordinator/
├── __init__.py          # Package exports
├── coordinator.py       # Main Coordinator agent
├── task_manager.py      # Task lifecycle management
├── handoff.py           # Session handoffs and retrospectives
├── project_hq.py        # PROJECT_HQ.md management
└── README.md            # This file
```

---

## Related Documentation

- [AI-TEAM-SPEC-V3](../../docs/AI-TEAM/AI-TEAM-SPEC-V3.md) - Full specification
- [Coordinator Contract](../../governance/contracts/coordinator.yaml) - Governance contract
- [ADR-003](../../.claude/plans/) - Autonomous Task Registration
- [WorkQueue](../../tasks/work_queue.py) - Task queue system

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-01-10 | ADR-003 task discovery integration |
| 2.0 | 2026-01-09 | Initial AI-TEAM-SPEC-V3 implementation |
| 1.0 | 2026-01-06 | Original design spec |
