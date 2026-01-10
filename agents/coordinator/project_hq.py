"""
Project HQ Manager for AI Team Coordinator
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Manages PROJECT_HQ.md - the central dashboard for project status.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import re


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PhaseInfo:
    """Information about a project phase."""
    number: int
    name: str
    status: str = "not_started"  # not_started, in_progress, completed
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_blocked: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class BlockerInfo:
    """Information about a blocker."""
    id: str
    task_id: str
    description: str
    category: str  # human_decision, external_dependency, technical, resource
    created_at: datetime = field(default_factory=utc_now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


@dataclass
class MilestoneInfo:
    """Information about a milestone."""
    id: str
    name: str
    target_date: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, missed
    completed_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT HQ MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectHQManager:
    """
    Manages PROJECT_HQ.md updates.

    PROJECT_HQ.md is the central dashboard showing:
    - Current phase and progress
    - Active blockers
    - Recent activity
    - Key metrics
    """

    def __init__(self, project_root: Path):
        """
        Initialize ProjectHQManager.

        Args:
            project_root: Path to project root (containing AI-Team-Plans/)
        """
        self.project_root = Path(project_root)
        self.hq_file = self.project_root / "AI-Team-Plans" / "PROJECT_HQ.md"

        # State
        self.phases: Dict[int, PhaseInfo] = {}
        self.blockers: Dict[str, BlockerInfo] = {}
        self.milestones: Dict[str, MilestoneInfo] = {}
        self.recent_activity: List[Dict[str, Any]] = []

        # Load existing HQ if present
        self._load_hq()

    # ───────────────────────────────────────────────────────────────────────────
    # Phase Management
    # ───────────────────────────────────────────────────────────────────────────

    def set_phase(
        self,
        number: int,
        name: str,
        tasks_total: int = 0
    ) -> PhaseInfo:
        """
        Set or update a phase.

        Args:
            number: Phase number
            name: Phase name
            tasks_total: Total tasks in phase

        Returns:
            PhaseInfo
        """
        if number in self.phases:
            phase = self.phases[number]
            phase.name = name
            phase.tasks_total = tasks_total
        else:
            phase = PhaseInfo(
                number=number,
                name=name,
                tasks_total=tasks_total,
            )
            self.phases[number] = phase

        self._write_hq()
        return phase

    def start_phase(self, number: int) -> Optional[PhaseInfo]:
        """Mark a phase as started."""
        if number not in self.phases:
            return None

        phase = self.phases[number]
        phase.status = "in_progress"
        phase.started_at = utc_now()

        self._add_activity(f"Phase {number} started: {phase.name}")
        self._write_hq()
        return phase

    def complete_phase(self, number: int) -> Optional[PhaseInfo]:
        """Mark a phase as completed."""
        if number not in self.phases:
            return None

        phase = self.phases[number]
        phase.status = "completed"
        phase.completed_at = utc_now()

        self._add_activity(f"Phase {number} completed: {phase.name}")
        self._write_hq()
        return phase

    def update_phase_progress(
        self,
        number: int,
        completed: int,
        blocked: int
    ) -> Optional[PhaseInfo]:
        """Update task counts for a phase."""
        if number not in self.phases:
            return None

        phase = self.phases[number]
        phase.tasks_completed = completed
        phase.tasks_blocked = blocked

        self._write_hq()
        return phase

    def get_current_phase(self) -> Optional[PhaseInfo]:
        """Get the current in-progress phase."""
        for phase in sorted(self.phases.values(), key=lambda p: p.number):
            if phase.status == "in_progress":
                return phase
        return None

    # ───────────────────────────────────────────────────────────────────────────
    # Blocker Management
    # ───────────────────────────────────────────────────────────────────────────

    def add_blocker(
        self,
        task_id: str,
        description: str,
        category: str = "human_decision"
    ) -> BlockerInfo:
        """
        Add a blocker.

        Args:
            task_id: ID of blocked task
            description: What's blocking
            category: Type of blocker

        Returns:
            BlockerInfo
        """
        blocker_id = f"BLOCK-{len(self.blockers) + 1:03d}"

        blocker = BlockerInfo(
            id=blocker_id,
            task_id=task_id,
            description=description,
            category=category,
        )

        self.blockers[blocker_id] = blocker
        self._add_activity(f"Blocker added: {description[:50]}...")
        self._write_hq()
        return blocker

    def resolve_blocker(
        self,
        blocker_id: str,
        resolution: str
    ) -> Optional[BlockerInfo]:
        """Resolve a blocker."""
        if blocker_id not in self.blockers:
            return None

        blocker = self.blockers[blocker_id]
        blocker.resolved = True
        blocker.resolved_at = utc_now()
        blocker.resolution = resolution

        self._add_activity(f"Blocker resolved: {blocker_id}")
        self._write_hq()
        return blocker

    def get_active_blockers(self) -> List[BlockerInfo]:
        """Get all unresolved blockers."""
        return [b for b in self.blockers.values() if not b.resolved]

    # ───────────────────────────────────────────────────────────────────────────
    # Milestone Management
    # ───────────────────────────────────────────────────────────────────────────

    def add_milestone(
        self,
        name: str,
        target_date: Optional[str] = None
    ) -> MilestoneInfo:
        """Add a milestone."""
        milestone_id = f"MS-{len(self.milestones) + 1:03d}"

        milestone = MilestoneInfo(
            id=milestone_id,
            name=name,
            target_date=target_date,
        )

        self.milestones[milestone_id] = milestone
        self._write_hq()
        return milestone

    def complete_milestone(self, milestone_id: str) -> Optional[MilestoneInfo]:
        """Mark milestone as completed."""
        if milestone_id not in self.milestones:
            return None

        milestone = self.milestones[milestone_id]
        milestone.status = "completed"
        milestone.completed_at = utc_now()

        self._add_activity(f"Milestone completed: {milestone.name}")
        self._write_hq()
        return milestone

    # ───────────────────────────────────────────────────────────────────────────
    # Activity Log
    # ───────────────────────────────────────────────────────────────────────────

    def add_activity(self, description: str) -> None:
        """Add an activity entry."""
        self._add_activity(description)
        self._write_hq()

    def _add_activity(self, description: str) -> None:
        """Internal: Add activity without writing."""
        self.recent_activity.insert(0, {
            "timestamp": utc_now().isoformat(),
            "description": description,
        })

        # Keep only last 20 activities
        self.recent_activity = self.recent_activity[:20]

    # ───────────────────────────────────────────────────────────────────────────
    # Metrics
    # ───────────────────────────────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Get current project metrics."""
        total_tasks = sum(p.tasks_total for p in self.phases.values())
        completed_tasks = sum(p.tasks_completed for p in self.phases.values())
        blocked_tasks = sum(p.tasks_blocked for p in self.phases.values())

        phases_completed = len([p for p in self.phases.values() if p.status == "completed"])
        phases_total = len(self.phases)

        return {
            "phases_total": phases_total,
            "phases_completed": phases_completed,
            "tasks_total": total_tasks,
            "tasks_completed": completed_tasks,
            "tasks_blocked": blocked_tasks,
            "active_blockers": len(self.get_active_blockers()),
            "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks else 0,
        }

    # ───────────────────────────────────────────────────────────────────────────
    # File I/O
    # ───────────────────────────────────────────────────────────────────────────

    def _load_hq(self) -> None:
        """Load existing HQ file and parse state."""
        if not self.hq_file.exists():
            return

        try:
            content = self.hq_file.read_text()
            self._parse_hq(content)
        except Exception as e:
            print(f"Warning: Could not parse HQ file: {e}")

    def _parse_hq(self, content: str) -> None:
        """Parse HQ markdown content into state."""
        # Parse phases from Phase Progress section
        phase_pattern = r'\| (\d+) \| ([^|]+) \| ([^|]+) \| (\d+)/(\d+) \|'
        for match in re.finditer(phase_pattern, content):
            num = int(match.group(1))
            name = match.group(2).strip()
            status_raw = match.group(3).strip().lower()
            completed = int(match.group(4))
            total = int(match.group(5))

            # Map emoji status to internal status
            if "✅" in status_raw or "completed" in status_raw:
                status = "completed"
            elif "🔄" in status_raw or "progress" in status_raw:
                status = "in_progress"
            else:
                status = "not_started"

            self.phases[num] = PhaseInfo(
                number=num,
                name=name,
                status=status,
                tasks_total=total,
                tasks_completed=completed,
            )

        # Parse blockers from Active Blockers section
        blocker_pattern = r'\| (BLOCK-\d+) \| (TASK-\d+) \| ([^|]+) \| ([^|]+) \|'
        for match in re.finditer(blocker_pattern, content):
            blocker_id = match.group(1)
            task_id = match.group(2)
            description = match.group(3).strip()
            category = match.group(4).strip().lower()

            self.blockers[blocker_id] = BlockerInfo(
                id=blocker_id,
                task_id=task_id,
                description=description,
                category=category,
            )

    def _write_hq(self) -> None:
        """Write current state to HQ file."""
        # Ensure directory exists
        self.hq_file.parent.mkdir(parents=True, exist_ok=True)

        content = self._generate_hq_content()
        self.hq_file.write_text(content)

    def _generate_hq_content(self) -> str:
        """Generate PROJECT_HQ.md content."""
        metrics = self.get_metrics()
        current_phase = self.get_current_phase()

        lines = [
            f"# PROJECT HQ: {self.project_root.name}",
            "",
            f"**Last Updated**: {utc_now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"**Generated By**: Coordinator (auto)",
            "",
            "---",
            "",
            "## Quick Status",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Current Phase | {current_phase.number if current_phase else 'N/A'} - {current_phase.name if current_phase else 'N/A'} |",
            f"| Overall Progress | {metrics['completion_rate']}% |",
            f"| Tasks Completed | {metrics['tasks_completed']}/{metrics['tasks_total']} |",
            f"| Active Blockers | {metrics['active_blockers']} |",
            "",
            "---",
            "",
            "## Phase Progress",
            "",
            "| Phase | Name | Status | Progress |",
            "|-------|------|--------|----------|",
        ]

        # Add phase rows
        for phase in sorted(self.phases.values(), key=lambda p: p.number):
            status_emoji = {
                "completed": "✅",
                "in_progress": "🔄",
                "not_started": "⏳",
            }.get(phase.status, "⏳")

            lines.append(
                f"| {phase.number} | {phase.name} | {status_emoji} {phase.status} | "
                f"{phase.tasks_completed}/{phase.tasks_total} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Active Blockers",
            "",
        ])

        active_blockers = self.get_active_blockers()
        if active_blockers:
            lines.extend([
                "| ID | Task | Description | Category |",
                "|----|------|-------------|----------|",
            ])
            for blocker in active_blockers:
                lines.append(
                    f"| {blocker.id} | {blocker.task_id} | "
                    f"{blocker.description[:40]}... | {blocker.category} |"
                )
        else:
            lines.append("No active blockers. 🎉")

        lines.extend([
            "",
            "---",
            "",
            "## Recent Activity",
            "",
        ])

        if self.recent_activity:
            for activity in self.recent_activity[:10]:
                timestamp = activity["timestamp"][:16].replace("T", " ")
                lines.append(f"- **{timestamp}**: {activity['description']}")
        else:
            lines.append("No recent activity.")

        lines.extend([
            "",
            "---",
            "",
            "## Milestones",
            "",
        ])

        if self.milestones:
            lines.extend([
                "| ID | Milestone | Target | Status |",
                "|----|-----------|--------|--------|",
            ])
            for ms in self.milestones.values():
                status_emoji = {
                    "completed": "✅",
                    "in_progress": "🔄",
                    "pending": "⏳",
                    "missed": "❌",
                }.get(ms.status, "⏳")

                lines.append(
                    f"| {ms.id} | {ms.name} | {ms.target_date or 'TBD'} | "
                    f"{status_emoji} {ms.status} |"
                )
        else:
            lines.append("No milestones defined.")

        lines.extend([
            "",
            "---",
            "",
            "<!--",
            "SYSTEM SECTION - DO NOT EDIT",
            "-->",
            "",
            "```yaml",
            "_system:",
            '  version: "3.0"',
            f'  project: "{self.project_root.name}"',
            f'  generated_at: "{utc_now().isoformat()}"',
            f"  phases_total: {len(self.phases)}",
            f"  blockers_active: {len(active_blockers)}",
            "```",
            "",
        ])

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python project_hq.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    manager = ProjectHQManager(project_root)

    # Set up test phases
    manager.set_phase(1, "Foundation", 5)
    manager.set_phase(2, "Core Implementation", 10)
    manager.set_phase(3, "Integration", 8)

    # Start phase 1
    manager.start_phase(1)
    manager.update_phase_progress(1, completed=2, blocked=0)

    # Add a blocker
    manager.add_blocker(
        task_id="TASK-0003",
        description="Need API credentials for external service",
        category="external_dependency",
    )

    print(f"HQ file written to: {manager.hq_file}")
    print(f"Metrics: {manager.get_metrics()}")
