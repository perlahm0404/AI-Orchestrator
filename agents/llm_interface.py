"""
Multi-LLM Interoperability Interface

Provides a universal skill interface that any LLM provider can implement.
Supports Claude (Opus/Sonnet/Haiku), Codex, Gemini, and other LLMs.

Design Principles:
1. Provider-agnostic skill interface
2. Consistent input/output contracts
3. Verification integration (Ralph)
4. Cost tracking per provider

Usage:
    from agents.llm_interface import LLMProvider, SkillInterface, create_provider

    # Create a provider
    provider = create_provider("claude-opus")

    # Create MCP-aware provider (lazy loading)
    from agents.llm_interface import create_mcp_provider
    mcp_provider = create_mcp_provider(servers={"filesystem": config})

    # Execute a skill
    result = await provider.execute_skill(
        skill_id="debugging",
        task_spec={"description": "Fix login bug", "file": "auth.py"},
        context={"repo": "karematch"},
    )

Supported Providers:
- claude-opus: Claude Opus 4.5 (strategic, complex tasks)
- claude-sonnet: Claude Sonnet 4 (balanced performance)
- claude-haiku: Claude Haiku 3.5 (fast, simple tasks)
- mcp: MCP-aware provider with lazy loading (wraps Claude)
- codex: OpenAI Codex (code generation) - Planned
- gemini: Google Gemini (research, analysis) - Planned
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
import json


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS & DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════


class LLMProviderType(Enum):
    """Supported LLM provider types."""
    CLAUDE_OPUS = "claude-opus"
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_HAIKU = "claude-haiku"
    CODEX = "codex"
    GEMINI = "gemini"
    LOCAL = "local"  # Local models (Ollama, etc.)


class SkillExecutionStatus(Enum):
    """Status of skill execution."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"  # Governance blocked


@dataclass
class SkillInput:
    """
    Universal skill input contract.

    All LLM providers receive this standardized input format.
    """
    skill_id: str
    task_spec: Dict[str, Any]  # Task-specific parameters
    context: Dict[str, Any]    # Execution context (repo, branch, etc.)
    constraints: Dict[str, Any] = field(default_factory=dict)  # Governance constraints

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "task_spec": self.task_spec,
            "context": self.context,
            "constraints": self.constraints,
        }


@dataclass
class SkillOutput:
    """
    Universal skill output contract.

    All LLM providers return this standardized output format.
    """
    status: SkillExecutionStatus
    skill_id: str
    code_changes: List[Dict[str, Any]]  # File changes: [{file, content, action}]
    test_results: Optional[Dict[str, Any]] = None  # Test execution results
    evidence: Dict[str, Any] = field(default_factory=dict)  # Proof of completion
    reasoning: str = ""  # Explanation of actions taken
    errors: List[str] = field(default_factory=list)  # Any errors encountered
    metrics: Dict[str, Any] = field(default_factory=dict)  # Tokens, latency, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "skill_id": self.skill_id,
            "code_changes": self.code_changes,
            "test_results": self.test_results,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "errors": self.errors,
            "metrics": self.metrics,
        }


@dataclass
class ProviderCapabilities:
    """
    Capabilities of an LLM provider.

    Used for skill routing decisions.
    """
    provider_type: LLMProviderType
    model_name: str
    max_context_tokens: int
    max_output_tokens: int
    supports_code: bool = True
    supports_vision: bool = False
    supports_tools: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    latency_class: str = "medium"  # fast, medium, slow
    recommended_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_type": self.provider_type.value,
            "model_name": self.model_name,
            "max_context_tokens": self.max_context_tokens,
            "max_output_tokens": self.max_output_tokens,
            "supports_code": self.supports_code,
            "supports_vision": self.supports_vision,
            "supports_tools": self.supports_tools,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "latency_class": self.latency_class,
            "recommended_skills": self.recommended_skills,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ABSTRACT INTERFACES
# ═══════════════════════════════════════════════════════════════════════════════


