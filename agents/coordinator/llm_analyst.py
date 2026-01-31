"""
LLM-Powered Analyst Agents for Council Pattern.

Replaces pattern-based analysis with actual LLM calls for dynamic,
context-aware architectural analysis.

Uses Claude Code CLI (claude.ai subscription) instead of Anthropic API.

Usage:
    from agents.coordinator.llm_analyst import LLMAnalyst, AnalystConfig

    config = AnalystConfig(
        perspective="cost",
        system_prompt="You are a cost analyst..."
    )
    analyst = LLMAnalyst(agent_id="cost", context=ctx, message_bus=bus, config=config)
    result = await analyst.analyze()
"""

import json
import subprocess
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from orchestration.debate_context import DebateContext, Position, Argument
from orchestration.message_bus import MessageBus


# Cost tracking for Claude.ai subscription usage
# These are estimates since Claude.ai subscription is flat-rate
# Used for budget tracking/circuit breakers, not actual billing
MODEL_PRICING = {
    "claude-sonnet": {"input": 0.00, "output": 0.00},  # Subscription - no per-token cost
    "claude-haiku": {"input": 0.00, "output": 0.00},
    "claude-opus": {"input": 0.00, "output": 0.00},
    # Estimate token usage for budget tracking (virtual cost)
    "default": {"input": 0.001, "output": 0.005},  # $0.001/1K input, $0.005/1K output
}


@dataclass
class AnalystConfig:
    """Configuration for an LLM analyst."""
    perspective: str
    system_prompt: str
    model: str = "claude-sonnet"  # Uses Claude Code CLI (claude.ai subscription)
    max_tokens: int = 1000
    temperature: float = 0.7


@dataclass
class AnalysisResult:
    """Result of an LLM analysis."""
    position: Position
    reasoning: str
    evidence: List[str]
    confidence: float
    cost_usd: float = 0.0


