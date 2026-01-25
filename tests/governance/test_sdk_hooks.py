"""
Tests for SDK Hooks (Ralph PostToolUse and Wiggum Stop hooks)

Tests verify that the SDK hooks properly integrate with Ralph verification
and Wiggum iteration control.
"""

import pytest
pytest_plugins = ('pytest_asyncio',)
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass
from enum import Enum


class VerdictType(Enum):
    """Mock VerdictType for testing."""
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass
class MockVerdict:
    """Mock Ralph Verdict for testing."""
    type: VerdictType
    safe_to_merge: bool = False
    regression_detected: bool = False

    def summary(self) -> str:
        return f"Verdict: {self.type.value}"


class TestRalphPostToolHook:
    """Tests for ralph_post_tool_hook."""

    @pytest.mark.asyncio
    async def test_skips_non_file_tools(self):
        """Test hook skips non-Edit/Write tools."""
        from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

        input_data = {"tool_name": "Read", "tool_input": {}}
        result = await ralph_post_tool_hook(input_data, "tool-123", {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_skips_without_app_context(self):
        """Test hook skips when no app_context provided."""
        from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

        input_data = {"tool_name": "Edit", "tool_input": {"file_path": "test.py"}}
        context = {}  # No app_context
        result = await ralph_post_tool_hook(input_data, "tool-123", context)
        assert result == {}

    @pytest.mark.asyncio
    async def test_tracks_changed_files(self):
        """Test hook tracks file changes in context."""
        from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/auth.py"},
        }
        context = {
            "app_context": MagicMock(project_name="test"),
            "changed_files": [],
        }

        # Mock Ralph to avoid actual verification
        with patch(
            "governance.hooks.sdk_ralph_hook._run_ralph_verification"
        ) as mock_verify:
            mock_verify.return_value = MockVerdict(VerdictType.PASS, safe_to_merge=True)
            await ralph_post_tool_hook(input_data, "tool-123", context)

        assert "src/auth.py" in context["changed_files"]

    @pytest.mark.asyncio
    async def test_pass_verdict_returns_empty(self):
        """Test PASS verdict returns empty dict (continue)."""
        from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "test.py"},
        }
        context = {
            "app_context": MagicMock(project_name="test"),
            "changed_files": ["test.py"],
        }

        with patch(
            "governance.hooks.sdk_ralph_hook._run_ralph_verification"
        ) as mock_verify:
            mock_verify.return_value = MockVerdict(VerdictType.PASS, safe_to_merge=True)
            result = await ralph_post_tool_hook(input_data, "tool-123", context)

        assert result == {}
        assert context["last_verdict"] is not None

    @pytest.mark.asyncio
    async def test_blocked_verdict_returns_stop_instruction(self):
        """Test BLOCKED verdict returns stop instruction."""
        from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py"},
        }
        context = {
            "app_context": MagicMock(project_name="test"),
            "changed_files": ["test.py"],
        }

        with patch(
            "governance.hooks.sdk_ralph_hook._run_ralph_verification"
        ) as mock_verify:
            mock_verify.return_value = MockVerdict(VerdictType.BLOCKED)
            result = await ralph_post_tool_hook(input_data, "tool-123", context)

        assert "instruction" in result
        assert "STOP" in result["instruction"]
        assert "GUARDRAIL" in result["instruction"]

    @pytest.mark.asyncio
    async def test_fail_regression_returns_warning(self):
        """Test FAIL with regression returns warning instruction."""
        from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py"},
        }
        context = {
            "app_context": MagicMock(project_name="test"),
            "changed_files": ["test.py"],
        }

        with patch(
            "governance.hooks.sdk_ralph_hook._run_ralph_verification"
        ) as mock_verify:
            mock_verify.return_value = MockVerdict(
                VerdictType.FAIL, regression_detected=True
            )
            result = await ralph_post_tool_hook(input_data, "tool-123", context)

        assert "instruction" in result
        assert "REGRESSION" in result["instruction"]

    @pytest.mark.asyncio
    async def test_fail_safe_to_merge_returns_empty(self):
        """Test FAIL with safe_to_merge returns empty (continue)."""
        from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py"},
        }
        context = {
            "app_context": MagicMock(project_name="test"),
            "changed_files": ["test.py"],
        }

        with patch(
            "governance.hooks.sdk_ralph_hook._run_ralph_verification"
        ) as mock_verify:
            mock_verify.return_value = MockVerdict(VerdictType.FAIL, safe_to_merge=True)
            result = await ralph_post_tool_hook(input_data, "tool-123", context)

        assert result == {}


