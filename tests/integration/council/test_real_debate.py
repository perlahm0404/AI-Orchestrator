"""
End-to-end integration test for Council Pattern with real analyst agents.

Tests full debate with CostAnalystAgent, IntegrationAnalystAgent, etc.
"""

import pytest
from pathlib import Path
import shutil

from agents.analyst.cost_analyst import CostAnalystAgent
from agents.analyst.integration_analyst import IntegrationAnalystAgent
from agents.analyst.performance_analyst import PerformanceAnalystAgent
from agents.analyst.alternatives_analyst import AlternativesAnalystAgent
from agents.analyst.security_analyst import SecurityAnalystAgent
from agents.coordinator.council_orchestrator import CouncilOrchestrator


class TestRealDebate:
    """Test debates with real analyst agents."""

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
    async def test_llamaindex_debate(self):
        """Test debate on 'Should we adopt LlamaIndex for RAG?'"""

        # Create orchestrator with real analyst agents
        council = CouncilOrchestrator(
            topic="Should we adopt LlamaIndex for RAG?",
            agent_types={
                "cost": CostAnalystAgent,
                "integration": IntegrationAnalystAgent,
                "performance": PerformanceAnalystAgent,
                "alternatives": AlternativesAnalystAgent,
                "security": SecurityAnalystAgent
            },
            rounds=3,
            council_id="TEST-LLAMAINDEX-001"
        )

        # Run debate
        result = await council.run_debate()

        # Verify result structure
        assert result.council_id == "TEST-LLAMAINDEX-001"
        assert result.topic == "Should we adopt LlamaIndex for RAG?"
        assert result.recommendation in ["ADOPT", "REJECT", "CONDITIONAL", "SPLIT"]
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.arguments) >= 5  # At least one per agent
        assert result.duration_seconds >= 0

        # Verify all perspectives participated
        perspectives = {arg.perspective for arg in result.arguments}
        assert "cost" in perspectives
        assert "integration" in perspectives
        assert "performance" in perspectives
        assert "alternatives" in perspectives
        assert "security" in perspectives

        # Verify vote breakdown
        assert "SUPPORT" in result.vote_breakdown
        assert "OPPOSE" in result.vote_breakdown
        assert "NEUTRAL" in result.vote_breakdown
        total_votes = sum(result.vote_breakdown.values())
        assert total_votes == 5  # 5 agents

        # Verify key considerations exist
        assert len(result.key_considerations) > 0

        # Verify manifest created
        manifest_path = Path(result.manifest_path)
        assert manifest_path.exists()

        # Print debate summary for manual inspection
        print("\n" + "="*60)
        print(f"Debate: {result.topic}")
        print(f"Recommendation: {result.recommendation} (confidence: {result.confidence:.2f})")
        print(f"Vote breakdown: {result.vote_breakdown}")
        print("\nKey considerations:")
        for i, consideration in enumerate(result.key_considerations, 1):
            print(f"{i}. {consideration}")
        print("="*60)

    @pytest.mark.asyncio
    async def test_sst_vs_vercel_debate(self):
        """Test debate on 'Choose between SST and Vercel for deployment?'"""

        council = CouncilOrchestrator(
            topic="Choose between SST and Vercel for CredentialMate deployment?",
            agent_types={
                "cost": CostAnalystAgent,
                "integration": IntegrationAnalystAgent,
                "performance": PerformanceAnalystAgent,
                "alternatives": AlternativesAnalystAgent,
                "security": SecurityAnalystAgent
            },
            rounds=3,
            council_id="TEST-SST-VERCEL-001"
        )

        result = await council.run_debate()

        # Verify result
        assert result.recommendation in ["ADOPT", "REJECT", "CONDITIONAL", "SPLIT"]
        assert len(result.arguments) >= 5

        # Print debate summary
        print("\n" + "="*60)
        print(f"Debate: {result.topic}")
        print(f"Recommendation: {result.recommendation} (confidence: {result.confidence:.2f})")
        print(f"Vote breakdown: {result.vote_breakdown}")
        print("\nKey considerations:")
        for i, consideration in enumerate(result.key_considerations, 1):
            print(f"{i}. {consideration}")
        print("="*60)

    @pytest.mark.asyncio
    async def test_jsonb_debate(self):
        """Test debate on 'Move to PostgreSQL JSONB columns?'"""

        council = CouncilOrchestrator(
            topic="Should we move from normalized tables to JSONB columns for physician licenses?",
            agent_types={
                "cost": CostAnalystAgent,
                "integration": IntegrationAnalystAgent,
                "performance": PerformanceAnalystAgent,
                "alternatives": AlternativesAnalystAgent,
                "security": SecurityAnalystAgent
            },
            rounds=3,
            council_id="TEST-JSONB-001"
        )

        result = await council.run_debate()

        # Verify result
        assert result.recommendation in ["ADOPT", "REJECT", "CONDITIONAL", "SPLIT"]
        assert len(result.arguments) >= 5

        # Print debate summary
        print("\n" + "="*60)
        print(f"Debate: {result.topic}")
        print(f"Recommendation: {result.recommendation} (confidence: {result.confidence:.2f})")
        print(f"Vote breakdown: {result.vote_breakdown}")
        print("\nKey considerations:")
        for i, consideration in enumerate(result.key_considerations, 1):
            print(f"{i}. {consideration}")
        print("="*60)

    @pytest.mark.asyncio
    async def test_debate_timeline_generation(self):
        """Verify debate timeline is generated correctly."""

        council = CouncilOrchestrator(
            topic="Should we adopt LlamaIndex?",
            agent_types={
                "cost": CostAnalystAgent,
                "performance": PerformanceAnalystAgent
            },
            rounds=2,
            council_id="TEST-TIMELINE-002"
        )

        await council.run_debate()

        # Get timeline
        timeline = council.get_debate_timeline()

        # Verify timeline contains expected events
        assert "INIT:" in timeline
        assert "Should we adopt LlamaIndex" in timeline
        assert "SPAWN:" in timeline
        assert "cost_analyst" in timeline
        assert "performance_analyst" in timeline
        assert "ROUND 1 START" in timeline
        assert "ROUND 2 START" in timeline
        assert "ARGUMENT:" in timeline
        assert "SYNTHESIS:" in timeline

    @pytest.mark.asyncio
    async def test_debate_stats_collection(self):
        """Verify debate statistics are collected correctly."""

        council = CouncilOrchestrator(
            topic="Test debate statistics",
            agent_types={
                "cost": CostAnalystAgent,
                "integration": IntegrationAnalystAgent
            },
            rounds=1,
            council_id="TEST-STATS-002"
        )

        await council.run_debate()

        # Get stats
        stats = council.get_stats()

        # Verify stats structure
        assert stats["council_id"] == "TEST-STATS-002"
        assert stats["topic"] == "Test debate statistics"
        assert stats["perspectives"] == ["cost", "integration"]
        assert stats["agents_spawned"] == 2
        assert "context_summary" in stats
        assert "manifest_stats" in stats
        assert "message_bus_stats" in stats

        # Verify context summary
        context_summary = stats["context_summary"]
        assert context_summary["total_arguments"] >= 2
        assert context_summary["status"] == "COMPLETED"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements
