"""
Parking Lot System - Idea capture and deferral management

Two-tier system:
1. Icebox: Quick capture for raw ideas (.aibrain/icebox/)
2. Work Queue Integration: Extended TaskStatus with "parked" status

Usage:
    from parking import capture_idea, list_ideas, promote_to_parked_task

    # Capture an idea
    idea = capture_idea(
        title="Add dark mode support",
        description="Allow users to toggle dark theme",
        project="credentialmate"
    )

    # Later, promote to work queue
    task_id = promote_to_parked_task(idea.id, project="credentialmate")
"""

from parking.icebox import IceboxIdea
from parking.service import (
    capture_idea,
    list_ideas,
    get_idea,
    promote_to_parked_task,
    promote_to_pending_task,
    archive_idea,
    get_stale_ideas,
)

__all__ = [
    "IceboxIdea",
    "capture_idea",
    "list_ideas",
    "get_idea",
    "promote_to_parked_task",
    "promote_to_pending_task",
    "archive_idea",
    "get_stale_ideas",
]
