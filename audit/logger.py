"""
Audit Logger

Logs all actions with causality tracking.

Usage:
    from audit import logger

    # Log an action
    action_id = logger.log(
        session_id="abc-123",
        agent="bugfix",
        action="file_write",
        details={"file": "src/auth.ts", "lines_added": 5},
        caused_by="action-456"  # Links to prior action
    )

    # Query causality chain
    chain = logger.get_causality_chain(action_id)

Implementation: Phase 0
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
import uuid


@dataclass
class AuditEntry:
    """A single audit log entry."""
    id: str
    session_id: str
    agent: str
    action: str
    details: dict[str, Any]
    caused_by: str | None  # ID of action that caused this one
    timestamp: datetime
    project: str | None = None
    task_id: str | None = None


def log(
    session_id: str,
    agent: str,
    action: str,
    details: dict[str, Any] | None = None,
    caused_by: str | None = None,
    project: str | None = None,
    task_id: str | None = None
) -> str:
    """
    Log an action to the audit log.

    Args:
        session_id: Current session ID
        agent: Agent that performed the action
        action: Action type (e.g., "file_write", "test_run")
        details: Action-specific details
        caused_by: ID of action that caused this one
        project: Target project
        task_id: Task being worked on

    Returns:
        ID of the created audit entry
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Audit logger not yet implemented")


def get_causality_chain(action_id: str) -> list[AuditEntry]:
    """
    Get the full causality chain for an action.

    Follows caused_by links backward to the root cause.

    Args:
        action_id: Action to trace

    Returns:
        List of AuditEntry from root cause to this action
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Audit logger not yet implemented")


def get_session_log(session_id: str) -> list[AuditEntry]:
    """
    Get all audit entries for a session.

    Args:
        session_id: Session to query

    Returns:
        List of AuditEntry in chronological order
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Audit logger not yet implemented")
