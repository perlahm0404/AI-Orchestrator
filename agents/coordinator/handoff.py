"""
Handoff Generator for AI Team Coordinator
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Generates session handoff documents and retrospectives.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from .task_manager import Task, TaskStatus


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SessionStats:
    """Statistics for a session."""
    duration_minutes: int = 0
    tasks_completed: int = 0
    tasks_in_progress: int = 0
    tasks_blocked: int = 0
    iterations_total: int = 0
    human_interventions: int = 0
    auto_decisions: int = 0
    ralph_pass: int = 0
    ralph_fail: int = 0
    ralph_blocked: int = 0
    files_changed: List[str] = field(default_factory=list)
    adrs_referenced: List[str] = field(default_factory=list)
    events_detailed: int = 0
    events_counted: int = 0


@dataclass
class PhaseStats:
    """Statistics for a phase retrospective."""
    phase_number: int
    phase_name: str
    start_date: str
    end_date: str
    tasks_completed: int = 0
    tasks_blocked: int = 0
    iterations_total: int = 0
    iterations_avg: float = 0.0
    human_interventions: int = 0
    auto_decisions: int = 0
    ralph_pass: int = 0
    ralph_fail: int = 0
    ralph_blocked: int = 0
    adrs_created: List[str] = field(default_factory=list)
    kos_created: List[str] = field(default_factory=list)
    sessions: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# HANDOFF GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class HandoffGenerator:
    """
    Generates session handoffs and phase retrospectives.

    Session Handoffs:
    - Created at end of each session
    - Summarize what was done, what's pending, what's blocked
    - Enable session continuity

    Phase Retrospectives:
    - Created at end of each phase
    - Analyze patterns, barriers, improvements
    - Feed into continuous improvement
    """

    def __init__(self, project_root: Path):
        """
        Initialize HandoffGenerator.

        Args:
            project_root: Path to project root (containing AI-Team-Plans/)
        """
        self.project_root = Path(project_root)
        self.sessions_dir = self.project_root / "AI-Team-Plans" / "sessions"
        self.retros_dir = self.project_root / "AI-Team-Plans" / "retrospectives"

        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.retros_dir.mkdir(parents=True, exist_ok=True)

    # ───────────────────────────────────────────────────────────────────────────
    # Session Handoffs
    # ───────────────────────────────────────────────────────────────────────────

    def generate_session_handoff(
        self,
        session_id: str,
        stats: SessionStats,
        completed_tasks: List[Task],
        in_progress_tasks: List[Task],
        blocked_tasks: List[Task],
        next_priorities: List[str],
        notes: str = "",
        previous_session: Optional[str] = None,
    ) -> Path:
        """
        Generate a session handoff document.

        Args:
            session_id: Unique session identifier
            stats: Session statistics
            completed_tasks: Tasks completed this session
            in_progress_tasks: Tasks still in progress
            blocked_tasks: Tasks that are blocked
            next_priorities: Top 3 priorities for next session
            notes: Additional notes
            previous_session: ID of previous session

        Returns:
            Path to generated handoff file
        """
        date_str = utc_now().strftime("%Y-%m-%d")
        seq = self._get_next_sequence(self.sessions_dir, date_str)

        filename = f"{date_str}-{seq:03d}-handoff.md"
        filepath = self.sessions_dir / filename

        content = self._format_handoff(
            session_id=session_id,
            stats=stats,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            next_priorities=next_priorities,
            notes=notes,
            previous_session=previous_session,
        )

        filepath.write_text(content)
        return filepath

    def _format_handoff(
        self,
        session_id: str,
        stats: SessionStats,
        completed_tasks: List[Task],
        in_progress_tasks: List[Task],
        blocked_tasks: List[Task],
        next_priorities: List[str],
        notes: str,
        previous_session: Optional[str],
    ) -> str:
        """Format handoff as markdown."""
        lines = [
            f"# Session Handoff: {session_id}",
            "",
            f"**Project**: {self.project_root.name}",
            f"**Created**: {utc_now().isoformat()}Z",
            "**Created By**: Coordinator",
            "",
            "---",
            "",
            "## Session Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Duration | {stats.duration_minutes} minutes |",
            f"| Tasks Completed | {stats.tasks_completed} |",
            f"| Tasks In Progress | {stats.tasks_in_progress} |",
            f"| Tasks Blocked | {stats.tasks_blocked} |",
            f"| Iterations Total | {stats.iterations_total} |",
            f"| Human Interventions | {stats.human_interventions} |",
            "",
            "---",
            "",
            "## Completed This Session",
            "",
        ]

        if completed_tasks:
            lines.extend([
                "| Task | Description | Agent | Iterations |",
                "|------|-------------|-------|------------|",
            ])
            for task in completed_tasks:
                lines.append(
                    f"| {task.id} | {task.title[:40]} | "
                    f"{task.assigned_agent or 'N/A'} | {task.iterations_used} |"
                )
        else:
            lines.append("No tasks completed this session.")

        lines.extend([
            "",
            "---",
            "",
            "## Still In Progress",
            "",
        ])

        if in_progress_tasks:
            lines.extend([
                "| Task | Status | Progress | Notes |",
                "|------|--------|----------|-------|",
            ])
            for task in in_progress_tasks:
                progress = f"{task.iterations_used}/{task.max_iterations}"
                lines.append(
                    f"| {task.id} | {task.status.value} | {progress} | "
                    f"{task.title[:30]} |"
                )
        else:
            lines.append("No tasks in progress.")

        lines.extend([
            "",
            "---",
            "",
            "## Blocked (Need Human)",
            "",
        ])

        if blocked_tasks:
            lines.extend([
                "| Task | Blocker | Details | Since |",
                "|------|---------|---------|-------|",
            ])
            for task in blocked_tasks:
                since = task.blocked_at.strftime("%Y-%m-%d %H:%M") if task.blocked_at else "N/A"
                lines.append(
                    f"| {task.id} | {task.blocked_reason or 'Unknown'} | "
                    f"{(task.blocked_details or '')[:30]} | {since} |"
                )
        else:
            lines.append("No blocked tasks. 🎉")

        lines.extend([
            "",
            "---",
            "",
            "## Next Session Should",
            "",
        ])

        for i, priority in enumerate(next_priorities[:3], 1):
            lines.append(f"{i}. {priority}")

        if len(next_priorities) < 3:
            for i in range(len(next_priorities) + 1, 4):
                lines.append(f"{i}. (No priority set)")

        lines.extend([
            "",
            "---",
            "",
            "## Files Changed",
            "",
        ])

        if stats.files_changed:
            lines.extend([
                "| File | Changes | Agent |",
                "|------|---------|-------|",
            ])
            for file in stats.files_changed[:20]:
                lines.append(f"| {file} | Modified | Auto |")
        else:
            lines.append("No files changed this session.")

        lines.extend([
            "",
            "---",
            "",
            "## ADRs Referenced",
            "",
        ])

        if stats.adrs_referenced:
            for adr in stats.adrs_referenced:
                lines.append(f"- {adr}")
        else:
            lines.append("No ADRs referenced.")

        lines.extend([
            "",
            "---",
            "",
            "## Events Logged",
            "",
            f"- Detailed: {stats.events_detailed}",
            f"- Counted: {stats.events_counted}",
            "",
            "---",
            "",
            "## Notes",
            "",
            f"> {notes if notes else 'No additional notes.'}",
            "",
            "---",
            "",
            "<!--",
            "SYSTEM SECTION - DO NOT EDIT",
            "Used for session continuity",
            "-->",
            "",
            "```yaml",
            "_system:",
            '  version: "3.0"',
            f'  session_id: "{session_id}"',
            f'  previous_session: "{previous_session or "none"}"',
            '  work_queue_snapshot: "auto"',
            '  project_hq_snapshot: "auto"',
            "  resumable: true",
            "```",
            "",
        ])

        return "\n".join(lines)

    # ───────────────────────────────────────────────────────────────────────────
    # Phase Retrospectives
    # ───────────────────────────────────────────────────────────────────────────

    def generate_retrospective(
        self,
        project_id: str,
        stats: PhaseStats,
        worked_well: List[str],
        didnt_work: List[str],
        barriers: List[Dict[str, str]],
        proposed_changes: List[Dict[str, str]],
        action_items: List[Dict[str, str]],
        patterns: List[str],
        recommendations: List[str],
        prev_phase_stats: Optional[PhaseStats] = None,
    ) -> Path:
        """
        Generate a phase retrospective document.

        Args:
            project_id: Project identifier
            stats: Phase statistics
            worked_well: Things that worked well
            didnt_work: Things that didn't work
            barriers: Barriers encountered (task, resolution)
            proposed_changes: Proposed changes (category, priority, rationale)
            action_items: Action items (owner, due, status)
            patterns: Patterns identified
            recommendations: Recommendations for next phase
            prev_phase_stats: Previous phase stats for comparison

        Returns:
            Path to generated retrospective file
        """
        filename = f"RETRO-{project_id}-phase-{stats.phase_number}.md"
        filepath = self.retros_dir / filename

        content = self._format_retrospective(
            project_id=project_id,
            stats=stats,
            worked_well=worked_well,
            didnt_work=didnt_work,
            barriers=barriers,
            proposed_changes=proposed_changes,
            action_items=action_items,
            patterns=patterns,
            recommendations=recommendations,
            prev_phase_stats=prev_phase_stats,
        )

        filepath.write_text(content)
        return filepath

    def _format_retrospective(
        self,
        project_id: str,
        stats: PhaseStats,
        worked_well: List[str],
        didnt_work: List[str],
        barriers: List[Dict[str, str]],
        proposed_changes: List[Dict[str, str]],
        action_items: List[Dict[str, str]],
        patterns: List[str],
        recommendations: List[str],
        prev_phase_stats: Optional[PhaseStats],
    ) -> str:
        """Format retrospective as markdown."""
        lines = [
            f"# Retrospective: {project_id} Phase {stats.phase_number} - {stats.phase_name}",
            "",
            f"**Phase**: {stats.phase_number} - {stats.phase_name}",
            f"**Project**: {self.project_root.name}",
            f"**Duration**: {stats.start_date} to {stats.end_date}",
            f"**Generated**: {utc_now().isoformat()}Z",
            "**Generated By**: Coordinator (auto)",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Tasks Completed | {stats.tasks_completed} |",
            f"| Tasks Blocked | {stats.tasks_blocked} |",
            f"| Total Iterations | {stats.iterations_total} |",
            f"| Avg Iterations/Task | {stats.iterations_avg:.2f} |",
            f"| Human Interventions | {stats.human_interventions} |",
            f"| Auto Decisions | {stats.auto_decisions} |",
            f"| Ralph PASS | {stats.ralph_pass} |",
            f"| Ralph FAIL | {stats.ralph_fail} |",
            f"| Ralph BLOCKED | {stats.ralph_blocked} |",
            "",
            "---",
            "",
            "## What Worked Well",
            "",
        ]

        if worked_well:
            for item in worked_well:
                lines.append(f"- {item}")
        else:
            lines.append("- (No items recorded)")

        lines.extend([
            "",
            "---",
            "",
            "## What Didn't Work",
            "",
        ])

        if didnt_work:
            for item in didnt_work:
                lines.append(f"- {item}")
        else:
            lines.append("- (No items recorded)")

        lines.extend([
            "",
            "---",
            "",
            "## Barriers Encountered",
            "",
        ])

        if barriers:
            lines.extend([
                "| Barrier | Task | Resolution |",
                "|---------|------|------------|",
            ])
            for b in barriers:
                lines.append(
                    f"| {b.get('barrier', 'N/A')} | {b.get('task', 'N/A')} | "
                    f"{b.get('resolution', 'N/A')} |"
                )
        else:
            lines.append("No barriers encountered.")

        lines.extend([
            "",
            "---",
            "",
            "## Proposed Changes",
            "",
        ])

        if proposed_changes:
            lines.extend([
                "| Change | Category | Priority | Rationale |",
                "|--------|----------|----------|-----------|",
            ])
            for c in proposed_changes:
                lines.append(
                    f"| {c.get('change', 'N/A')} | {c.get('category', 'N/A')} | "
                    f"{c.get('priority', 'N/A')} | {c.get('rationale', 'N/A')} |"
                )
        else:
            lines.append("No changes proposed.")

        lines.extend([
            "",
            "---",
            "",
            "## Action Items",
            "",
        ])

        if action_items:
            lines.extend([
                "| Action | Owner | Due | Status |",
                "|--------|-------|-----|--------|",
            ])
            for a in action_items:
                lines.append(
                    f"| {a.get('action', 'N/A')} | {a.get('owner', 'N/A')} | "
                    f"{a.get('due', 'N/A')} | {a.get('status', 'pending')} |"
                )
        else:
            lines.append("No action items.")

        lines.extend([
            "",
            "---",
            "",
            "## Patterns Identified",
            "",
        ])

        if patterns:
            for pattern in patterns:
                lines.append(f"- {pattern}")
        else:
            lines.append("No patterns identified.")

        lines.extend([
            "",
            "---",
            "",
            f"## Phase {stats.phase_number + 1} Recommendations",
            "",
        ])

        if recommendations:
            for rec in recommendations:
                lines.append(f"- {rec}")
        else:
            lines.append("No recommendations.")

        lines.extend([
            "",
            "---",
            "",
            "## Linked Artifacts",
            "",
            f"- **ADRs Created**: {', '.join(stats.adrs_created) if stats.adrs_created else 'None'}",
            f"- **Events Logged**: (see metrics.json)",
            f"- **Knowledge Objects**: {', '.join(stats.kos_created) if stats.kos_created else 'None'}",
            f"- **Session Handoffs**: {', '.join(stats.sessions) if stats.sessions else 'None'}",
            "",
            "---",
            "",
            "## Metrics Comparison",
            "",
        ])

        if prev_phase_stats:
            iter_change = stats.iterations_avg - prev_phase_stats.iterations_avg
            iter_change_str = f"{'+' if iter_change > 0 else ''}{iter_change:.2f}"

            auto_rate = (stats.auto_decisions / max(stats.auto_decisions + stats.human_interventions, 1)) * 100
            prev_auto_rate = (prev_phase_stats.auto_decisions / max(prev_phase_stats.auto_decisions + prev_phase_stats.human_interventions, 1)) * 100
            auto_change = auto_rate - prev_auto_rate
            auto_change_str = f"{'+' if auto_change > 0 else ''}{auto_change:.1f}%"

            block_rate = (stats.tasks_blocked / max(stats.tasks_completed + stats.tasks_blocked, 1)) * 100
            prev_block_rate = (prev_phase_stats.tasks_blocked / max(prev_phase_stats.tasks_completed + prev_phase_stats.tasks_blocked, 1)) * 100
            block_change = block_rate - prev_block_rate
            block_change_str = f"{'+' if block_change > 0 else ''}{block_change:.1f}%"

            lines.extend([
                "| Metric | This Phase | Previous Phase | Change |",
                "|--------|------------|----------------|--------|",
                f"| Avg Iterations/Task | {stats.iterations_avg:.2f} | {prev_phase_stats.iterations_avg:.2f} | {iter_change_str} |",
                f"| Auto Decision Rate | {auto_rate:.1f}% | {prev_auto_rate:.1f}% | {auto_change_str} |",
                f"| Block Rate | {block_rate:.1f}% | {prev_block_rate:.1f}% | {block_change_str} |",
            ])
        else:
            lines.append("No previous phase data for comparison.")

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
            f'  phase_id: "{project_id}-phase-{stats.phase_number}"',
            f'  generated_at: "{utc_now().isoformat()}"',
            f"  patterns_added: {len(patterns)}",
            f"  recommendations_added: {len(recommendations)}",
            "  thresholds_adjusted: []",
            "```",
            "",
        ])

        return "\n".join(lines)

    # ───────────────────────────────────────────────────────────────────────────
    # Utilities
    # ───────────────────────────────────────────────────────────────────────────

    def _get_next_sequence(self, directory: Path, date_str: str) -> int:
        """Get next sequence number for a date."""
        existing = list(directory.glob(f"{date_str}-*.md"))
        return len(existing) + 1

    def get_latest_handoff(self) -> Optional[Path]:
        """Get path to most recent handoff."""
        handoffs = sorted(self.sessions_dir.glob("*-handoff.md"))
        return handoffs[-1] if handoffs else None

    def get_handoffs_for_date(self, date_str: str) -> List[Path]:
        """Get all handoffs for a specific date."""
        return sorted(self.sessions_dir.glob(f"{date_str}-*-handoff.md"))


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python handoff.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    generator = HandoffGenerator(project_root)

    # Create test handoff
    stats = SessionStats(
        duration_minutes=45,
        tasks_completed=3,
        tasks_in_progress=1,
        tasks_blocked=1,
        iterations_total=12,
        human_interventions=1,
    )

    handoff_path = generator.generate_session_handoff(
        session_id="test-session-001",
        stats=stats,
        completed_tasks=[],
        in_progress_tasks=[],
        blocked_tasks=[],
        next_priorities=[
            "Continue implementing Phase 2",
            "Resolve blocked task TASK-0005",
            "Review ADR-002 decision",
        ],
        notes="Test session for demonstration.",
    )

    print(f"Handoff written to: {handoff_path}")
