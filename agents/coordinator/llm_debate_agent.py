"""
LLMDebateAgent - LLM-powered debate agent for dynamic analysis and rebuttals.

Extends DebateAgent with Claude-powered analysis, rebuttals, and synthesis.
Uses Claude Code CLI (claude.ai subscription) instead of Anthropic API.
"""

import asyncio
import shutil
from abc import abstractmethod
from typing import List, Optional, Dict, Any

from agents.coordinator.debate_agent import DebateAgent
from orchestration.debate_context import Argument, DebateContext, Position
from orchestration.message_bus import MessageBus


class LLMDebateAgent(DebateAgent):
    """
    LLM-powered debate agent base class.

    Uses Claude Code CLI for LLM calls (requires claude.ai subscription).

    Provides:
    - LLM-powered initial analysis
    - Dynamic rebuttals that respond to other agents' arguments
    - Contextual synthesis incorporating all perspectives
    - KO consultation for institutional knowledge

    Subclasses must implement:
    - perspective_prompt: System prompt for this perspective
    - analyze(): Use _llm_analyze() for LLM-powered analysis
    """

    # Default LLM settings (uses Claude Code CLI)
    DEFAULT_MODEL = "claude-sonnet"  # Claude Code uses subscription model
    MAX_TOKENS = 1024

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        perspective: str,
        use_llm: bool = True,
        model: Optional[str] = None
    ):
        super().__init__(agent_id, context, message_bus, perspective)
        self.use_llm = use_llm and self._check_claude_cli()
        self.model = model or self.DEFAULT_MODEL

    def _check_claude_cli(self) -> bool:
        """Check if Claude Code CLI is available."""
        return shutil.which("claude") is not None

    async def _call_claude_cli(self, prompt: str) -> Optional[str]:
        """
        Call Claude Code CLI with a prompt.

        Returns the response text or None if failed.
        """
        try:
            result = await asyncio.create_subprocess_exec(
                "claude",
                "-p", prompt,
                "--output-format", "text",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=120.0  # 2 minute timeout
            )

            if result.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                print(f"Claude CLI error: {error_msg}")
                return None

            return stdout.decode().strip()

        except asyncio.TimeoutError:
            print("Claude CLI timeout after 2 minutes")
            return None
        except FileNotFoundError:
            print("Claude CLI not found - install with: npm install -g @anthropic-ai/claude-code")
            return None
        except Exception as e:
            print(f"Claude CLI error: {e}")
            return None

    @property
    @abstractmethod
    def perspective_prompt(self) -> str:
        """
        System prompt defining this agent's perspective.

        Example for CostAnalyst:
            "You are a cost analyst evaluating architectural decisions.
             Focus on: licensing costs, operational costs, ROI, hidden costs."
        """
        pass

    async def _consult_knowledge_objects(self) -> str:
        """
        Consult Knowledge Objects for relevant institutional knowledge.

        Returns context string with relevant KO insights.
        """
        try:
            from knowledge.service import find_relevant

            # Build tags based on perspective and topic
            tags = [self.perspective, "council", "debate"]

            # Add topic-specific tags
            topic_lower = self.context.topic.lower()
            if "database" in topic_lower or "postgres" in topic_lower:
                tags.append("database")
            if "cache" in topic_lower or "redis" in topic_lower:
                tags.append("caching")
            if "deploy" in topic_lower or "infrastructure" in topic_lower:
                tags.append("deployment")
            if "auth" in topic_lower or "security" in topic_lower:
                tags.append("security")

            # Find relevant KOs
            kos = find_relevant(
                project="ai-orchestrator",  # Check orchestrator first
                tags=tags,
                top_k=3
            )

            if not kos:
                return ""

            # Build context from KOs
            context_parts = ["Previous council decisions on related topics:"]
            for ko in kos:
                context_parts.append(f"- {ko.title}: {ko.what_was_learned[:200]}")

            return "\n".join(context_parts)

        except Exception as e:
            # Graceful degradation - continue without KO context
            print(f"KO consultation warning: {e}")
            return ""

    async def _llm_analyze(
        self,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Use Claude Code CLI to analyze the debate topic from this perspective.

        Automatically consults Knowledge Objects for institutional learning.

        Args:
            additional_context: Extra context (e.g., from KO consultation)

        Returns:
            {
                "position": Position,
                "reasoning": str,
                "evidence": List[Dict],
                "confidence": float
            }
        """
        if not self.use_llm:
            return self._fallback_analysis()

        # Consult Knowledge Objects for institutional learning
        ko_context = await self._consult_knowledge_objects()
        if ko_context:
            additional_context = f"{ko_context}\n\n{additional_context}".strip()

        # Build prompt (combine system and user prompts for CLI)
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_analysis_prompt(additional_context)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Call Claude Code CLI
        response = await self._call_claude_cli(full_prompt)

        if response:
            return self._parse_analysis_response(response)
        else:
            return self._fallback_analysis()

    async def _llm_rebuttal(
        self,
        other_arguments: List[Argument]
    ) -> Optional[Dict[str, Any]]:
        """
        Use Claude Code CLI to generate rebuttal to other agents' arguments.

        Args:
            other_arguments: Arguments from other agents

        Returns:
            Rebuttal dict or None if nothing to add
        """
        if not self.use_llm or not other_arguments:
            return None

        # Build rebuttal prompt (combine system and user prompts for CLI)
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_rebuttal_prompt(other_arguments)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Call Claude Code CLI
        response = await self._call_claude_cli(full_prompt)

        if response:
            return self._parse_rebuttal_response(response)
        else:
            return None

    async def _llm_synthesize(
        self,
        all_arguments: List[Argument]
    ) -> str:
        """
        Use Claude Code CLI to synthesize final thoughts incorporating all perspectives.

        Args:
            all_arguments: All arguments from all agents

        Returns:
            Synthesis text
        """
        if not self.use_llm or not all_arguments:
            return self._default_synthesis()

        # Build synthesis prompt (combine system and user prompts for CLI)
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_synthesis_prompt(all_arguments)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Call Claude Code CLI
        response = await self._call_claude_cli(full_prompt)

        if response:
            return response.strip()
        else:
            return self._default_synthesis()

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM calls."""
        return f"""You are a {self.perspective} analyst participating in a structured debate about an architectural decision.

{self.perspective_prompt}

Guidelines:
- Be concise and specific
- Cite evidence when available
- Acknowledge trade-offs
- Express confidence as a number between 0.0 and 1.0
- Position must be one of: SUPPORT, OPPOSE, NEUTRAL"""

    def _build_analysis_prompt(self, additional_context: str = "") -> str:
        """Build the analysis prompt for initial topic analysis."""
        prompt = f"""Analyze this topic from your {self.perspective} perspective:

TOPIC: {self.context.topic}

{f"ADDITIONAL CONTEXT: {additional_context}" if additional_context else ""}

Provide your analysis in this format:
POSITION: [SUPPORT/OPPOSE/NEUTRAL]
CONFIDENCE: [0.0-1.0]
REASONING: [Your analysis in 2-3 sentences]
EVIDENCE:
- [Source 1]: [Brief description]
- [Source 2]: [Brief description]"""
        return prompt

    def _build_rebuttal_prompt(self, other_arguments: List[Argument]) -> str:
        """Build the rebuttal prompt."""
        args_text = "\n\n".join([
            f"**{arg.perspective.upper()} ({arg.position.value}, confidence {arg.confidence:.1%}):**\n{arg.reasoning}"
            for arg in other_arguments
        ])

        return f"""Other agents have made these arguments about: {self.context.topic}

{args_text}

Your initial position was: {self._my_arguments[0].position.value if self._my_arguments else "Not yet stated"}
Your initial reasoning: {self._my_arguments[0].reasoning if self._my_arguments else "None"}

From your {self.perspective} perspective, respond to these arguments:
1. Are there {self.perspective} considerations they missed?
2. Do their points change your position or confidence?
3. What clarification would you add?

Format:
POSITION: [SUPPORT/OPPOSE/NEUTRAL] (may be same or changed)
CONFIDENCE: [0.0-1.0]
REASONING: [Your response in 2-3 sentences]"""

    def _build_synthesis_prompt(self, all_arguments: List[Argument]) -> str:
        """Build the synthesis prompt."""
        args_text = "\n".join([
            f"- {arg.perspective.upper()}: {arg.position.value} ({arg.confidence:.0%}) - {arg.reasoning[:100]}..."
            for arg in all_arguments
        ])

        return f"""The debate on "{self.context.topic}" has concluded.

All positions:
{args_text}

Provide a 2-3 sentence synthesis from your {self.perspective} perspective:
1. What is your final position?
2. How do the other perspectives affect your recommendation?
3. What key caveat should decision-makers consider?"""

    def _parse_analysis_response(self, text: str) -> Dict[str, Any]:
        """Parse LLM response into structured analysis."""
        lines = text.strip().split("\n")

        position = Position.NEUTRAL
        confidence = 0.5
        reasoning = ""
        evidence: List[Dict[str, str]] = []

        for line in lines:
            line = line.strip()
            if line.startswith("POSITION:"):
                pos_str = line.replace("POSITION:", "").strip().upper()
                if "SUPPORT" in pos_str:
                    position = Position.SUPPORT
                elif "OPPOSE" in pos_str:
                    position = Position.OPPOSE
                else:
                    position = Position.NEUTRAL
            elif line.startswith("CONFIDENCE:"):
                try:
                    conf_str = line.replace("CONFIDENCE:", "").strip()
                    confidence = float(conf_str.replace("%", ""))
                    if confidence > 1:
                        confidence /= 100
                except ValueError:
                    confidence = 0.5
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("-") and ":" in line:
                parts = line[1:].split(":", 1)
                if len(parts) == 2:
                    evidence.append({
                        "source": parts[0].strip(),
                        "content": parts[1].strip()
                    })

        # If reasoning wasn't on a separate line, extract from full text
        if not reasoning:
            reasoning = text[:500]

        return {
            "position": position,
            "confidence": min(max(confidence, 0.0), 1.0),
            "reasoning": reasoning,
            "evidence": evidence
        }

    def _parse_rebuttal_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse LLM rebuttal response."""
        result = self._parse_analysis_response(text)

        # Only return if there's meaningful content
        if result["reasoning"] and len(result["reasoning"]) > 20:
            return result
        return None

    @abstractmethod
    def _fallback_analysis(self) -> Dict[str, Any]:
        """
        Fallback pattern-based analysis when LLM is unavailable.

        Subclasses should implement their domain-specific pattern matching.
        """
        pass

    async def rebuttal(self, other_arguments: List[Argument]) -> Optional[Argument]:
        """
        Respond to other agents' arguments using LLM.

        Overrides the base class default to use LLM-powered rebuttals.
        """
        result = await self._llm_rebuttal(other_arguments)

        if result:
            await self.post_argument(
                position=result["position"],
                reasoning=result["reasoning"],
                evidence=[e["source"] for e in result.get("evidence", [])],
                confidence=result["confidence"]
            )
            return self._my_arguments[-1]

        return None

    async def synthesize(self, all_arguments: List[Argument]) -> str:
        """
        Provide synthesis using LLM.

        Overrides the base class default to use LLM-powered synthesis.
        """
        return await self._llm_synthesize(all_arguments)


class LLMCostAnalyst(LLMDebateAgent):
    """LLM-powered cost analyst."""

    @property
    def perspective_prompt(self) -> str:
        return """Focus on cost implications:
- Licensing costs (open-source vs commercial)
- Operational costs (hosting, API calls, maintenance)
- ROI calculations (time saved, efficiency gains)
- Hidden costs (learning curve, migration, support)
- Cost-benefit analysis over 1-3 year horizon"""

    def _fallback_analysis(self) -> Dict[str, Any]:
        """Pattern-based cost analysis fallback."""
        topic_lower = self.context.topic.lower()

        if "open source" in topic_lower or "free" in topic_lower:
            return {
                "position": Position.SUPPORT,
                "reasoning": "Open source reduces licensing costs significantly.",
                "evidence": [],
                "confidence": 0.7
            }
        elif "enterprise" in topic_lower or "paid" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": "Enterprise solutions require cost-benefit analysis.",
                "evidence": [],
                "confidence": 0.5
            }
        else:
            return {
                "position": Position.NEUTRAL,
                "reasoning": "Cost analysis requires specific pricing data.",
                "evidence": [],
                "confidence": 0.5
            }

    async def analyze(self) -> Argument:
        """Analyze cost implications using LLM."""
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


class LLMIntegrationAnalyst(LLMDebateAgent):
    """LLM-powered integration analyst."""

    @property
    def perspective_prompt(self) -> str:
        return """Focus on integration implications:
- Integration complexity and effort required
- Team capacity and skill requirements
- Dependencies and compatibility issues
- Migration path and rollback options
- Impact on existing systems and workflows"""

    def _fallback_analysis(self) -> Dict[str, Any]:
        return {
            "position": Position.NEUTRAL,
            "reasoning": "Integration effort requires detailed assessment.",
            "evidence": [],
            "confidence": 0.5
        }

    async def analyze(self) -> Argument:
        """Analyze integration implications using LLM."""
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


class LLMPerformanceAnalyst(LLMDebateAgent):
    """LLM-powered performance analyst."""

    @property
    def perspective_prompt(self) -> str:
        return """Focus on performance implications:
- Latency and response time impact
- Throughput and scalability
- Resource utilization (CPU, memory, storage)
- Benchmark data and comparisons
- Performance at scale (10x, 100x current load)"""

    def _fallback_analysis(self) -> Dict[str, Any]:
        return {
            "position": Position.NEUTRAL,
            "reasoning": "Performance assessment requires benchmarking.",
            "evidence": [],
            "confidence": 0.5
        }

    async def analyze(self) -> Argument:
        """Analyze performance implications using LLM."""
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


class LLMAlternativesAnalyst(LLMDebateAgent):
    """LLM-powered alternatives analyst."""

    @property
    def perspective_prompt(self) -> str:
        return """Focus on alternative solutions:
- Competing technologies and approaches
- Feature comparison matrix
- Pros and cons of each alternative
- Market adoption and community support
- Future trajectory and vendor lock-in risks"""

    def _fallback_analysis(self) -> Dict[str, Any]:
        return {
            "position": Position.NEUTRAL,
            "reasoning": "Multiple alternatives exist and should be evaluated.",
            "evidence": [],
            "confidence": 0.5
        }

    async def analyze(self) -> Argument:
        """Analyze alternatives using LLM."""
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


class LLMSecurityAnalyst(LLMDebateAgent):
    """LLM-powered security analyst."""

    @property
    def perspective_prompt(self) -> str:
        return """Focus on security implications:
- Vulnerability and attack surface analysis
- Compliance requirements (HIPAA, SOC2, GDPR)
- Authentication and authorization impacts
- Data protection and privacy concerns
- Security track record and CVE history"""

    def _fallback_analysis(self) -> Dict[str, Any]:
        topic_lower = self.context.topic.lower()

        if "hipaa" in topic_lower or "compliance" in topic_lower:
            return {
                "position": Position.OPPOSE,
                "reasoning": "Security and compliance implications require careful review.",
                "evidence": [],
                "confidence": 0.7
            }
        else:
            return {
                "position": Position.NEUTRAL,
                "reasoning": "Security assessment needed before proceeding.",
                "evidence": [],
                "confidence": 0.5
            }

    async def analyze(self) -> Argument:
        """Analyze security implications using LLM."""
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


# Factory function for creating LLM-powered agents
def create_llm_agent(
    perspective: str,
    agent_id: str,
    context: DebateContext,
    message_bus: MessageBus,
    use_llm: bool = True
) -> LLMDebateAgent:
    """
    Create an LLM-powered debate agent for the given perspective.

    Args:
        perspective: One of "cost", "integration", "performance", "alternatives", "security"
        agent_id: Unique agent identifier
        context: Debate context
        message_bus: Message bus for inter-agent communication
        use_llm: Whether to use LLM (falls back to pattern-based if False)

    Returns:
        LLMDebateAgent instance
    """
    if perspective == "cost":
        return LLMCostAnalyst(agent_id, context, message_bus, perspective, use_llm)
    elif perspective == "integration":
        return LLMIntegrationAnalyst(agent_id, context, message_bus, perspective, use_llm)
    elif perspective == "performance":
        return LLMPerformanceAnalyst(agent_id, context, message_bus, perspective, use_llm)
    elif perspective == "alternatives":
        return LLMAlternativesAnalyst(agent_id, context, message_bus, perspective, use_llm)
    elif perspective == "security":
        return LLMSecurityAnalyst(agent_id, context, message_bus, perspective, use_llm)
    else:
        raise ValueError(f"Unknown perspective: {perspective}. "
                        f"Available: cost, integration, performance, alternatives, security")
