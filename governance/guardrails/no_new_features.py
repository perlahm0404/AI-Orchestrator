"""
No New Features Guardrail

Detects scope creep - when a bug fix tries to add new features.

Signals that indicate scope creep:
- New API routes added
- New database tables
- New UI components
- New dependencies
- Significant new code paths

See: v4 Planning.md Section "No-New-Features Guardrail"

Implementation: Phase 1
"""

from dataclasses import dataclass


@dataclass
class ScopeCreepWarning:
    """Warning about potential scope creep."""
    type: str  # e.g., "new_route", "new_dependency"
    file: str
    description: str


def analyze_changes(
    changed_files: list[str],
    diff_content: str
) -> list[ScopeCreepWarning]:
    """
    Analyze changes for scope creep indicators.

    Args:
        changed_files: List of files that changed
        diff_content: Git diff content

    Returns:
        List of warnings (empty if no scope creep detected)
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("No new features guardrail not yet implemented")
