"""
MCP Integration Manager (Phase 2A-5)

Integrates all MCP servers with IterationLoop and agents.

Manages:
- MCP server registration
- Tool invocation
- Cost tracking across servers
- Metrics aggregation
- Schema generation for agents

Author: Claude Code (TDD Implementation)
Date: 2026-02-07
Version: 1.0
"""

from typing import Dict, Any, List, Optional
import threading


class MCPIntegration:
    """Manages integration of all MCP servers"""

    def __init__(self) -> None:
        """Initialize MCP integration manager"""
        self._mcp_servers: Dict[str, Any] = {}
        self._servers_lock = threading.Lock()
        self._tool_to_server: Dict[str, str] = {}

    def register_mcp_server(self, server_name: str, mcp_server: Any) -> None:
        """Register an MCP server"""
        with self._servers_lock:
            self._mcp_servers[server_name] = mcp_server

            # Index tools for quick lookup
            if hasattr(mcp_server, "get_mcp_tools"):
                tools = mcp_server.get_mcp_tools()
                for tool_name in tools.keys():
                    self._tool_to_server[tool_name] = server_name

    def get_registered_servers(self) -> List[str]:
        """Get list of registered MCP servers"""
        with self._servers_lock:
            return list(self._mcp_servers.keys())

    def get_available_tools(self) -> List[str]:
        """Get all available tools from registered servers"""
        with self._servers_lock:
            return list(self._tool_to_server.keys())

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke a tool by name"""
        with self._servers_lock:
            if tool_name not in self._tool_to_server:
                return None

            server_name = self._tool_to_server[tool_name]
            server = self._mcp_servers[server_name]

            if hasattr(server, "invoke_tool"):
                return server.invoke_tool(tool_name, arguments)

        return None

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get JSON schema for a tool"""
        with self._servers_lock:
            if tool_name not in self._tool_to_server:
                return None

            server_name = self._tool_to_server[tool_name]
            server = self._mcp_servers[server_name]

            if hasattr(server, "get_tool_schema"):
                schema = server.get_tool_schema(tool_name)
                if isinstance(schema, dict):
                    return schema

        return None

    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all tools"""
        schemas = {}

        for tool_name in self.get_available_tools():
            schema = self.get_tool_schema(tool_name)
            if schema:
                schemas[tool_name] = schema

        return schemas

    def get_accumulated_cost(self) -> float:
        """Get total cost from all servers"""
        total = 0.0

        with self._servers_lock:
            for server in self._mcp_servers.values():
                if hasattr(server, "get_accumulated_cost"):
                    total += server.get_accumulated_cost()

        return total

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown by server"""
        breakdown = {}

        with self._servers_lock:
            for server_name, server in self._mcp_servers.items():
                if hasattr(server, "get_accumulated_cost"):
                    breakdown[server_name] = server.get_accumulated_cost()

        return breakdown

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all servers"""
        total_ops = 0
        total_cost = self.get_accumulated_cost()

        with self._servers_lock:
            for server in self._mcp_servers.values():
                if hasattr(server, "get_metrics"):
                    metrics = server.get_metrics()
                    if "total_operations" in metrics:
                        total_ops += metrics["total_operations"]

        return {
            "total_operations": total_ops,
            "total_cost_usd": total_cost
        }

    def get_server_metrics(
        self, server_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific server"""
        with self._servers_lock:
            if server_name not in self._mcp_servers:
                return None

            server = self._mcp_servers[server_name]
            if hasattr(server, "get_metrics"):
                metrics = server.get_metrics()
                if isinstance(metrics, dict):
                    return metrics

        return None

    def get_tool_description(self, tool_name: str) -> Optional[str]:
        """Get description for a tool"""
        with self._servers_lock:
            if tool_name not in self._tool_to_server:
                return None

            server_name = self._tool_to_server[tool_name]
            server = self._mcp_servers[server_name]

            if hasattr(server, "get_mcp_tools"):
                tools = server.get_mcp_tools()
                if tool_name in tools:
                    desc = tools[tool_name].get("description", "Tool")
                    if isinstance(desc, str):
                        return desc

        return None

    def generate_agent_prompt(self) -> str:
        """Generate system prompt for agents with available tools"""
        tools = self.get_available_tools()

        prompt = """You are an expert AI agent with access to specialized tools.

## Available Tools

"""

        for tool_name in sorted(tools):
            description = self.get_tool_description(tool_name)
            if description:
                prompt += f"- **{tool_name}**: {description}\n"

        prompt += "\n## Instructions\n"
        prompt += "1. Analyze the task carefully\n"
        prompt += "2. Use available tools to accomplish the task\n"
        prompt += "3. Verify your work using appropriate tools\n"
        prompt += "4. Report results clearly\n"

        return prompt

    def get_tool_by_name(self, tool_name: str) -> Optional[Any]:
        """Get the MCP server that provides a tool"""
        with self._servers_lock:
            if tool_name not in self._tool_to_server:
                return None

            server_name = self._tool_to_server[tool_name]
            return self._mcp_servers.get(server_name)

    def unregister_server(self, server_name: str) -> bool:
        """Unregister an MCP server"""
        with self._servers_lock:
            if server_name not in self._mcp_servers:
                return False

            # Remove server
            del self._mcp_servers[server_name]

            # Remove tool mappings for this server
            tools_to_remove = [
                tool for tool, srv in self._tool_to_server.items()
                if srv == server_name
            ]

            for tool in tools_to_remove:
                del self._tool_to_server[tool]

        return True

    def clear(self) -> None:
        """Clear all registrations"""
        with self._servers_lock:
            self._mcp_servers.clear()
            self._tool_to_server.clear()