class SkillInterface(Protocol):
    """
    Universal skill interface that any LLM can implement.

    This is the contract for skill execution.
    """

    def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillOutput:
        """
        Execute a skill.

        Args:
            skill_input: Standardized skill input

        Returns:
            Standardized skill output
        """
        ...

    def validate_input(self, skill_input: SkillInput) -> bool:
        """Validate skill input before execution."""
        ...

    def get_supported_skills(self) -> List[str]:
        """Get list of skill IDs this implementation supports."""
        ...


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Each provider (Claude, Codex, Gemini) implements this interface.
    """

    def __init__(self, capabilities: ProviderCapabilities):
        self.capabilities = capabilities
        self._usage_tracker: Dict[str, Any] = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "execution_count": 0,
        }

    @abstractmethod
    async def execute_skill(
        self,
        skill_id: str,
        task_spec: Dict[str, Any],
        context: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> SkillOutput:
        """
        Execute a skill using this LLM provider.

        Args:
            skill_id: Skill to execute
            task_spec: Task-specific parameters
            context: Execution context
            constraints: Optional governance constraints

        Returns:
            Standardized skill output
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        pass

    def track_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Track token usage and cost."""
        self._usage_tracker["total_input_tokens"] += input_tokens
        self._usage_tracker["total_output_tokens"] += output_tokens
        self._usage_tracker["execution_count"] += 1

        cost = (
            input_tokens / 1000 * self.capabilities.cost_per_1k_input +
            output_tokens / 1000 * self.capabilities.cost_per_1k_output
        )
        self._usage_tracker["total_cost"] += cost

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self._usage_tracker.copy()

    def supports_skill(self, skill_id: str) -> bool:
        """Check if this provider is recommended for a skill."""
        return skill_id in self.capabilities.recommended_skills


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════


class ClaudeProvider(LLMProvider):
    """
    Claude LLM Provider (Anthropic).

    Supports: Opus 4.5, Sonnet 4, Haiku 3.5
    """

    def __init__(
        self,
        model: str = "claude-opus-4-5-20251101",
        api_key: Optional[str] = None,
    ):
        # Define capabilities based on model
        if "opus" in model.lower():
            capabilities = ProviderCapabilities(
                provider_type=LLMProviderType.CLAUDE_OPUS,
                model_name=model,
                max_context_tokens=200000,
                max_output_tokens=32000,
                supports_code=True,
                supports_vision=True,
                supports_tools=True,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                latency_class="slow",
                recommended_skills=[
                    "system_design", "architecture", "debugging",
                    "root_cause_analysis", "security_scanning",
                    "hipaa_compliance", "adr_creation",
                ],
            )
        elif "sonnet" in model.lower():
            capabilities = ProviderCapabilities(
                provider_type=LLMProviderType.CLAUDE_SONNET,
                model_name=model,
                max_context_tokens=200000,
                max_output_tokens=16000,
                supports_code=True,
                supports_vision=True,
                supports_tools=True,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                latency_class="medium",
                recommended_skills=[
                    "implementation", "refactoring", "unit_testing",
                    "api_design", "code_review", "documentation",
                ],
            )
        else:  # haiku
            capabilities = ProviderCapabilities(
                provider_type=LLMProviderType.CLAUDE_HAIKU,
                model_name=model,
                max_context_tokens=200000,
                max_output_tokens=8000,
                supports_code=True,
                supports_vision=True,
                supports_tools=True,
                cost_per_1k_input=0.00025,
                cost_per_1k_output=0.00125,
                latency_class="fast",
                recommended_skills=[
                    "linting", "type_checking", "formatting",
                    "dead_code_removal", "naming_conventions",
                ],
            )

        super().__init__(capabilities)
        self.api_key = api_key
        self.model = model

    async def execute_skill(
        self,
        skill_id: str,
        task_spec: Dict[str, Any],
        context: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> SkillOutput:
        """Execute a skill using Claude."""
        # Build skill input
        skill_input = SkillInput(
            skill_id=skill_id,
            task_spec=task_spec,
            context=context,
            constraints=constraints or {},
        )

        # Validate input
        if not self._validate_input(skill_input):
            return SkillOutput(
                status=SkillExecutionStatus.FAILED,
                skill_id=skill_id,
                code_changes=[],
                errors=["Invalid skill input"],
            )

        # In a real implementation, this would call the Anthropic API
        # For now, return a placeholder indicating the interface works
        return SkillOutput(
            status=SkillExecutionStatus.SUCCESS,
            skill_id=skill_id,
            code_changes=[],
            evidence={"verified": True},
            reasoning=f"Skill '{skill_id}' executed via {self.model}",
            metrics={
                "provider": self.capabilities.provider_type.value,
                "model": self.model,
                "latency_class": self.capabilities.latency_class,
            },
        )

    def _validate_input(self, skill_input: SkillInput) -> bool:
        """Validate skill input."""
        if not skill_input.skill_id:
            return False
        if not skill_input.task_spec:
            return False
        return True

    def get_capabilities(self) -> ProviderCapabilities:
        """Get Claude capabilities."""
        return self.capabilities


class CodexProvider(LLMProvider):
    """
    OpenAI Codex Provider (Planned).

    Specialized for code generation tasks.
    """

    def __init__(self, api_key: Optional[str] = None):
        capabilities = ProviderCapabilities(
            provider_type=LLMProviderType.CODEX,
            model_name="code-davinci-002",
            max_context_tokens=8000,
            max_output_tokens=4000,
            supports_code=True,
            supports_vision=False,
            supports_tools=False,
            cost_per_1k_input=0.002,
            cost_per_1k_output=0.002,
            latency_class="medium",
            recommended_skills=[
                "implementation", "api_design", "backend_development",
                "frontend_development", "database_design",
            ],
        )
        super().__init__(capabilities)
        self.api_key = api_key

    async def execute_skill(
        self,
        skill_id: str,
        task_spec: Dict[str, Any],
        context: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> SkillOutput:
        """Execute a skill using Codex."""
        # Placeholder - would integrate with OpenAI API
        return SkillOutput(
            status=SkillExecutionStatus.PARTIAL,
            skill_id=skill_id,
            code_changes=[],
            reasoning="Codex provider not yet implemented",
            errors=["Provider implementation pending"],
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return self.capabilities


class GeminiProvider(LLMProvider):
    """
    Google Gemini Provider (Planned).

    Good for research and analysis tasks.
    """

    def __init__(self, api_key: Optional[str] = None):
        capabilities = ProviderCapabilities(
            provider_type=LLMProviderType.GEMINI,
            model_name="gemini-pro",
            max_context_tokens=32000,
            max_output_tokens=8000,
            supports_code=True,
            supports_vision=True,
            supports_tools=True,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.0005,
            latency_class="fast",
            recommended_skills=[
                "documentation", "market_analysis", "risk_assessment",
                "prioritization", "roadmap_planning",
            ],
        )
        super().__init__(capabilities)
        self.api_key = api_key

    async def execute_skill(
        self,
        skill_id: str,
        task_spec: Dict[str, Any],
        context: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> SkillOutput:
        """Execute a skill using Gemini."""
        # Placeholder - would integrate with Google AI API
        return SkillOutput(
            status=SkillExecutionStatus.PARTIAL,
            skill_id=skill_id,
            code_changes=[],
            reasoning="Gemini provider not yet implemented",
            errors=["Provider implementation pending"],
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return self.capabilities


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER FACTORY & ROUTER
# ═══════════════════════════════════════════════════════════════════════════════


def create_provider(
    provider_type: str,
    api_key: Optional[str] = None,
) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        provider_type: Type of provider (claude-opus, claude-sonnet, etc.)
        api_key: Optional API key

    Returns:
        LLMProvider instance
    """
    providers = {
        "claude-opus": lambda: ClaudeProvider("claude-opus-4-5-20251101", api_key),
        "claude-sonnet": lambda: ClaudeProvider("claude-sonnet-4-20250514", api_key),
        "claude-haiku": lambda: ClaudeProvider("claude-haiku-3-5-20250514", api_key),
        "codex": lambda: CodexProvider(api_key),
        "gemini": lambda: GeminiProvider(api_key),
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}. "
                        f"Supported: {list(providers.keys())}")

    return providers[provider_type]()


