"""Tests for ResourceTracker (ADR-004: Resource Protection)."""

import json
import pytest
from datetime import datetime, timezone, timedelta

from governance.resource_tracker import (
    ResourceTracker,
    ResourceLimits,
    ResourceUsage,
    LimitCheck,
)


class TestResourceLimits:
    """Tests for ResourceLimits dataclass."""

    def test_default_values(self):
        """Default limits are set correctly."""
        limits = ResourceLimits()

        assert limits.max_iterations == 500
        assert limits.max_api_calls == 10_000
        assert limits.max_file_writes == 200
        assert limits.max_session_hours == 8
        assert limits.max_lambda_deploys_daily == 50
        assert limits.max_cost_daily_usd == 50.0
        assert limits.retry_escalation_threshold == 10
        assert limits.circuit_breaker_pct == 0.8

    def test_custom_values(self):
        """Custom limits can be set."""
        limits = ResourceLimits(
            max_iterations=100,
            max_api_calls=1000,
            retry_escalation_threshold=5,
        )

        assert limits.max_iterations == 100
        assert limits.max_api_calls == 1000
        assert limits.retry_escalation_threshold == 5
        # Other values should be defaults
        assert limits.max_file_writes == 200

    def test_to_dict(self):
        """Limits can be serialized to dictionary."""
        limits = ResourceLimits(max_iterations=100)
        data = limits.to_dict()

        assert data["max_iterations"] == 100
        assert "max_api_calls" in data
        assert "circuit_breaker_pct" in data


class TestResourceUsage:
    """Tests for ResourceUsage dataclass."""

    def test_default_values(self):
        """Default usage is zero."""
        usage = ResourceUsage()

        assert usage.iterations == 0
        assert usage.api_calls == 0
        assert usage.file_writes == 0
        assert usage.lambda_deploys == 0
        assert usage.estimated_cost_usd == 0.0

    def test_to_dict(self):
        """Usage can be serialized to dictionary."""
        usage = ResourceUsage(iterations=10, api_calls=100)
        data = usage.to_dict()

        assert data["iterations"] == 10
        assert data["api_calls"] == 100
        assert "session_start" in data

    def test_from_dict(self):
        """Usage can be deserialized from dictionary."""
        data = {
            "iterations": 20,
            "api_calls": 200,
            "file_writes": 5,
            "session_start": datetime.now(timezone.utc).isoformat(),
            "lambda_deploys": 3,
            "npm_installs": 1,
            "estimated_cost_usd": 1.5,
        }
        usage = ResourceUsage.from_dict(data)

        assert usage.iterations == 20
        assert usage.api_calls == 200
        assert usage.file_writes == 5
        assert usage.lambda_deploys == 3
        assert usage.estimated_cost_usd == 1.5


class TestLimitCheck:
    """Tests for LimitCheck dataclass."""

    def test_not_exceeded(self):
        """Check with no exceeded limits."""
        check = LimitCheck(exceeded=False)

        assert not check.exceeded
        assert not check.should_stop()
        assert not check.should_pause()

    def test_exceeded(self):
        """Check with exceeded limits."""
        check = LimitCheck(
            exceeded=True,
            reasons=["Session iterations: 500/500"],
        )

        assert check.exceeded
        assert check.should_stop()
        assert check.should_pause()

    def test_warnings_only(self):
        """Check with warnings but no exceeded limits."""
        check = LimitCheck(
            exceeded=False,
            warnings=["Approaching iteration limit: 400/500"],
        )

        assert not check.exceeded
        assert not check.should_stop()
        assert check.should_pause()  # Warnings trigger pause


class TestResourceTracker:
    """Tests for ResourceTracker class."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create a temporary state directory."""
        return tmp_path / ".aibrain" / "resources"

    def test_initialization(self, temp_state_dir):
        """Tracker initializes with correct defaults."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        assert tracker.project == "test"
        assert tracker.usage.iterations == 0
        assert tracker.limits.max_iterations == 500

    def test_custom_limits(self, temp_state_dir):
        """Tracker accepts custom limits."""
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(max_iterations=100),
            state_dir=temp_state_dir,
        )

        assert tracker.limits.max_iterations == 100

    def test_record_iteration(self, temp_state_dir):
        """Recording iterations updates counter."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        check = tracker.record_iteration()

        assert tracker.usage.iterations == 1
        assert not check.exceeded

    def test_record_api_call(self, temp_state_dir):
        """Recording API calls updates counter."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        tracker.record_api_call(count=5)

        assert tracker.usage.api_calls == 5
        assert tracker.daily_usage.get("api_calls") == 5

    def test_record_lambda_deploy(self, temp_state_dir):
        """Recording Lambda deploys updates counter."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        tracker.record_lambda_deploy()

        assert tracker.usage.lambda_deploys == 1
        assert tracker.daily_usage.get("lambda_deploys") == 1
        assert tracker.usage.last_lambda_deploy is not None

    def test_record_cost(self, temp_state_dir):
        """Recording cost updates estimate."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        tracker.record_cost(0.50)

        assert tracker.usage.estimated_cost_usd == 0.50
        assert tracker.daily_usage.get("cost_usd") == 0.50


class TestResourceLimitChecking:
    """Tests for limit checking."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        return tmp_path / ".aibrain" / "resources"

    def test_iteration_limit_exceeded(self, temp_state_dir):
        """Detects when iteration limit is exceeded."""
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(max_iterations=10),
            state_dir=temp_state_dir,
        )

        # Run 10 iterations
        for _ in range(10):
            check = tracker.record_iteration()

        assert check.exceeded
        assert "Session iterations: 10/10" in check.reasons[0]

    def test_iteration_limit_warning(self, temp_state_dir):
        """Detects approaching iteration limit (circuit breaker)."""
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(max_iterations=10, circuit_breaker_pct=0.8),
            state_dir=temp_state_dir,
        )

        # Run 8 iterations (80% of limit)
        for _ in range(8):
            check = tracker.record_iteration()

        assert not check.exceeded
        assert len(check.warnings) > 0
        assert "Approaching iteration limit" in check.warnings[0]

    def test_daily_deploy_limit_exceeded(self, temp_state_dir):
        """Detects when daily deploy limit is exceeded."""
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(max_lambda_deploys_daily=5),
            state_dir=temp_state_dir,
        )

        # Do 5 deploys
        for _ in range(5):
            check = tracker.record_lambda_deploy()

        assert check.exceeded
        assert "Daily Lambda deploys: 5/5" in check.reasons[0]

    def test_daily_cost_limit_exceeded(self, temp_state_dir):
        """Detects when daily cost limit is exceeded."""
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(max_cost_daily_usd=10.0),
            state_dir=temp_state_dir,
        )

        tracker.record_cost(10.00)
        check = tracker.check_limits()

        assert check.exceeded
        assert "Daily cost" in check.reasons[0]