class TestWiggumStopHook:
    """Tests for wiggum_stop_hook."""

    @pytest.mark.asyncio
    async def test_allows_stop_without_agent(self):
        """Test hook allows stop when no agent in context."""
        from governance.hooks.sdk_stop_hook import wiggum_stop_hook

        result = await wiggum_stop_hook({}, {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_blocks_when_no_changes(self):
        """Test hook blocks when no file changes detected."""
        from governance.hooks.sdk_stop_hook import wiggum_stop_hook

        mock_agent = MagicMock()
        mock_agent.config.max_iterations = 10
        mock_agent.current_iteration = 0

        context = {
            "agent": mock_agent,
            "changed_files": [],
        }

        result = await wiggum_stop_hook({"content": ""}, context)
        assert result.get("continue") is True
        assert "No file changes" in result.get("message", "")

    @pytest.mark.asyncio
    async def test_budget_exhausted_requires_human(self):
        """Test hook requires human when budget exhausted."""
        from governance.hooks.sdk_stop_hook import wiggum_stop_hook

        mock_agent = MagicMock()
        mock_agent.config.max_iterations = 5
        mock_agent.current_iteration = 4  # Will become 5

        context = {
            "agent": mock_agent,
            "changed_files": ["test.py"],
        }

        result = await wiggum_stop_hook({"content": ""}, context)
        assert result.get("decision") == "ask_human"
        assert "budget exhausted" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_pass_verdict_allows_stop(self):
        """Test hook allows stop on PASS verdict."""
        from governance.hooks.sdk_stop_hook import wiggum_stop_hook

        mock_agent = MagicMock()
        mock_agent.config.max_iterations = 10
        mock_agent.current_iteration = 0
        mock_agent.check_completion_signal.return_value = None

        context = {
            "agent": mock_agent,
            "changed_files": ["test.py"],
            "last_verdict": MockVerdict(VerdictType.PASS, safe_to_merge=True),
        }

        result = await wiggum_stop_hook({"content": ""}, context)
        assert result == {}

    @pytest.mark.asyncio
    async def test_fail_regression_blocks(self):
        """Test hook blocks on FAIL with regression."""
        from governance.hooks.sdk_stop_hook import wiggum_stop_hook

        mock_agent = MagicMock()
        mock_agent.config.max_iterations = 10
        mock_agent.current_iteration = 0
        mock_agent.check_completion_signal.return_value = None

        context = {
            "agent": mock_agent,
            "changed_files": ["test.py"],
            "last_verdict": MockVerdict(VerdictType.FAIL, regression_detected=True),
        }

        result = await wiggum_stop_hook({"content": ""}, context)
        assert result.get("continue") is True

    @pytest.mark.asyncio
    async def test_fail_safe_to_merge_allows_stop(self):
        """Test hook allows stop on FAIL with safe_to_merge."""
        from governance.hooks.sdk_stop_hook import wiggum_stop_hook

        mock_agent = MagicMock()
        mock_agent.config.max_iterations = 10
        mock_agent.current_iteration = 0
        mock_agent.check_completion_signal.return_value = None

        context = {
            "agent": mock_agent,
            "changed_files": ["test.py"],
            "last_verdict": MockVerdict(VerdictType.FAIL, safe_to_merge=True),
        }

        result = await wiggum_stop_hook({"content": ""}, context)
        assert result == {}


class TestIterationBudgets:
    """Tests for iteration budget enforcement."""

    def test_get_max_iterations_from_config(self):
        """Test max iterations from agent config."""
        from governance.hooks.sdk_stop_hook import _get_max_iterations

        mock_agent = MagicMock()
        mock_agent.config.max_iterations = 25

        result = _get_max_iterations(mock_agent)
        assert result == 25

    def test_get_max_iterations_defaults(self):
        """Test max iterations defaults by agent type."""
        from governance.hooks.sdk_stop_hook import _get_max_iterations

        # Bugfix default
        mock_agent = MagicMock()
        mock_agent.config.agent_name = "bugfix"
        delattr(mock_agent.config, "max_iterations")
        # This will raise AttributeError, triggering fallback
        result = _get_max_iterations(mock_agent)
        assert result == 15

    def test_iteration_budgets_match_factory(self):
        """Test SDK hook budgets match factory defaults."""
        from agents.factory import ITERATION_BUDGETS

        # Verify key agent types have correct budgets
        assert ITERATION_BUDGETS["bugfix"] == 15
        assert ITERATION_BUDGETS["codequality"] == 20
        assert ITERATION_BUDGETS["feature"] == 50
        assert ITERATION_BUDGETS["test"] == 15
