"""
MCP (Model Context Protocol) Integration Package

Provides MCP-aware provider with lazy loading and response optimization.

Components:
- MCPProvider: Extends ClaudeProvider with MCP tool support
- MCPServerConfig: Configuration for MCP servers (npx/Docker)
- MCPToolFilter: Session-scoped tool filtering

Usage:
    from mcp_integration import MCPProvider, MCPServerConfig

    # Configure servers
    servers = {
        "filesystem": MCPServerConfig(
            name="filesystem",
            type="npx",
            package="@anthropic/mcp-filesystem"
        )
    }

    # Create provider with lazy loading
    provider = MCPProvider(servers=servers)

    # Only connects when tool is actually called
    result = await provider.call_tool("filesystem", "read_file", {"path": "/tmp/test.txt"})
"""

from .server_config import MCPServerConfig, MCPServerType
from .tool_filter import MCPToolFilter
from .provider import MCPProvider, MCPConnection

__all__ = [
    "MCPProvider",
    "MCPConnection",
    "MCPServerConfig",
    "MCPServerType",
    "MCPToolFilter",
]
