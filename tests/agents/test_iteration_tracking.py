"""
Unit tests for iteration tracking.

Tests the record_iteration() and get_iteration_summary() methods in BaseAgent.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent, AgentConfig


class MockAgent(BaseAgent):
    """Mock agent for testing BaseAgent methods."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.current_iteration = 0
        self.iteration_history = []

    def execute(self, task_id: str) -> dict:
        return {"task_id": task_id, "status": "completed"}

    def checkpoint(self) -> dict:
        return {}

    def halt(self, reason: str) -> None:
        pass


class MockVerdict:
    """Mock Ralph verdict for testing."""

    def __init__(self, verdict_type: str, safe_to_merge: bool = True, regression_detected: bool = False):
        self.type = Mock()
        self.type.value = verdict_type
        self.safe_to_merge = safe_to_merge
        self.regression_detected = regression_detected


class TestIterationTracking:
    """Test iteration tracking functionality."""

    def setup_method(self):
        """Setup mock agent for each test."""
        self.config = AgentConfig(
            project_name="test",
            agent_name="test",
            max_iterations=10
        )
        self.agent = MockAgent(self.config)

    def test_record_single_iteration(self):
        """Test recording a single iteration."""
        self.agent.current_iteration = 1
        verdict = MockVerdict("PASS")
        changes = ["file1.py", "file2.py"]

        self.agent.record_iteration(verdict, changes)

        assert len(self.agent.iteration_history) == 1
        record = self.agent.iteration_history[0]

        assert record["iteration"] == 1
        assert record["verdict"] == "PASS"
        assert record["safe_to_merge"] is True
        assert record["changes"] == changes
        assert record["regression"] is False
        assert "timestamp" in record

    def test_record_multiple_iterations(self):
        """Test recording multiple iterations."""
        for i in range(1, 4):
            self.agent.current_iteration = i
            verdict = MockVerdict("FAIL" if i < 3 else "PASS")
            self.agent.record_iteration(verdict, [f"file{i}.py"])

        assert len(self.agent.iteration_history) == 3
        assert self.agent.iteration_history[0]["verdict"] == "FAIL"
        assert self.agent.iteration_history[1]["verdict"] == "FAIL"
        assert self.agent.iteration_history[2]["verdict"] == "PASS"

    def test_record_iteration_with_regression(self):
        """Test recording iteration with regression detected."""
        self.agent.current_iteration = 1
        verdict = MockVerdict("FAIL", safe_to_merge=False, regression_detected=True)

        self.agent.record_iteration(verdict, ["file.py"])

        record = self.agent.iteration_history[0]
        assert record["verdict"] == "FAIL"
        assert record["safe_to_merge"] is False
        assert record["regression"] is True

    def test_record_iteration_with_none_verdict(self):
        """Test recording iteration with None verdict."""
        self.agent.current_iteration = 1

        self.agent.record_iteration(None, ["file.py"])

        record = self.agent.iteration_history[0]
        assert record["verdict"] == "UNKNOWN"
        assert record["safe_to_merge"] is False
        assert record["regression"] is False

    def test_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        self.agent.current_iteration = 1
        verdict = MockVerdict("PASS")

        self.agent.record_iteration(verdict, [])

        timestamp = self.agent.iteration_history[0]["timestamp"]
        # Should parse without error
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

    def test_empty_changes_list(self):
        """Test recording iteration with no changes."""
        self.agent.current_iteration = 1
        verdict = MockVerdict("PASS")

        self.agent.record_iteration(verdict, [])

        record = self.agent.iteration_history[0]
        assert record["changes"] == []


