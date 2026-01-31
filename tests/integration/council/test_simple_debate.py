"""
Simple integration test for Council Pattern Phase 2.

Tests end-to-end debate with SimpleDebateAgent.
"""

import asyncio
import pytest
from pathlib import Path
import shutil

from agents.coordinator.debate_agent import SimpleDebateAgent
from agents.coordinator.council_orchestrator import CouncilOrchestrator
from orchestration.debate_context import Position


class TestSimpleDebate:
    """Test basic debate flow with pre-determined positions."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test councils after each test."""
        yield
        # Clean up .aibrain/councils/TEST-* directories
        councils_dir = Path(".aibrain/councils")
        if councils_dir.exists():
            for council_dir in councils_dir.glob("TEST-*"):
                shutil.rmtree(council_dir)

    @pytest.mark.asyncio
    async def test_two_agent_debate_consensus(self):
        """Test debate with 2 agents reaching consensus (both SUPPORT)."""

        # Define agent types (using SimpleDebateAgent with pre-determined positions)
        def create_cost_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="ROI positive after 6 months. No licensing fees.",
                evidence=["https://example.com/pricing", "Internal cost analysis"],
                confidence=0.8
            )

        def create_integration_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Integration complexity is manageable with existing team.",
                evidence=["Team capacity assessment", "Existing codebase analysis"],
                confidence=0.7
            )

        # Create orchestrator
        council = CouncilOrchestrator(
            topic="Should we adopt LlamaIndex for RAG?",
            agent_types={
                "cost": create_cost_agent,
                "integration": create_integration_agent
            },
            rounds=3,
            council_id="TEST-CONSENSUS-001"
        )

        # Run debate
        result = await council.run_debate()

        # Verify result
        assert result.recommendation == "ADOPT"  # Both support → ADOPT
        assert result.confidence > 0.7  # High consensus
        assert result.vote_breakdown["SUPPORT"] == 2
        assert result.vote_breakdown["OPPOSE"] == 0
        assert len(result.arguments) >= 2  # At least one argument per agent
        assert result.duration_seconds >= 0

        # Verify manifest created
        manifest_path = Path(result.manifest_path)
        assert manifest_path.exists()
        assert manifest_path.read_text().strip()  # Not empty

    @pytest.mark.asyncio
    async def test_two_agent_debate_split(self):
        """Test debate with 2 agents in disagreement (SUPPORT vs OPPOSE)."""

        def create_cost_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="ROI positive after 6 months.",
                evidence=["Cost analysis"],
                confidence=0.8
            )

        def create_integration_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.OPPOSE,
                reasoning="Integration complexity too high for current team capacity.",
                evidence=["Team capacity assessment"],
                confidence=0.7
            )

        # Create orchestrator
        council = CouncilOrchestrator(
            topic="Should we adopt LlamaIndex for RAG?",
            agent_types={
                "cost": create_cost_agent,
                "integration": create_integration_agent
            },
            rounds=3,
            council_id="TEST-SPLIT-001"
        )

        # Run debate
        result = await council.run_debate()

        # Verify result (50-50 split → SPLIT or CONDITIONAL)
        assert result.recommendation in ["SPLIT", "CONDITIONAL"]
        assert result.vote_breakdown["SUPPORT"] == 1
        assert result.vote_breakdown["OPPOSE"] == 1
        assert len(result.arguments) >= 2

    @pytest.mark.asyncio
    async def test_three_agent_debate_conditional(self):
        """Test debate with 3 agents (2 SUPPORT, 1 NEUTRAL → CONDITIONAL)."""

        def create_cost_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="ROI positive after 6 months.",
                evidence=["Cost analysis"],
                confidence=0.8
            )

        def create_performance_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Performance gains significant for large document sets.",
                evidence=["Benchmark results"],
                confidence=0.85
            )

        def create_integration_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.NEUTRAL,
                reasoning="Integration complexity manageable but requires team training.",
                evidence=["Team assessment"],
                confidence=0.7
            )

        # Create orchestrator
        council = CouncilOrchestrator(
            topic="Should we adopt LlamaIndex for RAG?",
            agent_types={
                "cost": create_cost_agent,
                "performance": create_performance_agent,
                "integration": create_integration_agent
            },
            rounds=3,
            council_id="TEST-CONDITIONAL-001"
        )

        # Run debate
        result = await council.run_debate()

        # Verify result (66% SUPPORT → CONDITIONAL or ADOPT)
        assert result.recommendation in ["CONDITIONAL", "ADOPT"]
        assert result.vote_breakdown["SUPPORT"] == 2
        assert result.vote_breakdown["NEUTRAL"] == 1
        assert result.confidence > 0.5
        assert len(result.arguments) >= 3

    @pytest.mark.asyncio
    async def test_debate_timeline(self):
        """Test that debate timeline is generated correctly."""

        def create_cost_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="ROI positive.",
                evidence=["Cost analysis"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test timeline generation",
            agent_types={"cost": create_cost_agent},
            rounds=1,
            council_id="TEST-TIMELINE-001"
        )

        await council.run_debate()

        # Get timeline
        timeline = council.get_debate_timeline()

        # Verify timeline contains key events
        assert "INIT:" in timeline
        assert "Test timeline generation" in timeline
        assert "SPAWN:" in timeline
        assert "cost_analyst" in timeline
        assert "ROUND 1 START" in timeline

    @pytest.mark.asyncio
    async def test_debate_stats(self):
        """Test that debate statistics are collected correctly."""

        def create_cost_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="ROI positive.",
                evidence=["Cost analysis"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test stats collection",
            agent_types={"cost": create_cost_agent},
            rounds=1,
            council_id="TEST-STATS-001"
        )

        await council.run_debate()

        # Get stats
        stats = council.get_stats()

        # Verify stats
        assert stats["council_id"] == "TEST-STATS-001"
        assert stats["topic"] == "Test stats collection"
        assert stats["perspectives"] == ["cost"]
        assert stats["agents_spawned"] == 1
        assert "context_summary" in stats
        assert "manifest_stats" in stats
        assert "message_bus_stats" in stats


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
