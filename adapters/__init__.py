"""
Application Adapters

Thin wrappers that connect AI Brain to target application repos.

Adapters provide:
- Project-specific configuration (paths, commands)
- Ralph invocation for that project
- AppContext for the governance engine

Adapters do NOT:
- Define policy (that's in ralph/policy/)
- Make governance decisions (that's Ralph's job)
- Store state (stateless, config-only)

Each target app has its own adapter:
- adapters/karematch/
- adapters/credentialmate/

See: v4-RALPH-GOVERNANCE-ENGINE.md Section "Application-Level Design"
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adapters.base import BaseAdapter

from adapters.karematch import KareMatchAdapter
from adapters.credentialmate import CredentialMateAdapter

__all__ = ['get_adapter', 'KareMatchAdapter', 'CredentialMateAdapter']


def get_adapter(project: str | None = None) -> "BaseAdapter":
    """
    Get the appropriate adapter for a project.

    Args:
        project: Project name ("karematch", "credentialmate") or path to project root.
                If None, uses cwd to auto-detect.

    Returns:
        Adapter instance for the project

    Raises:
        ValueError: If project cannot be identified
    """
    # Handle explicit project names
    if project in ("karematch", "km"):
        return KareMatchAdapter()
    if project in ("credentialmate", "cm"):
        return CredentialMateAdapter()

    # Handle path-based detection
    if project is None:
        project = str(Path.cwd())

    path = Path(project).resolve()

    # Check for KareMatch
    if "karematch" in str(path).lower():
        return KareMatchAdapter()

    # Check for CredentialMate
    if "credentialmate" in str(path).lower():
        return CredentialMateAdapter()

    # Default to KareMatch if we can't determine
    # (This handles the case when Ralph runs from AI_Orchestrator repo)
    return KareMatchAdapter()