class TestRetryEscalation:
    """Tests for retry escalation (ADR-004)."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        return tmp_path / ".aibrain" / "resources"

    def test_escalation_threshold_not_reached(self, temp_state_dir):
        """No escalation when under threshold."""
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(retry_escalation_threshold=10),
            state_dir=temp_state_dir,
        )

        assert not tracker.check_retry_escalation(5)
        assert not tracker.check_retry_escalation(9)

    def test_escalation_threshold_reached(self, temp_state_dir):
        """Escalation triggered at threshold."""
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(retry_escalation_threshold=10),
            state_dir=temp_state_dir,
        )

        assert tracker.check_retry_escalation(10)
        assert tracker.check_retry_escalation(15)


class TestStatePersistence:
    """Tests for state persistence."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        return tmp_path / ".aibrain" / "resources"

    def test_state_persisted_to_file(self, temp_state_dir):
        """State is saved to file."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        tracker.record_iteration()
        tracker.record_api_call(10)

        # Check file exists
        state_file = temp_state_dir / "test-resources.json"
        assert state_file.exists()

        # Check content
        data = json.loads(state_file.read_text())
        assert data["iterations"] == 1
        assert data["api_calls"] == 10

    def test_state_loaded_from_file(self, temp_state_dir):
        """State is loaded from existing file."""
        # Create initial state
        tracker1 = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )
        tracker1.record_iteration()
        tracker1.record_iteration()

        # Create new tracker - should load state
        tracker2 = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        assert tracker2.usage.iterations == 2

    def test_expired_session_resets(self, temp_state_dir):
        """Expired session state is reset."""
        # Create state file with old timestamp
        temp_state_dir.mkdir(parents=True, exist_ok=True)
        state_file = temp_state_dir / "test-resources.json"

        old_time = datetime.now(timezone.utc) - timedelta(hours=10)
        state_data = {
            "iterations": 100,
            "api_calls": 1000,
            "file_writes": 50,
            "session_start": old_time.isoformat(),
            "lambda_deploys": 10,
            "npm_installs": 5,
            "estimated_cost_usd": 5.0,
        }
        state_file.write_text(json.dumps(state_data))

        # Create tracker with 8 hour limit - session should reset
        tracker = ResourceTracker(
            project="test",
            limits=ResourceLimits(max_session_hours=8),
            state_dir=temp_state_dir,
        )

        # State should be reset (session expired)
        assert tracker.usage.iterations == 0

    def test_reset_session(self, temp_state_dir):
        """Session can be manually reset."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        tracker.record_iteration()
        tracker.record_iteration()
        assert tracker.usage.iterations == 2

        tracker.reset_session()
        assert tracker.usage.iterations == 0


class TestSummaryAndReporting:
    """Tests for summary and reporting."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        return tmp_path / ".aibrain" / "resources"

    def test_get_summary(self, temp_state_dir):
        """Summary contains all expected fields."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        tracker.record_iteration()
        tracker.record_api_call(10)
        tracker.record_cost(0.50)

        summary = tracker.get_summary()

        assert summary["project"] == "test"
        assert summary["session"]["iterations"] == 1
        assert summary["session"]["api_calls"] == 10
        assert summary["session"]["cost_usd"] == 0.50
        assert "limits" in summary
        assert "status" in summary

    def test_get_usage_report(self, temp_state_dir):
        """Usage report is generated correctly."""
        tracker = ResourceTracker(
            project="test",
            state_dir=temp_state_dir,
        )

        tracker.record_iteration()
        report = tracker.get_usage_report()

        assert "# Resource Usage Report - test" in report
        assert "Session Stats" in report
        assert "Daily Stats" in report
        assert "Cost Estimate" in report