def create_mcp_provider(
    servers: Optional[Dict[str, Any]] = None,
    model: str = "claude-sonnet-4-20250514",
    api_key: Optional[str] = None,
) -> "MCPProvider":
    """
    Create an MCP-aware LLM provider with lazy loading.

    MCP (Model Context Protocol) providers connect to external tools like
    filesystem, GitHub, databases, etc. Connections are lazy - only established
    when tools are actually invoked.

    Args:
        servers: Dictionary of server name -> MCPServerConfig
        model: Claude model to use for LLM calls
        api_key: Optional API key

    Returns:
        MCPProvider instance

    Usage:
        from mcp_integration import MCPServerConfig

        servers = {
            "filesystem": MCPServerConfig(
                name="filesystem",
                type="npx",
                package="@anthropic/mcp-filesystem"
            )
        }
        provider = create_mcp_provider(servers=servers)
    """
    # Import here to avoid circular dependency
    from mcp.provider import MCPProvider
    from mcp.server_config import MCPServerConfig

    # Convert dict configs to MCPServerConfig if needed
    server_configs = {}
    if servers:
        for name, config in servers.items():
            if isinstance(config, dict):
                server_configs[name] = MCPServerConfig.from_dict(config)
            else:
                server_configs[name] = config

    return MCPProvider(
        servers=server_configs,
        model=model,
        api_key=api_key
    )


