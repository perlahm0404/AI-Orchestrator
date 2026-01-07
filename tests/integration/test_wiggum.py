"""
Integration tests for Wiggum iteration pattern.

Tests the full flow:
1. Agent executes
2. Stop hook evaluates (calls Ralph for verification)
3. Iteration continues or exits
4. State file management
5. Completion signal detection

Wiggum = Iteration control system (uses Ralph for verification)
Ralph = Code quality verification system (PASS/FAIL/BLOCKED)
"""

import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

from agents.base import BaseAgent, AgentConfig
from orchestration.iteration_loop import IterationLoop, IterationResult
from ralph.verdict import Verdict, VerdictType


# Mock agent for testing
class MockAgent(BaseAgent):
    """Mock agent that simulates different behaviors for testing."""

    def __init__(self, config: AgentConfig, behavior: str = "success"):
        """
        Initialize mock agent.

        Args:
            config: AgentConfig
            behavior: One of:
                - "success": Always succeeds on first try
                - "completion_signal": Outputs completion signal
                - "retry_once": Fails first, succeeds second
                - "max_iterations": Never completes (tests budget)
                - "ralph_fail": Fails Ralph verification
        """
        self.config = config
        self.behavior = behavior
        self.current_iteration = 0
        self.iteration_history = []
        self.baseline = None

    def execute(self, task_id: str) -> Dict[str, Any]:
        """Execute mock task based on behavior."""
        self.current_iteration += 1

        if self.behavior == "success":
            return {
                "task_id": task_id,
                "status": "completed",
                "output": "Task completed successfully",
                "iterations": self.current_iteration
            }

        elif self.behavior == "completion_signal":
            promise = self.config.expected_completion_signal
            return {
                "task_id": task_id,
                "status": "completed",
                "output": f"All done! <promise>{promise}</promise>",
                "iterations": self.current_iteration
            }

        elif self.behavior == "retry_once":
            if self.current_iteration == 1:
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "output": "First attempt failed, retrying",
                    "iterations": self.current_iteration
                }
            else:
                promise = self.config.expected_completion_signal or "DONE"
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "output": f"Second attempt succeeded <promise>{promise}</promise>",
                    "iterations": self.current_iteration
                }

        elif self.behavior == "max_iterations":
            return {
                "task_id": task_id,
                "status": "in_progress",
                "output": f"Still working... iteration {self.current_iteration}",
                "iterations": self.current_iteration
            }

        elif self.behavior == "ralph_fail":
            return {
                "task_id": task_id,
                "status": "completed",
                "output": "Changes made but will fail Ralph",
                "iterations": self.current_iteration,
                "will_fail_ralph": True
            }

    def checkpoint(self) -> Dict[str, Any]:
        """Checkpoint mock state."""
        return {
            "agent": "mock",
            "iteration": self.current_iteration,
            "behavior": self.behavior
        }

    def halt(self, reason: str) -> None:
        """Halt execution."""
        pass


# Mock app context
@dataclass
class MockAppContext:
    """Mock application context for testing."""
    project_name: str = "test-project"
    project_path: str = "/tmp/test-project"
    lint_command: str = "echo 'lint'"
    typecheck_command: str = "echo 'typecheck'"
    test_command: str = "echo 'test'"
    coverage_command: str = "echo 'coverage'"


