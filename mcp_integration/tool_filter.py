"""
MCP Tool Filter

Session-scoped tool filtering to reduce token usage by only exposing
relevant tools to each agent.

Design:
- Loads 5-10 relevant tools per agent instead of 50+ available
- Uses agent contract to determine allowed tools
- Compiles regex patterns once, caches for session lifetime
- Pre-filters tools before sending to LLM

Token Savings:
- Typical MCP server exposes 30-50 tools (~1-3K tokens each in descriptions)
- Filtering to 5-10 tools saves 2-5K tokens per session

Usage:
    from mcp.tool_filter import MCPToolFilter

    # Create filter for agent session
    filter = MCPToolFilter(
        agent_name="bugfix",
        contract=bugfix_contract,
        server_configs=servers
    )

    # Get filtered tools for LLM
    tools = filter.get_filtered_tools(available_tools)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Set
import re
import fnmatch


@dataclass
class Tool:
    """Represents an MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server: str  # Which MCP server provides this tool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def estimate_tokens(self) -> int:
        """
        Estimate token count for this tool definition.

        Rough heuristic: 1 token per 4 characters
        """
        total_chars = len(self.name) + len(self.description)
        total_chars += len(str(self.input_schema))
        return total_chars // 4


@dataclass
class MCPToolFilter:
    """
    Session-scoped filter for MCP tools.

    Reduces token usage by only exposing relevant tools to each agent
    based on governance contracts and task context.
    """
    agent_name: str
    allowed_servers: List[str] = field(default_factory=list)
    forbidden_tools: List[str] = field(default_factory=list)
    approval_required_tools: List[str] = field(default_factory=list)
    max_tools: int = 20  # Maximum tools to expose

    # Compiled patterns (cached for session)
    _allowed_patterns: List[Pattern[str]] = field(default_factory=list, repr=False)
    _forbidden_patterns: List[Pattern[str]] = field(default_factory=list, repr=False)
    _patterns_compiled: bool = field(default=False, repr=False)

    # Task-specific tool prioritization
    task_context: Optional[str] = None  # e.g., "debugging auth", "fixing tests"
    priority_tools: List[str] = field(default_factory=list)  # Tools to prioritize

    def __post_init__(self) -> None:
        """Compile regex patterns for efficient matching."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile glob patterns to regex for efficient matching."""
        if self._patterns_compiled:
            return

        for pattern in self.forbidden_tools:
            # Convert glob to regex: * -> .*, ? -> .
            regex = fnmatch.translate(pattern)
            self._forbidden_patterns.append(re.compile(regex, re.IGNORECASE))

        self._patterns_compiled = True

    def is_tool_allowed(self, tool: Tool) -> bool:
        """
        Check if a tool is allowed for this agent.

        Args:
            tool: Tool to check

        Returns:
            True if tool is allowed
        """
        # Check server allowlist first (fast path)
        if self.allowed_servers and tool.server not in self.allowed_servers:
            return False

        # Check forbidden patterns
        for pattern in self._forbidden_patterns:
            if pattern.match(tool.name):
                return False

        return True

    def requires_approval(self, tool_name: str) -> bool:
        """Check if a tool requires human approval before use."""
        return tool_name in self.approval_required_tools

    def get_filtered_tools(
        self,
        available_tools: List[Tool],
        task_intent: Optional[str] = None
    ) -> List[Tool]:
        """
        Filter and prioritize tools for LLM.

        Args:
            available_tools: All available tools from MCP servers
            task_intent: Optional task description for relevance scoring

        Returns:
            Filtered list of tools, sorted by relevance
        """
        # Filter by allowlist/blocklist
        allowed_tools = [t for t in available_tools if self.is_tool_allowed(t)]

        # Score and sort by relevance
        scored_tools = self._score_tools(allowed_tools, task_intent)

        # Take top N tools
        top_tools = sorted(scored_tools, key=lambda x: x[1], reverse=True)[:self.max_tools]

        return [tool for tool, _score in top_tools]

    def _score_tools(
        self,
        tools: List[Tool],
        task_intent: Optional[str] = None
    ) -> List[tuple[Tool, float]]:
        """
        Score tools by relevance to task.

        Returns:
            List of (tool, score) tuples
        """
        scored = []
        intent_words = set()
        if task_intent:
            # Extract keywords from intent
            intent_words = set(task_intent.lower().split())

        for tool in tools:
            score = 0.0

            # Priority tools get boost
            if tool.name in self.priority_tools:
                score += 10.0

            # Match intent keywords against tool name/description
            if intent_words:
                tool_words = set(tool.name.lower().split("_"))
                tool_words.update(tool.description.lower().split())
                matches = len(intent_words & tool_words)
                score += matches * 2.0

            # Smaller tools get slight preference (less token usage)
            token_estimate = tool.estimate_tokens()
            if token_estimate < 500:
                score += 1.0
            elif token_estimate > 2000:
                score -= 1.0

            scored.append((tool, score))

        return scored

    def get_token_estimate(self, tools: List[Tool]) -> int:
        """Estimate total tokens for tool definitions."""
        return sum(t.estimate_tokens() for t in tools)

    @classmethod
    def from_contract(
        cls,
        agent_name: str,
        contract: Any,  # governance.contract.Contract
        mcp_config: Optional[Dict[str, Any]] = None
    ) -> "MCPToolFilter":
        """
        Create filter from governance contract.

        Args:
            agent_name: Name of the agent
            contract: Governance contract for the agent
            mcp_config: Optional MCP-specific config from contract

        Returns:
            Configured MCPToolFilter
        """
        mcp_config = mcp_config or {}

        return cls(
            agent_name=agent_name,
            allowed_servers=mcp_config.get("allowed_servers", []),
            forbidden_tools=mcp_config.get("forbidden_tools", []),
            approval_required_tools=mcp_config.get("requires_approval", []),
            max_tools=mcp_config.get("max_tools", 20),
        )
