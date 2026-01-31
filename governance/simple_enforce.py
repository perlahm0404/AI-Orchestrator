"""
Simplified Governance Enforcement (Phase 5)

Single enforcement point for all governance checks.
Target: ~50 lines of core logic.

Usage:
    from governance.simple_enforce import check_action, ActionContext

    context = ActionContext(team="qa-team", action="write_file", branch="main")
    check_action(context)  # Raises ContractViolation if not allowed
"""

import fnmatch
import yaml  # type: ignore[import-untyped]
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class ContractViolation(Exception):
    """Raised when an action violates governance contract."""
    pass


@dataclass
class SimpleContract:
    """Simplified governance contract."""
    name: str
    branches: List[str]
    allowed_actions: List[str]
    forbidden_actions: List[str] = field(default_factory=list)
    max_lines_changed: int = 100
    max_files_changed: int = 5
    max_iterations: int = 15


@dataclass
class ActionContext:
    """Context for a governance check."""
    team: str
    action: str
    branch: str = "main"
    lines_changed: int = 0
    files_changed: int = 0
    iteration: int = 1


def load_contract(team: str, contracts_dir: Optional[Path] = None) -> SimpleContract:
    """
    Load a contract from YAML file.

    Args:
        team: Team name (e.g., "qa-team")
        contracts_dir: Directory containing contract YAML files

    Returns:
        SimpleContract loaded from file

    Raises:
        FileNotFoundError: If contract file doesn't exist
    """
    if contracts_dir is None:
        contracts_dir = Path(__file__).parent / "contracts"

    contract_file = contracts_dir / f"{team}.yaml"
    if not contract_file.exists():
        raise FileNotFoundError(f"Contract not found: {contract_file}")

    with contract_file.open() as f:
        data = yaml.safe_load(f)

    limits = data.get("limits", {})

    return SimpleContract(
        name=data["name"],
        branches=data.get("branches", ["main"]),
        allowed_actions=data.get("allowed_actions", []),
        forbidden_actions=data.get("forbidden_actions", []),
        max_lines_changed=limits.get("max_lines_changed", 100),
        max_files_changed=limits.get("max_files_changed", 5),
        max_iterations=limits.get("max_iterations", 15),
    )


def _matches_branch(branch: str, patterns: List[str]) -> bool:
    """Check if branch matches any pattern (supports * and ** wildcards)."""
    for pattern in patterns:
        # Convert ** to match any depth, * to match single level
        if "**" in pattern:
            # ** matches any path depth
            regex_pattern = pattern.replace("**", "*")
            if fnmatch.fnmatch(branch, regex_pattern):
                return True
        elif fnmatch.fnmatch(branch, pattern):
            return True
    return False


def check_action(context: ActionContext) -> bool:
    """
    Check if an action is allowed by governance.

    Args:
        context: ActionContext with action details

    Returns:
        True if action is allowed

    Raises:
        ContractViolation: If action violates contract
    """
    contract = load_contract(context.team)

    # Check forbidden actions first
    if context.action in contract.forbidden_actions:
        raise ContractViolation(
            f"Action '{context.action}' is forbidden for {context.team}"
        )

    # Check if action is allowed
    if context.action not in contract.allowed_actions:
        raise ContractViolation(
            f"Action '{context.action}' is not allowed for {context.team}"
        )

    # Check branch permissions
    if not _matches_branch(context.branch, contract.branches):
        raise ContractViolation(
            f"Branch '{context.branch}' is not allowed for {context.team}"
        )

    # Check limits
    if context.lines_changed > contract.max_lines_changed:
        raise ContractViolation(
            f"Too many lines changed: {context.lines_changed} > {contract.max_lines_changed}"
        )

    if context.files_changed > contract.max_files_changed:
        raise ContractViolation(
            f"Too many files changed: {context.files_changed} > {contract.max_files_changed}"
        )

    if context.iteration > contract.max_iterations:
        raise ContractViolation(
            f"Too many iterations: {context.iteration} > {contract.max_iterations}"
        )

    return True
