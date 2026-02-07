"""
Decision Audit Trail - JSONL Append-Only Logging

Phase 4 of Stateless Memory Architecture: Decision trees for full audit trail,
HIPAA compliance, and debugging support.

Features:
- JSONL format (JSON Lines - one JSON object per line)
- Append-only (immutable audit trail)
- Structured decision trees with parent-child relationships
- HIPAA-compliant with configurable PII redaction
- Thread-safe concurrent writes
- Efficient replay and filtering

File Structure:
    .aibrain/audit/decisions-{project}-{YYYYMMDD}.jsonl

Example Entry:
    {"id": "DEC-20260207-143052-001", "timestamp": "2026-02-07T14:30:52.123456",
     "type": "task_routed", "project": "credentialmate", "task_id": "TASK-001",
     "decision": "route_to_bugfix", "reason": "Low complexity, single file",
     "parent_id": null, "metadata": {...}}

Usage:
    from orchestration.decision_audit import DecisionAudit

    audit = DecisionAudit(project="credentialmate")

    # Log a decision
    audit.log_decision(
        decision_type="task_routed",
        task_id="TASK-001",
        decision="route_to_bugfix",
        reason="Low complexity, single file fix",
        metadata={"file": "auth.py", "agent": "bugfix"}
    )

    # Query decisions
    decisions = audit.get_decisions_for_task("TASK-001")
    tree = audit.build_decision_tree("TASK-001")
"""

import json
import threading
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Any, Iterator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    """Types of decisions that can be audited."""
    # Task lifecycle
    TASK_CREATED = "task_created"
    TASK_ROUTED = "task_routed"
    TASK_STARTED = "task_started"
    TASK_ITERATION = "task_iteration"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    TASK_FAILED = "task_failed"

    # Agent decisions
    AGENT_SELECTED = "agent_selected"
    AGENT_ESCALATED = "agent_escalated"
    AGENT_DELEGATED = "agent_delegated"

    # Verification
    RALPH_PASS = "ralph_pass"
    RALPH_FAIL = "ralph_fail"
    RALPH_BLOCKED = "ralph_blocked"

    # Knowledge
    KO_CONSULTED = "ko_consulted"
    KO_CREATED = "ko_created"
    KO_APPROVED = "ko_approved"

    # Resource management
    COST_WARNING = "cost_warning"
    COST_LIMIT_HIT = "cost_limit_hit"
    RETRY_ESCALATED = "retry_escalated"

    # Human interaction
    HUMAN_APPROVAL_REQUESTED = "human_approval_requested"
    HUMAN_APPROVAL_GRANTED = "human_approval_granted"
    HUMAN_APPROVAL_DENIED = "human_approval_denied"

    # Session
    SESSION_STARTED = "session_started"
    SESSION_RESUMED = "session_resumed"
    SESSION_COMPLETED = "session_completed"
    SESSION_ARCHIVED = "session_archived"

    # Custom
    CUSTOM = "custom"


