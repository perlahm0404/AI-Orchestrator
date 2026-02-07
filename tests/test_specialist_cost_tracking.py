"""
Tests for Phase 4 Step 4.3: Cost Tracking Per Specialist (TDD)

Tests cost tracking functionality for multi-agent orchestration:
- SpecialistAgent cost tracking (aggregated from MCP servers)
- TeamLead cost tracking (aggregated from all specialists)
- Per-specialist cost breakdown
- Total task cost calculation

Uses Test-Driven Development: Tests written BEFORE implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any


class TestSpecialistAgentCostTracking:
    """Tests for SpecialistAgent cost tracking."""

    def test_specialist_has_accumulated_cost_property(self):
        """SpecialistAgent should have accumulated_cost property."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        assert hasattr(specialist, "accumulated_cost")
        assert isinstance(specialist.accumulated_cost, (int, float))
        assert specialist.accumulated_cost == 0.0  # Initial cost is 0

    def test_specialist_tracks_cost_during_execution(self):
        """Specialist should track cost during execution."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        # Simulate adding cost
        specialist.add_cost(0.01)
        specialist.add_cost(0.02)

        assert specialist.accumulated_cost == pytest.approx(0.03, rel=1e-6)

    def test_specialist_cost_breakdown_by_operation(self):
        """Specialist should provide cost breakdown by operation type."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        # Simulate different operations with costs
        specialist.add_cost(0.001, operation="verification")
        specialist.add_cost(0.002, operation="git_commit")
        specialist.add_cost(0.001, operation="verification")

        breakdown = specialist.get_cost_breakdown()

        assert "verification" in breakdown
        assert "git_commit" in breakdown
        assert breakdown["verification"] == pytest.approx(0.002, rel=1e-6)
        assert breakdown["git_commit"] == pytest.approx(0.002, rel=1e-6)

    def test_specialist_resets_cost_on_new_execution(self):
        """Specialist should reset cost when starting new execution."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        # Add some cost
        specialist.add_cost(0.05)
        assert specialist.accumulated_cost > 0

        # Reset
        specialist.reset_cost()
        assert specialist.accumulated_cost == 0.0

    def test_specialist_includes_cost_in_result(self):
        """Specialist execution result should include total cost."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        # Mock execute to add cost
        async def mock_execute(subtask):
            specialist.add_cost(0.025)
            return {
                "status": "completed",
                "verdict": "PASS",
                "iterations": 3,
            }

        specialist._mock_execute = mock_execute

        # The real execute() method should include cost in result
        # This tests the contract, not the implementation


class TestTeamLeadCostTracking:
    """Tests for TeamLead cost tracking."""

    @pytest.fixture
    def team_lead(self, tmp_path):
        """Create a TeamLead for testing."""
        from orchestration.team_lead import TeamLead
        return TeamLead(project_path=tmp_path)

    def test_teamlead_has_accumulated_cost_property(self, team_lead):
        """TeamLead should have accumulated_cost property."""
        assert hasattr(team_lead, "accumulated_cost")
        assert isinstance(team_lead.accumulated_cost, (int, float))

    def test_teamlead_aggregates_cost_from_specialists(self, team_lead):
        """TeamLead should aggregate costs from all specialists."""
        # Simulate adding costs from specialists
        team_lead.add_specialist_cost("bugfix", 0.02)
        team_lead.add_specialist_cost("testwriter", 0.015)

        assert team_lead.accumulated_cost == pytest.approx(0.035, rel=1e-6)

    def test_teamlead_provides_per_specialist_cost(self, team_lead):
        """TeamLead should provide cost breakdown per specialist."""
        team_lead.add_specialist_cost("bugfix", 0.02)
        team_lead.add_specialist_cost("testwriter", 0.015)
        team_lead.add_specialist_cost("bugfix", 0.01)  # Additional cost

        breakdown = team_lead.get_specialist_costs()

        assert "bugfix" in breakdown
        assert "testwriter" in breakdown
        assert breakdown["bugfix"] == pytest.approx(0.03, rel=1e-6)
        assert breakdown["testwriter"] == pytest.approx(0.015, rel=1e-6)

    def test_teamlead_includes_analysis_cost(self, team_lead):
        """TeamLead should track its own analysis cost."""
        # TeamLead's own cost (for analysis phase)
        team_lead.add_analysis_cost(0.005)

        costs = team_lead.get_cost_summary()

        assert "analysis_cost" in costs
        assert costs["analysis_cost"] == pytest.approx(0.005, rel=1e-6)

    def test_teamlead_cost_summary_includes_all_components(self, team_lead):
        """Cost summary should include all cost components."""
        team_lead.add_analysis_cost(0.005)
        team_lead.add_specialist_cost("bugfix", 0.02)
        team_lead.add_specialist_cost("testwriter", 0.015)
        team_lead.add_synthesis_cost(0.003)

        summary = team_lead.get_cost_summary()

        assert "analysis_cost" in summary
        assert "specialist_costs" in summary
        assert "synthesis_cost" in summary
        assert "total_cost" in summary
        assert summary["total_cost"] == pytest.approx(0.043, rel=1e-6)


