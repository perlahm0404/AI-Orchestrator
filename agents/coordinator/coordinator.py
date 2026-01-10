"""
Coordinator Agent
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

The Coordinator is the autonomous orchestration agent that:
- Reads approved ADRs and breaks them into tasks
- Manages the work queue
- Assigns tasks to appropriate Builders
- Auto-updates PROJECT_HQ.md
- Creates session handoffs
- Triggers Advisors on 5+ file escalation
- Detects phase completion and generates retrospectives
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import re

from .task_manager import TaskManager, Task, TaskStatus, TaskType
from .project_hq import ProjectHQManager
from .handoff import HandoffGenerator

# ADR-003: Import for autonomous task registration
from tasks.work_queue import WorkQueue


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class CoordinatorEvent(Enum):
    """Events that trigger Coordinator actions."""
    ADR_APPROVED = "adr_approved"
    ADR_CLOSED = "adr_closed"  # ADR fully implemented and closed out
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    SESSION_END = "session_end"
    SCOPE_ESCALATION = "scope_escalation"
    PHASE_COMPLETE = "phase_complete"
    SESSION_START = "session_start"
    # ADR-003: Task discovery events
    TASK_DISCOVERED = "task_discovered"
    TASK_DUPLICATE_SKIPPED = "task_duplicate_skipped"


@dataclass
class CoordinatorConfig:
    """Configuration for Coordinator agent."""
    project_root: Path
    max_concurrent_tasks: int = 3
    max_queue_size: int = 50
    max_tasks_per_adr: int = 20
    scope_escalation_threshold: int = 5
    auto_assign: bool = True
    auto_update_hq: bool = True
    auto_handoff: bool = True


@dataclass
class ADR:
    """Represents an Architecture Decision Record."""
    id: str
    number: int
    title: str
    status: str
    advisor: str
    tags: List[str] = field(default_factory=list)
    applies_to: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    implementation_notes: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[Path] = None

    @classmethod
    def from_file(cls, file_path: Path) -> "ADR":
        """Parse ADR from markdown file."""
        content = file_path.read_text()

        # Extract ADR number from filename (ADR-XXX-title.md)
        match = re.match(r"ADR-(\d+)", file_path.stem)
        number = int(match.group(1)) if match else 0

        # Extract ID
        adr_id = file_path.stem

        # Extract title from first heading
        title_match = re.search(r"^#\s+ADR-\d+:\s*(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else file_path.stem

        # Extract status
        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
        status = status_match.group(1).lower() if status_match else "draft"

        # Extract advisor
        advisor_match = re.search(r"\*\*Advisor\*\*:\s*([\w-]+)", content)
        advisor = advisor_match.group(1) if advisor_match else "unknown"

        # Extract tags from YAML block
        tags = []
        tags_match = re.search(r"tags:\s*\[([^\]]+)\]", content)
        if tags_match:
            tags = [t.strip().strip("'\"") for t in tags_match.group(1).split(",")]

        # Extract applies_to patterns
        applies_to = []
        applies_match = re.search(r"applies_to:\s*\n((?:\s+-\s*.+\n)+)", content)
        if applies_match:
            applies_to = [
                line.strip().lstrip("- ").strip("'\"")
                for line in applies_match.group(1).strip().split("\n")
            ]

        # Extract domains
        domains = []
        domains_match = re.search(r"domains:\s*\[([^\]]+)\]", content)
        if domains_match:
            domains = [d.strip().strip("'\"") for d in domains_match.group(1).split(",")]

        # Extract implementation notes section
        impl_notes = {}
        impl_section = re.search(
            r"## Implementation Notes\s*\n(.*?)(?=\n##|\n---|\Z)",
            content,
            re.DOTALL
        )
        if impl_section:
            impl_content = impl_section.group(1)

            # Check for schema changes
            if re.search(r"schema|migration|table|column", impl_content, re.IGNORECASE):
                impl_notes["has_schema_changes"] = True

            # Check for API changes
            if re.search(r"api|endpoint|route", impl_content, re.IGNORECASE):
                impl_notes["has_api_changes"] = True
                api_desc = re.search(r"### API Changes\s*\n(.+?)(?=\n###|\Z)", impl_content, re.DOTALL)
                if api_desc:
                    impl_notes["api_description"] = api_desc.group(1).strip()

            # Check for UI changes
            if re.search(r"ui|component|interface|screen", impl_content, re.IGNORECASE):
                impl_notes["has_ui_changes"] = True
                ui_desc = re.search(r"### UI Changes\s*\n(.+?)(?=\n###|\Z)", impl_content, re.DOTALL)
                if ui_desc:
                    impl_notes["ui_description"] = ui_desc.group(1).strip()

            # Extract estimated files
            files_match = re.search(r"Files to modify:\s*(\d+)", impl_content)
            if files_match:
                impl_notes["estimated_files"] = int(files_match.group(1))

        return cls(
            id=adr_id,
            number=number,
            title=title,
            status=status,
            advisor=advisor,
            tags=tags,
            applies_to=applies_to,
            domains=domains,
            implementation_notes=impl_notes,
            file_path=file_path,
        )


class Coordinator:
    """
    Coordinator agent for AI Team orchestration.

    Manages the flow from ADR approval through task execution,
    maintaining PROJECT_HQ.md and creating session handoffs.
    """

    def __init__(self, config: CoordinatorConfig):
        """
        Initialize Coordinator.

        Args:
            config: Coordinator configuration
        """
        self.config = config
        self.project_root = Path(config.project_root)
        self.ai_team_dir = self.project_root / "AI-Team-Plans"

        # Initialize sub-managers
        self.task_manager = TaskManager(self.ai_team_dir / "tasks" / "work_queue.json")
        self.hq_manager = ProjectHQManager(self.ai_team_dir / "PROJECT_HQ.md")
        self.handoff_generator = HandoffGenerator(self.ai_team_dir / "sessions")

        # Event handlers
        self._event_handlers: Dict[CoordinatorEvent, List[Callable]] = {
            event: [] for event in CoordinatorEvent
        }

        # Session state
        self.session_id = f"session-{utc_now().strftime('%Y-%m-%d-%H%M%S')}"
        self.session_start = utc_now()
        self.events_logged = 0

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════════

    def on_adr_approved(self, adr_path: Path) -> List[Task]:
        """
        Handle ADR approval event.

        Parses the ADR, breaks it into tasks, and adds to queue.

        Args:
            adr_path: Path to approved ADR file

        Returns:
            List of created tasks
        """
        # Parse ADR
        adr = ADR.from_file(adr_path)

        # Break into tasks
        tasks = self._break_into_tasks(adr)

        # Add to queue
        for task in tasks:
            self.task_manager.add_task(task)

        # Update PROJECT_HQ
        if self.config.auto_update_hq:
            self.hq_manager.add_decision(adr)
            self.hq_manager.update_dashboard(self.task_manager.get_all_tasks())
            self.hq_manager.update_roadmap(adr)

        # Log event
        self._log_event("COORDINATOR_TASK_CREATED", {
            "adr": adr.id,
            "tasks_created": len(tasks),
            "task_ids": [t.id for t in tasks],
        })

        # Auto-assign first task if enabled
        if self.config.auto_assign:
            self._assign_next_task()

        return tasks

    def on_task_completed(self, task_id: str, result: Dict[str, Any]) -> Optional[Task]:
        """
        Handle task completion event.

        Args:
            task_id: ID of completed task
            result: Result from Builder

        Returns:
            Next assigned task, if any
        """
        # Mark task complete
        task = self.task_manager.get_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = utc_now()
            task.iterations = result.get("iterations", 0)
            self.task_manager.update_task(task)

        # Update PROJECT_HQ
        if self.config.auto_update_hq:
            self.hq_manager.update_dashboard(self.task_manager.get_all_tasks())
            self.hq_manager.update_stats(self.task_manager.get_summary())

        # Log event
        self._log_event("BUILDER_COMPLETED", {
            "task_id": task_id,
            "iterations": result.get("iterations", 0),
            "agent": task.agent if task else "unknown",
        })

        # Check phase completion
        if self._check_phase_complete():
            self._on_phase_complete()

        # Assign next task
        if self.config.auto_assign:
            return self._assign_next_task(exclude=task_id)

        return None

    def on_task_blocked(self, task_id: str, reason: str, details: str) -> None:
        """
        Handle task blocked event.

        Args:
            task_id: ID of blocked task
            reason: Why task is blocked
            details: Additional details
        """
        # Mark task blocked
        task = self.task_manager.get_task(task_id)
        if task:
            task.status = TaskStatus.BLOCKED
            task.blocked_at = utc_now()
            task.blocked_reason = reason
            self.task_manager.update_task(task)

        # Update PROJECT_HQ blockers section
        if self.config.auto_update_hq:
            self.hq_manager.add_blocker(task_id, reason, details)
            self.hq_manager.update_dashboard(self.task_manager.get_all_tasks())

        # Log event
        self._log_event("BUILDER_BLOCKED", {
            "task_id": task_id,
            "reason": reason,
            "details": details,
        })

        # Continue with other tasks
        if self.config.auto_assign:
            self._assign_next_task(exclude=task_id)

    def on_session_end(self) -> Path:
        """
        Handle session end event.

        Creates handoff document and updates PROJECT_HQ.

        Returns:
            Path to created handoff file
        """
        # Gather session state
        state = {
            "session_id": self.session_id,
            "duration": str(utc_now() - self.session_start),
            "completed_tasks": self.task_manager.get_tasks_by_status(TaskStatus.COMPLETED),
            "in_progress_tasks": self.task_manager.get_tasks_by_status(TaskStatus.IN_PROGRESS),
            "blocked_tasks": self.task_manager.get_tasks_by_status(TaskStatus.BLOCKED),
            "pending_tasks": self.task_manager.get_tasks_by_status(TaskStatus.PENDING),
        }

        # Create handoff
        handoff_path = self.handoff_generator.create_handoff(state)

        # Update PROJECT_HQ
        if self.config.auto_update_hq:
            self.hq_manager.add_session(self.session_id, handoff_path)
            self.hq_manager.update_stats(self.task_manager.get_summary())

        # Log event
        self._log_event("COORDINATOR_HANDOFF_CREATED", {
            "session_id": self.session_id,
            "handoff_path": str(handoff_path),
            "tasks_completed": len(state["completed_tasks"]),
        })

        # Persist queue state
        self.task_manager.save()

        return handoff_path

    def on_adr_closed(self, adr_path: Path) -> Dict[str, Any]:
        """
        Handle ADR close-out when all tasks are complete.

        This method:
        1. Verifies all tasks from the ADR are complete
        2. Updates ADR status to "Complete ✅"
        3. Checks acceptance criteria boxes
        4. Adds completion summary
        5. Updates ADR-INDEX.md
        6. Logs the ADR_CLOSED event

        Args:
            adr_path: Path to ADR file to close out

        Returns:
            Close-out result with status and details

        Raises:
            ValueError: If ADR has incomplete tasks
        """
        # Parse ADR
        adr = ADR.from_file(adr_path)

        # Get all tasks for this ADR
        all_tasks = self.task_manager.get_all_tasks()
        adr_tasks = [t for t in all_tasks if t.adr == adr.id]

        # Verify all tasks are complete
        incomplete = [t for t in adr_tasks if t.status != TaskStatus.COMPLETED]
        if incomplete:
            incomplete_ids = [t.id for t in incomplete]
            raise ValueError(
                f"Cannot close ADR {adr.id}: {len(incomplete)} tasks incomplete: {incomplete_ids}"
            )

        # Update ADR file
        updated_content = self._update_adr_for_close(adr_path, adr, adr_tasks)

        # Update ADR-INDEX.md
        self._update_adr_index(adr)

        # Log event
        self._log_event("ADR_CLOSED", {
            "adr_id": adr.id,
            "adr_number": adr.number,
            "title": adr.title,
            "tasks_completed": len(adr_tasks),
            "completed_at": utc_now().isoformat(),
        })

        # Update PROJECT_HQ if enabled
        if self.config.auto_update_hq:
            self.hq_manager.update_stats(self.task_manager.get_summary())

        return {
            "status": "closed",
            "adr_id": adr.id,
            "adr_number": adr.number,
            "title": adr.title,
            "tasks_completed": len(adr_tasks),
            "task_ids": [t.id for t in adr_tasks],
            "completed_at": utc_now().isoformat(),
            "adr_path": str(adr_path),
        }

    def _update_adr_for_close(
        self,
        adr_path: Path,
        adr: ADR,
        tasks: List[Task]
    ) -> str:
        """
        Update ADR file for close-out.

        Updates:
        - Status: "Approved" → "Complete ✅"
        - Adds "Completed" date
        - Checks acceptance criteria boxes
        - Adds completion summary section

        Args:
            adr_path: Path to ADR file
            adr: Parsed ADR object
            tasks: Completed tasks for this ADR

        Returns:
            Updated file content
        """
        content = adr_path.read_text()

        # Update status
        content = re.sub(
            r'\*\*Status\*\*:\s*\w+',
            '**Status**: Complete ✅',
            content
        )

        # Add completed date if not present
        if '**Completed**:' not in content:
            content = re.sub(
                r'(\*\*Status\*\*: Complete ✅)',
                f'\\1\n**Completed**: {utc_now().strftime("%Y-%m-%d")}',
                content
            )

        # Check acceptance criteria boxes
        content = re.sub(r'- \[ \]', '- [x]', content)

        # Add completion summary if not present
        if '## Completion Summary' not in content:
            # Find where to insert (before References section if exists)
            completion_summary = self._generate_completion_summary(adr, tasks)

            if '## References' in content:
                content = content.replace(
                    '## References',
                    f'{completion_summary}\n\n## References'
                )
            else:
                content += f'\n\n{completion_summary}'

        # Write updated content
        adr_path.write_text(content)

        return content

    def _generate_completion_summary(self, adr: ADR, tasks: List[Task]) -> str:
        """Generate completion summary section for ADR."""
        lines = [
            "## Completion Summary",
            "",
            f"**All {len(tasks)} tasks completed on {utc_now().strftime('%Y-%m-%d')}**",
            "",
        ]

        # Group tasks by phase
        phases: Dict[int, List[Task]] = {}
        for task in tasks:
            phase = getattr(task, 'phase', 1)
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(task)

        # Generate table for each phase
        for phase_num in sorted(phases.keys()):
            phase_tasks = phases[phase_num]
            lines.append(f"### Phase {phase_num}")
            lines.append("| Task | Title | Agent | Iterations |")
            lines.append("|------|-------|-------|------------|")

            for task in phase_tasks:
                iterations = getattr(task, 'iterations', 'N/A')
                lines.append(f"| {task.id} | {task.title} | {task.agent} | {iterations} |")

            lines.append("")

        return '\n'.join(lines)

    def _update_adr_index(self, adr: ADR) -> None:
        """
        Update ADR-INDEX.md to mark ADR as complete.

        Args:
            adr: ADR to mark as complete
        """
        index_path = self.ai_team_dir / "ADR-INDEX.md"
        if not index_path.exists():
            return

        content = index_path.read_text()

        # Update Last Updated timestamp
        content = re.sub(
            r'\*\*Last Updated\*\*:\s*[\w\d\-:TZ]+',
            f'**Last Updated**: {utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")}',
            content
        )

        # Update status in main registry table (handle various status words)
        # Match: | ADR-XXX | ... | approved/pending/draft | ...
        pattern = rf'(\|\s*ADR-{adr.number:03d}\s*\|[^|]+\|[^|]+\|)\s*\w+\s*(\|)'
        content = re.sub(pattern, r'\1 ✅ complete \2', content)

        # Update status in By Project section
        pattern = rf'(\|\s*ADR-{adr.number:03d}\s*\|[^|]+\|)\s*\w+\s*(\|)'
        content = re.sub(pattern, r'\1 ✅ complete \2', content)

        # Write updated content
        index_path.write_text(content)

    def on_scope_escalation(
        self,
        task: Task,
        estimated_files: int,
        advisor_callback: Callable
    ) -> Dict[str, Any]:
        """
        Handle scope escalation (5+ files).

        Args:
            task: Task that triggered escalation
            estimated_files: Number of files to be touched
            advisor_callback: Function to call Advisor

        Returns:
            Escalation result
        """
        # Log event
        self._log_event("SCOPE_ESCALATION", {
            "task_id": task.id,
            "estimated_files": estimated_files,
            "threshold": self.config.scope_escalation_threshold,
        })

        # Determine advisor type from task
        advisor_type = self._infer_advisor_type(task)

        # Request advisor consultation
        response = advisor_callback(
            advisor_type=advisor_type,
            task=task,
            question="Should this task be broken into smaller pieces?",
        )

        # Handle response
        if response.get("recommendation") == "SPLIT_TASK":
            # Replace task with subtasks
            self.task_manager.remove_task(task.id)
            new_tasks = []
            for subtask_data in response.get("suggested_tasks", []):
                subtask = Task(**subtask_data)
                self.task_manager.add_task(subtask)
                new_tasks.append(subtask)

            return {"action": "SPLIT", "new_tasks": new_tasks}

        elif response.get("recommendation") == "PROCEED":
            return {"action": "PROCEED", "guidance": response.get("guidance")}

        else:
            # Needs human decision
            self.on_task_blocked(
                task.id,
                "SCOPE_ESCALATION",
                f"Task touches {estimated_files} files. Advisor recommends human review."
            )
            return {"action": "ESCALATE_HUMAN", "options": response.get("options")}

    def on_advisor_decision(
        self,
        decision: Any,  # AdvisorDecision from agents.advisor.base_advisor
        work_queue: WorkQueue,
    ) -> Dict[str, Any]:
        """
        Handle advisor decision and register discovered tasks (ADR-003).

        When advisors analyze questions, they may discover issues that warrant
        new tasks. This method registers those tasks in the work queue.

        Args:
            decision: AdvisorDecision with discovered_tasks list
            work_queue: WorkQueue instance to register tasks into

        Returns:
            Summary of registered tasks
        """
        results = {
            "tasks_registered": [],
            "duplicates_skipped": [],
        }

        # Check if decision has discovered_tasks
        if not hasattr(decision, 'discovered_tasks') or not decision.discovered_tasks:
            return results

        # Register each discovered task
        for discovered in decision.discovered_tasks:
            task_id = work_queue.register_discovered_task(
                source=discovered.source,
                description=discovered.description,
                file=discovered.file,
                discovered_by=decision.advisor,
                priority=discovered.priority,
                task_type=discovered.task_type,
            )

            if task_id:
                # Task was registered successfully
                results["tasks_registered"].append({
                    "task_id": task_id,
                    "source": discovered.source,
                    "file": discovered.file,
                })

                # Log event
                self._log_event("TASK_DISCOVERED", {
                    "task_id": task_id,
                    "source": discovered.source,
                    "file": discovered.file,
                    "discovered_by": decision.advisor,
                    "description": discovered.description[:100],
                })
            else:
                # Task was duplicate
                results["duplicates_skipped"].append({
                    "file": discovered.file,
                    "description": discovered.description[:50],
                })

                # Log event
                self._log_event("TASK_DUPLICATE_SKIPPED", {
                    "file": discovered.file,
                    "discovered_by": decision.advisor,
                })

        # Save updated queue if any tasks were registered
        if results["tasks_registered"]:
            # Note: Caller is responsible for saving the queue
            pass

        return results

    def resume_session(self) -> Dict[str, Any]:
        """
        Resume from previous session.

        Returns:
            Session state summary
        """
        # Load work queue
        self.task_manager.load()

        # Get current state
        summary = self.task_manager.get_summary()

        # Update session ID
        self.session_id = f"session-{utc_now().strftime('%Y-%m-%d-%H%M%S')}"
        self.session_start = utc_now()

        # Log event
        self._log_event("SESSION_START", {
            "session_id": self.session_id,
            "pending_tasks": summary["pending"],
            "in_progress_tasks": summary["in_progress"],
            "blocked_tasks": summary["blocked"],
        })

        return summary

    # ═══════════════════════════════════════════════════════════════════════════
    # INTERNAL METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _break_into_tasks(self, adr: ADR) -> List[Task]:
        """Break an ADR into executable tasks."""
        tasks = []
        impl = adr.implementation_notes
        task_seq = 1

        # Migration task (if schema changes)
        if impl.get("has_schema_changes"):
            tasks.append(Task(
                id=f"TASK-{adr.number:03d}-{task_seq:03d}",
                adr=adr.id,
                title=f"Create migration for {adr.title}",
                description="Create database migration based on ADR schema changes",
                type=TaskType.MIGRATION,
                agent="manual",
                priority="P0",
                dependencies=[],
                phase=1,
                tags=["migration", "schema"] + adr.tags,
            ))
            task_seq += 1

        # API task (if API changes)
        if impl.get("has_api_changes"):
            deps = [tasks[-1].id] if impl.get("has_schema_changes") else []
            tasks.append(Task(
                id=f"TASK-{adr.number:03d}-{task_seq:03d}",
                adr=adr.id,
                title=f"Implement API for {adr.title}",
                description=impl.get("api_description", "Implement API endpoints"),
                type=TaskType.FEATURE,
                agent="FeatureBuilder",
                priority="P1",
                dependencies=deps,
                phase=1,
                tags=["api", "feature"] + adr.tags,
            ))
            task_seq += 1

        # UI task (if UI changes)
        if impl.get("has_ui_changes"):
            deps = [tasks[-1].id] if impl.get("has_api_changes") else []
            tasks.append(Task(
                id=f"TASK-{adr.number:03d}-{task_seq:03d}",
                adr=adr.id,
                title=f"Implement UI for {adr.title}",
                description=impl.get("ui_description", "Implement UI components"),
                type=TaskType.FEATURE,
                agent="FeatureBuilder",
                priority="P2",
                dependencies=deps,
                phase=1,
                tags=["ui", "feature"] + adr.tags,
            ))
            task_seq += 1

        # Test task (always add if there are implementation tasks)
        impl_tasks = [t for t in tasks if t.agent != "manual"]
        if impl_tasks:
            tasks.append(Task(
                id=f"TASK-{adr.number:03d}-{task_seq:03d}",
                adr=adr.id,
                title=f"Write tests for {adr.title}",
                description="Write unit and integration tests for new functionality",
                type=TaskType.TEST,
                agent="TestWriter",
                priority="P3",
                dependencies=[t.id for t in impl_tasks],
                phase=1,
                tags=["test"] + adr.tags,
            ))

        return tasks

    def _assign_next_task(self, exclude: Optional[str] = None) -> Optional[Task]:
        """Assign next ready task to appropriate Builder."""
        # Get pending tasks with satisfied dependencies
        pending = self.task_manager.get_tasks_by_status(TaskStatus.PENDING)
        ready = [
            t for t in pending
            if t.id != exclude and self._dependencies_satisfied(t)
        ]

        if not ready:
            return None

        # Sort by priority
        ready.sort(key=lambda t: t.priority)

        # Assign first ready task
        task = ready[0]
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = utc_now()
        self.task_manager.update_task(task)

        # Update PROJECT_HQ
        if self.config.auto_update_hq:
            self.hq_manager.set_current_focus(task)
            self.hq_manager.update_dashboard(self.task_manager.get_all_tasks())

        # Log event
        self._log_event("COORDINATOR_TASK_ASSIGNED", {
            "task_id": task.id,
            "agent": task.agent,
            "priority": task.priority,
        })

        return task

    def _dependencies_satisfied(self, task: Task) -> bool:
        """Check if all task dependencies are complete."""
        for dep_id in task.dependencies:
            dep_task = self.task_manager.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def _check_phase_complete(self) -> bool:
        """Check if current phase is complete."""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            return False

        # Get current phase
        current_phase = max(t.phase for t in tasks)
        phase_tasks = [t for t in tasks if t.phase == current_phase]

        # Check if all phase tasks are complete or blocked
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.BLOCKED)
            for t in phase_tasks
        )

    def _on_phase_complete(self) -> None:
        """Handle phase completion."""
        # Log event
        self._log_event("PHASE_COMPLETE", {
            "phase": self._get_current_phase(),
            "tasks_completed": len(self.task_manager.get_tasks_by_status(TaskStatus.COMPLETED)),
        })

        # Generate retrospective would be called here
        # For now, just update PROJECT_HQ
        if self.config.auto_update_hq:
            self.hq_manager.update_stats(self.task_manager.get_summary())

    def _get_current_phase(self) -> int:
        """Get current phase number."""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            return 1
        return max(t.phase for t in tasks)

    def _infer_advisor_type(self, task: Task) -> str:
        """Infer which advisor should handle a task."""
        # Check task tags and description
        text = f"{task.title} {task.description} {' '.join(task.tags)}".lower()

        if any(kw in text for kw in ["schema", "database", "migration", "table", "column"]):
            return "data-advisor"
        elif any(kw in text for kw in ["ui", "component", "interface", "screen", "page"]):
            return "uiux-advisor"
        else:
            return "app-advisor"

    def _log_event(self, event_type: str, context: Dict[str, Any]) -> None:
        """Log an event (integrates with EventLogger)."""
        self.events_logged += 1
        # In production, this would call the EventLogger
        # For now, we track the count


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_coordinator(project_root: Path, **kwargs) -> Coordinator:
    """
    Create a Coordinator instance.

    Args:
        project_root: Path to project root
        **kwargs: Additional config options

    Returns:
        Configured Coordinator instance
    """
    config = CoordinatorConfig(project_root=project_root, **kwargs)
    return Coordinator(config)
