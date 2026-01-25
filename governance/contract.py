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
from typing import Any, Dict, List, Optional
import yaml


class ContractViolation(Exception):
    """Raised when an autonomy contract is violated."""
    pass


@dataclass
class MCPToolsConfig:
    """MCP tools configuration for an agent contract."""
    allowed_servers: List[str]
    forbidden_servers: List[str]
    requires_approval: List[str]
    max_tools: int = 20
    priority_tools: Optional[List[str]] = None

    def __post_init__(self):
        if self.priority_tools is None:
            self.priority_tools = []


@dataclass
class Contract:
    """Autonomy contract for an agent or team."""
    agent: str
    version: str
    allowed_actions: List[str]
    forbidden_actions: List[str]
    requires_approval: List[str]
    limits: Dict[str, Any]
    invariants: Dict[str, Any]
    on_violation: str
    # v5: Branch restrictions for team contracts
    branch_restrictions: Optional[Dict[str, List[str]]] = None
    team: Optional[str] = None
    autonomy_level: Optional[str] = None
    # v6: MCP tools configuration
    mcp_tools: Optional[MCPToolsConfig] = None

    def is_allowed(self, action: str) -> bool:
        """Check if action is allowed."""
        if action in self.forbidden_actions:
            return False
        if action in self.allowed_actions:
            return True
        # Action not listed - default to forbidden for safety
        return False

    def is_mcp_tool_allowed(self, server: str, tool: str) -> bool:
        """
        Check if an MCP tool is allowed for this agent.

        Args:
            server: MCP server name (e.g., "filesystem", "github")
            tool: Tool name (e.g., "read_file", "create_pr")

        Returns:
            True if the tool is allowed
        """
        if self.mcp_tools is None:
            return True  # No MCP restrictions = all allowed

        # Check forbidden servers
        if server in self.mcp_tools.forbidden_servers:
            return False

        # Check allowed servers (empty list = all allowed)
        if self.mcp_tools.allowed_servers and server not in self.mcp_tools.allowed_servers:
            return False

        return True

    def requires_mcp_approval(self, server: str, tool: str) -> bool:
        """
        Check if an MCP tool requires human approval.

        Args:
            server: MCP server name
            tool: Tool name

        Returns:
            True if tool requires approval before use
        """
        if self.mcp_tools is None:
            return False

        # Check tool-level approval requirements
        tool_key = f"{server}:{tool}"
        if tool_key in self.mcp_tools.requires_approval:
            return True

        # Check server-level approval (e.g., "github:*")
        server_wildcard = f"{server}:*"
        if server_wildcard in self.mcp_tools.requires_approval:
            return True

        return False

    def requires_human_approval(self, action: str) -> bool:
        """Check if action requires human approval."""
        return action in self.requires_approval

    def is_branch_allowed(self, branch: str) -> bool:
        """
        Check if the contract allows working on a given branch.

        Args:
            branch: Current git branch name

        Returns:
            True if branch is allowed, False otherwise
        """
        if self.branch_restrictions is None:
            return True  # No restrictions = all branches allowed

        allowed_patterns = self.branch_restrictions.get("allowed_patterns", [])
        forbidden_patterns = self.branch_restrictions.get("forbidden_patterns", [])

        # Check forbidden first
        for pattern in forbidden_patterns:
            if self._branch_matches_pattern(branch, pattern):
                return False

        # Check allowed
        if not allowed_patterns:
            return True  # No allowed list = all branches allowed (except forbidden)

        for pattern in allowed_patterns:
            if self._branch_matches_pattern(branch, pattern):
                return True

        return False  # Not in allowed list

    def _branch_matches_pattern(self, branch: str, pattern: str) -> bool:
        """Check if branch matches a pattern like 'feature/*' or 'main'."""
        if pattern.endswith("/*"):
            prefix = pattern[:-2]
            return branch.startswith(prefix + "/") or branch == prefix
        return branch == pattern


def load(agent_name: str, contracts_dir: Optional[Path] = None) -> Contract:
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

    # Parse MCP tools config if present
    mcp_tools_data = data.get("mcp_tools")
    mcp_tools = None
    if mcp_tools_data:
        mcp_tools = MCPToolsConfig(
            allowed_servers=mcp_tools_data.get("allowed_servers", []),
            forbidden_servers=mcp_tools_data.get("forbidden_servers", []),
            requires_approval=mcp_tools_data.get("requires_approval", []),
            max_tools=mcp_tools_data.get("max_tools", 20),
            priority_tools=mcp_tools_data.get("priority_tools"),
        )

    return Contract(
        agent=data["agent"],
        version=data["version"],
        allowed_actions=data.get("allowed_actions", []),
        forbidden_actions=data.get("forbidden_actions", []),
        requires_approval=data.get("requires_approval", []),
        limits=data.get("limits", {}),
        invariants=data.get("invariants", {}),
        on_violation=data.get("on_violation", "halt"),
        # v5: Team-specific fields
        branch_restrictions=data.get("branch_restrictions"),
        team=data.get("team"),
        autonomy_level=data.get("autonomy_level"),
        # v6: MCP tools configuration
        mcp_tools=mcp_tools,
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


def require_branch(contract: Contract, branch: str) -> None:
    """
    Require that the current branch is allowed by the contract.

    Args:
        contract: The contract to check against
        branch: Current git branch name

    Raises:
        ContractViolation: If branch is not allowed
    """
    if not contract.is_branch_allowed(branch):
        allowed = contract.branch_restrictions.get("allowed_patterns", []) if contract.branch_restrictions else []
        raise ContractViolation(
            f"Branch '{branch}' is not allowed for {contract.agent} contract. "
            f"Allowed patterns: {allowed}"
        )


def get_current_branch(project_path: Path) -> str:
    """Get the current git branch name for a project."""
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get current branch: {result.stderr}")
    return result.stdout.strip()
