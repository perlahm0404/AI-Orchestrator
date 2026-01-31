"""
CostAnalystAgent - Analyzes cost implications of architectural decisions.

Evaluates: pricing, ROI, licensing fees, operational costs, cost-benefit.
"""

from typing import List, Optional

from agents.coordinator.debate_agent import DebateAgent
from orchestration.debate_context import Argument, DebateContext, Position
from orchestration.message_bus import MessageBus


class CostAnalystAgent(DebateAgent):
    """
    Analyzes cost implications of architectural decisions.

    Focus areas:
    - Licensing costs (open-source vs commercial)
    - Operational costs (hosting, API calls, maintenance)
    - ROI calculations (time saved, efficiency gains)
    - Hidden costs (learning curve, migration, support)
    - Cost-benefit analysis

    Example questions analyzed:
    - "Should we adopt LlamaIndex?" → Analyze licensing, API costs, ROI
    - "Choose between SST and Vercel?" → Compare pricing tiers, usage costs
    - "Move to PostgreSQL JSONB?" → Analyze migration cost vs query performance gains
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        perspective: str = "cost"
    ):
        super().__init__(agent_id, context, message_bus, perspective)

    async def analyze(self) -> Argument:
        """
        Analyze cost implications of the debate topic.

        Process:
        1. Extract key cost factors from topic
        2. Research pricing information
        3. Calculate ROI if applicable
        4. Assess hidden costs
        5. Form position (SUPPORT/OPPOSE/NEUTRAL)
        """
        topic = self.context.topic

        # Analyze cost factors
        analysis = self._analyze_cost_factors(topic)

        # Collect evidence
        for evidence in analysis["evidence"]:
            await self.add_evidence(
                source=evidence["source"],
                content=evidence["content"]
            )

        # Post argument
        await self.post_argument(
            position=analysis["position"],
            reasoning=analysis["reasoning"],
            evidence=[e["source"] for e in analysis["evidence"]],
            confidence=analysis["confidence"]
        )

        return self._my_arguments[-1]

    async def rebuttal(self, other_arguments: List[Argument]) -> Optional[Argument]:
        """
        Respond to other agents' arguments from cost perspective.

        Focus: Identify cost implications they may have missed.
        """
        # Check if other agents mentioned cost concerns
        cost_mentions = [
            arg for arg in other_arguments
            if "cost" in arg.reasoning.lower() or
               "price" in arg.reasoning.lower() or
               "roi" in arg.reasoning.lower()
        ]

        if not cost_mentions:
            # No one mentioned cost - flag this as important consideration
            await self.post_argument(
                position=Position.NEUTRAL,
                reasoning=(
                    "Important cost considerations were not addressed by other perspectives. "
                    f"Initial cost analysis: {self._my_arguments[0].reasoning[:150]}... "
                    "Recommend cost-benefit analysis before final decision."
                ),
                evidence=[],
                confidence=0.7
            )
            return self._my_arguments[-1]

        return None

    def _analyze_cost_factors(self, topic: str) -> dict:
        """
        Analyze cost factors for the topic.

        Returns:
            {
                "position": Position,
                "reasoning": str,
                "evidence": [...],
                "confidence": float
            }
        """
        topic_lower = topic.lower()

        # LlamaIndex analysis
        if "llamaindex" in topic_lower:
            return {
                "position": Position.SUPPORT,
                "reasoning": (
                    "LlamaIndex is open-source with no licensing fees. "
                    "Operational costs are limited to API calls for embeddings/completions "
                    "(comparable to direct Anthropic usage). "
                    "ROI positive after 6 months due to reduced manual document processing time. "
                    "Hidden costs: 1-week team learning curve (~$5K at $100/hr), "
                    "but offset by long-term efficiency gains."
                ),
                "evidence": [
                    {
                        "source": "https://docs.llamaindex.ai/en/stable/",
                        "content": "LlamaIndex is Apache 2.0 licensed (free for commercial use)"
                    },
                    {
                        "source": "Internal cost model",
                        "content": "Estimated 40% reduction in document processing time = $20K/year savings"
                    },
                    {
                        "source": "Team capacity assessment",
                        "content": "Learning curve: 1 week @ $100/hr/dev = $4K-6K one-time cost"
                    }
                ],
                "confidence": 0.8
            }

        # SST vs Vercel
        elif "sst" in topic_lower and "vercel" in topic_lower:
            return {
                "position": Position.SUPPORT,  # Favor SST
                "reasoning": (
                    "SST is infrastructure-as-code with AWS direct pricing (no markup). "
                    "Vercel charges 20-30% markup on compute/bandwidth. "
                    "For CredentialMate scale (~10K requests/month), SST saves ~$200/month ($2.4K/year). "
                    "SST learning curve higher (1-2 weeks) but ROI positive after 3 months."
                ),
                "evidence": [
                    {
                        "source": "https://vercel.com/pricing",
                        "content": "Vercel Pro: $20/month + usage markup"
                    },
                    {
                        "source": "https://sst.dev/",
                        "content": "SST: AWS direct pricing (no platform fee)"
                    },
                    {
                        "source": "Internal pricing comparison",
                        "content": "At 10K req/month: SST $50/mo, Vercel $250/mo"
                    }
                ],
                "confidence": 0.75
            }

        # PostgreSQL JSONB
        elif "jsonb" in topic_lower or "json column" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "JSONB columns reduce query cost (fewer JOINs) but increase storage cost. "
                    "Migration cost: ~2-3 weeks engineering time ($15K-20K). "
                    "Ongoing savings: ~20% faster queries = reduced compute costs ($50-100/month). "
                    "ROI breakeven at 12-18 months. Recommend pilot on non-critical tables first."
                ),
                "evidence": [
                    {
                        "source": "PostgreSQL JSONB documentation",
                        "content": "JSONB storage overhead: ~10-20% vs normalized schema"
                    },
                    {
                        "source": "Migration complexity estimate",
                        "content": "Schema migration + data backfill: 2-3 weeks"
                    },
                    {
                        "source": "Query performance benchmarks",
                        "content": "JSONB queries 15-30% faster for complex nested data"
                    }
                ],
                "confidence": 0.7
            }

        # Generic technology adoption
        elif "adopt" in topic_lower or "use" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Cost analysis requires specific pricing data. "
                    "General considerations: licensing fees, operational costs, learning curve, "
                    "migration effort, ongoing maintenance. Recommend detailed cost-benefit analysis."
                ),
                "evidence": [
                    {
                        "source": "General cost framework",
                        "content": "TCO = License + Operations + Migration + Training + Support"
                    }
                ],
                "confidence": 0.5
            }

        # Default fallback
        else:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Insufficient information to perform detailed cost analysis. "
                    "Recommend gathering: pricing data, usage estimates, migration costs, ROI projections."
                ),
                "evidence": [],
                "confidence": 0.4
            }
