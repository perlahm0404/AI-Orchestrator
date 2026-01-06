"""
Knowledge Object Service

CRUD operations, matching, and consultation for Knowledge Objects.

Usage:
    from knowledge import service

    # Consult before starting work
    relevant = service.find_relevant(
        project="karematch",
        tags=["auth", "null-check"],
        file_patterns=["src/auth/*"]
    )

    # Create draft after resolution
    service.create_draft(
        issue_id=123,
        what_was_learned="...",
        why_it_matters="...",
        prevention_rule="...",
        detection_pattern="..."
    )

    # Approve draft
    service.approve("KO-km-001")

Implementation: Phase 1
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class KnowledgeObject:
    """
    A Knowledge Object captures institutional learning.

    Fields:
        id: Unique identifier (e.g., "KO-km-001")
        project: Source project
        issue_id: Source issue that generated this knowledge
        what_was_learned: The irreducible insight (1-3 sentences)
        why_it_matters: Impact if ignored
        prevention_rule: How to prevent recurrence
        detection_pattern: Regex/glob to detect similar issues
        tags: For pattern matching
        status: draft | approved
        created_at: Creation timestamp
        approved_at: Approval timestamp (if approved)
    """
    id: str
    project: str
    issue_id: int
    what_was_learned: str
    why_it_matters: str
    prevention_rule: str
    detection_pattern: str
    tags: list[str]
    status: str  # "draft" | "approved"
    created_at: datetime
    approved_at: datetime | None = None


def find_relevant(
    project: str,
    tags: list[str] | None = None,
    file_patterns: list[str] | None = None
) -> list[KnowledgeObject]:
    """
    Find Knowledge Objects relevant to current work.

    Uses tag-based matching (no vector embeddings in v1).

    Args:
        project: Project to search within
        tags: Tags to match
        file_patterns: File patterns to match against detection_pattern

    Returns:
        List of relevant Knowledge Objects
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Knowledge service not yet implemented")


def create_draft(
    issue_id: int,
    what_was_learned: str,
    why_it_matters: str,
    prevention_rule: str,
    detection_pattern: str,
    tags: list[str] | None = None
) -> KnowledgeObject:
    """
    Create a draft Knowledge Object.

    Saves to knowledge/drafts/ as markdown and pending in DB.

    Returns:
        The created KnowledgeObject with status="draft"
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Knowledge service not yet implemented")


def approve(ko_id: str) -> KnowledgeObject:
    """
    Approve a draft Knowledge Object.

    Moves from drafts/ to approved/ and updates DB status.

    Returns:
        The approved KnowledgeObject
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Knowledge service not yet implemented")
