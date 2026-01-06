"""
Checkpoint / Resume Capability

Saves session state for resume after interruption.

Checkpoint schema (JSON):
{
    "session_id": "abc-123",
    "issue_id": 123,
    "project": "karematch",
    "branch": "fix/TASK-123-null-check",
    "phase": "fix_applied",
    "started_at": "2026-01-05T14:00:00Z",
    "last_checkpoint_at": "2026-01-05T14:32:00Z",
    "actions_completed": [...],
    "next_action": "run_ralph_verification",
    "evidence": {...}
}

Checkpoints are saved:
- After each major phase (test written, fix applied, etc.)
- Periodically during long operations
- Before any risky operation

Implementation: Phase 0
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json


@dataclass
class Checkpoint:
    """Session checkpoint for resume."""
    session_id: str
    issue_id: int
    project: str
    branch: str
    phase: str
    started_at: datetime
    last_checkpoint_at: datetime
    actions_completed: list[str]
    next_action: str
    evidence: dict


CHECKPOINT_DIR = Path("state/checkpoints")


def save(checkpoint: Checkpoint) -> Path:
    """
    Save a checkpoint.

    Args:
        checkpoint: Checkpoint to save

    Returns:
        Path to saved checkpoint file
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Checkpoint not yet implemented")


def load(session_id: str) -> Checkpoint | None:
    """
    Load a checkpoint.

    Args:
        session_id: Session to load checkpoint for

    Returns:
        Checkpoint if found, None otherwise
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Checkpoint not yet implemented")


def delete(session_id: str) -> None:
    """
    Delete a checkpoint (after successful completion).

    Args:
        session_id: Session to delete checkpoint for
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Checkpoint not yet implemented")