class TestIterationSummary:
    """Test iteration summary functionality."""

    def setup_method(self):
        """Setup mock agent for each test."""
        self.config = AgentConfig(
            project_name="test",
            agent_name="test",
            max_iterations=10
        )
        self.agent = MockAgent(self.config)

    def test_summary_with_no_iterations(self):
        """Test summary when no iterations recorded."""
        summary = self.agent.get_iteration_summary()

        assert summary["total_iterations"] == 0
        assert summary["max_iterations"] == 10
        assert summary["pass_count"] == 0
        assert summary["fail_count"] == 0
        assert summary["blocked_count"] == 0
        assert summary["history"] == []

    def test_summary_with_iterations(self):
        """Test summary with recorded iterations."""
        # Record 3 iterations: FAIL, FAIL, PASS
        for i in range(1, 4):
            self.agent.current_iteration = i
            verdict_type = "PASS" if i == 3 else "FAIL"
            verdict = MockVerdict(verdict_type)
            self.agent.record_iteration(verdict, [])

        summary = self.agent.get_iteration_summary()

        assert summary["total_iterations"] == 3
        assert summary["max_iterations"] == 10
        assert summary["pass_count"] == 1
        assert summary["fail_count"] == 2
        assert summary["blocked_count"] == 0
        assert len(summary["history"]) == 3

    def test_summary_with_blocked_verdicts(self):
        """Test summary counting BLOCKED verdicts."""
        verdicts = ["FAIL", "BLOCKED", "BLOCKED", "PASS"]

        for i, verdict_type in enumerate(verdicts, 1):
            self.agent.current_iteration = i
            verdict = MockVerdict(verdict_type)
            self.agent.record_iteration(verdict, [])

        summary = self.agent.get_iteration_summary()

        assert summary["total_iterations"] == 4
        assert summary["pass_count"] == 1
        assert summary["fail_count"] == 1
        assert summary["blocked_count"] == 2

    def test_summary_includes_full_history(self):
        """Test that summary includes complete iteration history."""
        self.agent.current_iteration = 1
        verdict = MockVerdict("PASS")
        changes = ["file1.py", "file2.py"]

        self.agent.record_iteration(verdict, changes)

        summary = self.agent.get_iteration_summary()
        history = summary["history"]

        assert len(history) == 1
        assert history[0]["iteration"] == 1
        assert history[0]["verdict"] == "PASS"
        assert history[0]["changes"] == changes

    def test_summary_with_custom_max_iterations(self):
        """Test summary reflects custom max_iterations from config."""
        self.config.max_iterations = 25
        self.agent.config = self.config

        summary = self.agent.get_iteration_summary()

        assert summary["max_iterations"] == 25

    def test_summary_with_no_config(self):
        """Test summary defaults when agent has no config."""
        agent_no_config = MockAgent.__new__(MockAgent)
        agent_no_config.current_iteration = 0
        agent_no_config.iteration_history = []
        # No config set

        summary = agent_no_config.get_iteration_summary()

        # Should use default of 10
        assert summary["max_iterations"] == 10


class TestIterationWorkflow:
    """Test full iteration tracking workflow."""

    def setup_method(self):
        """Setup mock agent for each test."""
        self.config = AgentConfig(
            project_name="test",
            agent_name="test",
            max_iterations=15
        )
        self.agent = MockAgent(self.config)

    def test_typical_success_workflow(self):
        """Test typical workflow: FAIL → FAIL → PASS."""
        workflow = [
            ("FAIL", ["file.py"], True),   # Iteration 1
            ("FAIL", ["file.py"], False),  # Iteration 2 (regression)
            ("PASS", ["file.py"], True),   # Iteration 3
        ]

        for i, (verdict_type, changes, safe) in enumerate(workflow, 1):
            self.agent.current_iteration = i
            verdict = MockVerdict(verdict_type, safe_to_merge=safe)
            self.agent.record_iteration(verdict, changes)

        summary = self.agent.get_iteration_summary()

        assert summary["total_iterations"] == 3
        assert summary["pass_count"] == 1
        assert summary["fail_count"] == 2

        # Check regression was detected
        assert summary["history"][1]["safe_to_merge"] is False

    def test_budget_exhaustion_tracking(self):
        """Test tracking when approaching iteration limit."""
        max_iters = self.config.max_iterations

        # Fill up to max iterations
        for i in range(1, max_iters + 1):
            self.agent.current_iteration = i
            verdict = MockVerdict("FAIL")
            self.agent.record_iteration(verdict, [])

        summary = self.agent.get_iteration_summary()

        assert summary["total_iterations"] == max_iters
        assert summary["max_iterations"] == max_iters
        # Agent is at budget limit
        assert summary["total_iterations"] >= summary["max_iterations"]

    def test_iteration_history_preserves_order(self):
        """Test that iteration history preserves chronological order."""
        for i in range(1, 6):
            self.agent.current_iteration = i
            verdict = MockVerdict(f"VERDICT_{i}")
            self.agent.record_iteration(verdict, [f"file{i}.py"])

        summary = self.agent.get_iteration_summary()
        history = summary["history"]

        for i, record in enumerate(history, 1):
            assert record["iteration"] == i
            assert record["verdict"] == f"VERDICT_{i}"
            assert record["changes"] == [f"file{i}.py"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