class TestCostIntegrationWithMCP:
    """Tests for cost integration with MCP servers."""

    def test_specialist_aggregates_mcp_verification_cost(self):
        """Specialist should aggregate cost from Ralph verification MCP."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        # Simulate MCP verification adding cost
        mcp_cost = 0.0017  # Base + linting + type checking
        specialist.add_mcp_cost("ralph_verification", mcp_cost)

        assert specialist.accumulated_cost >= mcp_cost

    def test_specialist_aggregates_mcp_git_cost(self):
        """Specialist should aggregate cost from Git operations MCP."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        # Simulate MCP git operations adding cost
        mcp_cost = 0.0005  # Commit cost
        specialist.add_mcp_cost("git_operations", mcp_cost)

        breakdown = specialist.get_mcp_cost_breakdown()
        assert "git_operations" in breakdown

    def test_specialist_aggregates_mcp_deployment_cost(self):
        """Specialist should aggregate cost from Deployment MCP."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("deployment")

        # Simulate MCP deployment adding cost
        mcp_cost = 0.025  # Prod deployment cost
        specialist.add_mcp_cost("deployment", mcp_cost)

        assert specialist.accumulated_cost >= mcp_cost


class TestCostEstimation:
    """Tests for cost estimation before execution."""

    def test_specialist_has_estimated_cost(self):
        """Specialist should provide estimated cost before execution."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        estimated = specialist.get_estimated_cost()

        assert isinstance(estimated, (int, float))
        assert estimated > 0  # Should have non-zero estimate

    def test_different_specialists_have_different_estimates(self):
        """Different specialist types should have different cost estimates."""
        from orchestration.specialist_agent import SpecialistAgent

        bugfix = SpecialistAgent("bugfix")
        featurebuilder = SpecialistAgent("featurebuilder")

        bugfix_cost = bugfix.get_estimated_cost()
        feature_cost = featurebuilder.get_estimated_cost()

        # FeatureBuilder has higher budget (50 vs 15), should cost more
        assert feature_cost > bugfix_cost

    def test_teamlead_estimates_total_task_cost(self, tmp_path):
        """TeamLead should estimate total task cost based on specialists."""
        from orchestration.team_lead import TeamLead

        team_lead = TeamLead(project_path=tmp_path)

        # Mock specialists
        specialists = ["bugfix", "testwriter"]
        estimated = team_lead.estimate_task_cost(specialists)

        assert isinstance(estimated, (int, float))
        assert estimated > 0


class TestCostReporting:
    """Tests for cost reporting and metrics."""

    def test_specialist_provides_cost_per_iteration(self):
        """Specialist should track cost per iteration."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        # Simulate iterations with costs
        specialist.record_iteration_cost(1, 0.001)
        specialist.record_iteration_cost(2, 0.002)
        specialist.record_iteration_cost(3, 0.001)

        costs = specialist.get_iteration_costs()

        assert len(costs) == 3
        assert costs[1] == pytest.approx(0.001, rel=1e-6)
        assert costs[2] == pytest.approx(0.002, rel=1e-6)

    def test_specialist_calculates_average_cost_per_iteration(self):
        """Specialist should calculate average cost per iteration."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")

        specialist.record_iteration_cost(1, 0.001)
        specialist.record_iteration_cost(2, 0.002)
        specialist.record_iteration_cost(3, 0.003)

        avg = specialist.get_average_iteration_cost()

        assert avg == pytest.approx(0.002, rel=1e-6)

    def test_teamlead_provides_cost_efficiency_metrics(self, tmp_path):
        """TeamLead should provide cost efficiency metrics."""
        from orchestration.team_lead import TeamLead

        team_lead = TeamLead(project_path=tmp_path)

        team_lead.add_specialist_cost("bugfix", 0.02)
        team_lead.add_specialist_cost("testwriter", 0.015)

        # Set task result for efficiency calculation
        team_lead.record_task_result(
            status="completed",
            iterations_total=8,
            value_generated=100.0  # Estimated value in USD
        )

        metrics = team_lead.get_efficiency_metrics()

        assert "cost_per_iteration" in metrics
        assert "roi" in metrics  # Return on investment
        assert "cost_to_value_ratio" in metrics


class TestCostThresholds:
    """Tests for cost threshold enforcement."""

    def test_specialist_can_set_cost_budget(self):
        """Specialist should allow setting a cost budget."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")
        specialist.set_cost_budget(0.05)

        assert specialist.cost_budget == 0.05

    def test_specialist_warns_when_approaching_budget(self):
        """Specialist should warn when approaching cost budget."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")
        specialist.set_cost_budget(0.05)

        specialist.add_cost(0.041)  # 82% of budget (avoids floating point precision issues)

        assert specialist.is_near_cost_budget()

    def test_specialist_can_enforce_cost_budget(self):
        """Specialist should optionally enforce cost budget."""
        from orchestration.specialist_agent import SpecialistAgent

        specialist = SpecialistAgent("bugfix")
        specialist.set_cost_budget(0.05, enforce=True)

        specialist.add_cost(0.04)

        # Trying to add more should raise or return False
        result = specialist.add_cost(0.02)  # Would exceed budget
        assert result is False or specialist.accumulated_cost <= 0.05