class LLMProvider:
    """
    LLM provider using Claude Code CLI (claude.ai subscription).

    Uses subprocess to call the `claude` CLI tool instead of direct API calls.
    This allows using your Claude.ai subscription instead of paying per API call.
    """

    def __init__(self, model: str = "claude-sonnet"):
        self.model = model
        self._pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate virtual cost for budget tracking.

        Note: Claude.ai subscription is flat-rate, but we track virtual costs
        for circuit breaker budget limits.
        """
        input_cost = input_tokens * self._pricing["input"] / 1_000
        output_cost = output_tokens * self._pricing["output"] / 1_000
        return input_cost + output_cost

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Call Claude Code CLI.

        Returns dict with:
            - content: The response text
            - usage: {input_tokens, output_tokens} (estimated)
        """
        try:
            # Combine system and user prompts for Claude Code
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Run claude CLI as subprocess
            result = await asyncio.create_subprocess_exec(
                "claude",
                "-p", full_prompt,
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
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            content = stdout.decode().strip()

            # Estimate token usage (rough approximation)
            input_tokens = len(full_prompt) // 4  # ~4 chars per token
            output_tokens = len(content) // 4

            return {
                "content": content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            }

        except FileNotFoundError:
            # Claude CLI not installed
            return {
                "content": json.dumps({
                    "position": "neutral",
                    "reasoning": "Analysis unavailable - Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code",
                    "evidence": [],
                    "confidence": 0.5,
                }),
                "usage": {"input_tokens": 100, "output_tokens": 50},
            }
        except asyncio.TimeoutError:
            return {
                "content": json.dumps({
                    "position": "neutral",
                    "reasoning": "Analysis timed out after 2 minutes.",
                    "evidence": [],
                    "confidence": 0.5,
                }),
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "error": "Timeout",
            }
        except Exception as e:
            # Other error - return error response
            return {
                "content": json.dumps({
                    "position": "neutral",
                    "reasoning": f"Analysis unavailable due to error: {str(e)[:100]}",
                    "evidence": [],
                    "confidence": 0.5,
                }),
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "error": str(e),
            }


class LLMAnalyst:
    """
    LLM-powered analyst agent for council debates.

    Uses actual LLM calls to analyze topics from a specific perspective,
    incorporating context from other agents' arguments.
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        config: AnalystConfig,
    ):
        self.agent_id = agent_id
        self.context = context
        self.message_bus = message_bus
        self.config = config
        self.perspective = config.perspective
        self._provider = LLMProvider(model=config.model)
        self._total_cost = 0.0

    async def analyze(self) -> AnalysisResult:
        """
        Perform LLM-powered analysis of the debate topic.

        Returns:
            AnalysisResult with position, reasoning, evidence, and confidence
        """
        # Build prompt with context
        prompt = self._build_analysis_prompt()

        try:
            response = await self._call_llm(prompt)

            # Parse response
            position_str = response.get("position", "neutral").lower()
            position = self._parse_position(position_str)

            # Calculate cost
            usage = response.get("usage", {})
            cost = self._provider.calculate_cost(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            )
            self._total_cost += cost

            return AnalysisResult(
                position=position,
                reasoning=response.get("reasoning", "No reasoning provided."),
                evidence=response.get("evidence", []),
                confidence=float(response.get("confidence", 0.5)),
                cost_usd=cost,
            )

        except Exception as e:
            # Return neutral on error
            return AnalysisResult(
                position=Position.NEUTRAL,
                reasoning=f"Analysis unavailable due to error: {str(e)[:100]}",
                evidence=[],
                confidence=0.5,
                cost_usd=0.0,
            )

    async def participate_in_round(self, round_num: int) -> None:
        """
        Participate in a debate round.

        Analyzes the topic and publishes argument to the context.
        """
        result = await self.analyze()

        # Create argument object
        argument = Argument(
            agent_id=self.agent_id,
            perspective=self.perspective,
            position=result.position,
            evidence=result.evidence,
            reasoning=result.reasoning,
            confidence=result.confidence,
            round_number=round_num,
        )

        # Add argument to context
        await self.context.post_argument(argument)

        # Publish to message bus if it has publish method
        if hasattr(self.message_bus, 'publish'):
            await self.message_bus.publish(
                topic="debate.argument",
                message={
                    "agent_id": self.agent_id,
                    "round": round_num,
                    "position": result.position.value if hasattr(result.position, 'value') else str(result.position),
                    "reasoning": result.reasoning,
                    "confidence": result.confidence,
                },
            )

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call the LLM and parse the response.

        Args:
            prompt: The user prompt to send

        Returns:
            Parsed response dict with position, reasoning, evidence, confidence
        """
        response = await self._provider.call(
            system_prompt=self.config.system_prompt,
            user_prompt=prompt,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        # Parse JSON from response
        content = response.get("content", "{}")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract from text
            parsed = self._extract_from_text(content)

        # Include usage info
        parsed["usage"] = response.get("usage", {})

        return dict(parsed)

    def _build_analysis_prompt(self) -> str:
        """Build the analysis prompt with debate context."""
        topic = self.context.topic
        existing_args = self.context.get_arguments()  # Get all arguments

        prompt_parts = [
            f"Analyze this architectural decision from a {self.perspective} perspective:",
            f"\nTopic: {topic}",
        ]

        if existing_args:
            prompt_parts.append("\nOther perspectives so far:")
            for arg in existing_args[-5:]:  # Last 5 arguments
                pos_str = arg.position.value if hasattr(arg.position, 'value') else str(arg.position)
                prompt_parts.append(
                    f"- {arg.agent_id}: {pos_str} - "
                    f"{arg.reasoning[:100]}..."
                )

        prompt_parts.append("""
Please respond with a JSON object containing:
{
    "position": "support" | "oppose" | "neutral",
    "reasoning": "Your detailed reasoning",
    "evidence": ["List of supporting evidence or data points"],
    "confidence": 0.0-1.0
}
""")

        return "\n".join(prompt_parts)

    def _parse_position(self, position_str: str) -> Position:
        """Parse position string to Position enum."""
        position_map = {
            "support": Position.SUPPORT,
            "oppose": Position.OPPOSE,
            "neutral": Position.NEUTRAL,
        }
        return position_map.get(position_str.lower(), Position.NEUTRAL)

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract analysis from non-JSON text response."""
        # Simple heuristic extraction
        position = Position.NEUTRAL
        if "support" in text.lower():
            position = Position.SUPPORT
        elif "oppose" in text.lower() or "against" in text.lower():
            position = Position.OPPOSE

        return {
            "position": position.value if hasattr(position, 'value') else str(position),
            "reasoning": text[:500],
            "evidence": [],
            "confidence": 0.6,
        }

    def get_total_cost(self) -> float:
        """Get total cost incurred by this analyst."""
        return self._total_cost


# Predefined analyst configurations
ANALYST_CONFIGS = {
    "cost": AnalystConfig(
        perspective="cost",
        system_prompt="""You are a Cost Analyst specializing in technology decisions.
Analyze financial implications including:
- Licensing and subscription costs
- Infrastructure and hosting costs
- Development and maintenance costs
- ROI and payback period
- Hidden costs and long-term implications

Provide concrete numbers and estimates where possible.
Respond with a JSON object containing position, reasoning, evidence, and confidence.""",
    ),
    "integration": AnalystConfig(
        perspective="integration",
        system_prompt="""You are an Integration Analyst specializing in system architecture.
Analyze integration complexity including:
- API compatibility and design
- Data flow and transformation needs
- Existing system dependencies
- Migration complexity
- Team learning curve

Consider both short-term and long-term integration challenges.
Respond with a JSON object containing position, reasoning, evidence, and confidence.""",
    ),
    "performance": AnalystConfig(
        perspective="performance",
        system_prompt="""You are a Performance Analyst specializing in system optimization.
Analyze performance implications including:
- Latency and throughput characteristics
- Scalability under load
- Resource utilization (CPU, memory, network)
- Caching and optimization opportunities
- Benchmarks and real-world performance data

Provide specific metrics and comparisons where possible.
Respond with a JSON object containing position, reasoning, evidence, and confidence.""",
    ),
    "alternatives": AnalystConfig(
        perspective="alternatives",
        system_prompt="""You are an Alternatives Analyst specializing in technology evaluation.
Analyze alternative solutions including:
- Competing technologies and their trade-offs
- Build vs buy considerations
- Open source vs commercial options
- Future technology trends
- Market adoption and community support

Provide balanced comparison of options.
Respond with a JSON object containing position, reasoning, evidence, and confidence.""",
    ),
    "security": AnalystConfig(
        perspective="security",
        system_prompt="""You are a Security Analyst specializing in application security.
Analyze security implications including:
- Authentication and authorization
- Data protection and encryption
- Compliance requirements (GDPR, HIPAA, SOC2)
- Attack surface and vulnerabilities
- Security best practices and auditing

Consider both technical and organizational security aspects.
Respond with a JSON object containing position, reasoning, evidence, and confidence.""",
    ),
}


def create_llm_analyst(
    perspective: str,
    context: DebateContext,
    message_bus: MessageBus,
    model: str = "claude-sonnet",  # Uses Claude Code CLI
) -> LLMAnalyst:
    """
    Factory function to create an LLM analyst with predefined config.

    Args:
        perspective: One of "cost", "integration", "performance", "alternatives", "security"
        context: Debate context
        message_bus: Message bus for communication
        model: LLM model to use

    Returns:
        Configured LLMAnalyst instance
    """
    if perspective not in ANALYST_CONFIGS:
        raise ValueError(f"Unknown perspective: {perspective}. "
                        f"Available: {list(ANALYST_CONFIGS.keys())}")

    config = ANALYST_CONFIGS[perspective]
    config.model = model

    return LLMAnalyst(
        agent_id=f"{perspective}_analyst",
        context=context,
        message_bus=message_bus,
        config=config,
    )
