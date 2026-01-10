"""
Event Logger for AI Team Orchestration
Version: 3.0
Part of: AI Team Governance (AI-TEAM-SPEC-V3)

Provides observability by logging significant events to detailed markdown files
and counting all events in metrics.json.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class EventType:
    """Event type constants with metadata."""

    # Advisor Events
    ADVISOR_TRIGGERED = "ADVISOR_TRIGGERED"
    ADVISOR_AUTO_DECIDED = "ADVISOR_AUTO_DECIDED"
    ADVISOR_ESCALATED = "ADVISOR_ESCALATED"

    # Coordinator Events
    COORDINATOR_TASK_CREATED = "COORDINATOR_TASK_CREATED"
    COORDINATOR_TASK_ASSIGNED = "COORDINATOR_TASK_ASSIGNED"
    COORDINATOR_HANDOFF_CREATED = "COORDINATOR_HANDOFF_CREATED"

    # Builder Events
    BUILDER_ITERATION = "BUILDER_ITERATION"
    BUILDER_COMPLETED = "BUILDER_COMPLETED"
    BUILDER_BLOCKED = "BUILDER_BLOCKED"

    # Ralph Events
    RALPH_PASS = "RALPH_PASS"
    RALPH_FAIL = "RALPH_FAIL"
    RALPH_BLOCKED = "RALPH_BLOCKED"

    # Escalation Events
    SCOPE_ESCALATION = "SCOPE_ESCALATION"
    ADR_CONFLICT = "ADR_CONFLICT"

    # Phase Events
    PHASE_COMPLETE = "PHASE_COMPLETE"
    RETROSPECTIVE_CREATED = "RETROSPECTIVE_CREATED"

    # ADR-003: Task Discovery Events
    TASK_DISCOVERED = "TASK_DISCOVERED"
    TASK_DUPLICATE_SKIPPED = "TASK_DUPLICATE_SKIPPED"
    TASK_REGISTERED_MANUALLY = "TASK_REGISTERED_MANUALLY"

    # ADR-004: Resource Protection Events
    RESOURCE_LIMIT_WARNING = "RESOURCE_LIMIT_WARNING"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    RETRY_ESCALATION = "RETRY_ESCALATION"
    COST_THRESHOLD_REACHED = "COST_THRESHOLD_REACHED"


# Events that get detailed markdown logs (significant events)
SIGNIFICANT_EVENTS = {
    EventType.ADVISOR_TRIGGERED,
    EventType.ADVISOR_AUTO_DECIDED,
    EventType.ADVISOR_ESCALATED,
    EventType.COORDINATOR_TASK_CREATED,
    EventType.COORDINATOR_HANDOFF_CREATED,
    EventType.BUILDER_COMPLETED,
    EventType.BUILDER_BLOCKED,
    EventType.RALPH_BLOCKED,
    EventType.SCOPE_ESCALATION,
    EventType.ADR_CONFLICT,
    EventType.PHASE_COMPLETE,
    EventType.RETROSPECTIVE_CREATED,
    # ADR-003: Task discovery events
    EventType.TASK_DISCOVERED,
    # ADR-004: Resource protection events
    EventType.RESOURCE_LIMIT_EXCEEDED,
    EventType.RETRY_ESCALATION,
}


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Event:
    """Represents an event in the AI Team system."""

    type: str
    agent: str
    timestamp: datetime = field(default_factory=utc_now)
    session_id: Optional[str] = None

    # Context about what triggered the event
    context: Dict[str, Any] = field(default_factory=dict)

    # Decision made (if applicable)
    decision: Optional[Dict[str, Any]] = None

    # Impact of the event
    impact: Optional[Dict[str, Any]] = None

    # Escalation info
    escalated: bool = False
    escalation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "agent": self.agent,
            "timestamp": self.timestamp.isoformat() + "Z",
            "session_id": self.session_id,
            "context": self.context,
            "decision": self.decision,
            "impact": self.impact,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

class EventLogger:
    """
    Logs events for AI Team observability.

    - Significant events get detailed markdown files in events/current/
    - All events update counts in events/metrics.json
    """

    def __init__(self, project_root: Path):
        """
        Initialize EventLogger.

        Args:
            project_root: Path to project root (containing AI-Team-Plans/)
        """
        self.project_root = Path(project_root)
        self.events_dir = self.project_root / "AI-Team-Plans" / "events"
        self.current_dir = self.events_dir / "current"
        self.archive_dir = self.events_dir / "archive"
        self.metrics_file = self.events_dir / "metrics.json"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create event directories if they don't exist."""
        self.current_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    # ───────────────────────────────────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────────────────────────────────

    def log_event(self, event: Event) -> str:
        """
        Log an event.

        - Always updates metrics.json counts
        - Creates detailed markdown if significant event

        Args:
            event: The event to log

        Returns:
            Event ID (filename for significant events, or "counted" for others)
        """
        # Always update metrics
        self._update_metrics(event)

        # Create detailed log if significant
        if self._is_significant(event):
            event_id = self._write_detail_log(event)
            return event_id

        return "counted"

    def log(
        self,
        event_type: str,
        agent: str,
        context: Optional[Dict[str, Any]] = None,
        decision: Optional[Dict[str, Any]] = None,
        impact: Optional[Dict[str, Any]] = None,
        escalated: bool = False,
        escalation_reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Convenience method to log an event with individual parameters.

        Args:
            event_type: Type of event (use EventType constants)
            agent: Name of agent that triggered the event
            context: Context about what triggered the event
            decision: Decision made (if applicable)
            impact: Impact of the event
            escalated: Whether this led to escalation
            escalation_reason: Why escalation occurred
            session_id: Current session ID

        Returns:
            Event ID
        """
        event = Event(
            type=event_type,
            agent=agent,
            context=context or {},
            decision=decision,
            impact=impact,
            escalated=escalated,
            escalation_reason=escalation_reason,
            session_id=session_id,
        )
        return self.log_event(event)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.

        Returns:
            Metrics dictionary
        """
        return self._load_metrics()

    def get_events_for_date(self, date: datetime) -> List[Path]:
        """
        Get all detailed event files for a specific date.

        Args:
            date: Date to get events for

        Returns:
            List of event file paths
        """
        date_str = date.strftime("%Y-%m-%d")
        return sorted(self.current_dir.glob(f"{date_str}-*.md"))

    def archive_old_events(self, days_to_keep: int = 7) -> int:
        """
        Archive events older than specified days.

        Args:
            days_to_keep: Number of days of events to keep in current/

        Returns:
            Number of events archived
        """
        cutoff = utc_now().date()
        archived = 0

        for event_file in self.current_dir.glob("*.md"):
            try:
                # Parse date from filename (YYYY-MM-DD-NNN-type.md)
                date_str = event_file.name[:10]
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                days_old = (cutoff - file_date).days
                if days_old > days_to_keep:
                    # Move to archive
                    archive_path = self.archive_dir / event_file.name
                    event_file.rename(archive_path)
                    archived += 1
            except (ValueError, IndexError):
                # Skip files that don't match expected format
                continue

        return archived

    # ───────────────────────────────────────────────────────────────────────────
    # Internal Methods
    # ───────────────────────────────────────────────────────────────────────────

    def _is_significant(self, event: Event) -> bool:
        """Check if event should get detailed logging."""
        return event.type in SIGNIFICANT_EVENTS

    def _write_detail_log(self, event: Event) -> str:
        """
        Write detailed markdown event file.

        Returns:
            Event ID (filename without extension)
        """
        date_str = event.timestamp.strftime("%Y-%m-%d")

        # Get next sequence number for today
        existing = list(self.current_dir.glob(f"{date_str}-*.md"))
        seq = len(existing) + 1

        # Create filename
        event_type_slug = event.type.lower().replace("_", "-")
        event_id = f"{date_str}-{seq:03d}-{event_type_slug}"
        filename = f"{event_id}.md"
        filepath = self.current_dir / filename

        # Generate markdown content
        content = self._format_event_markdown(event, event_id)
        filepath.write_text(content)

        return event_id

    def _format_event_markdown(self, event: Event, event_id: str) -> str:
        """Format event as markdown document."""

        lines = [
            f"# EVENT-{event_id.upper()}",
            "",
            f"**Timestamp**: {event.timestamp.isoformat()}Z",
            f"**Type**: {event.type}",
            f"**Agent**: {event.agent}",
        ]

        if event.session_id:
            lines.append(f"**Session**: {event.session_id}")

        lines.extend([
            "",
            "---",
            "",
            "## Context",
            "",
        ])

        if event.context:
            for key, value in event.context.items():
                lines.append(f"- **{key}**: {value}")
        else:
            lines.append("No additional context.")

        lines.extend([
            "",
            "---",
            "",
            "## Decision Made",
            "",
        ])

        if event.decision:
            for key, value in event.decision.items():
                lines.append(f"- **{key}**: {value}")
        else:
            lines.append("N/A")

        lines.extend([
            "",
            "---",
            "",
            "## Impact",
            "",
        ])

        if event.impact:
            for key, value in event.impact.items():
                lines.append(f"- **{key}**: {value}")
        else:
            lines.append("N/A")

        lines.extend([
            "",
            "---",
            "",
            "## Escalation",
            "",
            f"- **Escalated**: {'Yes' if event.escalated else 'No'}",
            f"- **Reason**: {event.escalation_reason or 'N/A'}",
        ])

        return "\n".join(lines)

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file or create default."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Return default metrics structure
        return self._create_default_metrics()

    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save metrics to file."""
        metrics["generated_at"] = utc_now().isoformat()

        with open(self.metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

    def _create_default_metrics(self) -> Dict[str, Any]:
        """Create default metrics structure."""
        return {
            "version": "3.0",
            "project": self.project_root.name,
            "period": utc_now().strftime("%Y-%m-%d"),
            "generated_at": utc_now().isoformat(),
            "totals": {
                "events_total": 0,
                "events_logged_detail": 0,
                "events_counted_only": 0,
            },
            "by_agent": {},
            "ralph_verdicts": {
                "pass": 0,
                "fail": 0,
                "blocked": 0,
            },
            "escalations": {
                "to_human": 0,
                "scope_triggers": 0,
                "adr_conflicts": 0,
                "low_confidence": 0,
                "strategic_domain": 0,
            },
            "phase_progress": {
                "current_phase": 1,
                "tasks_in_phase": 0,
                "tasks_completed": 0,
                "tasks_blocked": 0,
                "tasks_pending": 0,
            },
            # ADR-003: Task discovery metrics
            "task_discovery": {
                "total_discovered": 0,
                "by_source": {},  # e.g., {"advisor": 5, "cli": 3}
                "duplicates_skipped": 0,
            },
            # ADR-004: Resource usage metrics
            "resource_usage": {
                "limit_warnings": 0,
                "limit_exceeded": 0,
                "retry_escalations": 0,
                "cost_threshold_reached": 0,
            },
            "daily_counts": [],
        }

    def _update_metrics(self, event: Event) -> None:
        """Update metrics.json with event counts."""
        metrics = self._load_metrics()

        # Update totals
        metrics["totals"]["events_total"] += 1
        if self._is_significant(event):
            metrics["totals"]["events_logged_detail"] += 1
        else:
            metrics["totals"]["events_counted_only"] += 1

        # Update by-agent counts
        agent_key = event.agent.lower().replace(" ", "_").replace("-", "_")
        if agent_key not in metrics["by_agent"]:
            metrics["by_agent"][agent_key] = {}

        event_key = event.type.lower()
        metrics["by_agent"][agent_key][event_key] = \
            metrics["by_agent"][agent_key].get(event_key, 0) + 1

        # Update Ralph verdicts
        if event.type == EventType.RALPH_PASS:
            metrics["ralph_verdicts"]["pass"] += 1
        elif event.type == EventType.RALPH_FAIL:
            metrics["ralph_verdicts"]["fail"] += 1
        elif event.type == EventType.RALPH_BLOCKED:
            metrics["ralph_verdicts"]["blocked"] += 1

        # Update escalation counts
        if event.escalated:
            metrics["escalations"]["to_human"] += 1

        if event.type == EventType.SCOPE_ESCALATION:
            metrics["escalations"]["scope_triggers"] += 1
        elif event.type == EventType.ADR_CONFLICT:
            metrics["escalations"]["adr_conflicts"] += 1

        if event.escalation_reason == "LOW_CONFIDENCE":
            metrics["escalations"]["low_confidence"] += 1
        elif event.escalation_reason == "STRATEGIC_DOMAIN":
            metrics["escalations"]["strategic_domain"] += 1

        # ADR-003: Update task discovery metrics
        if event.type == EventType.TASK_DISCOVERED:
            # Ensure task_discovery section exists (backwards compatibility)
            if "task_discovery" not in metrics:
                metrics["task_discovery"] = {
                    "total_discovered": 0,
                    "by_source": {},
                    "duplicates_skipped": 0,
                }

            metrics["task_discovery"]["total_discovered"] += 1

            # Track by source (discovered_by field in context)
            source = event.context.get("discovered_by", "unknown")
            metrics["task_discovery"]["by_source"][source] = \
                metrics["task_discovery"]["by_source"].get(source, 0) + 1

        elif event.type == EventType.TASK_DUPLICATE_SKIPPED:
            if "task_discovery" not in metrics:
                metrics["task_discovery"] = {
                    "total_discovered": 0,
                    "by_source": {},
                    "duplicates_skipped": 0,
                }
            metrics["task_discovery"]["duplicates_skipped"] += 1

        # ADR-004: Update resource usage metrics
        if event.type in (
            EventType.RESOURCE_LIMIT_WARNING,
            EventType.RESOURCE_LIMIT_EXCEEDED,
            EventType.RETRY_ESCALATION,
            EventType.COST_THRESHOLD_REACHED,
        ):
            # Ensure resource_usage section exists (backwards compatibility)
            if "resource_usage" not in metrics:
                metrics["resource_usage"] = {
                    "limit_warnings": 0,
                    "limit_exceeded": 0,
                    "retry_escalations": 0,
                    "cost_threshold_reached": 0,
                }

            if event.type == EventType.RESOURCE_LIMIT_WARNING:
                metrics["resource_usage"]["limit_warnings"] += 1
            elif event.type == EventType.RESOURCE_LIMIT_EXCEEDED:
                metrics["resource_usage"]["limit_exceeded"] += 1
            elif event.type == EventType.RETRY_ESCALATION:
                metrics["resource_usage"]["retry_escalations"] += 1
            elif event.type == EventType.COST_THRESHOLD_REACHED:
                metrics["resource_usage"]["cost_threshold_reached"] += 1

        self._save_metrics(metrics)


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_logger(project_root: Path) -> EventLogger:
    """
    Get an EventLogger instance for a project.

    Args:
        project_root: Path to project root

    Returns:
        EventLogger instance
    """
    return EventLogger(project_root)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python event_logger.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    logger = EventLogger(project_root)

    # Log a test event
    event_id = logger.log(
        event_type=EventType.ADVISOR_TRIGGERED,
        agent="data-advisor",
        context={
            "trigger": "User invoked @data-advisor",
            "topic": "schema design",
        },
        session_id="test-session",
    )

    print(f"Logged event: {event_id}")
    print(f"Metrics: {json.dumps(logger.get_metrics(), indent=2)}")
