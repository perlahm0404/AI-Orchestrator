"""
Escalation System for AI Team Orchestration
Version: 3.0
Part of: AI Team Governance (AI-TEAM-SPEC-V3)

Handles scope escalation, ADR conflicts, and human intervention routing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class EscalationType(Enum):
    """Types of escalation."""
    SCOPE = "scope"                    # Task exceeds scope limits
    ADR_CONFLICT = "adr_conflict"      # Conflicts with existing ADR
    LOW_CONFIDENCE = "low_confidence"  # Advisor not confident
    STRATEGIC = "strategic"            # Strategic domain requires human
    BLOCKED = "blocked"                # Task is blocked
    GUARDRAIL = "guardrail"           # Guardrail violation


class EscalationSeverity(Enum):
    """Severity levels for escalation."""
    INFO = "info"           # FYI, no action needed
    WARNING = "warning"     # Needs attention soon
    URGENT = "urgent"       # Needs immediate attention
    CRITICAL = "critical"   # Blocks all progress


class EscalationStatus(Enum):
    """Status of an escalation."""
    PENDING = "pending"      # Waiting for human
    ACKNOWLEDGED = "acknowledged"  # Human saw it
    RESOLVED = "resolved"    # Human resolved it
    DISMISSED = "dismissed"  # Human dismissed it


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Escalation:
    """Represents an escalation to human."""

    id: str
    type: EscalationType
    severity: EscalationSeverity
    status: EscalationStatus = EscalationStatus.PENDING

    # Context
    source_agent: str = ""
    source_task: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    # For scope escalations
    estimated_files: int = 0
    scope_limit: int = 5

    # For ADR conflicts
    conflicting_adrs: List[str] = field(default_factory=list)
    proposed_action: Optional[str] = None

    # Resolution
    resolved_by: Optional[str] = None
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=utc_now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "source_agent": self.source_agent,
            "source_task": self.source_task,
            "description": self.description,
            "details": self.details,
            "estimated_files": self.estimated_files,
            "scope_limit": self.scope_limit,
            "conflicting_adrs": self.conflicting_adrs,
            "proposed_action": self.proposed_action,
            "resolved_by": self.resolved_by,
            "resolution": self.resolution,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ESCALATION MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class EscalationManager:
    """
    Manages escalations to humans.

    Responsibilities:
    - Create and track escalations
    - Route escalations appropriately
    - Record resolutions
    - Provide escalation history
    """

    # Scope limits by team
    SCOPE_LIMITS = {
        "qa_team": 5,      # 5 files triggers escalation
        "dev_team": 10,    # 10 files triggers escalation
        "advisor": 5,      # Advisors escalate at 5 files
    }

    def __init__(self, project_root: Path):
        """
        Initialize EscalationManager.

        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root)
        self.escalations: Dict[str, Escalation] = {}
        self._sequence = 0

        # Callbacks for different escalation types
        self._callbacks: Dict[EscalationType, List[Callable]] = {
            t: [] for t in EscalationType
        }

    # ───────────────────────────────────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────────────────────────────────

    def escalate_scope(
        self,
        agent: str,
        task_id: str,
        estimated_files: int,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Escalation:
        """
        Escalate due to scope exceeding limits.

        Args:
            agent: Agent that triggered escalation
            task_id: Task that exceeded scope
            estimated_files: Number of files estimated
            description: Description of the scope issue
            details: Additional details

        Returns:
            Created Escalation
        """
        team = self._get_team(agent)
        limit = self.SCOPE_LIMITS.get(team, 5)

        escalation = self._create_escalation(
            type=EscalationType.SCOPE,
            severity=EscalationSeverity.WARNING,
            source_agent=agent,
            source_task=task_id,
            description=description,
            details=details or {},
            estimated_files=estimated_files,
            scope_limit=limit,
        )

        self._trigger_callbacks(escalation)
        return escalation

    def escalate_adr_conflict(
        self,
        agent: str,
        conflicting_adrs: List[str],
        proposed_action: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Escalation:
        """
        Escalate due to ADR conflict.

        Args:
            agent: Agent that detected conflict
            conflicting_adrs: List of conflicting ADR IDs
            proposed_action: What the agent wants to do
            description: Description of the conflict
            details: Additional details

        Returns:
            Created Escalation
        """
        escalation = self._create_escalation(
            type=EscalationType.ADR_CONFLICT,
            severity=EscalationSeverity.URGENT,
            source_agent=agent,
            description=description,
            details=details or {},
            conflicting_adrs=conflicting_adrs,
            proposed_action=proposed_action,
        )

        self._trigger_callbacks(escalation)
        return escalation

    def escalate_low_confidence(
        self,
        agent: str,
        confidence_score: float,
        question: str,
        recommendation: str,
    ) -> Escalation:
        """
        Escalate due to low confidence.

        Args:
            agent: Advisor that lacks confidence
            confidence_score: The confidence score
            question: The question being answered
            recommendation: The proposed recommendation

        Returns:
            Created Escalation
        """
        escalation = self._create_escalation(
            type=EscalationType.LOW_CONFIDENCE,
            severity=EscalationSeverity.INFO,
            source_agent=agent,
            description=f"Low confidence ({confidence_score:.1%}) on: {question[:100]}",
            details={
                "confidence_score": confidence_score,
                "question": question,
                "recommendation": recommendation,
            },
        )

        self._trigger_callbacks(escalation)
        return escalation

    def escalate_strategic(
        self,
        agent: str,
        domain: str,
        question: str,
        recommendation: str,
    ) -> Escalation:
        """
        Escalate due to strategic domain.

        Args:
            agent: Advisor that detected strategic domain
            domain: The strategic domain
            question: The question
            recommendation: The proposed recommendation

        Returns:
            Created Escalation
        """
        escalation = self._create_escalation(
            type=EscalationType.STRATEGIC,
            severity=EscalationSeverity.WARNING,
            source_agent=agent,
            description=f"Strategic decision required in domain: {domain}",
            details={
                "domain": domain,
                "question": question,
                "recommendation": recommendation,
            },
        )

        self._trigger_callbacks(escalation)
        return escalation

    def escalate_blocked(
        self,
        agent: str,
        task_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Escalation:
        """
        Escalate due to blocked task.

        Args:
            agent: Agent that is blocked
            task_id: Blocked task
            reason: Why it's blocked
            details: Additional details

        Returns:
            Created Escalation
        """
        escalation = self._create_escalation(
            type=EscalationType.BLOCKED,
            severity=EscalationSeverity.URGENT,
            source_agent=agent,
            source_task=task_id,
            description=f"Task blocked: {reason}",
            details=details or {},
        )

        self._trigger_callbacks(escalation)
        return escalation

    def escalate_guardrail(
        self,
        agent: str,
        guardrail: str,
        violation: str,
        file_path: Optional[str] = None,
    ) -> Escalation:
        """
        Escalate due to guardrail violation.

        Args:
            agent: Agent that violated guardrail
            guardrail: Which guardrail was violated
            violation: Description of violation
            file_path: File where violation occurred

        Returns:
            Created Escalation
        """
        escalation = self._create_escalation(
            type=EscalationType.GUARDRAIL,
            severity=EscalationSeverity.CRITICAL,
            source_agent=agent,
            description=f"Guardrail violation: {guardrail}",
            details={
                "guardrail": guardrail,
                "violation": violation,
                "file_path": file_path,
            },
        )

        self._trigger_callbacks(escalation)
        return escalation

    # ───────────────────────────────────────────────────────────────────────────
    # Resolution
    # ───────────────────────────────────────────────────────────────────────────

    def acknowledge(self, escalation_id: str) -> Optional[Escalation]:
        """Acknowledge an escalation."""
        if escalation_id not in self.escalations:
            return None

        esc = self.escalations[escalation_id]
        esc.status = EscalationStatus.ACKNOWLEDGED
        esc.acknowledged_at = utc_now()
        return esc

    def resolve(
        self,
        escalation_id: str,
        resolved_by: str,
        resolution: str,
        notes: Optional[str] = None,
    ) -> Optional[Escalation]:
        """
        Resolve an escalation.

        Args:
            escalation_id: Escalation to resolve
            resolved_by: Who resolved it
            resolution: How it was resolved
            notes: Additional notes

        Returns:
            Resolved Escalation
        """
        if escalation_id not in self.escalations:
            return None

        esc = self.escalations[escalation_id]
        esc.status = EscalationStatus.RESOLVED
        esc.resolved_by = resolved_by
        esc.resolution = resolution
        esc.resolution_notes = notes
        esc.resolved_at = utc_now()
        return esc

    def dismiss(
        self,
        escalation_id: str,
        dismissed_by: str,
        reason: str,
    ) -> Optional[Escalation]:
        """Dismiss an escalation."""
        if escalation_id not in self.escalations:
            return None

        esc = self.escalations[escalation_id]
        esc.status = EscalationStatus.DISMISSED
        esc.resolved_by = dismissed_by
        esc.resolution_notes = f"Dismissed: {reason}"
        esc.resolved_at = utc_now()
        return esc

    # ───────────────────────────────────────────────────────────────────────────
    # Queries
    # ───────────────────────────────────────────────────────────────────────────

    def get_pending(self) -> List[Escalation]:
        """Get all pending escalations."""
        return [
            e for e in self.escalations.values()
            if e.status == EscalationStatus.PENDING
        ]

    def get_by_type(self, type: EscalationType) -> List[Escalation]:
        """Get escalations by type."""
        return [e for e in self.escalations.values() if e.type == type]

    def get_by_agent(self, agent: str) -> List[Escalation]:
        """Get escalations from specific agent."""
        return [e for e in self.escalations.values() if e.source_agent == agent]

    def get_stats(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        all_esc = list(self.escalations.values())

        by_type = {}
        for t in EscalationType:
            by_type[t.value] = len([e for e in all_esc if e.type == t])

        by_status = {}
        for s in EscalationStatus:
            by_status[s.value] = len([e for e in all_esc if e.status == s])

        return {
            "total": len(all_esc),
            "pending": len(self.get_pending()),
            "by_type": by_type,
            "by_status": by_status,
        }

    # ───────────────────────────────────────────────────────────────────────────
    # Callbacks
    # ───────────────────────────────────────────────────────────────────────────

    def register_callback(
        self,
        type: EscalationType,
        callback: Callable[[Escalation], None],
    ) -> None:
        """Register callback for escalation type."""
        self._callbacks[type].append(callback)

    def _trigger_callbacks(self, escalation: Escalation) -> None:
        """Trigger callbacks for escalation."""
        for callback in self._callbacks[escalation.type]:
            try:
                callback(escalation)
            except Exception as e:
                print(f"Callback error: {e}")

    # ───────────────────────────────────────────────────────────────────────────
    # Internal
    # ───────────────────────────────────────────────────────────────────────────

    def _create_escalation(self, **kwargs) -> Escalation:
        """Create and store an escalation."""
        self._sequence += 1
        esc_id = f"ESC-{self._sequence:04d}"

        escalation = Escalation(id=esc_id, **kwargs)
        self.escalations[esc_id] = escalation
        return escalation

    def _get_team(self, agent: str) -> str:
        """Determine team from agent name."""
        agent_lower = agent.lower()
        if "advisor" in agent_lower:
            return "advisor"
        if any(kw in agent_lower for kw in ["bugfix", "codequality", "testfixer"]):
            return "qa_team"
        return "dev_team"


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPE CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class ScopeChecker:
    """
    Checks if a task exceeds scope limits.

    Used before task execution to determine if escalation needed.
    """

    def __init__(self, escalation_manager: EscalationManager):
        """
        Initialize ScopeChecker.

        Args:
            escalation_manager: Manager for creating escalations
        """
        self.escalation_manager = escalation_manager

    def check_scope(
        self,
        agent: str,
        task_id: str,
        estimated_files: int,
        file_list: Optional[List[str]] = None,
        on_exceed: Optional[Callable[["Escalation"], None]] = None,
    ) -> bool:
        """
        Check if task scope is acceptable.

        Args:
            agent: Agent that will execute
            task_id: Task being checked
            estimated_files: Estimated number of files
            file_list: Optional list of specific files
            on_exceed: Callback if scope exceeded

        Returns:
            True if scope is OK, False if exceeded (escalation created)
        """
        team = self.escalation_manager._get_team(agent)
        limit = EscalationManager.SCOPE_LIMITS.get(team, 5)

        if estimated_files <= limit:
            return True

        # Scope exceeded - create escalation
        description = (
            f"Task {task_id} estimates {estimated_files} files, "
            f"exceeding limit of {limit} for {team}"
        )

        escalation = self.escalation_manager.escalate_scope(
            agent=agent,
            task_id=task_id,
            estimated_files=estimated_files,
            description=description,
            details={"file_list": file_list} if file_list else None,
        )

        if on_exceed:
            on_exceed(escalation)

        return False

    def estimate_scope(self, files: List[str]) -> int:
        """Estimate scope from file list."""
        return len(files)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python escalation.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    manager = EscalationManager(project_root)

    # Test scope escalation
    esc1 = manager.escalate_scope(
        agent="BugFixAgent",
        task_id="TASK-0001",
        estimated_files=8,
        description="Bug fix touches 8 files",
    )
    print(f"Created: {esc1.id} - {esc1.type.value}")

    # Test ADR conflict
    esc2 = manager.escalate_adr_conflict(
        agent="data-advisor",
        conflicting_adrs=["ADR-001", "ADR-003"],
        proposed_action="Use MongoDB instead of PostgreSQL",
        description="Proposed change conflicts with existing ADR",
    )
    print(f"Created: {esc2.id} - {esc2.type.value}")

    # Print stats
    print(f"\nStats: {json.dumps(manager.get_stats(), indent=2)}")
