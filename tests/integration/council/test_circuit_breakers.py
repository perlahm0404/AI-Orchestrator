"""
Integration tests for Council Pattern circuit breakers.

Tests the governance limits defined in council-team.yaml:
- Budget circuit breaker ($2.00 max per debate)
- Timeout circuit breaker (30 minute max)
- Cost tracking accuracy
"""

import asyncio
import pytest
from pathlib import Path
import shutil
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from agents.coordinator.debate_agent import SimpleDebateAgent
from agents.coordinator.council_orchestrator import (
    CouncilOrchestrator,
    CostTracker,
    BudgetExceededError,
    DebateTimeoutError
)
from orchestration.debate_context import Position


class TestCostTracker:
    """Test cost tracking functionality."""

    def test_cost_tracker_initialization(self):
        """Test CostTracker initializes with zero costs."""
        tracker = CostTracker()

        assert tracker.total_cost == 0.0
        assert tracker.cost_by_agent == {}
        assert tracker.cost_by_round == {}
        assert not tracker.is_budget_exceeded()
        assert tracker.remaining_budget() == 2.0

    def test_add_cost(self):
        """Test adding costs for agents and rounds."""
        tracker = CostTracker()

        tracker.add_cost("cost_analyst", 1, 0.13)
        tracker.add_cost("integration_analyst", 1, 0.13)
        tracker.add_cost("cost_analyst", 2, 0.13)

        assert tracker.total_cost == pytest.approx(0.39, rel=0.01)
        assert tracker.cost_by_agent["cost_analyst"] == pytest.approx(0.26, rel=0.01)
        assert tracker.cost_by_agent["integration_analyst"] == pytest.approx(0.13, rel=0.01)
        assert tracker.cost_by_round[1] == pytest.approx(0.26, rel=0.01)
        assert tracker.cost_by_round[2] == pytest.approx(0.13, rel=0.01)

    def test_budget_exceeded_detection(self):
        """Test budget exceeded detection at $2.00 limit."""
        tracker = CostTracker()

        # Add costs up to limit
        for i in range(15):
            tracker.add_cost(f"agent_{i}", 1, 0.13)

        # 15 * 0.13 = 1.95 - not exceeded
        assert not tracker.is_budget_exceeded()

        # Add one more to exceed
        tracker.add_cost("agent_16", 1, 0.13)
        # 16 * 0.13 = 2.08 - exceeded
        assert tracker.is_budget_exceeded()

    def test_remaining_budget(self):
        """Test remaining budget calculation."""
        tracker = CostTracker()

        tracker.add_cost("agent", 1, 0.50)
        assert tracker.remaining_budget() == pytest.approx(1.50, rel=0.01)

        tracker.add_cost("agent", 2, 1.00)
        assert tracker.remaining_budget() == pytest.approx(0.50, rel=0.01)

        tracker.add_cost("agent", 3, 1.00)
        # When over budget, remaining is 0
        assert tracker.remaining_budget() == 0.0

    def test_to_dict_serialization(self):
        """Test CostTracker serialization."""
        tracker = CostTracker()
        tracker.add_cost("cost_analyst", 1, 0.5)

        data = tracker.to_dict()

        assert "total_cost" in data
        assert "cost_by_agent" in data
        assert "cost_by_round" in data
        assert "budget_exceeded" in data
        assert "remaining_budget" in data


class TestBudgetCircuitBreaker:
    """Test budget circuit breaker functionality."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test councils after each test."""
        yield
        councils_dir = Path(".aibrain/councils")
        if councils_dir.exists():
            for council_dir in councils_dir.glob("TEST-BUDGET-*"):
                shutil.rmtree(council_dir)

    @pytest.mark.asyncio
    async def test_budget_enforced_halts_debate(self):
        """Test that debate halts when budget is exceeded."""

        def create_expensive_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Expensive analysis requiring lots of tokens.",
                evidence=["Large dataset analysis"],
                confidence=0.9
            )

        council = CouncilOrchestrator(
            topic="Test budget enforcement",
            agent_types={
                "agent1": create_expensive_agent,
                "agent2": create_expensive_agent,
                "agent3": create_expensive_agent,
                "agent4": create_expensive_agent,
                "agent5": create_expensive_agent,
            },
            rounds=3,
            council_id="TEST-BUDGET-001",
            enforce_budget=True
        )

        # Manually set high costs to trigger circuit breaker
        council.cost_tracker.add_cost("test", 0, 2.50)

        # Should complete but with halted=True in result
        result = await council.run_debate()

        assert result.cost_summary is not None
        assert result.cost_summary["halted"] is True
        assert "budget" in result.cost_summary.get("halt_reason", "").lower()

    @pytest.mark.asyncio
    async def test_budget_not_enforced_allows_high_cost(self):
        """Test that debate continues when budget enforcement is disabled."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test",
                evidence=["Test"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test budget enforcement disabled",
            agent_types={"agent1": create_agent},
            rounds=1,
            council_id="TEST-BUDGET-002",
            enforce_budget=False  # Disabled
        )

        # Manually set high costs
        council.cost_tracker.add_cost("test", 0, 5.00)

        # Should complete normally even though over budget
        result = await council.run_debate()

        assert result.cost_summary is not None
        assert result.cost_summary["halted"] is False
        assert result.cost_summary["budget_exceeded"] is True

    @pytest.mark.asyncio
    async def test_cost_tracking_during_debate(self):
        """Test that costs are tracked during debate execution."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Cost tracking test.",
                evidence=["Evidence"],
                confidence=0.7
            )

        council = CouncilOrchestrator(
            topic="Test cost tracking",
            agent_types={
                "cost": create_agent,
                "integration": create_agent
            },
            rounds=3,
            council_id="TEST-BUDGET-003",
            enforce_budget=True
        )

        result = await council.run_debate()

        # Verify cost tracking
        assert result.cost_summary is not None
        assert result.cost_summary["total_cost"] > 0
        assert len(result.cost_summary["cost_by_agent"]) == 2
        assert len(result.cost_summary["cost_by_round"]) == 3

        # Each agent should have costs for 3 rounds
        for agent_cost in result.cost_summary["cost_by_agent"].values():
            assert agent_cost > 0