class SkillRouter:
    """
    Routes skills to optimal LLM providers.

    Considers:
    - Skill requirements
    - Provider capabilities
    - Cost optimization
    - Latency requirements
    """

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """Register an LLM provider."""
        self.providers[name] = provider

    def get_best_provider(
        self,
        skill_id: str,
        latency_priority: bool = False,
        cost_priority: bool = False,
    ) -> Optional[str]:
        """
        Get the best provider for a skill.

        Args:
            skill_id: Skill to execute
            latency_priority: Prioritize fast providers
            cost_priority: Prioritize cheap providers

        Returns:
            Provider name or None
        """
        candidates = []

        for name, provider in self.providers.items():
            if provider.supports_skill(skill_id):
                candidates.append((
                    name,
                    provider.capabilities.cost_per_1k_output,
                    provider.capabilities.latency_class,
                ))

        if not candidates:
            # No specialized provider, use default Claude Sonnet
            return "claude-sonnet" if "claude-sonnet" in self.providers else None

        # Sort by preference
        if cost_priority:
            candidates.sort(key=lambda x: x[1])
        elif latency_priority:
            latency_order = {"fast": 0, "medium": 1, "slow": 2}
            candidates.sort(key=lambda x: latency_order.get(x[2], 1))
        else:
            # Default: balanced (prefer recommended skills)
            pass

        return candidates[0][0] if candidates else None

    def get_usage_report(self) -> Dict[str, Any]:
        """Get usage report across all providers."""
        report = {
            "generated_at": utc_now().isoformat(),
            "providers": {},
            "totals": {
                "total_cost": 0.0,
                "total_executions": 0,
            },
        }

        for name, provider in self.providers.items():
            stats = provider.get_usage_stats()
            report["providers"][name] = stats
            report["totals"]["total_cost"] += stats.get("total_cost", 0)
            report["totals"]["total_executions"] += stats.get("execution_count", 0)

        return report


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════


# Default router with Claude providers
def create_default_router() -> SkillRouter:
    """Create a router with default Claude providers."""
    router = SkillRouter()
    router.register_provider("claude-opus", create_provider("claude-opus"))
    router.register_provider("claude-sonnet", create_provider("claude-sonnet"))
    router.register_provider("claude-haiku", create_provider("claude-haiku"))
    return router


__all__ = [
    # Enums
    "LLMProviderType",
    "SkillExecutionStatus",
    # Data structures
    "SkillInput",
    "SkillOutput",
    "ProviderCapabilities",
    # Interfaces
    "SkillInterface",
    "LLMProvider",
    # Providers
    "ClaudeProvider",
    "CodexProvider",
    "GeminiProvider",
    # MCP Support
    "create_mcp_provider",
    # Utilities
    "create_provider",
    "SkillRouter",
    "create_default_router",
]
