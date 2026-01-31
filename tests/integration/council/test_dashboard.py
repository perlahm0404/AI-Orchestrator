"""
Tests for council dashboard functionality.

Tests the comprehensive metrics dashboard for tracking
debate quality, trends, and effectiveness over time.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from pathlib import Path

from orchestration.council_dashboard import (
    get_dashboard_data,
    get_debate_quality_metrics,
    get_trend_analysis,
    DebateQualityMetrics,
    TrendPoint
)


class TestDashboardData:
    """Test dashboard data generation."""

    def test_empty_dashboard_when_no_debates(self, tmp_path: Path):
        """Dashboard returns empty structure with no debates."""
        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            data = get_dashboard_data(days=30)

            assert data["summary"]["total_debates"] == 0
            assert data["trends"] == []
            assert data["quality"] == []
            assert data["cost_analysis"]["total"] == 0.0
            assert data["recommendations"] == {}
            assert data["period_days"] == 30

    def test_dashboard_summary_fields(self, tmp_path: Path):
        """Dashboard summary has all required fields."""
        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            data = get_dashboard_data()

            summary = data["summary"]
            assert "total_debates" in summary
            assert "total_cost" in summary
            assert "avg_cost_per_debate" in summary
            assert "avg_confidence" in summary
            assert "most_common_recommendation" in summary
            assert "success_rate" in summary
            assert "outcomes_recorded" in summary

    def test_dashboard_cost_analysis_fields(self, tmp_path: Path):
        """Dashboard cost analysis has all required fields."""
        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            data = get_dashboard_data()

            cost = data["cost_analysis"]
            assert "total" in cost
            assert "average" in cost
            assert "min" in cost
            assert "max" in cost
            assert "budget_utilization" in cost


class TestDebateQualityMetrics:
    """Test quality metrics calculation."""

    def test_quality_metrics_returns_none_for_missing_council(self, tmp_path: Path):
        """Returns None when council doesn't exist."""
        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            result = get_debate_quality_metrics("COUNCIL-NONEXISTENT")
            assert result is None

    def test_quality_metrics_returns_none_for_empty_manifest(self, tmp_path: Path):
        """Returns None when manifest is empty."""
        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            council_dir = tmp_path / "COUNCIL-TEST"
            council_dir.mkdir()
            manifest = council_dir / "manifest.jsonl"
            manifest.write_text("")

            result = get_debate_quality_metrics("COUNCIL-TEST")
            assert result is None

    def test_quality_metrics_dataclass_fields(self):
        """Quality metrics dataclass has expected fields."""
        metrics = DebateQualityMetrics(
            council_id="TEST",
            total_arguments=10,
            arguments_per_agent=2.0,
            avg_confidence=0.75,
            confidence_spread=0.1,
            rebuttal_depth=3,
            consensus_strength=0.8,
            evidence_count=5,
            unique_perspectives=5,
            duration_seconds=120.0,
            cost_efficiency=75.0
        )

        assert metrics.council_id == "TEST"
        assert metrics.total_arguments == 10
        assert metrics.arguments_per_agent == 2.0
        assert metrics.avg_confidence == 0.75
        assert metrics.consensus_strength == 0.8
        assert metrics.cost_efficiency == 75.0


class TestTrendAnalysis:
    """Test trend analysis over time."""

    def test_empty_trends_when_no_data(self, tmp_path: Path):
        """Returns empty list when no debates exist."""
        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            trends = get_trend_analysis(period="week", lookback=4)
            assert trends == []

    def test_trend_point_structure(self):
        """TrendPoint has expected structure."""
        point = TrendPoint(
            period="2026-W05",
            debates=3,
            avg_confidence=0.75,
            avg_cost=0.50,
            success_rate=80.0,
            dominant_recommendation="ADOPT"
        )

        assert point.period == "2026-W05"
        assert point.debates == 3
        assert point.avg_confidence == 0.75
        assert point.avg_cost == 0.50
        assert point.dominant_recommendation == "ADOPT"

    @pytest.mark.parametrize("period", ["day", "week", "month"])
    def test_trend_analysis_supports_all_periods(self, tmp_path: Path, period: str):
        """Trend analysis works for all period types."""
        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            # Should not raise
            trends = get_trend_analysis(period=period, lookback=4)
            assert isinstance(trends, list)


