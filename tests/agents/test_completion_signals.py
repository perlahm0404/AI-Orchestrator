"""
Unit tests for completion signal detection.

Tests the <promise>TEXT</promise> pattern detection in BaseAgent.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent, AgentConfig
from unittest.mock import Mock


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


class TestCompletionSignals:
    """Test completion signal detection."""

    def setup_method(self):
        """Setup mock agent for each test."""
        self.config = AgentConfig(
            project_name="test",
            agent_name="test",
            expected_completion_signal="DONE"
        )
        self.agent = MockAgent(self.config)

    def test_detect_simple_promise(self):
        """Test detection of simple <promise>TEXT</promise> tag."""
        output = "Task complete. <promise>DONE</promise>"
        result = self.agent.check_completion_signal(output)
        assert result == "DONE"

    def test_detect_promise_with_context(self):
        """Test detection when promise is embedded in text."""
        output = """
        I have successfully completed the task.
        All tests are passing.
        <promise>COMPLETE</promise>
        The changes are ready for review.
        """
        result = self.agent.check_completion_signal(output)
        assert result == "COMPLETE"

    def test_detect_multiword_promise(self):
        """Test detection of multi-word promises."""
        output = "Work finished. <promise>ALL TESTS PASS</promise>"
        result = self.agent.check_completion_signal(output)
        assert result == "ALL TESTS PASS"

    def test_no_promise_returns_none(self):
        """Test that missing promise returns None."""
        output = "Task in progress. Still working on it."
        result = self.agent.check_completion_signal(output)
        assert result is None

    def test_empty_promise_returns_empty_string(self):
        """Test that empty promise tag returns empty string."""
        output = "Task complete. <promise></promise>"
        result = self.agent.check_completion_signal(output)
        assert result == ""

    def test_whitespace_normalization(self):
        """Test that whitespace is normalized."""
        output = "<promise>  DONE  \n  </promise>"
        result = self.agent.check_completion_signal(output)
        assert result == "DONE"

    def test_multiline_promise(self):
        """Test promise with newlines inside."""
        output = """
        <promise>
        TASK
        COMPLETE
        </promise>
        """
        result = self.agent.check_completion_signal(output)
        assert result == "TASK COMPLETE"

    def test_case_sensitive_matching(self):
        """Test that promise matching is case-sensitive."""
        output1 = "<promise>Done</promise>"
        output2 = "<promise>DONE</promise>"
        output3 = "<promise>done</promise>"

        assert self.agent.check_completion_signal(output1) == "Done"
        assert self.agent.check_completion_signal(output2) == "DONE"
        assert self.agent.check_completion_signal(output3) == "done"

    def test_multiple_promises_returns_first(self):
        """Test that multiple promises return the first match."""
        output = "Step 1: <promise>STEP1</promise> Step 2: <promise>STEP2</promise>"
        result = self.agent.check_completion_signal(output)
        assert result == "STEP1"

    def test_promise_with_special_characters(self):
        """Test promise with special characters."""
        output = "<promise>Task #123 - DONE!</promise>"
        result = self.agent.check_completion_signal(output)
        assert result == "Task #123 - DONE!"

    def test_promise_exact_match_required(self):
        """Test that exact match is required for completion."""
        self.config.expected_completion_signal = "DONE"
        self.agent.config = self.config

        # Exact match
        output1 = "<promise>DONE</promise>"
        promise1 = self.agent.check_completion_signal(output1)
        assert promise1 == "DONE"
        assert promise1 == self.config.expected_completion_signal

        # Not exact match
        output2 = "<promise>DONE!</promise>"
        promise2 = self.agent.check_completion_signal(output2)
        assert promise2 == "DONE!"
        assert promise2 != self.config.expected_completion_signal

    def test_malformed_promise_tags(self):
        """Test handling of malformed promise tags."""
        # Missing closing tag
        output1 = "<promise>DONE"
        assert self.agent.check_completion_signal(output1) is None

        # Missing opening tag
        output2 = "DONE</promise>"
        assert self.agent.check_completion_signal(output2) is None

        # Wrong tag name
        output3 = "<completion>DONE</completion>"
        assert self.agent.check_completion_signal(output3) is None


class TestCompletionSignalIntegration:
    """Test completion signal integration with agent config."""

    def test_agent_config_default_no_signal(self):
        """Test that default config has no completion signal."""
        config = AgentConfig(
            project_name="test",
            agent_name="test"
        )
        assert config.expected_completion_signal is None

    def test_agent_config_with_signal(self):
        """Test config with completion signal."""
        config = AgentConfig(
            project_name="test",
            agent_name="test",
            expected_completion_signal="COMPLETE"
        )
        assert config.expected_completion_signal == "COMPLETE"

    def test_completion_check_workflow(self):
        """Test full workflow: check signal, compare with config."""
        config = AgentConfig(
            project_name="test",
            agent_name="test",
            expected_completion_signal="DONE",
            max_iterations=10
        )
        agent = MockAgent(config)

        # Agent outputs completion signal
        output = "All work complete. <promise>DONE</promise>"
        promise = agent.check_completion_signal(output)

        # Verify signal matches expected
        assert promise is not None
        assert promise == config.expected_completion_signal

        # This would trigger completion in real agent
        should_complete = (promise == config.expected_completion_signal)
        assert should_complete is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
