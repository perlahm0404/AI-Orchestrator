"""
Autonomy Contract Loader and Enforcer

Loads agent contracts from YAML and enforces them at runtime.

Usage:
    from governance import contract

    # Load contract
    bugfix_contract = contract.load("bugfix")

    # Check action
    contract.require_allowed(bugfix_contract, "write_file")

    # Check limits
    contract.check_limits(bugfix_contract, lines_added=50, files_changed=3)

Implementation: Phase 0
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import yaml


class ContractViolation(Exception):
    """Raised when an autonomy contract is violated."""
    pass


@dataclass
class Contract:
    """Autonomy contract for an agent."""
    agent: str
    version: str
    allowed_actions: List[str]
    forbidden_actions: List[str]
    requires_approval: List[str]
    limits: Dict[str, Any]
    invariants: Dict[str, Any]
    on_violation: str

    def is_allowed(self, action: str) -> bool:
        """Check if action is allowed."""
        if action in self.forbidden_actions:
            return False
        if action in self.allowed_actions:
            return True
        # Action not listed - default to forbidden for safety
        return False

    def requires_human_approval(self, action: str) -> bool:
        """Check if action requires human approval."""
        return action in self.requires_approval


def load(agent_name: str, contracts_dir: Path | None = None) -> Contract:
    """
    Load autonomy contract for an agent.

    Args:
        agent_name: Name of the agent (e.g., "bugfix", "codequality")
        contracts_dir: Directory containing contracts (defaults to governance/contracts/)

    Returns:
        Loaded Contract

    Raises:
        FileNotFoundError: If contract file doesn't exist
        ValueError: If contract is invalid
    """
    if contracts_dir is None:
        # Default to governance/contracts/ relative to this file
        contracts_dir = Path(__file__).parent / "contracts"

    contract_file = contracts_dir / f"{agent_name}.yaml"

    if not contract_file.exists():
        raise FileNotFoundError(f"Contract not found: {contract_file}")

    with open(contract_file, "r") as f:
        data = yaml.safe_load(f)

    # Validate required fields
    required_fields = ["agent", "version", "allowed_actions", "forbidden_actions"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Contract missing required field: {field}")

    return Contract(
        agent=data["agent"],
        version=data["version"],
        allowed_actions=data["allowed_actions"],
        forbidden_actions=data["forbidden_actions"],
        requires_approval=data.get("requires_approval", []),
        limits=data.get("limits", {}),
        invariants=data.get("invariants", {}),
        on_violation=data.get("on_violation", "halt"),
    )


def require_allowed(contract: Contract, action: str) -> None:
    """
    Require that action is allowed by contract.

    Args:
        contract: The contract to check against
        action: The action to check

    Raises:
        ContractViolation: If action is not allowed
    """
    if action in contract.forbidden_actions:
        raise ContractViolation(
            f"Action '{action}' is forbidden by {contract.agent} contract"
        )

    if not contract.is_allowed(action):
        raise ContractViolation(
            f"Action '{action}' is not in allowed list for {contract.agent} contract"
        )


def check_limits(contract: Contract, **kwargs) -> None:
    """
    Check that limits are not exceeded.

    Args:
        contract: The contract to check against
        **kwargs: Limit values to check (e.g., lines_added=50, files_changed=3)

    Raises:
        ContractViolation: If any limit is exceeded
    """
    for limit_name, limit_value in contract.limits.items():
        # Convert limit names from contract format to kwargs format
        # e.g., max_lines_added -> lines_added
        if limit_name.startswith("max_"):
            kwarg_name = limit_name[4:]  # Remove "max_" prefix
        else:
            kwarg_name = limit_name

        if kwarg_name in kwargs:
            actual_value = kwargs[kwarg_name]
            if actual_value > limit_value:
                raise ContractViolation(
                    f"Limit exceeded: {limit_name}={limit_value}, actual={actual_value}"
                )


def check_invariants(contract: Contract, **kwargs) -> None:
    """
    Check that invariants are satisfied.

    Args:
        contract: The contract to check against
        **kwargs: Invariant values to check (e.g., test_count_unchanged=True)

    Raises:
        ContractViolation: If any invariant is violated
    """
    for invariant_name, expected_value in contract.invariants.items():
        if invariant_name in kwargs:
            actual_value = kwargs[invariant_name]
            if actual_value != expected_value:
                raise ContractViolation(
                    f"Invariant violated: {invariant_name} expected={expected_value}, actual={actual_value}"
                )
