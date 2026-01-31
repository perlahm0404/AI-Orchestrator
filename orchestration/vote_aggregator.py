"""
VoteAggregator - Synthesizes debate arguments into recommendations.

Collects agent positions, weights by confidence, detects consensus.
"""

from typing import Dict, List

from orchestration.debate_context import Argument, DebateContext, Position


class VoteAggregator:
    """
    Synthesizes council debate into final recommendation.

    Algorithm:
    1. Collect all agent positions (SUPPORT/OPPOSE/NEUTRAL)
    2. Weight by confidence scores
    3. Detect consensus (>70% agreement) vs split decision
    4. Generate recommendation with caveats

    Recommendation types:
    - ADOPT: Strong support (>70% SUPPORT)
    - REJECT: Strong opposition (>70% OPPOSE)
    - CONDITIONAL: Moderate support with caveats (40-70% SUPPORT)
    - SPLIT: No clear consensus (<40% agreement)

    Usage:
        aggregator = VoteAggregator(context)
        result = await aggregator.synthesize()
    """

    def __init__(self, context: DebateContext):
        self.context = context

    async def synthesize(self) -> Dict:
        """
        Synthesize debate into recommendation.

        Returns:
            {
                "recommendation": "ADOPT" | "REJECT" | "CONDITIONAL" | "SPLIT",
                "confidence": 0.0-1.0,
                "vote_breakdown": {"SUPPORT": 2, "OPPOSE": 1, "NEUTRAL": 1},
                "key_considerations": [...],
                "agent_details": [...]
            }
        """
        # Get latest arguments from each agent (Round 3 if available, else latest)
        agent_positions = self._get_latest_positions()

        if not agent_positions:
            return {
                "recommendation": "SPLIT",
                "confidence": 0.0,
                "vote_breakdown": {},
                "key_considerations": ["No arguments posted"],
                "agent_details": []
            }

        # Count votes
        vote_counts = self._count_votes(agent_positions)

        # Calculate weighted confidence
        weighted_confidence = self._calculate_weighted_confidence(agent_positions)

        # Determine recommendation
        recommendation = self._determine_recommendation(vote_counts, len(agent_positions))

        # Extract key considerations
        key_considerations = self._extract_considerations(agent_positions)

        return {
            "recommendation": recommendation,
            "confidence": weighted_confidence,
            "vote_breakdown": vote_counts,
            "key_considerations": key_considerations,
            "agent_details": [
                {
                    "agent_id": arg.agent_id,
                    "perspective": arg.perspective,
                    "position": arg.position.value,
                    "confidence": arg.confidence,
                    "reasoning_preview": arg.reasoning[:200]
                }
                for arg in agent_positions.values()
            ]
        }

    def _get_latest_positions(self) -> Dict[str, Argument]:
        """
        Get latest argument from each agent.

        Returns:
            {agent_id: Argument} (one per agent)
        """
        all_args = self.context.get_arguments()

        # Group by agent, take latest (highest round number)
        latest_by_agent = {}
        for arg in all_args:
            if arg.agent_id not in latest_by_agent or \
               arg.round_number > latest_by_agent[arg.agent_id].round_number:
                latest_by_agent[arg.agent_id] = arg

        return latest_by_agent

    def _count_votes(self, positions: Dict[str, Argument]) -> Dict[str, int]:
        """Count votes by position."""
        counts = {
            "SUPPORT": 0,
            "OPPOSE": 0,
            "NEUTRAL": 0
        }

        for arg in positions.values():
            counts[arg.position.value] += 1

        return counts

    def _calculate_weighted_confidence(self, positions: Dict[str, Argument]) -> float:
        """
        Calculate average confidence weighted by agreement.

        Algorithm:
        - Find majority position (SUPPORT/OPPOSE/NEUTRAL)
        - Average confidence of agents in majority
        - If no majority, average all confidences
        """
        vote_counts = self._count_votes(positions)
        total_agents = len(positions)

        if total_agents == 0:
            return 0.0

        # Find majority position
        majority_position = max(vote_counts.items(), key=lambda item: item[1])[0]
        majority_count = vote_counts[majority_position]

        # If majority < 50%, no clear consensus
        if majority_count < total_agents * 0.5:
            # Average all confidences
            avg_conf = sum(arg.confidence for arg in positions.values()) / total_agents
            # Reduce confidence due to split decision
            return avg_conf * 0.6

        # Average confidence of majority agents
        majority_args = [
            arg for arg in positions.values()
            if arg.position.value == majority_position
        ]
        majority_conf = sum(arg.confidence for arg in majority_args) / len(majority_args)

        # Weight by consensus strength
        consensus_strength = majority_count / total_agents
        return majority_conf * consensus_strength

    def _determine_recommendation(self, vote_counts: Dict[str, int], total_agents: int) -> str:
        """
        Determine recommendation based on vote distribution.

        Rules:
        - >70% SUPPORT → ADOPT
        - >70% OPPOSE → REJECT
        - 40-70% SUPPORT with some NEUTRAL → CONDITIONAL
        - <40% agreement → SPLIT
        """
        if total_agents == 0:
            return "SPLIT"

        support_pct = vote_counts["SUPPORT"] / total_agents
        oppose_pct = vote_counts["OPPOSE"] / total_agents

        # Strong support
        if support_pct > 0.7:
            return "ADOPT"

        # Strong opposition
        if oppose_pct > 0.7:
            return "REJECT"

        # Moderate support
        if 0.4 <= support_pct <= 0.7:
            return "CONDITIONAL"

        # No clear consensus
        return "SPLIT"

    def _extract_considerations(self, positions: Dict[str, Argument]) -> List[str]:
        """
        Extract key considerations from arguments.

        Returns:
            List of consideration strings (max 5)
        """
        considerations = []

        # Group by position
        support_args = [arg for arg in positions.values() if arg.position == Position.SUPPORT]
        oppose_args = [arg for arg in positions.values() if arg.position == Position.OPPOSE]
        neutral_args = [arg for arg in positions.values() if arg.position == Position.NEUTRAL]

        # Add support considerations (top 2 by confidence)
        if support_args:
            top_support = sorted(support_args, key=lambda a: a.confidence, reverse=True)[:2]
            for arg in top_support:
                considerations.append(
                    f"{arg.perspective.title()}: {arg.reasoning[:150]}"
                )

        # Add opposition considerations (top 2 by confidence)
        if oppose_args:
            top_oppose = sorted(oppose_args, key=lambda a: a.confidence, reverse=True)[:2]
            for arg in top_oppose:
                considerations.append(
                    f"{arg.perspective.title()} concern: {arg.reasoning[:150]}"
                )

        # Add neutral considerations (top 1)
        if neutral_args:
            top_neutral = sorted(neutral_args, key=lambda a: a.confidence, reverse=True)[:1]
            for arg in top_neutral:
                considerations.append(
                    f"{arg.perspective.title()} trade-off: {arg.reasoning[:150]}"
                )

        return considerations[:5]  # Max 5 considerations
