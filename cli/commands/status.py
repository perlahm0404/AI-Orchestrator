"""
Status Command

Shows system status or specific task status.

Usage:
    aibrain status              # Overall system status
    aibrain status TASK-123     # Specific task status

Implementation: Phase 1
"""


def system_status() -> dict:
    """
    Get overall system status.

    Returns:
        Dict with:
        - mode: Current AI_BRAIN_MODE
        - active_sessions: Count of running sessions
        - pending_review: Tasks awaiting approval
        - pending_ko: Knowledge Objects awaiting approval
        - circuit_breakers: Any tripped circuits
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Status command not yet implemented")


def task_status(task_id: str) -> dict:
    """
    Get specific task status.

    Args:
        task_id: Task to query

    Returns:
        Dict with:
        - task_id: The task ID
        - status: Current status
        - agent: Assigned agent
        - session_id: Current session (if active)
        - evidence: Collected evidence
        - audit_log: Recent audit entries
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Status command not yet implemented")
