"""
BaseProjectManager - Framework-level Project Manager Agent

Coordinates single-project execution:
- Takes project specification from Program Manager/Business Architect
- Breaks down into epics, features, and tasks
- Assigns tasks to Feature Builder, Bug Fixer, Test Writer, Code Quality agents
- Creates work queue and task dependencies
- Tracks progress and manages blockers
- Reports project status

This is a COORDINATION agent (not EXECUTION agent):
- Generates work queues (not code)
- Plans projects (not executes features)
- Manages dependencies (not writes tests)

Autonomy Level: L2
- Reports to: Program Manager / Engineering Manager
- Authority: Task assignment, sprint planning, escalation
- Authority: Cannot commit code, only queue work for execution agents

Completion Signal: PROJECT_PLAN_COMPLETE
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import json

from agents.base import BaseAgent, AgentConfig


@dataclass
class Task:
    """Single task to be assigned to an agent."""
    task_id: str                      # e.g., "TASK-001"
    title: str                         # e.g., "Build authentication API"
    description: str                   # Detailed requirements
    epic_id: str                      # Which epic this belongs to
    assigned_to: str                  # Agent type: "feature_builder", "test_writer", etc.
    estimated_days: float             # How long this should take
    priority: str                     # "critical", "high", "medium", "low"
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    status: str = "pending"           # "pending", "in_progress", "blocked", "completed"
    completion_signal: Optional[str] = None  # e.g., "FEATURE_COMPLETE", "TESTS_COMPLETE"
    blocked_by: Optional[str] = None  # If blocked, why
    notes: str = ""                   # Additional context


@dataclass
class Epic:
    """Collection of related features/fixes."""
    epic_id: str                      # e.g., "EPIC-001"
    title: str                         # e.g., "Authentication System"
    description: str
    tasks: List[Task] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    owner: str = ""                   # Lead engineer/epic owner
    status: str = "pending"           # "pending", "in_progress", "blocked", "completed"


@dataclass
class ProjectSpecification:
    """Input from Business Architect or Program Manager."""
    project_id: str
    project_name: str                 # e.g., "Patient Portal"
    description: str
    business_requirements: Dict[str, Any]
    technical_requirements: Dict[str, Any]
    constraints: Dict[str, str]       # "timeline", "budget", "team_size", etc.
    success_criteria: List[str]
    key_milestones: List[Dict[str, str]]  # date, description
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkQueueItem:
    """Task formatted for agent work queue."""
    task_id: str
    agent_type: str                   # "feature_builder", "test_writer", etc.
    title: str
    description: str
    completion_signal: str
    max_iterations: int
    dependencies: List[str]
    files_to_modify: List[str] = field(default_factory=list)
    tests_required: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)


class BaseProjectManager(BaseAgent):
    """
    Base framework for Project Manager agents.

    Projects extend this with domain-specific task assignment logic:
    - HealthcareProjectManager: HIPAA-aware task management
    - EcommerceProjectManager: Payment-aware task management
    - etc.

    Workflow:
    1. receive_project_spec(spec) - Get project from Business Architect
    2. break_down_into_epics() - Create epics from requirements
    3. break_epics_into_tasks() - Create individual tasks
    4. assign_to_agents() - Assign each task to appropriate agent
    5. create_work_queue() - Generate executable work queue
    6. validate_dependencies() - Verify task ordering
    7. execute() - Main entry point that orchestrates above
    """

    def __init__(self, adapter, config: AgentConfig):
        """Initialize Project Manager with adapter and config."""
        self.adapter = adapter
        self.config = config
        self.project_spec: Optional[ProjectSpecification] = None
        self.epics: Dict[str, Epic] = {}
        self.tasks: Dict[str, Task] = {}
        self.work_queue: List[WorkQueueItem] = []
        self.current_iteration = 0
        self.iteration_history = []
        self.audit_log: List[Dict[str, Any]] = []
        self.blockers: List[Dict[str, str]] = []

    def execute(self, task_id: str) -> dict[str, Any]:
        """
        Main entry point: execute project planning workflow.

        Args:
            task_id: Project task ID (e.g., "PROJECT-001")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - work_queue: Executable tasks for other agents
            - epics: Project breakdown by epic
            - tasks: All individual tasks
            - timeline: Estimated timeline
            - blockers: Any issues encountered
        """
        self._log_action(f"Project Manager starting execution for {task_id}")

        try:
            # Step 1: Load project specification
            project_spec = self._load_project_specification(task_id)
            if not project_spec:
                return self._failed("Could not load project specification")

            self.project_spec = project_spec

            # Step 2: Break down into epics
            self._log_action("Breaking down project into epics")
            self._break_down_into_epics()

            # Step 3: Break epics into tasks
            self._log_action("Breaking down epics into individual tasks")
            self._break_epics_into_tasks()

            # Step 4: Assign tasks to agents
            self._log_action("Assigning tasks to agents")
            self._assign_to_agents()

            # Step 5: Create work queue
            self._log_action("Creating work queue for execution")
            self.work_queue = self._create_work_queue()

            # Step 6: Validate dependencies
            self._log_action("Validating task dependencies and ordering")
            blocking_issues = self._validate_dependencies()
            if blocking_issues:
                self.blockers.extend(blocking_issues)

            # Step 7: Generate timeline
            timeline = self._generate_timeline()

            # Step 8: Prepare result
            result = {
                "status": "blocked" if self.blockers else "completed",
                "task_id": task_id,
                "project_id": self.project_spec.project_id,
                "epics": {eid: self._epic_to_dict(e) for eid, e in self.epics.items()},
                "tasks": {tid: self._task_to_dict(t) for tid, t in self.tasks.items()},
                "work_queue": [self._workqueue_to_dict(wq) for wq in self.work_queue],
                "timeline": timeline,
                "blockers": self.blockers,
                "audit_log": self.audit_log,
                "accomplished": [
                    f"Created {len(self.epics)} epics",
                    f"Created {len(self.tasks)} tasks",
                    f"Generated work queue with {len(self.work_queue)} items",
                ],
                "handoff_notes": f"Project {self.project_spec.project_name} planned and ready for execution"
            }

            # Add completion signal if no blockers
            if not self.blockers:
                result["completion_signal"] = f"<promise>{self.config.expected_completion_signal}</promise>"

            self._log_action("Project Manager planning completed")
            return result

        except Exception as e:
            self._log_action(f"ERROR: {str(e)}")
            return self._failed(f"Project planning failed: {str(e)}")

    def checkpoint(self) -> dict[str, Any]:
        """Capture state for resume capability."""
        return {
            "project_id": self.project_spec.project_id if self.project_spec else None,
            "epics": {eid: self._epic_to_dict(e) for eid, e in self.epics.items()},
            "tasks": {tid: self._task_to_dict(t) for tid, t in self.tasks.items()},
            "work_queue": [self._workqueue_to_dict(wq) for wq in self.work_queue],
            "blockers": self.blockers,
            "current_iteration": self.current_iteration,
            "iteration_history": self.iteration_history,
            "audit_log": self.audit_log,
        }

    def halt(self, reason: str) -> None:
        """Graceful halt on error or violation."""
        self._log_action(f"HALTING: {reason}")

    # ─────────────────────────────────────────────────────────────────
    # Core Workflow Methods (override in subclasses for customization)
    # ─────────────────────────────────────────────────────────────────

    def _load_project_specification(self, task_id: str) -> Optional[ProjectSpecification]:
        """
        Load project specification from requirements document.

        Override in subclasses to load from domain-specific sources.
        """
        # This would normally load from a specification document
        # For now, return a placeholder
        return ProjectSpecification(
            project_id=task_id,
            project_name="Sample Project",
            description="Sample project for testing",
            business_requirements={},
            technical_requirements={},
            constraints={},
            success_criteria=[],
            key_milestones=[]
        )

    def _break_down_into_epics(self) -> None:
        """
        Break project into major epics (2-4 week chunks).

        Framework version creates basic structure.
        Subclasses override to create domain-specific epics.
        """
        if not self.project_spec:
            return

        # Default: create one epic per key milestone
        for i, milestone in enumerate(self.project_spec.key_milestones):
            epic_id = f"EPIC-{i+1:03d}"
            self.epics[epic_id] = Epic(
                epic_id=epic_id,
                title=milestone.get("description", f"Milestone {i+1}"),
                description=f"Work for milestone: {milestone}",
                start_date=milestone.get("date"),
                owner="TBD"
            )

    def _break_epics_into_tasks(self) -> None:
        """
        Break each epic into individual tasks (1-3 day tasks).

        Framework version creates placeholder tasks.
        Subclasses override to create domain-specific task breakdown.
        """
        task_counter = 1

        for epic_id, epic in self.epics.items():
            # Create sample tasks for each epic
            for i in range(3):  # 3 tasks per epic by default
                task_id = f"TASK-{task_counter:03d}"
                task_counter += 1

                task = Task(
                    task_id=task_id,
                    title=f"{epic.title} - Component {i+1}",
                    description=f"Implement component {i+1} for {epic.title}",
                    epic_id=epic_id,
                    assigned_to="feature_builder",  # Default assignment
                    estimated_days=1.0,
                    priority="high"
                )
                self.tasks[task_id] = task
                epic.tasks.append(task)

    def _assign_to_agents(self) -> None:
        """
        Assign tasks to appropriate agent types.

        Factors:
        - Task type (feature, bug fix, test, quality)
        - Task complexity
        - Domain requirements

        Framework version uses simple heuristic.
        Subclasses override for domain-specific assignment logic.
        """
        agent_assignments = {
            "feature": "feature_builder",
            "test": "test_writer",
            "bug": "bug_fixer",
            "quality": "code_quality",
            "refactor": "feature_builder",
        }

        for task in self.tasks.values():
            # Determine agent type based on task title
            task_type = next(
                (key for key in agent_assignments if key in task.title.lower()),
                "feature_builder"
            )
            task.assigned_to = agent_assignments[task_type]

            # Set completion signal based on agent type
            signal_map = {
                "feature_builder": "FEATURE_COMPLETE",
                "test_writer": "TESTS_COMPLETE",
                "bug_fixer": "BUGFIX_COMPLETE",
                "code_quality": "CODEQUALITY_COMPLETE",
            }
            task.completion_signal = signal_map.get(task.assigned_to, "COMPLETE")

    def _create_work_queue(self) -> List[WorkQueueItem]:
        """
        Create work queue items for execution agents.

        This is what other agents will execute on.
        """
        work_queue = []

        for task in self.tasks.values():
            iteration_budgets = {
                "feature_builder": 50,
                "test_writer": 15,
                "bug_fixer": 15,
                "code_quality": 20,
            }

            wq_item = WorkQueueItem(
                task_id=task.task_id,
                agent_type=task.assigned_to,
                title=task.title,
                description=task.description,
                completion_signal=task.completion_signal or "COMPLETE",
                max_iterations=iteration_budgets.get(task.assigned_to, 10),
                dependencies=task.dependencies,
                success_criteria=[f"Implement {task.title}"]
            )
            work_queue.append(wq_item)

        return work_queue

    def _validate_dependencies(self) -> List[Dict[str, str]]:
        """
        Validate task dependencies and detect issues.

        Returns list of blocking issues found.
        """
        blockers = []

        # Check for circular dependencies
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                dep_task = self.tasks.get(dep_id)
                if dep_task and task_id in dep_task.dependencies:
                    blockers.append({
                        "type": "circular_dependency",
                        "tasks": [task_id, dep_id],
                        "severity": "high"
                    })

        # Check for missing dependencies
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    blockers.append({
                        "type": "missing_dependency",
                        "task": task_id,
                        "missing_task": dep_id,
                        "severity": "high"
                    })

        return blockers

    def _generate_timeline(self) -> Dict[str, Any]:
        """Generate project timeline from task estimates."""
        total_days = sum(t.estimated_days for t in self.tasks.values())
        start_date = datetime.now()
        end_date = start_date + timedelta(days=total_days)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_estimated_days": total_days,
            "number_of_tasks": len(self.tasks),
            "number_of_epics": len(self.epics),
            "tasks_per_epic": len(self.tasks) / len(self.epics) if self.epics else 0,
        }

    # ─────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────

    def _epic_to_dict(self, epic: Epic) -> dict:
        """Convert epic to serializable dict."""
        return {
            "epic_id": epic.epic_id,
            "title": epic.title,
            "description": epic.description,
            "start_date": epic.start_date,
            "end_date": epic.end_date,
            "owner": epic.owner,
            "status": epic.status,
            "task_count": len(epic.tasks),
        }

    def _task_to_dict(self, task: Task) -> dict:
        """Convert task to serializable dict."""
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "epic_id": task.epic_id,
            "assigned_to": task.assigned_to,
            "estimated_days": task.estimated_days,
            "priority": task.priority,
            "dependencies": task.dependencies,
            "status": task.status,
            "completion_signal": task.completion_signal,
            "blocked_by": task.blocked_by,
            "notes": task.notes,
        }

    def _workqueue_to_dict(self, wq: WorkQueueItem) -> dict:
        """Convert work queue item to serializable dict."""
        return {
            "task_id": wq.task_id,
            "agent_type": wq.agent_type,
            "title": wq.title,
            "description": wq.description,
            "completion_signal": wq.completion_signal,
            "max_iterations": wq.max_iterations,
            "dependencies": wq.dependencies,
            "files_to_modify": wq.files_to_modify,
            "tests_required": wq.tests_required,
            "success_criteria": wq.success_criteria,
        }

    def _log_action(self, message: str) -> None:
        """Log action to audit trail."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": message
        })

    def _failed(self, reason: str) -> dict[str, Any]:
        """Return failed result."""
        return {
            "status": "failed",
            "error": reason,
            "audit_log": self.audit_log,
            "accomplished": [],
            "incomplete": [reason],
        }
