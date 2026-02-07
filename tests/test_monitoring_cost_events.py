"""
Tests for Phase 4 Step 4.4: Operational Monitoring - Cost Events (TDD)

Tests the cost tracking events in MonitoringIntegration:
- cost_update event for real-time cost tracking
- cost_summary event at task completion
- cost_warning event when approaching budget
- efficiency_metrics event for ROI reporting

Uses Test-Driven Development: Tests written BEFORE implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any


class TestCostUpdateEvent:
    """Tests for cost_update event streaming."""

    @pytest.mark.asyncio
    async def test_cost_update_streams_event_when_enabled(self):
        """cost_update should stream event when monitoring enabled."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.cost_update(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            cost_usd=0.002,
            accumulated_cost=0.015,
            operation="verification"
        )

        monitoring._stream_event.assert_called_once()
        call_args = monitoring._stream_event.call_args
        assert call_args[0][0] == "cost_update"
        assert call_args[0][1]["task_id"] == "TASK-001"
        assert call_args[0][1]["cost_usd"] == 0.002
        assert call_args[0][1]["accumulated_cost"] == 0.015
        assert call_args[0][1]["operation"] == "verification"

    @pytest.mark.asyncio
    async def test_cost_update_does_nothing_when_disabled(self):
        """cost_update should not stream when monitoring disabled."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=False)
        monitoring._stream_event = AsyncMock()

        await monitoring.cost_update(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            cost_usd=0.002,
            accumulated_cost=0.015
        )

        monitoring._stream_event.assert_not_called()


class TestCostSummaryEvent:
    """Tests for cost_summary event streaming."""

    @pytest.mark.asyncio
    async def test_cost_summary_streams_event_when_enabled(self):
        """cost_summary should stream complete cost breakdown."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        specialist_costs = {
            "bugfix": 0.015,
            "testwriter": 0.012
        }

        await monitoring.cost_summary(
            task_id="TASK-001",
            project="test_project",
            analysis_cost=0.005,
            specialist_costs=specialist_costs,
            synthesis_cost=0.003,
            total_cost=0.035
        )

        monitoring._stream_event.assert_called_once()
        call_args = monitoring._stream_event.call_args
        assert call_args[0][0] == "cost_summary"
        assert call_args[0][1]["analysis_cost"] == 0.005
        assert call_args[0][1]["specialist_costs"] == specialist_costs
        assert call_args[0][1]["synthesis_cost"] == 0.003
        assert call_args[0][1]["total_cost"] == 0.035

    @pytest.mark.asyncio
    async def test_cost_summary_includes_all_specialists(self):
        """cost_summary should include costs for all specialists."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        specialist_costs = {
            "bugfix": 0.015,
            "testwriter": 0.012,
            "featurebuilder": 0.045,
            "codequality": 0.018
        }

        await monitoring.cost_summary(
            task_id="TASK-001",
            project="test_project",
            analysis_cost=0.005,
            specialist_costs=specialist_costs,
            synthesis_cost=0.003,
            total_cost=0.098
        )

        call_args = monitoring._stream_event.call_args
        streamed_costs = call_args[0][1]["specialist_costs"]
        assert len(streamed_costs) == 4
        assert "bugfix" in streamed_costs
        assert "featurebuilder" in streamed_costs


class TestCostWarningEvent:
    """Tests for cost_warning event streaming."""

    @pytest.mark.asyncio
    async def test_cost_warning_streams_warning_at_80_percent(self):
        """cost_warning should stream with warning severity at 80%."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.cost_warning(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            current_cost=0.04,
            budget=0.05,
            percentage=0.8
        )

        monitoring._stream_event.assert_called_once()
        call_args = monitoring._stream_event.call_args
        assert call_args[0][0] == "cost_warning"
        assert call_args[1]["severity"] == "warning"

    @pytest.mark.asyncio
    async def test_cost_warning_streams_error_at_95_percent(self):
        """cost_warning should stream with error severity at 95%."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.cost_warning(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            current_cost=0.048,
            budget=0.05,
            percentage=0.96
        )

        call_args = monitoring._stream_event.call_args
        assert call_args[1]["severity"] == "error"

    @pytest.mark.asyncio
    async def test_cost_warning_streams_info_below_80_percent(self):
        """cost_warning should stream with info severity below 80%."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.cost_warning(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            current_cost=0.03,
            budget=0.05,
            percentage=0.6
        )

        call_args = monitoring._stream_event.call_args
        assert call_args[1]["severity"] == "info"


