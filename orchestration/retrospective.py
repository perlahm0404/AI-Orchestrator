"""
Retrospective Generator for AI Team Orchestration
Version: 3.0
Part of: AI Team Governance (AI-TEAM-SPEC-V3)

Generates phase retrospectives with pattern analysis and recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import re


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Pattern:
    """Represents a pattern identified during retrospective."""

    id: str
    name: str
    description: str
    category: str  # success, failure, barrier, improvement
    occurrences: int = 1
    first_seen: datetime = field(default_factory=utc_now)
    last_seen: datetime = field(default_factory=utc_now)
    related_tasks: List[str] = field(default_factory=list)
    actionable: bool = False
    action_taken: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "occurrences": self.occurrences,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "related_tasks": self.related_tasks,
            "actionable": self.actionable,
            "action_taken": self.action_taken,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            occurrences=data.get("occurrences", 1),
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            related_tasks=data.get("related_tasks", []),
            actionable=data.get("actionable", False),
            action_taken=data.get("action_taken"),
        )


@dataclass
class PhaseMetrics:
    """Metrics for a completed phase."""

    phase_number: int
    phase_name: str
    start_date: str
    end_date: str

    # Task metrics
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_blocked: int = 0
    tasks_cancelled: int = 0

    # Iteration metrics
    iterations_total: int = 0
    iterations_per_task_avg: float = 0.0
    iterations_per_task_min: int = 0
    iterations_per_task_max: int = 0

    # Decision metrics
    auto_decisions: int = 0
    human_decisions: int = 0
    escalations_total: int = 0
    escalations_resolved: int = 0

    # Ralph metrics
    ralph_pass: int = 0
    ralph_fail: int = 0
    ralph_blocked: int = 0

    # Artifact metrics
    adrs_created: List[str] = field(default_factory=list)
    kos_created: List[str] = field(default_factory=list)
    events_detailed: int = 0
    events_counted: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "tasks_blocked": self.tasks_blocked,
            "tasks_cancelled": self.tasks_cancelled,
            "iterations_total": self.iterations_total,
            "iterations_per_task_avg": round(self.iterations_per_task_avg, 2),
            "iterations_per_task_min": self.iterations_per_task_min,
            "iterations_per_task_max": self.iterations_per_task_max,
            "auto_decisions": self.auto_decisions,
            "human_decisions": self.human_decisions,
            "escalations_total": self.escalations_total,
            "escalations_resolved": self.escalations_resolved,
            "ralph_pass": self.ralph_pass,
            "ralph_fail": self.ralph_fail,
            "ralph_blocked": self.ralph_blocked,
            "adrs_created": self.adrs_created,
            "kos_created": self.kos_created,
            "events_detailed": self.events_detailed,
            "events_counted": self.events_counted,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PATTERN ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class PatternAnalyzer:
    """
    Analyzes events and tasks to identify patterns.

    Looks for:
    - Success patterns (what worked well)
    - Failure patterns (what didn't work)
    - Barriers (recurring blockers)
    - Improvement opportunities
    """

    def __init__(self, project_root: Path):
        """
        Initialize PatternAnalyzer.

        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root)
        self.patterns_file = (
            self.project_root / "AI-Team-Plans" / "retrospectives" / "patterns.json"
        )
        self.patterns: Dict[str, Pattern] = {}

        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load existing patterns from file."""
        if not self.patterns_file.exists():
            return

        try:
            with open(self.patterns_file, "r") as f:
                data = json.load(f)
            for p_data in data.get("patterns", []):
                pattern = Pattern.from_dict(p_data)
                self.patterns[pattern.id] = pattern
        except (json.JSONDecodeError, IOError):
            pass

    def _save_patterns(self) -> None:
        """Save patterns to file."""
        self.patterns_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "3.0",
            "generated_at": utc_now().isoformat(),
            "patterns": [p.to_dict() for p in self.patterns.values()],
        }

        with open(self.patterns_file, "w") as f:
            json.dump(data, f, indent=2)

    def analyze_phase(
        self,
        tasks: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        escalations: List[Dict[str, Any]],
    ) -> List[Pattern]:
        """
        Analyze phase data for patterns.

        Args:
            tasks: Completed tasks from the phase
            events: Events from the phase
            escalations: Escalations from the phase

        Returns:
            List of identified patterns
        """
        new_patterns = []

        # Analyze task patterns
        new_patterns.extend(self._analyze_task_patterns(tasks))

        # Analyze iteration patterns
        new_patterns.extend(self._analyze_iteration_patterns(tasks))

        # Analyze escalation patterns
        new_patterns.extend(self._analyze_escalation_patterns(escalations))

        # Analyze event patterns
        new_patterns.extend(self._analyze_event_patterns(events))

        # Update pattern store
        for pattern in new_patterns:
            if pattern.id in self.patterns:
                existing = self.patterns[pattern.id]
                existing.occurrences += 1
                existing.last_seen = utc_now()
                existing.related_tasks.extend(pattern.related_tasks)
            else:
                self.patterns[pattern.id] = pattern

        self._save_patterns()
        return new_patterns

    def _analyze_task_patterns(self, tasks: List[Dict[str, Any]]) -> List[Pattern]:
        """Analyze task completion patterns."""
        patterns = []

        # Check for high completion rate
        completed = [t for t in tasks if t.get("status") == "completed"]
        if len(completed) / max(len(tasks), 1) > 0.9:
            patterns.append(Pattern(
                id="P-HIGH-COMPLETION",
                name="High Task Completion Rate",
                description=f"Completed {len(completed)}/{len(tasks)} tasks (>90%)",
                category="success",
            ))

        # Check for blocked tasks pattern
        blocked = [t for t in tasks if t.get("status") == "blocked"]
        if len(blocked) / max(len(tasks), 1) > 0.2:
            patterns.append(Pattern(
                id="P-HIGH-BLOCK-RATE",
                name="High Block Rate",
                description=f"{len(blocked)}/{len(tasks)} tasks blocked (>20%)",
                category="barrier",
                actionable=True,
            ))

        # Check for task type patterns
        by_type: Dict[str, int] = {}
        for t in tasks:
            task_type = t.get("task_type", "unknown")
            by_type[task_type] = by_type.get(task_type, 0) + 1

        dominant = max(by_type.items(), key=lambda x: x[1], default=(None, 0))
        if dominant[0] and dominant[1] / len(tasks) > 0.5:
            patterns.append(Pattern(
                id=f"P-DOMINANT-{dominant[0].upper()}",
                name=f"Dominant Task Type: {dominant[0]}",
                description=f"{dominant[0]} tasks dominate ({dominant[1]}/{len(tasks)})",
                category="improvement",
            ))

        return patterns

    def _analyze_iteration_patterns(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """Analyze iteration count patterns."""
        patterns = []

        iterations = [t.get("iterations_used", 0) for t in tasks if t.get("status") == "completed"]
        if not iterations:
            return patterns

        avg_iter = sum(iterations) / len(iterations)
        max_iter = max(iterations)

        # Check for efficient completion
        if avg_iter <= 3:
            patterns.append(Pattern(
                id="P-EFFICIENT-ITERATIONS",
                name="Efficient Task Completion",
                description=f"Average {avg_iter:.1f} iterations per task (≤3)",
                category="success",
            ))

        # Check for iteration budget exhaustion
        if max_iter >= 15:
            patterns.append(Pattern(
                id="P-ITERATION-EXHAUSTION",
                name="Iteration Budget Exhaustion",
                description=f"Some tasks reached {max_iter} iterations",
                category="failure",
                actionable=True,
            ))

        return patterns

    def _analyze_escalation_patterns(
        self,
        escalations: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """Analyze escalation patterns."""
        patterns = []

        if not escalations:
            patterns.append(Pattern(
                id="P-NO-ESCALATIONS",
                name="No Escalations Needed",
                description="Phase completed without human escalations",
                category="success",
            ))
            return patterns

        # Group by type
        by_type: Dict[str, int] = {}
        for e in escalations:
            esc_type = e.get("type", "unknown")
            by_type[esc_type] = by_type.get(esc_type, 0) + 1

        # Check for scope escalations
        if by_type.get("scope", 0) > 2:
            patterns.append(Pattern(
                id="P-FREQUENT-SCOPE-ESC",
                name="Frequent Scope Escalations",
                description=f"{by_type['scope']} scope escalations - tasks may be too broad",
                category="barrier",
                actionable=True,
            ))

        # Check for ADR conflicts
        if by_type.get("adr_conflict", 0) > 0:
            patterns.append(Pattern(
                id="P-ADR-CONFLICTS",
                name="ADR Conflicts Detected",
                description=f"{by_type['adr_conflict']} ADR conflicts - review decision coherence",
                category="improvement",
                actionable=True,
            ))

        return patterns

    def _analyze_event_patterns(self, events: List[Dict[str, Any]]) -> List[Pattern]:
        """Analyze event patterns."""
        patterns = []

        # Group events by type
        by_type: Dict[str, int] = {}
        for e in events:
            event_type = e.get("type", "unknown")
            by_type[event_type] = by_type.get(event_type, 0) + 1

        # Check for high auto-decision rate
        auto = by_type.get("ADVISOR_AUTO_DECIDED", 0)
        escalated = by_type.get("ADVISOR_ESCALATED", 0)
        if auto + escalated > 0:
            auto_rate = auto / (auto + escalated)
            if auto_rate > 0.8:
                patterns.append(Pattern(
                    id="P-HIGH-AUTO-RATE",
                    name="High Auto-Decision Rate",
                    description=f"{auto_rate:.0%} of advisor decisions auto-approved",
                    category="success",
                ))

        return patterns

    def get_actionable_patterns(self) -> List[Pattern]:
        """Get patterns that need action."""
        return [p for p in self.patterns.values() if p.actionable and not p.action_taken]


# ═══════════════════════════════════════════════════════════════════════════════
# RETROSPECTIVE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class RetrospectiveGenerator:
    """
    Generates phase retrospectives.

    Auto-generated at phase completion with:
    - Metrics summary
    - Pattern analysis
    - Barrier documentation
    - Improvement recommendations
    """

    def __init__(self, project_root: Path):
        """
        Initialize RetrospectiveGenerator.

        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root)
        self.retro_dir = self.project_root / "AI-Team-Plans" / "retrospectives"
        self.pattern_analyzer = PatternAnalyzer(project_root)

        self.retro_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        project_id: str,
        metrics: PhaseMetrics,
        tasks: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        escalations: List[Dict[str, Any]],
        previous_metrics: Optional[PhaseMetrics] = None,
    ) -> Path:
        """
        Generate a phase retrospective.

        Args:
            project_id: Project identifier
            metrics: Phase metrics
            tasks: Tasks from the phase
            events: Events from the phase
            escalations: Escalations from the phase
            previous_metrics: Previous phase for comparison

        Returns:
            Path to generated retrospective
        """
        # Analyze patterns
        patterns = self.pattern_analyzer.analyze_phase(tasks, events, escalations)

        # Generate content sections
        worked_well = self._generate_worked_well(patterns, metrics)
        didnt_work = self._generate_didnt_work(patterns, metrics)
        barriers = self._generate_barriers(escalations, tasks)
        proposed_changes = self._generate_proposed_changes(patterns)
        action_items = self._generate_action_items(patterns, escalations)
        recommendations = self._generate_recommendations(patterns, metrics, previous_metrics)

        # Generate markdown
        content = self._format_retrospective(
            project_id=project_id,
            metrics=metrics,
            worked_well=worked_well,
            didnt_work=didnt_work,
            barriers=barriers,
            proposed_changes=proposed_changes,
            action_items=action_items,
            patterns=[p.name for p in patterns],
            recommendations=recommendations,
            previous_metrics=previous_metrics,
        )

        # Write file
        filename = f"RETRO-{project_id}-phase-{metrics.phase_number}.md"
        filepath = self.retro_dir / filename
        filepath.write_text(content)

        return filepath

    def _generate_worked_well(
        self,
        patterns: List[Pattern],
        metrics: PhaseMetrics,
    ) -> List[str]:
        """Generate 'what worked well' section."""
        items = []

        # From patterns
        for p in patterns:
            if p.category == "success":
                items.append(p.description)

        # From metrics
        if metrics.tasks_completed >= metrics.tasks_total * 0.9:
            items.append(f"High task completion rate ({metrics.tasks_completed}/{metrics.tasks_total})")

        if metrics.iterations_per_task_avg <= 5:
            items.append(f"Efficient iteration usage (avg {metrics.iterations_per_task_avg:.1f} per task)")

        auto_rate = metrics.auto_decisions / max(metrics.auto_decisions + metrics.human_decisions, 1)
        if auto_rate >= 0.7:
            items.append(f"High autonomy achieved ({auto_rate:.0%} auto-decisions)")

        return items if items else ["No specific successes identified"]

    def _generate_didnt_work(
        self,
        patterns: List[Pattern],
        metrics: PhaseMetrics,
    ) -> List[str]:
        """Generate 'what didn't work' section."""
        items = []

        # From patterns
        for p in patterns:
            if p.category == "failure":
                items.append(p.description)

        # From metrics
        if metrics.tasks_blocked > metrics.tasks_total * 0.2:
            items.append(f"High block rate ({metrics.tasks_blocked} tasks blocked)")

        if metrics.ralph_blocked > 0:
            items.append(f"Ralph blocked {metrics.ralph_blocked} changes")

        if metrics.iterations_per_task_max >= 15:
            items.append(f"Some tasks exhausted iteration budget ({metrics.iterations_per_task_max} iterations)")

        return items if items else ["No significant issues identified"]

    def _generate_barriers(
        self,
        escalations: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Generate barriers table."""
        barriers = []

        # From escalations
        for esc in escalations:
            barriers.append({
                "barrier": esc.get("description", "Unknown")[:50],
                "task": esc.get("source_task", "N/A"),
                "resolution": esc.get("resolution", "Pending"),
            })

        # From blocked tasks
        for task in tasks:
            if task.get("status") == "blocked":
                barriers.append({
                    "barrier": task.get("blocked_reason", "Unknown"),
                    "task": task.get("id", "N/A"),
                    "resolution": "Pending",
                })

        return barriers

    def _generate_proposed_changes(
        self,
        patterns: List[Pattern],
    ) -> List[Dict[str, str]]:
        """Generate proposed changes table."""
        changes = []

        for p in patterns:
            if p.actionable:
                changes.append({
                    "change": f"Address: {p.name}",
                    "category": p.category,
                    "priority": "high" if p.occurrences > 2 else "medium",
                    "rationale": p.description,
                })

        return changes

    def _generate_action_items(
        self,
        patterns: List[Pattern],
        escalations: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Generate action items table."""
        items = []

        # From actionable patterns
        for p in patterns:
            if p.actionable and not p.action_taken:
                items.append({
                    "action": f"Investigate and address: {p.name}",
                    "owner": "Human",
                    "due": "Next phase start",
                    "status": "pending",
                })

        # From unresolved escalations
        unresolved = [e for e in escalations if e.get("status") == "pending"]
        for esc in unresolved[:3]:  # Limit to top 3
            items.append({
                "action": f"Resolve escalation: {esc.get('id', 'Unknown')}",
                "owner": "Human",
                "due": "Before next phase",
                "status": "pending",
            })

        return items

    def _generate_recommendations(
        self,
        patterns: List[Pattern],
        metrics: PhaseMetrics,
        previous_metrics: Optional[PhaseMetrics],
    ) -> List[str]:
        """Generate recommendations for next phase."""
        recs = []

        # Based on patterns
        barrier_patterns = [p for p in patterns if p.category == "barrier"]
        if barrier_patterns:
            recs.append(f"Address {len(barrier_patterns)} recurring barriers before starting")

        # Based on metrics
        if metrics.tasks_blocked > 2:
            recs.append("Break down tasks into smaller units to reduce blocking")

        if metrics.iterations_per_task_avg > 10:
            recs.append("Improve task clarity to reduce iteration count")

        # Based on comparison
        if previous_metrics:
            if metrics.auto_decisions < previous_metrics.auto_decisions:
                recs.append("Review autonomy settings - auto-decisions decreased")

        # Default recommendations
        if not recs:
            recs.append("Continue current practices - metrics look healthy")

        return recs

    def _format_retrospective(
        self,
        project_id: str,
        metrics: PhaseMetrics,
        worked_well: List[str],
        didnt_work: List[str],
        barriers: List[Dict[str, str]],
        proposed_changes: List[Dict[str, str]],
        action_items: List[Dict[str, str]],
        patterns: List[str],
        recommendations: List[str],
        previous_metrics: Optional[PhaseMetrics],
    ) -> str:
        """Format retrospective as markdown."""
        lines = [
            f"# Retrospective: {project_id} Phase {metrics.phase_number} - {metrics.phase_name}",
            "",
            f"**Phase**: {metrics.phase_number} - {metrics.phase_name}",
            f"**Project**: {self.project_root.name}",
            f"**Duration**: {metrics.start_date} to {metrics.end_date}",
            f"**Generated**: {utc_now().isoformat()}Z",
            "**Generated By**: Coordinator (auto)",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Tasks Completed | {metrics.tasks_completed} |",
            f"| Tasks Blocked | {metrics.tasks_blocked} |",
            f"| Total Iterations | {metrics.iterations_total} |",
            f"| Avg Iterations/Task | {metrics.iterations_per_task_avg:.2f} |",
            f"| Human Interventions | {metrics.human_decisions} |",
            f"| Auto Decisions | {metrics.auto_decisions} |",
            f"| Ralph PASS | {metrics.ralph_pass} |",
            f"| Ralph FAIL | {metrics.ralph_fail} |",
            f"| Ralph BLOCKED | {metrics.ralph_blocked} |",
            "",
            "---",
            "",
            "## What Worked Well",
            "",
        ]

        for item in worked_well:
            lines.append(f"- {item}")

        lines.extend([
            "",
            "---",
            "",
            "## What Didn't Work",
            "",
        ])

        for item in didnt_work:
            lines.append(f"- {item}")

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
                lines.append(f"| {b['barrier']} | {b['task']} | {b['resolution']} |")
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
                lines.append(f"| {c['change']} | {c['category']} | {c['priority']} | {c['rationale']} |")
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
                lines.append(f"| {a['action']} | {a['owner']} | {a['due']} | {a['status']} |")
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
            for p in patterns:
                lines.append(f"- {p}")
        else:
            lines.append("No patterns identified.")

        lines.extend([
            "",
            "---",
            "",
            f"## Phase {metrics.phase_number + 1} Recommendations",
            "",
        ])

        for rec in recommendations:
            lines.append(f"- {rec}")

        lines.extend([
            "",
            "---",
            "",
            "## Linked Artifacts",
            "",
            f"- **ADRs Created**: {', '.join(metrics.adrs_created) if metrics.adrs_created else 'None'}",
            f"- **Events Logged**: {metrics.events_detailed} detailed, {metrics.events_counted} counted",
            f"- **Knowledge Objects**: {', '.join(metrics.kos_created) if metrics.kos_created else 'None'}",
            "",
            "---",
            "",
        ])

        # Metrics comparison
        if previous_metrics:
            lines.extend([
                "## Metrics Comparison",
                "",
                "| Metric | This Phase | Previous Phase | Change |",
                "|--------|------------|----------------|--------|",
            ])

            iter_change = metrics.iterations_per_task_avg - previous_metrics.iterations_per_task_avg
            lines.append(
                f"| Avg Iterations/Task | {metrics.iterations_per_task_avg:.2f} | "
                f"{previous_metrics.iterations_per_task_avg:.2f} | "
                f"{'+' if iter_change > 0 else ''}{iter_change:.2f} |"
            )

            auto_rate = metrics.auto_decisions / max(metrics.auto_decisions + metrics.human_decisions, 1)
            prev_auto_rate = previous_metrics.auto_decisions / max(previous_metrics.auto_decisions + previous_metrics.human_decisions, 1)
            auto_change = (auto_rate - prev_auto_rate) * 100
            lines.append(
                f"| Auto Decision Rate | {auto_rate:.0%} | "
                f"{prev_auto_rate:.0%} | "
                f"{'+' if auto_change > 0 else ''}{auto_change:.1f}% |"
            )

            block_rate = metrics.tasks_blocked / max(metrics.tasks_completed + metrics.tasks_blocked, 1)
            prev_block_rate = previous_metrics.tasks_blocked / max(previous_metrics.tasks_completed + previous_metrics.tasks_blocked, 1)
            block_change = (block_rate - prev_block_rate) * 100
            lines.append(
                f"| Block Rate | {block_rate:.0%} | "
                f"{prev_block_rate:.0%} | "
                f"{'+' if block_change > 0 else ''}{block_change:.1f}% |"
            )

            lines.append("")
            lines.append("---")
            lines.append("")

        lines.extend([
            "<!--",
            "SYSTEM SECTION - DO NOT EDIT",
            "-->",
            "",
            "```yaml",
            "_system:",
            '  version: "3.0"',
            f'  phase_id: "{project_id}-phase-{metrics.phase_number}"',
            f'  generated_at: "{utc_now().isoformat()}"',
            f"  patterns_added: {len(patterns)}",
            f"  recommendations_added: {len(recommendations)}",
            "  thresholds_adjusted: []",
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
        print("Usage: python retrospective.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    generator = RetrospectiveGenerator(project_root)

    # Create test metrics
    metrics = PhaseMetrics(
        phase_number=1,
        phase_name="Foundation",
        start_date="2024-01-01",
        end_date="2024-01-15",
        tasks_total=10,
        tasks_completed=8,
        tasks_blocked=2,
        iterations_total=45,
        iterations_per_task_avg=5.6,
        auto_decisions=15,
        human_decisions=5,
        ralph_pass=12,
        ralph_fail=3,
        ralph_blocked=1,
    )

    # Generate retrospective
    filepath = generator.generate(
        project_id="TEST",
        metrics=metrics,
        tasks=[],
        events=[],
        escalations=[],
    )

    print(f"Retrospective written to: {filepath}")
