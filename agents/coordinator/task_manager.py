"""
Task Manager for AI Team Coordinator
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Manages work queue, task lifecycle, and persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class TaskStatus(Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Types of tasks the system handles."""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0  # Blocking issues
    HIGH = 1      # Important features/fixes
    MEDIUM = 2    # Normal work
    LOW = 3       # Nice to have


# ═══════════════════════════════════════════════════════════════════════════════
# TASK DATA CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Task:
    """Represents a work item in the queue."""

    id: str
    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING

    # Source and context
    source_adr: Optional[str] = None
    phase: int = 1
    tags: List[str] = field(default_factory=list)

    # Assignment
    assigned_agent: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Files involved
    target_files: List[str] = field(default_factory=list)
    estimated_files: int = 1

    # Completion tracking
    completion_promise: Optional[str] = None
    max_iterations: int = 15
    iterations_used: int = 0

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)

    # Blocking info
    blocked_reason: Optional[str] = None
    blocked_details: Optional[str] = None
    blocked_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    completed_at: Optional[datetime] = None

    # Result
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "source_adr": self.source_adr,
            "phase": self.phase,
            "tags": self.tags,
            "assigned_agent": self.assigned_agent,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "target_files": self.target_files,
            "estimated_files": self.estimated_files,
            "completion_promise": self.completion_promise,
            "max_iterations": self.max_iterations,
            "iterations_used": self.iterations_used,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "blocked_reason": self.blocked_reason,
            "blocked_details": self.blocked_details,
            "blocked_at": self.blocked_at.isoformat() if self.blocked_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary."""
        # Parse enums
        task_type = TaskType(data.get("task_type", "feature"))
        priority = TaskPriority(data.get("priority", 2))
        status = TaskStatus(data.get("status", "pending"))

        # Parse datetimes
        def parse_dt(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val.rstrip("Z"))

        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            task_type=task_type,
            priority=priority,
            status=status,
            source_adr=data.get("source_adr"),
            phase=data.get("phase", 1),
            tags=data.get("tags", []),
            assigned_agent=data.get("assigned_agent"),
            assigned_at=parse_dt(data.get("assigned_at")),
            target_files=data.get("target_files", []),
            estimated_files=data.get("estimated_files", 1),
            completion_promise=data.get("completion_promise"),
            max_iterations=data.get("max_iterations", 15),
            iterations_used=data.get("iterations_used", 0),
            depends_on=data.get("depends_on", []),
            blocks=data.get("blocks", []),
            blocked_reason=data.get("blocked_reason"),
            blocked_details=data.get("blocked_details"),
            blocked_at=parse_dt(data.get("blocked_at")),
            created_at=parse_dt(data.get("created_at")) or utc_now(),
            updated_at=parse_dt(data.get("updated_at")) or utc_now(),
            completed_at=parse_dt(data.get("completed_at")),
            result=data.get("result"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TASK MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class TaskManager:
    """
    Manages the work queue for AI Team Coordinator.

    Responsibilities:
    - Add/remove/update tasks
    - Persist queue to JSON
    - Query tasks by status, phase, priority
    - Track dependencies
    """

    def __init__(self, project_root: Path):
        """
        Initialize TaskManager.

        Args:
            project_root: Path to project root (containing AI-Team-Plans/)
        """
        self.project_root = Path(project_root)
        self.queue_file = self.project_root / "AI-Team-Plans" / "tasks" / "work_queue.json"
        self.tasks: Dict[str, Task] = {}
        self._sequence = 0

        # Load existing queue
        self._load_queue()

    # ───────────────────────────────────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────────────────────────────────

    def add_task(self, task: Task) -> str:
        """
        Add a task to the queue.

        Args:
            task: Task to add

        Returns:
            Task ID
        """
        self.tasks[task.id] = task
        self._persist_queue()
        return task.id

    def create_task(
        self,
        title: str,
        description: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.MEDIUM,
        source_adr: Optional[str] = None,
        phase: int = 1,
        tags: Optional[List[str]] = None,
        target_files: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None,
        completion_promise: Optional[str] = None,
        max_iterations: int = 15,
    ) -> Task:
        """
        Create and add a new task.

        Returns:
            Created Task
        """
        self._sequence += 1
        task_id = f"TASK-{self._sequence:04d}"

        # Infer completion promise if not provided
        if not completion_promise:
            completion_promise = self._infer_completion_promise(task_type)

        task = Task(
            id=task_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            source_adr=source_adr,
            phase=phase,
            tags=tags or [],
            target_files=target_files or [],
            estimated_files=len(target_files) if target_files else 1,
            depends_on=depends_on or [],
            completion_promise=completion_promise,
            max_iterations=max_iterations,
        )

        self.add_task(task)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """
        Update task fields.

        Args:
            task_id: Task to update
            **kwargs: Fields to update

        Returns:
            Updated task or None if not found
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.updated_at = utc_now()
        self._persist_queue()
        return task

    def assign_task(self, task_id: str, agent: str) -> Optional[Task]:
        """
        Assign task to an agent.

        Args:
            task_id: Task to assign
            agent: Agent name

        Returns:
            Updated task or None
        """
        return self.update_task(
            task_id,
            assigned_agent=agent,
            assigned_at=utc_now(),
            status=TaskStatus.ASSIGNED,
        )

    def start_task(self, task_id: str) -> Optional[Task]:
        """Mark task as in progress."""
        return self.update_task(task_id, status=TaskStatus.IN_PROGRESS)

    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        Mark task as completed.

        Args:
            task_id: Task to complete
            result: Optional result data

        Returns:
            Updated task or None
        """
        return self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            completed_at=utc_now(),
            result=result,
        )

    def block_task(
        self,
        task_id: str,
        reason: str,
        details: Optional[str] = None
    ) -> Optional[Task]:
        """
        Mark task as blocked.

        Args:
            task_id: Task to block
            reason: Why it's blocked
            details: Additional details

        Returns:
            Updated task or None
        """
        return self.update_task(
            task_id,
            status=TaskStatus.BLOCKED,
            blocked_reason=reason,
            blocked_details=details,
            blocked_at=utc_now(),
        )

    def unblock_task(self, task_id: str) -> Optional[Task]:
        """Unblock a task, returning it to pending."""
        return self.update_task(
            task_id,
            status=TaskStatus.PENDING,
            blocked_reason=None,
            blocked_details=None,
            blocked_at=None,
        )

    def cancel_task(self, task_id: str, reason: str) -> Optional[Task]:
        """Cancel a task."""
        return self.update_task(
            task_id,
            status=TaskStatus.CANCELLED,
            blocked_reason=reason,
        )

    def increment_iteration(self, task_id: str) -> Optional[Task]:
        """Increment iteration count for a task."""
        task = self.tasks.get(task_id)
        if task:
            return self.update_task(
                task_id,
                iterations_used=task.iterations_used + 1
            )
        return None

    # ───────────────────────────────────────────────────────────────────────────
    # Query Methods
    # ───────────────────────────────────────────────────────────────────────────

    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks, sorted by priority."""
        return sorted(
            [t for t in self.tasks.values() if t.status == TaskStatus.PENDING],
            key=lambda t: (t.priority.value, t.created_at)
        )

    def get_blocked_tasks(self) -> List[Task]:
        """Get all blocked tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED]

    def get_in_progress_tasks(self) -> List[Task]:
        """Get all in-progress tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]

    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]

    def get_tasks_by_phase(self, phase: int) -> List[Task]:
        """Get all tasks for a specific phase."""
        return [t for t in self.tasks.values() if t.phase == phase]

    def get_tasks_by_adr(self, adr_id: str) -> List[Task]:
        """Get all tasks from a specific ADR."""
        return [t for t in self.tasks.values() if t.source_adr == adr_id]

    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to work on.

        A task is ready if:
        - Status is PENDING
        - All dependencies are completed
        """
        completed_ids = {t.id for t in self.get_completed_tasks()}

        ready = []
        for task in self.get_pending_tasks():
            if all(dep in completed_ids for dep in task.depends_on):
                ready.append(task)

        return ready

    def get_next_task(self) -> Optional[Task]:
        """
        Get the next task to work on.

        Returns highest priority ready task.
        """
        ready = self.get_ready_tasks()
        return ready[0] if ready else None

    # ───────────────────────────────────────────────────────────────────────────
    # Statistics
    # ───────────────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        all_tasks = list(self.tasks.values())

        by_status = {}
        for status in TaskStatus:
            by_status[status.value] = len([
                t for t in all_tasks if t.status == status
            ])

        by_type = {}
        for task_type in TaskType:
            by_type[task_type.value] = len([
                t for t in all_tasks if t.task_type == task_type
            ])

        completed = self.get_completed_tasks()
        total_iterations = sum(t.iterations_used for t in completed)
        avg_iterations = total_iterations / len(completed) if completed else 0

        return {
            "total": len(all_tasks),
            "by_status": by_status,
            "by_type": by_type,
            "total_iterations": total_iterations,
            "avg_iterations": round(avg_iterations, 2),
        }

    def get_phase_progress(self, phase: int) -> Dict[str, Any]:
        """Get progress for a specific phase."""
        phase_tasks = self.get_tasks_by_phase(phase)

        completed = len([t for t in phase_tasks if t.status == TaskStatus.COMPLETED])
        blocked = len([t for t in phase_tasks if t.status == TaskStatus.BLOCKED])
        pending = len([t for t in phase_tasks if t.status == TaskStatus.PENDING])
        in_progress = len([t for t in phase_tasks if t.status == TaskStatus.IN_PROGRESS])

        return {
            "phase": phase,
            "total": len(phase_tasks),
            "completed": completed,
            "blocked": blocked,
            "pending": pending,
            "in_progress": in_progress,
            "completion_rate": round(completed / len(phase_tasks) * 100, 1) if phase_tasks else 0,
        }

    # ───────────────────────────────────────────────────────────────────────────
    # Internal Methods
    # ───────────────────────────────────────────────────────────────────────────

    def _infer_completion_promise(self, task_type: TaskType) -> str:
        """Infer completion promise from task type."""
        promises = {
            TaskType.FEATURE: "FEATURE_COMPLETE",
            TaskType.BUGFIX: "BUGFIX_COMPLETE",
            TaskType.REFACTOR: "REFACTOR_COMPLETE",
            TaskType.TEST: "TESTS_COMPLETE",
            TaskType.DOCUMENTATION: "DOCS_COMPLETE",
            TaskType.INFRASTRUCTURE: "INFRA_COMPLETE",
        }
        return promises.get(task_type, "TASK_COMPLETE")

    def _load_queue(self) -> None:
        """Load queue from JSON file."""
        if not self.queue_file.exists():
            return

        try:
            with open(self.queue_file, "r") as f:
                data = json.load(f)

            self._sequence = data.get("sequence", 0)

            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                self.tasks[task.id] = task

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load queue: {e}")

    def _persist_queue(self) -> None:
        """Save queue to JSON file."""
        # Ensure directory exists
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "3.0",
            "project": self.project_root.name,
            "generated_at": utc_now().isoformat(),
            "sequence": self._sequence,
            "stats": self.get_stats(),
            "tasks": [t.to_dict() for t in self.tasks.values()],
        }

        with open(self.queue_file, "w") as f:
            json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python task_manager.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    manager = TaskManager(project_root)

    # Create a test task
    task = manager.create_task(
        title="Test Task",
        description="A test task for demonstration",
        task_type=TaskType.FEATURE,
        priority=TaskPriority.MEDIUM,
        phase=1,
        tags=["test"],
    )

    print(f"Created task: {task.id}")
    print(f"Stats: {json.dumps(manager.get_stats(), indent=2)}")