class TestRalphLoopIntegration:
    """Integration tests for Ralph loop iteration pattern."""

    def test_completion_signal_detected(self, tmp_path):
        """Test that completion signal is detected and loop exits."""
        config = AgentConfig(
            project_name="test",
            agent_name="mock",
            expected_completion_signal="COMPLETE",
            max_iterations=5
        )
        agent = MockAgent(config, behavior="completion_signal")
        app_context = MockAppContext(project_path=str(tmp_path))

        loop = IterationLoop(agent, app_context, state_dir=tmp_path / ".aibrain")

        # Run the loop - should complete successfully
        result = loop.run(task_id="test-1", task_description="Test task")

        # Verify completion
        assert result.status == "completed"
        assert result.iterations == 1
        assert "Completion signal detected" in result.reason

    def test_iteration_budget_enforced(self, tmp_path):
        """Test that iteration budget is enforced."""
        config = AgentConfig(
            project_name="test",
            agent_name="mock",
            expected_completion_signal="DONE",
            max_iterations=3
        )
        agent = MockAgent(config, behavior="max_iterations")
        app_context = MockAppContext(project_path=str(tmp_path))

        loop = IterationLoop(agent, app_context, state_dir=tmp_path / ".aibrain")

        # Run the loop - should hit iteration budget
        result = loop.run(task_id="test-2", task_description="Test task")

        # Verify budget was enforced
        assert result.status in ["blocked", "completed"]
        assert result.iterations <= 3

    def test_state_file_created(self, tmp_path):
        """Test that state file is created during loop execution."""
        config = AgentConfig(
            project_name="test",
            agent_name="mock",
            expected_completion_signal="DONE",
            max_iterations=5
        )
        agent = MockAgent(config, behavior="completion_signal")  # Use completion_signal for clean exit
        app_context = MockAppContext(project_path=str(tmp_path))

        state_dir = tmp_path / ".aibrain"
        loop = IterationLoop(agent, app_context, state_dir=state_dir)

        result = loop.run(task_id="test-3", task_description="Test task")

        # State dir should have been created
        assert state_dir.exists()

        # State file should have been cleaned up after successful completion
        state_file = state_dir / "agent-loop.local.md"
        assert not state_file.exists()  # Cleaned up on completion

    def test_agent_config_integration(self):
        """Test that AgentConfig is properly integrated with agents."""
        config = AgentConfig(
            project_name="test",
            agent_name="mock",
            expected_completion_signal="COMPLETE",
            max_iterations=10,
            max_retries=3
        )

        agent = MockAgent(config)

        assert agent.config.project_name == "test"
        assert agent.config.agent_name == "mock"
        assert agent.config.expected_completion_signal == "COMPLETE"
        assert agent.config.max_iterations == 10
        assert agent.config.max_retries == 3

    def test_completion_signal_check(self):
        """Test completion signal checking in agent."""
        config = AgentConfig(
            project_name="test",
            agent_name="mock",
            expected_completion_signal="DONE"
        )

        agent = MockAgent(config)

        # Test signal detection
        output1 = "Task completed <promise>DONE</promise>"
        signal1 = agent.check_completion_signal(output1)
        assert signal1 == "DONE"

        # Test no signal
        output2 = "Task completed successfully"
        signal2 = agent.check_completion_signal(output2)
        assert signal2 is None

        # Test wrong signal
        output3 = "Task completed <promise>COMPLETE</promise>"
        signal3 = agent.check_completion_signal(output3)
        assert signal3 == "COMPLETE"  # Detects signal but doesn't match expected

    def test_iteration_tracking(self):
        """Test iteration tracking in agent."""
        config = AgentConfig(
            project_name="test",
            agent_name="mock",
            max_iterations=5
        )

        agent = MockAgent(config)

        # Initial state
        summary = agent.get_iteration_summary()
        assert summary["total_iterations"] == 0
        assert summary["max_iterations"] == 5

        # Simulate some iterations
        from ralph.verdict import Verdict, VerdictType

        verdict1 = Verdict(
            type=VerdictType.PASS,
            steps=[],
            safe_to_merge=True,
            regression_detected=False
        )
        agent.current_iteration = 1  # Simulate first iteration
        agent.record_iteration(verdict1, ["file1.py"])

        verdict2 = Verdict(
            type=VerdictType.FAIL,
            steps=[],
            safe_to_merge=False,
            regression_detected=True
        )
        agent.current_iteration = 2  # Simulate second iteration
        agent.record_iteration(verdict2, ["file2.py"])

        summary = agent.get_iteration_summary()
        assert summary["total_iterations"] == 2
        assert summary["pass_count"] == 1
        assert summary["fail_count"] == 1


class TestAgentLoopMethods:
    """Test the run_with_loop convenience methods."""

    def test_bugfix_agent_has_run_with_loop(self):
        """Test that BugFixAgent has run_with_loop method."""
        from agents.bugfix import BugFixAgent

        # Check method exists
        assert hasattr(BugFixAgent, "run_with_loop")

        # Check it's callable
        assert callable(getattr(BugFixAgent, "run_with_loop"))

    def test_codequality_agent_has_run_with_loop(self):
        """Test that CodeQualityAgent has run_with_loop method."""
        from agents.codequality import CodeQualityAgent

        # Check method exists
        assert hasattr(CodeQualityAgent, "run_with_loop")

        # Check it's callable
        assert callable(getattr(CodeQualityAgent, "run_with_loop"))
