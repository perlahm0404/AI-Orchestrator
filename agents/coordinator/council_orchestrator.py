"""
CouncilOrchestrator - Manages council debate lifecycle.

Spawns perspective agents, runs debate rounds, triggers synthesis.
Includes cost tracking and circuit breakers per council-team.yaml governance contract.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Type

from agents.coordinator.debate_agent import DebateAgent
from orchestration.debate_context import Argument, DebateContext
from orchestration.debate_manifest import DebateManifest
from orchestration.message_bus import MessageBus


@dataclass
class CostTracker:
    """
    Tracks LLM costs for a council debate.

    Per council-team.yaml:
    - max_cost_per_debate: $2.00
    - daily_debate_budget: $10.00
    """
    # Estimated costs per agent per round (from governance contract)
    # 5 agents × 3 rounds × ~$0.13/round = ~$2.00 max
    ESTIMATED_COST_PER_AGENT_ROUND = 0.13
    MAX_COST_PER_DEBATE = 2.0

    total_cost: float = 0.0
    cost_by_agent: Dict[str, float] = field(default_factory=dict)
    cost_by_round: Dict[int, float] = field(default_factory=dict)

    def add_cost(self, agent_id: str, round_number: int, cost: float) -> None:
        """Record cost for an agent in a round."""
        self.total_cost += cost

        if agent_id not in self.cost_by_agent:
            self.cost_by_agent[agent_id] = 0.0
        self.cost_by_agent[agent_id] += cost

        if round_number not in self.cost_by_round:
            self.cost_by_round[round_number] = 0.0
        self.cost_by_round[round_number] += cost

    def estimate_round_cost(self, num_agents: int) -> float:
        """Estimate cost for a round based on agent count."""
        return num_agents * self.ESTIMATED_COST_PER_AGENT_ROUND

    def is_budget_exceeded(self) -> bool:
        """Check if debate cost exceeds $2.00 limit."""
        return self.total_cost > self.MAX_COST_PER_DEBATE

    def remaining_budget(self) -> float:
        """Get remaining budget for this debate."""
        return max(0.0, self.MAX_COST_PER_DEBATE - self.total_cost)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "total_cost": round(self.total_cost, 4),
            "cost_by_agent": {k: round(v, 4) for k, v in self.cost_by_agent.items()},
            "cost_by_round": {k: round(v, 4) for k, v in self.cost_by_round.items()},
            "budget_exceeded": self.is_budget_exceeded(),
            "remaining_budget": round(self.remaining_budget(), 4)
        }


class BudgetExceededError(Exception):
    """Raised when debate budget is exceeded (circuit breaker)."""
    pass


class DebateTimeoutError(Exception):
    """Raised when debate exceeds max duration (circuit breaker)."""
    pass


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
    cost_summary: Optional[Dict] = None  # Cost tracking summary

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
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
        if self.cost_summary:
            result["cost_summary"] = self.cost_summary
        return result


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
        council_id: Optional[str] = None,
        enforce_budget: bool = True,
        create_ko: bool = True
    ):
        self.topic = topic
        self.agent_types = agent_types
        self.rounds = rounds
        self.max_duration_minutes = max_duration_minutes
        self.enforce_budget = enforce_budget
        self.create_ko = create_ko  # Create Knowledge Object after debate

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

        # Cost tracking (per council-team.yaml governance)
        self.cost_tracker = CostTracker()

        # Spawned agents
        self._agents: Dict[str, DebateAgent] = {}

        # Track start time for timeout circuit breaker
        self._start_time: Optional[datetime] = None

    async def run_debate(self) -> DebateResult:
        """
        Run complete debate lifecycle.

        Includes circuit breakers for:
        - Budget exceeded ($2.00 max per debate)
        - Timeout exceeded (30 minutes max)

        Returns:
            DebateResult with recommendation and evidence

        Raises:
            BudgetExceededError: If debate cost exceeds $2.00
            DebateTimeoutError: If debate exceeds max duration
        """
        # Track start time for timeout
        self._start_time = datetime.now(timezone.utc)

        # Log debate initialization
        self.manifest.log_council_init(
            topic=self.topic,
            perspectives=list(self.agent_types.keys()),
            metadata={
                "rounds": self.rounds,
                "max_duration_minutes": self.max_duration_minutes,
                "max_cost": CostTracker.MAX_COST_PER_DEBATE,
                "enforce_budget": self.enforce_budget
            }
        )

        # Mark debate started
        await self.context.mark_started()

        try:
            # Spawn agents
            await self._spawn_agents()

            # Run debate rounds with circuit breaker checks
            for round_num in range(1, self.rounds + 1):
                # Check timeout circuit breaker
                self._check_timeout()

                # Check budget circuit breaker before round
                if self.enforce_budget:
                    self._check_budget()

                await self._run_round(round_num)

            # Generate result (includes cost summary)
            result = await self._generate_result()

            # Mark debate completed
            await self.context.mark_completed()

            # Create Knowledge Object if enabled
            if self.create_ko:
                self._create_knowledge_object(result)

            return result

        except (BudgetExceededError, DebateTimeoutError) as e:
            # Log circuit breaker trigger
            self.manifest.log_event("circuit_breaker", {
                "type": type(e).__name__,
                "message": str(e),
                "cost_at_halt": self.cost_tracker.total_cost,
                "duration_at_halt": self._get_elapsed_seconds()
            })
            # Still generate partial result
            result = await self._generate_result(halted=True, halt_reason=str(e))
            await self.context.mark_completed()

            # Create Knowledge Object if enabled (even for halted debates)
            if self.create_ko:
                self._create_knowledge_object(result)

            return result

        except Exception as e:
            # Log error
            self.manifest.log_event("error", {
                "error": str(e),
                "stage": "debate_execution",
                "cost_at_error": self.cost_tracker.total_cost
            })
            raise

    def _check_timeout(self) -> None:
        """Check if debate has exceeded max duration. Raises DebateTimeoutError."""
        if self._start_time is None:
            return

        elapsed_seconds = self._get_elapsed_seconds()
        max_seconds = self.max_duration_minutes * 60

        if elapsed_seconds > max_seconds:
            raise DebateTimeoutError(
                f"Debate exceeded {self.max_duration_minutes} minute limit "
                f"(elapsed: {elapsed_seconds / 60:.1f} minutes)"
            )

    def _check_budget(self) -> None:
        """Check if debate has exceeded cost budget. Raises BudgetExceededError."""
        if self.cost_tracker.is_budget_exceeded():
            raise BudgetExceededError(
                f"Debate exceeded ${CostTracker.MAX_COST_PER_DEBATE:.2f} budget "
                f"(spent: ${self.cost_tracker.total_cost:.2f})"
            )

    def _get_elapsed_seconds(self) -> float:
        """Get elapsed time since debate started."""
        if self._start_time is None:
            return 0.0
        return (datetime.now(timezone.utc) - self._start_time).total_seconds()

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

        Tracks costs for each agent operation.
        """
        # Log round start
        self.manifest.log_round_start(round_number)
        await self.context.advance_round()

        # Estimate cost for this round
        estimated_round_cost = self.cost_tracker.estimate_round_cost(len(self._agents))

        if round_number == 1:
            # Round 1: Initial analysis (parallel)
            tasks = [agent.analyze() for agent in self._agents.values()]
            await asyncio.gather(*tasks)

            # Track estimated costs per agent
            per_agent_cost = estimated_round_cost / len(self._agents)
            for agent_id in self._agents.keys():
                self.cost_tracker.add_cost(agent_id, round_number, per_agent_cost)

        elif round_number == 2:
            # Round 2: Rebuttals (sequential, so agents can read previous arguments)
            for agent in self._agents.values():
                other_args = agent.get_other_arguments(round_number=1)
                await agent.rebuttal(other_args)
                # Track cost per agent
                self.cost_tracker.add_cost(
                    agent.agent_id, round_number,
                    CostTracker.ESTIMATED_COST_PER_AGENT_ROUND
                )

        elif round_number == 3:
            # Round 3: Synthesis (parallel)
            all_args = self.context.get_arguments()
            tasks = [agent.synthesize(all_args) for agent in self._agents.values()]
            await asyncio.gather(*tasks)

            # Track estimated costs per agent
            per_agent_cost = estimated_round_cost / len(self._agents)
            for agent_id in self._agents.keys():
                self.cost_tracker.add_cost(agent_id, round_number, per_agent_cost)

        # Log arguments posted this round (with cost info)
        for arg in self.context.get_arguments(round_number=round_number):
            self.manifest.log_argument(
                agent_id=arg.agent_id,
                perspective=arg.perspective,
                position=arg.position.value,
                confidence=arg.confidence,
                reasoning=arg.reasoning
            )

        # Log round cost summary
        self.manifest.log_event("round_cost", {
            "round": round_number,
            "estimated_cost": round(estimated_round_cost, 4),
            "cumulative_cost": round(self.cost_tracker.total_cost, 4),
            "remaining_budget": round(self.cost_tracker.remaining_budget(), 4)
        })

    async def _generate_result(
        self,
        halted: bool = False,
        halt_reason: Optional[str] = None
    ) -> DebateResult:
        """
        Generate final debate result.

        Args:
            halted: Whether debate was halted by circuit breaker
            halt_reason: Reason for halt (if halted)

        Returns:
            DebateResult with recommendation, cost summary, and evidence
        """
        from orchestration.vote_aggregator import VoteAggregator

        # Aggregate votes
        aggregator = VoteAggregator(self.context)
        synthesis = await aggregator.synthesize()

        # Build cost summary
        cost_summary = self.cost_tracker.to_dict()
        cost_summary["halted"] = halted
        if halt_reason:
            cost_summary["halt_reason"] = halt_reason

        # Log synthesis with cost info
        self.manifest.log_synthesis(
            recommendation=synthesis["recommendation"],
            confidence=synthesis["confidence"],
            vote_breakdown=synthesis["vote_breakdown"]
        )

        # Log final cost summary
        self.manifest.log_event("cost_summary", cost_summary)

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
            manifest_path=str(self.manifest.manifest_path),
            cost_summary=cost_summary
        )

        return result

    def get_debate_timeline(self) -> str:
        """Get human-readable debate timeline."""
        return self.manifest.get_timeline()

    def get_stats(self) -> dict:
        """Get debate statistics including cost tracking."""
        return {
            "council_id": self.council_id,
            "topic": self.topic,
            "perspectives": list(self.agent_types.keys()),
            "agents_spawned": len(self._agents),
            "context_summary": self.context.get_summary(),
            "manifest_stats": self.manifest.get_stats(),
            "message_bus_stats": self.message_bus.get_stats(),
            "cost_tracker": self.cost_tracker.to_dict()
        }

    def get_cost_summary(self) -> dict:
        """Get cost tracking summary for this debate."""
        return self.cost_tracker.to_dict()

    def _create_knowledge_object(self, result: DebateResult) -> Optional[str]:
        """
        Create a Knowledge Object from the debate result.

        Per council-team.yaml integration:
        - create_ko_on_completion: true
        - ko_type: council_decision
        - ko_effectiveness_tracking: true

        Returns:
            KO ID if created, None if skipped or failed
        """
        try:
            from orchestration.council_ko_integration import (
                create_ko_from_debate,
                should_create_ko
            )

            # Check if we should create a KO for this debate
            if not should_create_ko(result):
                return None

            ko_id = create_ko_from_debate(result)

            if ko_id:
                # Log KO creation in manifest
                self.manifest.log_event("ko_created", {
                    "ko_id": ko_id,
                    "recommendation": result.recommendation,
                    "confidence": result.confidence
                })

            return ko_id

        except Exception as e:
            # Log but don't fail - KO creation is optional
            self.manifest.log_event("ko_creation_failed", {
                "error": str(e)
            })
            return None