class TestTimeoutCircuitBreaker:
    """Test timeout circuit breaker functionality."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test councils after each test."""
        yield
        councils_dir = Path(".aibrain/councils")
        if councils_dir.exists():
            for council_dir in councils_dir.glob("TEST-TIMEOUT-*"):
                shutil.rmtree(council_dir)

    @pytest.mark.asyncio
    async def test_timeout_halts_debate(self):
        """Test that debate halts when timeout is exceeded."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test",
                evidence=["Test"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test timeout enforcement",
            agent_types={"agent1": create_agent},
            rounds=3,
            max_duration_minutes=1,  # 1 minute timeout
            council_id="TEST-TIMEOUT-001",
            enforce_budget=True
        )

        # Mock _get_elapsed_seconds to return a value > max_duration
        original_get_elapsed = council._get_elapsed_seconds

        def mock_elapsed():
            # Return 5 minutes (300 seconds), which exceeds 1 minute limit
            return 300.0

        council._get_elapsed_seconds = mock_elapsed

        # Should halt due to timeout
        result = await council.run_debate()

        assert result.cost_summary is not None
        assert result.cost_summary["halted"] is True
        assert "limit" in result.cost_summary.get("halt_reason", "").lower() or \
               "minute" in result.cost_summary.get("halt_reason", "").lower()

    @pytest.mark.asyncio
    async def test_normal_debate_does_not_timeout(self):
        """Test that normal debate completes without timeout."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test",
                evidence=["Test"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test no timeout",
            agent_types={"agent1": create_agent},
            rounds=1,
            max_duration_minutes=30,  # 30 minute timeout (plenty of time)
            council_id="TEST-TIMEOUT-002",
            enforce_budget=True
        )

        result = await council.run_debate()

        assert result.cost_summary is not None
        assert result.cost_summary["halted"] is False


class TestCostSummaryInResult:
    """Test that cost summary is properly included in DebateResult."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test councils after each test."""
        yield
        councils_dir = Path(".aibrain/councils")
        if councils_dir.exists():
            for council_dir in councils_dir.glob("TEST-COST-*"):
                shutil.rmtree(council_dir)

    @pytest.mark.asyncio
    async def test_cost_summary_in_result(self):
        """Test that DebateResult includes cost summary."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test",
                evidence=["Test"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test cost summary",
            agent_types={"cost": create_agent},
            rounds=2,
            council_id="TEST-COST-001"
        )

        result = await council.run_debate()

        # Verify cost summary structure
        assert result.cost_summary is not None
        assert "total_cost" in result.cost_summary
        assert "cost_by_agent" in result.cost_summary
        assert "cost_by_round" in result.cost_summary
        assert "budget_exceeded" in result.cost_summary
        assert "remaining_budget" in result.cost_summary
        assert "halted" in result.cost_summary

    @pytest.mark.asyncio
    async def test_cost_summary_in_stats(self):
        """Test that get_stats() includes cost tracker data."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test",
                evidence=["Test"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test stats with cost",
            agent_types={"cost": create_agent},
            rounds=1,
            council_id="TEST-COST-002"
        )

        await council.run_debate()
        stats = council.get_stats()

        assert "cost_tracker" in stats
        assert stats["cost_tracker"]["total_cost"] > 0

    @pytest.mark.asyncio
    async def test_cost_summary_serializable(self):
        """Test that cost summary is JSON-serializable via to_dict()."""
        import json

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test",
                evidence=["Test"],
                confidence=0.8
            )

        council = CouncilOrchestrator(
            topic="Test serialization",
            agent_types={"cost": create_agent},
            rounds=1,
            council_id="TEST-COST-003"
        )

        result = await council.run_debate()

        # Should serialize without error
        result_dict = result.to_dict()
        json_str = json.dumps(result_dict)
        assert json_str  # Not empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
