"""
CouncilOrchestrator - Manages council debate lifecycle.

Spawns perspective agents, runs debate rounds, triggers synthesis.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Type

from agents.coordinator.debate_agent import DebateAgent
from orchestration.debate_context import Argument, DebateContext, Position
from orchestration.debate_manifest import DebateManifest
from orchestration.message_bus import MessageBus


@dataclass
class DebateResult:
    """Final result of a council debate."""
    council_id: str
    topic: str
    recommendation: str  # "ADOPT", "REJECT", "CONDITIONAL", "SPLIT"
    confidence: float    # 0.0-1.0
    vote_breakdown: Dict[str, int]  # {"SUPPORT": 2, "OPPOSE": 1, "NEUTRAL": 1}
    key_considerations: List[str]  # Caveats, conditions, trade-offs
    arguments: List[Argument]
    duration_seconds: float
    manifest_path: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "council_id": self.council_id,
            "topic": self.topic,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "vote_breakdown": self.vote_breakdown,
            "key_considerations": self.key_considerations,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "duration_seconds": self.duration_seconds,
            "manifest_path": self.manifest_path
        }


class CouncilOrchestrator:
    """
    Orchestrates council debates for architectural decisions.

    Workflow:
    1. Parse debate topic
    2. Spawn perspective-specific agents
    3. Run debate rounds:
       - Round 1: Initial analysis (all agents in parallel)
       - Round 2: Rebuttals (agents read others' arguments)
       - Round 3: Synthesis (final thoughts)
    4. Aggregate votes
    5. Generate DebateResult

    Usage:
        council = CouncilOrchestrator(
            topic="Should we adopt LlamaIndex for RAG?",
            agent_types={
                "cost": CostAnalystAgent,
                "integration": IntegrationAnalystAgent,
                "performance": PerformanceAnalystAgent,
                "alternatives": AlternativesAnalystAgent
            },
            rounds=3
        )
        result = await council.run_debate()
    """

    def __init__(
        self,
        topic: str,
        agent_types: Dict[str, Type[DebateAgent]],
        rounds: int = 3,
        max_duration_minutes: int = 30,
        council_id: Optional[str] = None
    ):
        self.topic = topic
        self.agent_types = agent_types
        self.rounds = rounds
        self.max_duration_minutes = max_duration_minutes

        # Generate council ID
        if council_id is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            council_id = f"COUNCIL-{timestamp}"
        self.council_id = council_id

        # Initialize infrastructure
        self.context = DebateContext(
            topic=topic,
            perspectives=list(agent_types.keys()),
            council_id=council_id
        )
        self.message_bus = MessageBus()
        self.manifest = DebateManifest(council_id=council_id)

        # Spawned agents
        self._agents: Dict[str, DebateAgent] = {}

    async def run_debate(self) -> DebateResult:
        """
        Run complete debate lifecycle.

        Returns:
            DebateResult with recommendation and evidence
        """
        # Log debate initialization
        self.manifest.log_council_init(
            topic=self.topic,
            perspectives=list(self.agent_types.keys()),
            metadata={"rounds": self.rounds, "max_duration_minutes": self.max_duration_minutes}
        )

        # Mark debate started
        await self.context.mark_started()

        try:
            # Spawn agents
            await self._spawn_agents()

            # Run debate rounds
            for round_num in range(1, self.rounds + 1):
                await self._run_round(round_num)

            # Generate result
            result = await self._generate_result()

            # Mark debate completed
            await self.context.mark_completed()

            return result

        except Exception as e:
            # Log error
            self.manifest.log_event("error", {
                "error": str(e),
                "stage": "debate_execution"
            })
            raise

    async def _spawn_agents(self):
        """Spawn perspective-specific agents."""
        for perspective, agent_class in self.agent_types.items():
            agent_id = f"{perspective}_analyst"

            # Instantiate agent
            agent = agent_class(
                agent_id=agent_id,
                context=self.context,
                message_bus=self.message_bus,
                perspective=perspective
            )

            self._agents[agent_id] = agent

            # Log spawn
            self.manifest.log_agent_spawn(
                agent_id=agent_id,
                agent_type=agent_class.__name__,
                perspective=perspective
            )

    async def _run_round(self, round_number: int):
        """
        Run a single debate round.

        Round 1: Initial analysis (parallel)
        Round 2: Rebuttals (agents read others' arguments)
        Round 3: Synthesis (final thoughts)
        """
        # Log round start
        self.manifest.log_round_start(round_number)
        await self.context.advance_round()

        if round_number == 1:
            # Round 1: Initial analysis (parallel)
            tasks = [agent.analyze() for agent in self._agents.values()]
            await asyncio.gather(*tasks)

        elif round_number == 2:
            # Round 2: Rebuttals (sequential, so agents can read previous arguments)
            for agent in self._agents.values():
                other_args = agent.get_other_arguments(round_number=1)
                await agent.rebuttal(other_args)

        elif round_number == 3:
            # Round 3: Synthesis (parallel)
            all_args = self.context.get_arguments()
            tasks = [agent.synthesize(all_args) for agent in self._agents.values()]
            await asyncio.gather(*tasks)

        # Log arguments posted this round
        for arg in self.context.get_arguments(round_number=round_number):
            self.manifest.log_argument(
                agent_id=arg.agent_id,
                perspective=arg.perspective,
                position=arg.position.value,
                confidence=arg.confidence,
                reasoning=arg.reasoning
            )

    async def _generate_result(self) -> DebateResult:
        """Generate final debate result."""
        from orchestration.vote_aggregator import VoteAggregator

        # Aggregate votes
        aggregator = VoteAggregator(self.context)
        synthesis = await aggregator.synthesize()

        # Log synthesis
        self.manifest.log_synthesis(
            recommendation=synthesis["recommendation"],
            confidence=synthesis["confidence"],
            vote_breakdown=synthesis["vote_breakdown"]
        )

        # Create result
        result = DebateResult(
            council_id=self.council_id,
            topic=self.topic,
            recommendation=synthesis["recommendation"],
            confidence=synthesis["confidence"],
            vote_breakdown=synthesis["vote_breakdown"],
            key_considerations=synthesis["key_considerations"],
            arguments=self.context.get_arguments(),
            duration_seconds=self.context.get_duration_seconds() or 0,
            manifest_path=str(self.manifest.manifest_path)
        )

        return result

    def get_debate_timeline(self) -> str:
        """Get human-readable debate timeline."""
        return self.manifest.get_timeline()

    def get_stats(self) -> dict:
        """Get debate statistics."""
        return {
            "council_id": self.council_id,
            "topic": self.topic,
            "perspectives": list(self.agent_types.keys()),
            "agents_spawned": len(self._agents),
            "context_summary": self.context.get_summary(),
            "manifest_stats": self.manifest.get_stats(),
            "message_bus_stats": self.message_bus.get_stats()
        }