class TestDashboardWithMockedData:
    """Test dashboard with mocked debate data."""

    def test_dashboard_with_mock_debates(self, tmp_path: Path):
        """Dashboard computes metrics from mocked debates."""
        # Create a mock council directory with manifest
        council_dir = tmp_path / "COUNCIL-20260130-000001"
        council_dir.mkdir()
        manifest = council_dir / "manifest.jsonl"

        import json
        now = datetime.now(timezone.utc).isoformat()

        events = [
            {
                "event_type": "council_init",
                "timestamp": now,
                "topic": "Should we adopt X?",
                "perspectives": ["cost", "integration"]
            },
            {
                "event_type": "argument_posted",
                "timestamp": now,
                "data": {
                    "agent_id": "cost-analyst",
                    "perspective": "cost",
                    "position": "SUPPORT",
                    "confidence": 0.75,
                    "evidence": ["cost study"]
                }
            },
            {
                "event_type": "synthesis",
                "timestamp": now,
                "data": {
                    "recommendation": "ADOPT",
                    "confidence": 0.80,
                    "vote_breakdown": {"SUPPORT": 2, "OPPOSE": 0}
                }
            },
            {
                "event_type": "cost_summary",
                "timestamp": now,
                "data": {
                    "total_cost": 0.50
                }
            }
        ]

        manifest.write_text("\n".join(json.dumps(e) for e in events))

        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            # Patch the import location for get_effectiveness_report
            with patch("orchestration.council_effectiveness.get_effectiveness_report") as mock_eff:
                mock_eff.return_value = {"success_rate": 75.0, "total_decisions": 5}

                data = get_dashboard_data(days=30)

                assert data["summary"]["total_debates"] == 1
                assert data["summary"]["total_cost"] == 0.50
                assert data["summary"]["avg_confidence"] == 0.80
                assert "ADOPT" in data["recommendations"]

    def test_quality_metrics_computed_correctly(self, tmp_path: Path):
        """Quality metrics are computed from manifest data."""
        council_dir = tmp_path / "COUNCIL-QUALITY-TEST"
        council_dir.mkdir()
        manifest = council_dir / "manifest.jsonl"

        import json
        now = datetime.now(timezone.utc).isoformat()

        events = [
            {
                "event_type": "council_init",
                "timestamp": now,
                "topic": "Test topic"
            },
            {
                "event_type": "round_start",
                "timestamp": now,
                "data": {"round_number": 1}
            },
            {
                "event_type": "argument_posted",
                "timestamp": now,
                "data": {
                    "agent_id": "agent-1",
                    "perspective": "cost",
                    "confidence": 0.80,
                    "evidence": ["ev1", "ev2"]
                }
            },
            {
                "event_type": "argument_posted",
                "timestamp": now,
                "data": {
                    "agent_id": "agent-2",
                    "perspective": "integration",
                    "confidence": 0.60,
                    "evidence": ["ev3"]
                }
            },
            {
                "event_type": "synthesis",
                "timestamp": now,
                "data": {
                    "recommendation": "ADOPT",
                    "confidence": 0.70,
                    "vote_breakdown": {"SUPPORT": 2, "OPPOSE": 0}
                }
            },
            {
                "event_type": "cost_summary",
                "timestamp": now,
                "data": {"total_cost": 0.25}
            }
        ]

        manifest.write_text("\n".join(json.dumps(e) for e in events))

        with patch("orchestration.council_dashboard.COUNCILS_DIR", tmp_path):
            metrics = get_debate_quality_metrics("COUNCIL-QUALITY-TEST")

            assert metrics is not None
            assert metrics.total_arguments == 2
            assert metrics.unique_perspectives == 2
            assert metrics.evidence_count == 3
            assert metrics.avg_confidence == 0.70  # Average of 0.80 and 0.60
            assert metrics.consensus_strength == 1.0  # 2/2 = 100% consensus
            assert metrics.cost_efficiency == 0.70 / 0.25  # confidence / cost