@dataclass
class DecisionEntry:
    """A single decision entry in the audit trail."""
    id: str
    timestamp: str
    type: str
    project: str
    task_id: Optional[str]
    decision: str
    reason: str
    parent_id: Optional[str] = None
    agent: Optional[str] = None
    iteration: Optional[int] = None
    cost_usd: Optional[float] = None
    tokens_used: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        # Generate checksum for integrity verification
        data_for_checksum = {k: v for k, v in data.items() if k != 'checksum'}
        data['checksum'] = hashlib.sha256(
            json.dumps(data_for_checksum, sort_keys=True).encode()
        ).hexdigest()[:16]
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "DecisionEntry":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class DecisionAudit:
    """
    JSONL-based decision audit trail.

    Thread-safe, append-only logging of all agent decisions
    for compliance, debugging, and analytics.
    """

    def __init__(
        self,
        project: str,
        audit_dir: Optional[Path] = None,
        redact_pii: bool = False,
    ):
        """
        Initialize decision audit.

        Args:
            project: Project name (e.g., "credentialmate")
            audit_dir: Directory for audit files (default: .aibrain/audit)
            redact_pii: Enable PII redaction for HIPAA compliance
        """
        self.project = project
        self.redact_pii = redact_pii
        self.audit_dir = audit_dir or Path(".aibrain/audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._decision_counter = 0
        self._parent_stack: list[str] = []  # For nested decision tracking

    def _get_audit_file(self, for_date: Optional[date] = None) -> Path:
        """Get the audit file path for a given date."""
        target_date = for_date or date.today()
        filename = f"decisions-{self.project}-{target_date.strftime('%Y%m%d')}.jsonl"
        return self.audit_dir / filename

    def _generate_id(self) -> str:
        """Generate unique decision ID."""
        now = datetime.now()
        with self._lock:
            self._decision_counter += 1
            return f"DEC-{now.strftime('%Y%m%d-%H%M%S')}-{self._decision_counter:03d}"

    def _redact_if_needed(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact PII fields if redaction is enabled."""
        if not self.redact_pii:
            return data

        pii_fields = ['email', 'phone', 'ssn', 'address', 'name', 'patient_id']
        redacted = data.copy()

        for key, value in redacted.items():
            if isinstance(value, str):
                key_lower = key.lower()
                if any(pii in key_lower for pii in pii_fields):
                    redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_if_needed(value)

        return redacted

    def log_decision(
        self,
        decision_type: str | DecisionType,
        decision: str,
        reason: str,
        task_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        agent: Optional[str] = None,
        iteration: Optional[int] = None,
        cost_usd: Optional[float] = None,
        tokens_used: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Log a decision to the audit trail.

        Args:
            decision_type: Type of decision (from DecisionType enum or string)
            decision: The decision that was made
            reason: Why this decision was made
            task_id: Associated task ID (optional)
            parent_id: Parent decision ID for tree structure (optional)
            agent: Agent that made the decision (optional)
            iteration: Iteration number (optional)
            cost_usd: Cost incurred (optional)
            tokens_used: Tokens used (optional)
            metadata: Additional metadata (optional)

        Returns:
            Decision ID
        """
        decision_id = self._generate_id()

        # Use parent from stack if not explicitly provided
        if parent_id is None and self._parent_stack:
            parent_id = self._parent_stack[-1]

        # Handle enum or string
        type_str = decision_type.value if isinstance(decision_type, DecisionType) else decision_type

        entry = DecisionEntry(
            id=decision_id,
            timestamp=datetime.now().isoformat(),
            type=type_str,
            project=self.project,
            task_id=task_id,
            decision=decision,
            reason=reason,
            parent_id=parent_id,
            agent=agent,
            iteration=iteration,
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            metadata=self._redact_if_needed(metadata or {}),
        )

        # Append to JSONL file (thread-safe)
        with self._lock:
            audit_file = self._get_audit_file()
            with open(audit_file, 'a') as f:
                f.write(entry.to_json() + '\n')

        logger.debug(f"Decision logged: {decision_id} - {type_str}: {decision}")
        return decision_id

    def push_parent(self, decision_id: str) -> None:
        """Push a decision ID onto the parent stack for nested tracking."""
        self._parent_stack.append(decision_id)

    def pop_parent(self) -> Optional[str]:
        """Pop a decision ID from the parent stack."""
        if self._parent_stack:
            return self._parent_stack.pop()
        return None

    def log_task_started(
        self,
        task_id: str,
        agent: str,
        description: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Log task start and push as parent for subsequent decisions."""
        decision_id = self.log_decision(
            decision_type=DecisionType.TASK_STARTED,
            decision=f"start_{agent}",
            reason=description,
            task_id=task_id,
            agent=agent,
            metadata=metadata,
        )
        self.push_parent(decision_id)
        return decision_id

    def log_task_completed(
        self,
        task_id: str,
        verdict: str,
        iterations: int,
        cost_usd: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Log task completion and pop from parent stack."""
        self.pop_parent()
        return self.log_decision(
            decision_type=DecisionType.TASK_COMPLETED,
            decision=f"completed_{verdict}",
            reason=f"Task completed after {iterations} iterations",
            task_id=task_id,
            iteration=iterations,
            cost_usd=cost_usd,
            metadata=metadata,
        )

    def log_iteration(
        self,
        task_id: str,
        iteration: int,
        action: str,
        result: str,
        agent: Optional[str] = None,
        cost_usd: Optional[float] = None,
        tokens_used: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Log an iteration within a task."""
        return self.log_decision(
            decision_type=DecisionType.TASK_ITERATION,
            decision=action,
            reason=result,
            task_id=task_id,
            agent=agent,
            iteration=iteration,
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            metadata=metadata,
        )

    def log_ralph_verdict(
        self,
        task_id: str,
        verdict: str,
        reason: str,
        files_changed: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Log Ralph verification result."""
        verdict_upper = verdict.upper()
        decision_type = {
            "PASS": DecisionType.RALPH_PASS,
            "FAIL": DecisionType.RALPH_FAIL,
            "BLOCKED": DecisionType.RALPH_BLOCKED,
        }.get(verdict_upper, DecisionType.RALPH_FAIL)

        return self.log_decision(
            decision_type=decision_type,
            decision=f"ralph_{verdict_upper.lower()}",
            reason=reason,
            task_id=task_id,
            metadata={**(metadata or {}), "files_changed": files_changed or []},
        )

    def get_decisions_for_task(self, task_id: str) -> list[DecisionEntry]:
        """Get all decisions for a specific task."""
        decisions = []

        # Search across all audit files
        for audit_file in sorted(self.audit_dir.glob(f"decisions-{self.project}-*.jsonl")):
            with open(audit_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = DecisionEntry.from_json(line)
                        if entry.task_id == task_id:
                            decisions.append(entry)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse audit line: {e}")

        return sorted(decisions, key=lambda d: d.timestamp)

    def get_decisions_for_date(self, target_date: date) -> Iterator[DecisionEntry]:
        """Get all decisions for a specific date."""
        audit_file = self._get_audit_file(target_date)
        if not audit_file.exists():
            return

        with open(audit_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield DecisionEntry.from_json(line)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse audit line: {e}")

    def build_decision_tree(self, task_id: str) -> dict[str, Any]:
        """
        Build a decision tree for a task.

        Returns a nested dictionary representing the decision hierarchy.
        """
        decisions = self.get_decisions_for_task(task_id)

        # Build lookup table
        by_id: dict[str, DecisionEntry] = {d.id: d for d in decisions}
        children: dict[str, list[str]] = {d.id: [] for d in decisions}

        # Find root decisions and build tree
        roots: list[str] = []
        for d in decisions:
            if d.parent_id and d.parent_id in children:
                children[d.parent_id].append(d.id)
            else:
                roots.append(d.id)

        def build_node(decision_id: str) -> dict[str, Any]:
            decision = by_id[decision_id]
            node: dict[str, Any] = {
                "id": decision.id,
                "type": decision.type,
                "decision": decision.decision,
                "reason": decision.reason,
                "timestamp": decision.timestamp,
                "agent": decision.agent,
                "iteration": decision.iteration,
                "children": [build_node(c) for c in children[decision_id]],
            }
            if decision.cost_usd is not None:
                node["cost_usd"] = decision.cost_usd
            return node

        return {
            "task_id": task_id,
            "project": self.project,
            "decision_count": len(decisions),
            "tree": [build_node(r) for r in roots],
        }

    def get_summary_stats(self, target_date: Optional[date] = None) -> dict[str, Any]:
        """Get summary statistics for audit entries."""
        target_date = target_date or date.today()
        decisions = list(self.get_decisions_for_date(target_date))

        if not decisions:
            return {"date": target_date.isoformat(), "count": 0}

        type_counts: dict[str, int] = {}
        total_cost = 0.0
        total_tokens = 0

        for d in decisions:
            type_counts[d.type] = type_counts.get(d.type, 0) + 1
            if d.cost_usd:
                total_cost += d.cost_usd
            if d.tokens_used:
                total_tokens += d.tokens_used

        return {
            "date": target_date.isoformat(),
            "project": self.project,
            "count": len(decisions),
            "by_type": type_counts,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "unique_tasks": len(set(d.task_id for d in decisions if d.task_id)),
        }

    def verify_integrity(self, target_date: Optional[date] = None) -> dict[str, Any]:
        """Verify checksum integrity of audit entries."""
        target_date = target_date or date.today()
        decisions = list(self.get_decisions_for_date(target_date))

        valid = 0
        invalid = 0
        missing_checksum = 0

        for d in decisions:
            if not d.checksum:
                missing_checksum += 1
                continue

            # Recalculate checksum
            data = asdict(d)
            data_for_checksum = {k: v for k, v in data.items() if k != 'checksum'}
            expected = hashlib.sha256(
                json.dumps(data_for_checksum, sort_keys=True).encode()
            ).hexdigest()[:16]

            if expected == d.checksum:
                valid += 1
            else:
                invalid += 1

        return {
            "date": target_date.isoformat(),
            "total": len(decisions),
            "valid": valid,
            "invalid": invalid,
            "missing_checksum": missing_checksum,
            "integrity_ok": invalid == 0,
        }


# Convenience function for quick logging
_default_audits: dict[str, DecisionAudit] = {}


def get_audit(project: str) -> DecisionAudit:
    """Get or create a DecisionAudit instance for a project."""
    if project not in _default_audits:
        _default_audits[project] = DecisionAudit(project=project)
    return _default_audits[project]


def log_decision(
    project: str,
    decision_type: str | DecisionType,
    decision: str,
    reason: str,
    **kwargs: Any,
) -> str:
    """Quick log a decision to the audit trail."""
    return get_audit(project).log_decision(
        decision_type=decision_type,
        decision=decision,
        reason=reason,
        **kwargs,
    )
