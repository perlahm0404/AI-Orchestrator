"""
Custom Agent Template System

Enables easy creation of new analyst perspectives for council debates.

Usage:
    # Create a new perspective from template
    from agents.coordinator.agent_templates import (
        create_custom_agent,
        register_perspective,
        list_perspectives
    )

    # Register a new perspective
    register_perspective(
        name="compliance",
        focus="Regulatory requirements and compliance implications",
        prompts={
            "analysis": "Evaluate regulatory compliance...",
            "considerations": ["HIPAA", "SOC2", "GDPR", "accessibility"]
        }
    )

    # Create agent from perspective
    agent = create_custom_agent("compliance", agent_id, context, message_bus)
"""

import json
import yaml  # type: ignore[import-untyped]
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, List, Dict, Any

from agents.coordinator.llm_debate_agent import LLMDebateAgent
from orchestration.debate_context import DebateContext, Position
from orchestration.message_bus import MessageBus


# Directory for custom perspective templates
TEMPLATES_DIR = Path(".aibrain/council-templates")
PERSPECTIVES_FILE = TEMPLATES_DIR / "perspectives.json"


@dataclass
class PerspectiveTemplate:
    """Template for a custom analyst perspective."""
    name: str                    # e.g., "compliance"
    display_name: str            # e.g., "Compliance Analyst"
    focus: str                   # What this perspective focuses on
    analysis_prompt: str         # LLM prompt for analysis
    considerations: List[str]    # Key considerations for this perspective
    tags: List[str] = field(default_factory=list)  # Tags for KO lookup
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerspectiveTemplate":
        return cls(**data)


# Built-in perspectives (always available)
BUILTIN_PERSPECTIVES: Dict[str, PerspectiveTemplate] = {
    "cost": PerspectiveTemplate(
        name="cost",
        display_name="Cost Analyst",
        focus="Cost implications including licensing, operations, ROI, and hidden costs",
        analysis_prompt="""Focus on cost implications:
- Licensing costs (open-source vs commercial)
- Operational costs (hosting, API calls, maintenance)
- ROI calculations (time saved, efficiency gains)
- Hidden costs (learning curve, migration, support)
- Cost-benefit analysis over 1-3 year horizon""",
        considerations=["licensing", "operations", "ROI", "TCO", "migration costs"],
        tags=["cost", "pricing", "budget"]
    ),
    "integration": PerspectiveTemplate(
        name="integration",
        display_name="Integration Analyst",
        focus="Integration complexity, team capacity, and system compatibility",
        analysis_prompt="""Focus on integration implications:
- Integration complexity and effort required
- Team capacity and skill requirements
- Dependencies and compatibility issues
- Migration path and rollback options
- Impact on existing systems and workflows""",
        considerations=["complexity", "team skills", "dependencies", "migration"],
        tags=["integration", "compatibility", "migration"]
    ),
    "performance": PerspectiveTemplate(
        name="performance",
        display_name="Performance Analyst",
        focus="Latency, throughput, scalability, and resource utilization",
        analysis_prompt="""Focus on performance implications:
- Latency and response time impact
- Throughput and scalability
- Resource utilization (CPU, memory, storage)
- Benchmark data and comparisons
- Performance at scale (10x, 100x current load)""",
        considerations=["latency", "throughput", "scalability", "resources"],
        tags=["performance", "scalability", "benchmarks"]
    ),
    "alternatives": PerspectiveTemplate(
        name="alternatives",
        display_name="Alternatives Analyst",
        focus="Competing solutions, feature comparisons, and trade-offs",
        analysis_prompt="""Focus on alternative solutions:
- Competing technologies and approaches
- Feature comparison matrix
- Pros and cons of each alternative
- Market adoption and community support
- Future trajectory and vendor lock-in risks""",
        considerations=["alternatives", "trade-offs", "vendor lock-in"],
        tags=["alternatives", "comparison", "options"]
    ),
    "security": PerspectiveTemplate(
        name="security",
        display_name="Security Analyst",
        focus="Security vulnerabilities, compliance, and data protection",
        analysis_prompt="""Focus on security implications:
- Vulnerability and attack surface analysis
- Compliance requirements (HIPAA, SOC2, GDPR)
- Authentication and authorization impacts
- Data protection and privacy concerns
- Security track record and CVE history""",
        considerations=["vulnerabilities", "compliance", "auth", "privacy"],
        tags=["security", "compliance", "privacy", "hipaa"]
    )
}


