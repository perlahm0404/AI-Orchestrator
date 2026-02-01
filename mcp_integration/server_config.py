"""
MCP Server Configuration

Defines configuration for MCP servers including npx and Docker-based servers.

Usage:
    from mcp.server_config import MCPServerConfig, MCPServerType

    # npx-based server
    filesystem = MCPServerConfig(
        name="filesystem",
        type=MCPServerType.NPX,
        package="@anthropic/mcp-filesystem",
        args={"allowed_directories": ["/tmp"]}
    )

    # Docker-based server
    postgres = MCPServerConfig(
        name="postgres",
        type=MCPServerType.DOCKER,
        image="mcp/postgres:latest",
        env={"POSTGRES_URL": "postgresql://..."}
    )
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MCPServerType(Enum):
    """Type of MCP server transport."""
    NPX = "npx"  # npm package executed via npx
    DOCKER = "docker"  # Docker container
    STDIO = "stdio"  # Direct stdio process
    SSE = "sse"  # Server-sent events (HTTP)


@dataclass
class MCPServerConfig:
    """
    Configuration for an MCP server.

    Supports npx packages, Docker containers, and direct stdio processes.
    """
    name: str  # Unique server identifier
    type: MCPServerType = MCPServerType.NPX

    # npx configuration
    package: Optional[str] = None  # e.g., "@anthropic/mcp-filesystem"
    npx_args: List[str] = field(default_factory=list)

    # Docker configuration
    image: Optional[str] = None  # e.g., "mcp/postgres:latest"
    container_args: List[str] = field(default_factory=list)

    # stdio configuration
    command: Optional[str] = None  # e.g., "python"
    args: List[str] = field(default_factory=list)

    # Common configuration
    env: Dict[str, str] = field(default_factory=dict)  # Environment variables
    working_dir: Optional[str] = None
    timeout_seconds: int = 30  # Connection timeout

    # Governance integration
    allowed_agents: List[str] = field(default_factory=list)  # e.g., ["bugfix", "codequality"]
    requires_approval: List[str] = field(default_factory=list)  # Tools needing human approval
    max_tools_exposed: int = 50  # Limit exposed tools to save tokens

    # Token optimization
    summarize_responses: bool = True  # Use Haiku to summarize large responses
    response_token_threshold: int = 15000  # Threshold for summarization

    def get_command(self) -> List[str]:
        """
        Get the command to start this MCP server.

        Returns:
            List of command parts for subprocess execution
        """
        if self.type == MCPServerType.NPX:
            cmd = ["npx", "-y", self.package] if self.package else ["npx"]
            cmd.extend(self.npx_args)
            return cmd

        elif self.type == MCPServerType.DOCKER:
            cmd = ["docker", "run", "-i", "--rm"]
            for key, value in self.env.items():
                cmd.extend(["-e", f"{key}={value}"])
            if self.working_dir:
                cmd.extend(["-w", self.working_dir])
            cmd.extend(self.container_args)
            if self.image:
                cmd.append(self.image)
            return cmd

        elif self.type == MCPServerType.STDIO:
            cmd = [self.command] if self.command else []
            cmd.extend(self.args)
            return cmd

        else:
            raise ValueError(f"Unsupported server type: {self.type}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.type.value,
            "package": self.package,
            "image": self.image,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "working_dir": self.working_dir,
            "timeout_seconds": self.timeout_seconds,
            "allowed_agents": self.allowed_agents,
            "requires_approval": self.requires_approval,
            "max_tools_exposed": self.max_tools_exposed,
            "summarize_responses": self.summarize_responses,
            "response_token_threshold": self.response_token_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary."""
        server_type = MCPServerType(data.get("type", "npx"))
        return cls(
            name=data["name"],
            type=server_type,
            package=data.get("package"),
            image=data.get("image"),
            command=data.get("command"),
            args=data.get("args", []),
            env=data.get("env", {}),
            working_dir=data.get("working_dir"),
            timeout_seconds=data.get("timeout_seconds", 30),
            allowed_agents=data.get("allowed_agents", []),
            requires_approval=data.get("requires_approval", []),
            max_tools_exposed=data.get("max_tools_exposed", 50),
            summarize_responses=data.get("summarize_responses", True),
            response_token_threshold=data.get("response_token_threshold", 15000),
        )


# Predefined server configurations for common MCP servers
BUILTIN_SERVERS: Dict[str, MCPServerConfig] = {
    "filesystem": MCPServerConfig(
        name="filesystem",
        type=MCPServerType.NPX,
        package="@anthropic/mcp-filesystem",
        allowed_agents=["bugfix", "codequality", "featurebuilder"],
    ),
    "github": MCPServerConfig(
        name="github",
        type=MCPServerType.NPX,
        package="@anthropic/mcp-github",
        allowed_agents=["featurebuilder", "coordinator"],
        requires_approval=["create_pr", "merge_pr", "delete_branch"],
    ),
    "postgres": MCPServerConfig(
        name="postgres",
        type=MCPServerType.DOCKER,
        image="mcp/postgres:latest",
        allowed_agents=["bugfix", "featurebuilder"],
        requires_approval=["execute_query"],  # Write queries need approval
    ),
    "memory": MCPServerConfig(
        name="memory",
        type=MCPServerType.NPX,
        package="@anthropic/mcp-memory",
        allowed_agents=["*"],  # All agents can use memory
    ),
}
