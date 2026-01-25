"""
MCP Governance Hook

PreToolUse and PostToolUse hooks for MCP tool governance.
Enforces agent permissions, rate limits, and audit logging.

This hook is called by the MCP provider before and after each tool call.

Token Optimization:
- Compiles regex patterns once at startup
- Caches permission checks for session
- Batches audit log writes

Usage:
    from governance.hooks.mcp_hook import MCPGovernanceHook

    hook = MCPGovernanceHook.from_contract("mcp-tools")

    # Before tool call
    if hook.pre_tool_use(agent="bugfix", server="filesystem", tool="read_file"):
        result = await connection.call_tool(...)

        # After tool call
        hook.post_tool_use(agent="bugfix", server="filesystem", tool="read_file", result=result)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set
import fnmatch
import json
import re
import time
import threading
import yaml


@dataclass
class ToolPermission:
    """Permission for a specific tool."""
    tool_name: str
    allowed: bool = True
    requires_approval: bool = False
    approval_reason: Optional[str] = None


@dataclass
class RateLimitState:
    """Rate limiting state for an agent."""
    calls_this_minute: int = 0
    calls_this_session: int = 0
    minute_start: float = 0.0
    blocked_until: Optional[float] = None


class MCPGovernanceHook:
    """
    Governance hook for MCP tool calls.

    Enforces:
    - Agent permissions (which agents can use which servers/tools)
    - Tool allowlist/blocklist
    - Rate limiting
    - Audit logging
    - Human approval gates
    """

    def __init__(
        self,
        servers: Dict[str, Dict[str, Any]],
        agent_overrides: Dict[str, Dict[str, Any]],
        limits: Dict[str, Any],
        security: Dict[str, Any],
    ):
        self._servers = servers
        self._agent_overrides = agent_overrides
        self._limits = limits
        self._security = security

        # Compiled patterns (cached)
        self._sensitive_patterns: List[tuple] = []
        self._compile_patterns()

        # Permission cache (session-scoped)
        self._permission_cache: Dict[str, bool] = {}

        # Rate limit tracking
        self._rate_limits: Dict[str, RateLimitState] = {}
        self._rate_lock = threading.Lock()

        # Audit buffer (batched writes)
        self._audit_buffer: List[Dict[str, Any]] = []
        self._audit_lock = threading.Lock()
        self._last_audit_flush = time.time()

    def _compile_patterns(self) -> None:
        """Compile sensitive operation patterns for efficient matching."""
        for op in self._security.get("sensitive_operations", []):
            pattern = op.get("pattern", "")
            requires = op.get("requires", "human_approval")

            # Convert glob to regex
            regex = fnmatch.translate(pattern)
            compiled = re.compile(regex, re.IGNORECASE)
            self._sensitive_patterns.append((compiled, requires))

    def pre_tool_use(
        self,
        agent: str,
        server: str,
        tool: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> ToolPermission:
        """
        Check if tool use is allowed before execution.

        Args:
            agent: Agent name
            server: MCP server name
            tool: Tool name
            arguments: Tool arguments (for context-aware checks)

        Returns:
            ToolPermission with allowed status and any approval requirements
        """
        # Check cache first
        cache_key = f"{agent}:{server}:{tool}"
        if cache_key in self._permission_cache:
            cached = self._permission_cache[cache_key]
            if not cached:
                return ToolPermission(tool_name=tool, allowed=False)

        # Check server exists
        server_config = self._servers.get(server)
        if not server_config:
            self._permission_cache[cache_key] = False
            return ToolPermission(
                tool_name=tool,
                allowed=False,
                approval_reason=f"Unknown server: {server}"
            )

        # Check agent is allowed for this server
        allowed_agents = server_config.get("allowed_agents", [])
        if "*" not in allowed_agents and agent not in allowed_agents:
            self._permission_cache[cache_key] = False
            return ToolPermission(
                tool_name=tool,
                allowed=False,
                approval_reason=f"Agent '{agent}' not allowed for server '{server}'"
            )

        # Check for agent-specific forbidden servers
        agent_config = self._agent_overrides.get(agent, {})
        forbidden_servers = agent_config.get("forbidden_servers", [])
        if server in forbidden_servers:
            self._permission_cache[cache_key] = False
            return ToolPermission(
                tool_name=tool,
                allowed=False,
                approval_reason=f"Server '{server}' forbidden for agent '{agent}'"
            )

        # Check rate limits
        if not self._check_rate_limit(agent):
            return ToolPermission(
                tool_name=tool,
                allowed=False,
                approval_reason="Rate limit exceeded"
            )

        # Check if tool requires approval
        requires_approval = server_config.get("requires_approval", [])
        if tool in requires_approval:
            return ToolPermission(
                tool_name=tool,
                allowed=True,
                requires_approval=True,
                approval_reason=f"Tool '{tool}' requires human approval"
            )

        # Check sensitive operation patterns
        for pattern, requires in self._sensitive_patterns:
            if pattern.match(tool):
                return ToolPermission(
                    tool_name=tool,
                    allowed=True,
                    requires_approval=True,
                    approval_reason=f"Sensitive operation ({requires})"
                )

        # Cache positive result
        self._permission_cache[cache_key] = True

        return ToolPermission(tool_name=tool, allowed=True)

    def post_tool_use(
        self,
        agent: str,
        server: str,
        tool: str,
        result: Any,
        duration_ms: float = 0.0,
        error: Optional[str] = None
    ) -> None:
        """
        Process tool use after execution.

        Handles:
        - Audit logging
        - Rate limit updates
        - Error tracking

        Args:
            agent: Agent name
            server: MCP server name
            tool: Tool name
            result: Tool result
            duration_ms: Execution duration in milliseconds
            error: Optional error message
        """
        # Update rate limits
        self._increment_rate_limit(agent)

        # Audit log
        if self._security.get("audit_all_calls", True):
            self._log_audit(
                agent=agent,
                server=server,
                tool=tool,
                result_size=len(str(result)) if result else 0,
                duration_ms=duration_ms,
                error=error
            )

    def _check_rate_limit(self, agent: str) -> bool:
        """Check if agent is within rate limits."""
        with self._rate_lock:
            now = time.time()

            if agent not in self._rate_limits:
                self._rate_limits[agent] = RateLimitState(minute_start=now)

            state = self._rate_limits[agent]

            # Check if blocked
            if state.blocked_until and now < state.blocked_until:
                return False

            # Reset minute counter if needed
            if now - state.minute_start > 60:
                state.calls_this_minute = 0
                state.minute_start = now

            # Check limits
            max_per_minute = self._limits.get("max_calls_per_minute", 60)
            max_per_session = self._limits.get("max_calls_per_session", 1000)

            if state.calls_this_minute >= max_per_minute:
                state.blocked_until = state.minute_start + 60
                return False

            if state.calls_this_session >= max_per_session:
                return False

            return True

    def _increment_rate_limit(self, agent: str) -> None:
        """Increment rate limit counters."""
        with self._rate_lock:
            if agent not in self._rate_limits:
                self._rate_limits[agent] = RateLimitState(minute_start=time.time())

            state = self._rate_limits[agent]
            state.calls_this_minute += 1
            state.calls_this_session += 1

    def _log_audit(
        self,
        agent: str,
        server: str,
        tool: str,
        result_size: int,
        duration_ms: float,
        error: Optional[str]
    ) -> None:
        """Log tool use to audit trail."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "server": server,
            "tool": tool,
            "result_size_bytes": result_size,
            "duration_ms": duration_ms,
            "error": error,
        }

        with self._audit_lock:
            self._audit_buffer.append(entry)

            # Flush if buffer is large or time elapsed
            if len(self._audit_buffer) >= 100 or time.time() - self._last_audit_flush > 10:
                self._flush_audit_buffer()

    def _flush_audit_buffer(self) -> None:
        """Flush audit buffer to file."""
        if not self._audit_buffer:
            return

        audit_path = Path(self._security.get("audit_log_path", ".meta/audit/mcp-tools.log"))
        audit_path.parent.mkdir(parents=True, exist_ok=True)

        with open(audit_path, "a") as f:
            for entry in self._audit_buffer:
                f.write(json.dumps(entry) + "\n")

        self._audit_buffer.clear()
        self._last_audit_flush = time.time()

    def get_filtered_tools(
        self,
        agent: str,
        available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter tools based on agent permissions.

        Args:
            agent: Agent name
            available_tools: All available tools from MCP servers

        Returns:
            Filtered list of tools agent can use
        """
        agent_config = self._agent_overrides.get(agent, {})
        max_tools = agent_config.get("max_tools", self._limits.get("max_tools_per_session", 20))
        priority_tools = agent_config.get("priority_tools", [])

        allowed_tools = []

        for tool_info in available_tools:
            server = tool_info.get("server", "")
            tool_name = tool_info.get("name", "")

            # Check permission
            permission = self.pre_tool_use(agent, server, tool_name)
            if permission.allowed:
                # Add priority score
                priority = 1.0 if tool_name in priority_tools else 0.0
                allowed_tools.append((tool_info, priority))

        # Sort by priority and take top N
        allowed_tools.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in allowed_tools[:max_tools]]

    @classmethod
    def from_contract(cls, contract_name: str = "mcp-tools") -> "MCPGovernanceHook":
        """
        Create hook from governance contract file.

        Args:
            contract_name: Name of contract file (without .yaml)

        Returns:
            Configured MCPGovernanceHook
        """
        contracts_dir = Path(__file__).parent.parent / "contracts"
        contract_file = contracts_dir / f"{contract_name}.yaml"

        with open(contract_file, "r") as f:
            config = yaml.safe_load(f)

        return cls(
            servers=config.get("servers", {}),
            agent_overrides=config.get("agent_overrides", {}),
            limits=config.get("limits", {}),
            security=config.get("security", {}),
        )

    def __del__(self):
        """Flush audit buffer on destruction."""
        try:
            with self._audit_lock:
                self._flush_audit_buffer()
        except Exception:
            pass  # Ignore errors during cleanup