def _ensure_dir() -> None:
    """Ensure templates directory exists."""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def _load_custom_perspectives() -> Dict[str, PerspectiveTemplate]:
    """Load custom perspectives from file."""
    if not PERSPECTIVES_FILE.exists():
        return {}

    try:
        with open(PERSPECTIVES_FILE) as f:
            data = json.load(f)
            return {
                name: PerspectiveTemplate.from_dict(template_data)
                for name, template_data in data.items()
            }
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_custom_perspectives(perspectives: Dict[str, PerspectiveTemplate]) -> None:
    """Save custom perspectives to file."""
    _ensure_dir()
    data = {name: template.to_dict() for name, template in perspectives.items()}
    with open(PERSPECTIVES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def list_perspectives() -> Dict[str, PerspectiveTemplate]:
    """
    List all available perspectives (built-in + custom).

    Returns:
        Dict of perspective name -> template
    """
    result = dict(BUILTIN_PERSPECTIVES)
    result.update(_load_custom_perspectives())
    return result


def get_perspective(name: str) -> Optional[PerspectiveTemplate]:
    """
    Get a perspective template by name.

    Args:
        name: Perspective name (e.g., "cost", "compliance")

    Returns:
        PerspectiveTemplate or None if not found
    """
    perspectives = list_perspectives()
    return perspectives.get(name)


def register_perspective(
    name: str,
    focus: str,
    analysis_prompt: Optional[str] = None,
    considerations: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    display_name: Optional[str] = None
) -> PerspectiveTemplate:
    """
    Register a new custom perspective.

    Args:
        name: Unique perspective name (e.g., "compliance")
        focus: Brief description of what this perspective analyzes
        analysis_prompt: Optional custom LLM prompt (auto-generated if None)
        considerations: List of key considerations
        tags: Tags for KO lookup
        display_name: Human-readable name (defaults to "{Name} Analyst")

    Returns:
        Created PerspectiveTemplate
    """
    from datetime import datetime, timezone

    # Don't override built-in perspectives
    if name in BUILTIN_PERSPECTIVES:
        raise ValueError(f"Cannot override built-in perspective: {name}")

    # Generate default values
    if display_name is None:
        display_name = f"{name.title()} Analyst"

    if analysis_prompt is None:
        analysis_prompt = f"""Focus on {name} implications:
- Key {name} considerations for this decision
- Potential {name}-related risks and mitigations
- Impact on {name} requirements
- Best practices and recommendations"""

    if considerations is None:
        considerations = [name, "implications", "risks"]

    if tags is None:
        tags = [name]

    template = PerspectiveTemplate(
        name=name,
        display_name=display_name,
        focus=focus,
        analysis_prompt=analysis_prompt,
        considerations=considerations,
        tags=tags,
        created_at=datetime.now(timezone.utc).isoformat()
    )

    # Save to custom perspectives
    custom = _load_custom_perspectives()
    custom[name] = template
    _save_custom_perspectives(custom)

    return template


def delete_perspective(name: str) -> bool:
    """
    Delete a custom perspective.

    Args:
        name: Perspective name to delete

    Returns:
        True if deleted, False if not found or is built-in
    """
    if name in BUILTIN_PERSPECTIVES:
        return False

    custom = _load_custom_perspectives()
    if name not in custom:
        return False

    del custom[name]
    _save_custom_perspectives(custom)
    return True


class CustomLLMAnalyst(LLMDebateAgent):
    """
    Dynamic LLM analyst created from a perspective template.
    """

    def __init__(
        self,
        template: PerspectiveTemplate,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        use_llm: bool = True
    ):
        super().__init__(agent_id, context, message_bus, template.name, use_llm)
        self._template = template

    @property
    def perspective_prompt(self) -> str:
        return self._template.analysis_prompt

    def _fallback_analysis(self) -> Dict[str, Any]:
        """Pattern-based fallback using template considerations."""
        topic_lower = self.context.topic.lower()

        # Check if any consideration keywords appear in topic
        matching = [c for c in self._template.considerations if c.lower() in topic_lower]

        if matching:
            return {
                "position": Position.NEUTRAL,
                "reasoning": f"From {self._template.display_name} perspective: "
                            f"Topic touches on {', '.join(matching)}. "
                            f"Focus: {self._template.focus}",
                "evidence": [],
                "confidence": 0.6
            }
        else:
            return {
                "position": Position.NEUTRAL,
                "reasoning": f"{self._template.display_name} assessment needed. "
                            f"Focus: {self._template.focus}",
                "evidence": [],
                "confidence": 0.5
            }

    async def analyze(self) -> Any:
        """Analyze using LLM with template prompt."""
        analysis = await self._llm_analyze()

        for evidence in analysis.get("evidence", []):
            await self.add_evidence(
                source=evidence.get("source", "Unknown"),
                content=evidence.get("content", "")
            )

        await self.post_argument(
            position=analysis["position"],
            reasoning=analysis["reasoning"],
            evidence=[e.get("source", "") for e in analysis.get("evidence", [])],
            confidence=analysis["confidence"]
        )

        return self._my_arguments[-1]


@dataclass
class AgentTemplate:
    """YAML-based agent template for LLM analysts."""
    name: str
    perspective: str
    system_prompt: str
    model: str = "claude-sonnet"
    max_tokens: int = 1000
    temperature: float = 0.7
    focus_areas: List[str] = field(default_factory=list)

    def create_analyst(
        self,
        context: DebateContext,
        message_bus: MessageBus,
    ) -> "CustomLLMAnalyst":
        """Create an analyst from this template."""
        template = PerspectiveTemplate(
            name=self.name,
            display_name=f"{self.perspective.title()} Analyst",
            focus=self.system_prompt[:100],
            analysis_prompt=self.system_prompt,
            considerations=self.focus_areas,
            tags=[self.perspective],
        )
        return CustomLLMAnalyst(
            template=template,
            agent_id=f"{self.perspective}_analyst",
            context=context,
            message_bus=message_bus,
        )


def load_template_from_yaml(path: Path) -> AgentTemplate:
    """
    Load an agent template from a YAML file.

    Args:
        path: Path to YAML template file

    Returns:
        AgentTemplate instance
    """
    with path.open() as f:
        data = yaml.safe_load(f)

    return AgentTemplate(
        name=data.get("name", path.stem),
        perspective=data.get("perspective", path.stem),
        system_prompt=data.get("system_prompt", ""),
        model=data.get("model", "claude-sonnet"),
        max_tokens=data.get("max_tokens", 1000),
        temperature=data.get("temperature", 0.7),
        focus_areas=data.get("focus_areas", []),
    )


class TemplateRegistry:
    """Registry for managing YAML-based agent templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path("agents/coordinator/templates")
        self.templates: Dict[str, AgentTemplate] = {}

    def load_all(self) -> None:
        """Load all templates from the templates directory."""
        if not self.templates_dir.exists():
            return

        for yaml_file in self.templates_dir.glob("*.yaml"):
            try:
                template = load_template_from_yaml(yaml_file)
                self.templates[template.perspective] = template
            except Exception as e:
                print(f"Warning: Failed to load template {yaml_file}: {e}")

    def get(self, perspective: str) -> Optional[AgentTemplate]:
        """Get a template by perspective name."""
        return self.templates.get(perspective)


def create_custom_agent(
    perspective: str,
    agent_id: str,
    context: DebateContext,
    message_bus: MessageBus,
    use_llm: bool = True
) -> LLMDebateAgent:
    """
    Create an agent from a perspective template.

    Works with both built-in and custom perspectives.

    Args:
        perspective: Perspective name
        agent_id: Unique agent identifier
        context: Debate context
        message_bus: Message bus
        use_llm: Whether to use LLM

    Returns:
        LLMDebateAgent instance
    """
    template = get_perspective(perspective)

    if template is None:
        raise ValueError(f"Unknown perspective: {perspective}. "
                        f"Available: {list(list_perspectives().keys())}")

    return CustomLLMAnalyst(
        template=template,
        agent_id=agent_id,
        context=context,
        message_bus=message_bus,
        use_llm=use_llm
    )
