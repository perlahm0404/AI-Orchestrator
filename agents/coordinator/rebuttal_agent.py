"""
LLM-Powered Rebuttal Agent for Council Pattern.

Generates dynamic rebuttals in response to other agents' arguments.

Usage:
    from agents.coordinator.rebuttal_agent import RebuttalAgent, RebuttalConfig

    agent = RebuttalAgent(agent_id="perf", context=ctx, config=config)
    result = await agent.generate_rebuttal(round_num=2)
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from orchestration.debate_context import DebateContext, Position, Argument
from agents.coordinator.llm_analyst import LLMProvider


@dataclass
class RebuttalConfig:
    """Configuration for a rebuttal agent."""
    perspective: str
    system_prompt: str
    model: str = "claude-3-haiku-20240307"
    max_tokens: int = 1500
    temperature: float = 0.7


@dataclass
class RebuttalResult:
    """Result of rebuttal generation."""
    position: Position
    reasoning: str
    rebuttals: List[Dict[str, str]]  # [{"to": agent_id, "response": text}]
    evidence: List[str]
    confidence: float
    cost_usd: float = 0.0


class RebuttalAgent:
    """
    Agent that generates rebuttals to other agents' arguments.

    Unlike the base LLMAnalyst, this agent specifically focuses on
    responding to and countering other perspectives.
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        config: RebuttalConfig,
    ):
        self.agent_id = agent_id
        self.context = context
        self.config = config
        self.perspective = config.perspective
        self._provider = LLMProvider(model=config.model)
        self._total_cost = 0.0

    async def generate_rebuttal(self, round_num: int) -> RebuttalResult:
        """
        Generate rebuttals to other agents' arguments.

        Args:
            round_num: Current debate round

        Returns:
            RebuttalResult with position, rebuttals, and reasoning
        """
        prompt = self._build_rebuttal_prompt(round_num)

        try:
            response = await self._call_llm(prompt)

            position = self._parse_position(response.get("position", "neutral"))

            # Parse rebuttals
            rebuttals = response.get("rebuttals", [])
            if not isinstance(rebuttals, list):
                rebuttals = []

            # Calculate cost
            usage = response.get("usage", {})
            cost = self._provider.calculate_cost(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            )
            self._total_cost += cost

            return RebuttalResult(
                position=position,
                reasoning=response.get("reasoning", ""),
                rebuttals=rebuttals,
                evidence=response.get("evidence", []),
                confidence=float(response.get("confidence", 0.7)),
                cost_usd=cost,
            )

        except Exception as e:
            return RebuttalResult(
                position=Position.NEUTRAL,
                reasoning=f"Rebuttal generation failed: {str(e)[:100]}",
                rebuttals=[],
                evidence=[],
                confidence=0.5,
                cost_usd=0.0,
            )

    def _build_rebuttal_prompt(self, round_num: int) -> str:
        """Build prompt for rebuttal generation."""
        topic = self.context.topic
        existing_args = self.context.get_arguments()

        # Find arguments to rebut (from other agents)
        other_args = [a for a in existing_args if a.agent_id != self.agent_id]

        prompt_parts = [
            f"Topic: {topic}",
            f"\nYou are the {self.perspective} analyst in round {round_num}.",
            "\nOther agents have made the following arguments:",
        ]

        for arg in other_args:
            pos_str = arg.position.value if hasattr(arg.position, 'value') else str(arg.position)
            prompt_parts.append(
                f"\n{arg.agent_id} ({arg.perspective}): {pos_str}"
                f"\n  Reasoning: {arg.reasoning}"
                f"\n  Evidence: {', '.join(arg.evidence[:3])}"
            )

        prompt_parts.append("""

Please respond with a JSON object:
{
    "position": "support" | "oppose" | "neutral",
    "reasoning": "Your overall position considering all arguments",
    "rebuttals": [
        {"to": "agent_id", "response": "Your response to their argument"}
    ],
    "evidence": ["Your supporting evidence"],
    "confidence": 0.0-1.0
}

Focus on:
1. Addressing the strongest opposing arguments
2. Building on supporting arguments
3. Presenting new evidence from your perspective
""")

        return "\n".join(prompt_parts)

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call LLM and parse response."""
        response = await self._provider.call(
            system_prompt=self.config.system_prompt,
            user_prompt=prompt,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        content = response.get("content", "{}")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {
                "position": "neutral",
                "reasoning": content[:500],
                "rebuttals": [],
                "evidence": [],
                "confidence": 0.6,
            }

        parsed["usage"] = response.get("usage", {})
        return dict(parsed)

    def _parse_position(self, position_str: str) -> Position:
        """Parse position string to enum."""
        position_map = {
            "support": Position.SUPPORT,
            "oppose": Position.OPPOSE,
            "neutral": Position.NEUTRAL,
        }
        return position_map.get(position_str.lower(), Position.NEUTRAL)

    def get_total_cost(self) -> float:
        """Get total cost incurred."""
        return self._total_cost