class TestEfficiencyMetricsEvent:
    """Tests for efficiency_metrics event streaming."""

    @pytest.mark.asyncio
    async def test_efficiency_metrics_streams_event_when_enabled(self):
        """efficiency_metrics should stream complete metrics."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.efficiency_metrics(
            task_id="TASK-001",
            project="test_project",
            cost_per_iteration=0.004375,
            roi=1.86,
            cost_to_value_ratio=0.35,
            value_generated=100.0,
            total_cost=35.0
        )

        monitoring._stream_event.assert_called_once()
        call_args = monitoring._stream_event.call_args
        assert call_args[0][0] == "efficiency_metrics"
        assert call_args[0][1]["roi"] == 1.86
        assert call_args[0][1]["cost_per_iteration"] == 0.004375

    @pytest.mark.asyncio
    async def test_efficiency_metrics_info_severity_for_positive_roi(self):
        """efficiency_metrics should have info severity for ROI >= 1."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.efficiency_metrics(
            task_id="TASK-001",
            project="test_project",
            cost_per_iteration=0.002,
            roi=2.0,  # Positive ROI
            cost_to_value_ratio=0.33,
            value_generated=100.0,
            total_cost=33.0
        )

        call_args = monitoring._stream_event.call_args
        assert call_args[1]["severity"] == "info"

    @pytest.mark.asyncio
    async def test_efficiency_metrics_warning_severity_for_low_roi(self):
        """efficiency_metrics should have warning severity for ROI < 1."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.efficiency_metrics(
            task_id="TASK-001",
            project="test_project",
            cost_per_iteration=0.01,
            roi=0.5,  # Low ROI - cost more than generated value
            cost_to_value_ratio=2.0,
            value_generated=50.0,
            total_cost=100.0
        )

        call_args = monitoring._stream_event.call_args
        assert call_args[1]["severity"] == "warning"

    @pytest.mark.asyncio
    async def test_efficiency_metrics_error_severity_for_negative_roi(self):
        """efficiency_metrics should have error severity for negative ROI."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        await monitoring.efficiency_metrics(
            task_id="TASK-001",
            project="test_project",
            cost_per_iteration=0.02,
            roi=-0.5,  # Negative ROI - lost money
            cost_to_value_ratio=3.0,
            value_generated=50.0,
            total_cost=150.0
        )

        call_args = monitoring._stream_event.call_args
        assert call_args[1]["severity"] == "error"


class TestMonitoringIntegrationWithCost:
    """Integration tests for monitoring with cost tracking."""

    @pytest.mark.asyncio
    async def test_full_cost_lifecycle(self):
        """Test complete cost tracking lifecycle through monitoring."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        # 1. Cost updates during execution
        await monitoring.cost_update(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            cost_usd=0.005,
            accumulated_cost=0.005,
            operation="analysis"
        )

        await monitoring.cost_update(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            cost_usd=0.002,
            accumulated_cost=0.007,
            operation="verification"
        )

        # 2. Cost summary at completion
        await monitoring.cost_summary(
            task_id="TASK-001",
            project="test_project",
            analysis_cost=0.005,
            specialist_costs={"bugfix": 0.007},
            synthesis_cost=0.003,
            total_cost=0.015
        )

        # 3. Efficiency metrics
        await monitoring.efficiency_metrics(
            task_id="TASK-001",
            project="test_project",
            cost_per_iteration=0.003,
            roi=6.67,
            cost_to_value_ratio=0.15,
            value_generated=100.0,
            total_cost=15.0
        )

        # Verify all events were streamed
        assert monitoring._stream_event.call_count == 4

        # Verify event types
        event_types = [call[0][0] for call in monitoring._stream_event.call_args_list]
        assert "cost_update" in event_types
        assert "cost_summary" in event_types
        assert "efficiency_metrics" in event_types

    @pytest.mark.asyncio
    async def test_cost_warning_triggers_at_threshold(self):
        """Test that cost warnings trigger appropriately."""
        from orchestration.monitoring_integration import MonitoringIntegration

        monitoring = MonitoringIntegration(enabled=True)
        monitoring._stream_event = AsyncMock()

        # Simulate approaching budget
        budget = 0.05
        current_cost = 0.041  # 82% of budget

        await monitoring.cost_warning(
            task_id="TASK-001",
            project="test_project",
            specialist_type="bugfix",
            current_cost=current_cost,
            budget=budget,
            percentage=current_cost / budget
        )

        call_args = monitoring._stream_event.call_args
        assert call_args[0][0] == "cost_warning"
        assert call_args[1]["severity"] == "warning"
