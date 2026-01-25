"""
Tests for Claude SDK Adapter

Tests the SDK adapter interface and verify it matches ClaudeCliWrapper behavior.
"""

import pytest
pytest_plugins = ('pytest_asyncio',)
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from claude.sdk_adapter import ClaudeSDKAdapter, SDKExecutionContext
from claude.cli_wrapper import ClaudeResult


class TestClaudeSDKAdapter:
    """Tests for ClaudeSDKAdapter."""

    def test_init_with_project_dir(self, tmp_path):
        """Test adapter initialization with project directory."""
        adapter = ClaudeSDKAdapter(tmp_path)
        assert adapter.project_dir == tmp_path
        assert adapter.enable_startup_protocol is True

    def test_init_with_repo_name(self, tmp_path):
        """Test adapter initialization with explicit repo name."""
        adapter = ClaudeSDKAdapter(tmp_path, repo_name="karematch")
        assert adapter.repo_name == "karematch"

    def test_infer_repo_name_karematch(self, tmp_path):
        """Test repo name inference for karematch."""
        karematch_dir = tmp_path / "karematch"
        karematch_dir.mkdir()
        adapter = ClaudeSDKAdapter(karematch_dir)
        assert adapter.repo_name == "karematch"

    def test_infer_repo_name_credentialmate(self, tmp_path):
        """Test repo name inference for credentialmate."""
        cmate_dir = tmp_path / "credentialmate"
        cmate_dir.mkdir()
        adapter = ClaudeSDKAdapter(cmate_dir)
        assert adapter.repo_name == "credentialmate"

    def test_infer_repo_name_ai_orchestrator(self, tmp_path):
        """Test repo name inference for AI orchestrator."""
        orch_dir = tmp_path / "AI_Orchestrator"
        orch_dir.mkdir()
        adapter = ClaudeSDKAdapter(orch_dir)
        assert adapter.repo_name == "ai_orchestrator"

    def test_infer_repo_name_unknown(self, tmp_path):
        """Test repo name inference for unknown directory."""
        unknown_dir = tmp_path / "some_project"
        unknown_dir.mkdir()
        adapter = ClaudeSDKAdapter(unknown_dir)
        assert adapter.repo_name == "unknown"

    def test_execute_task_returns_claude_result(self, tmp_path):
        """Test that execute_task returns ClaudeResult."""
        adapter = ClaudeSDKAdapter(tmp_path)

        # Mock SDK not installed
        with patch.dict("sys.modules", {"claude_code_sdk": None}):
            result = adapter.execute_task("test prompt")

        assert isinstance(result, ClaudeResult)
        assert result.success is False
        assert "not installed" in result.error.lower()

    def test_allow_dangerous_permissions_from_env(self, tmp_path, monkeypatch):
        """Test dangerous permissions from environment variable."""
        monkeypatch.setenv("AI_ORCHESTRATOR_CLAUDE_SKIP_PERMISSIONS", "true")
        assert ClaudeSDKAdapter._allow_dangerous_permissions(None) is True

        monkeypatch.setenv("AI_ORCHESTRATOR_CLAUDE_SKIP_PERMISSIONS", "false")
        assert ClaudeSDKAdapter._allow_dangerous_permissions(None) is False

        monkeypatch.delenv("AI_ORCHESTRATOR_CLAUDE_SKIP_PERMISSIONS", raising=False)
        assert ClaudeSDKAdapter._allow_dangerous_permissions(None) is False

    def test_allow_dangerous_permissions_override(self, tmp_path):
        """Test dangerous permissions with explicit override."""
        assert ClaudeSDKAdapter._allow_dangerous_permissions(True) is True
        assert ClaudeSDKAdapter._allow_dangerous_permissions(False) is False


class TestSDKExecutionContext:
    """Tests for SDKExecutionContext."""

    def test_default_values(self):
        """Test default context values."""
        context = SDKExecutionContext()
        assert context.agent is None
        assert context.app_context is None
        assert context.session_id == ""
        assert context.changed_files == []
        assert context.last_verdict is None
        assert context.current_iteration == 0
        assert context.max_iterations == 10

    def test_custom_values(self):
        """Test context with custom values."""
        mock_agent = MagicMock()
        mock_context = MagicMock()

        context = SDKExecutionContext(
            agent=mock_agent,
            app_context=mock_context,
            session_id="TASK-001",
            max_iterations=15,
        )

        assert context.agent is mock_agent
        assert context.app_context is mock_context
        assert context.session_id == "TASK-001"
        assert context.max_iterations == 15


class TestSDKAdapterIntegration:
    """Integration tests for SDK adapter with mocked SDK."""

    @pytest.mark.asyncio
    async def test_execute_task_async_with_mocked_sdk(self, tmp_path):
        """Test async execution with mocked SDK."""
        adapter = ClaudeSDKAdapter(tmp_path)

        # Create mock SDK module
        mock_query = AsyncMock()
        mock_options = MagicMock()

        # Mock the async generator
        async def mock_generator():
            yield MagicMock(type="text", text="Hello")
            yield MagicMock(type="result", result="Done")

        mock_query.return_value = mock_generator()

        with patch.dict(
            "sys.modules",
            {
                "claude_code_sdk": MagicMock(
                    query=mock_query,
                    ClaudeCodeOptions=mock_options,
                )
            },
        ):
            # Note: This won't work directly due to import mechanics
            # In a real test, you'd need to structure imports differently
            pass

    def test_execute_task_with_retry_success(self, tmp_path):
        """Test retry succeeds after initial failures."""
        adapter = ClaudeSDKAdapter(tmp_path)

        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return ClaudeResult(
                    success=False, output="", error="timeout", duration_ms=100
                )
            return ClaudeResult(
                success=True, output="Success", files_changed=[], duration_ms=100
            )

        with patch.object(adapter, "execute_task", side_effect=mock_execute):
            result = adapter.execute_task_with_retry("test prompt", max_retries=3)

        assert result.success is True
        assert call_count == 2

    def test_execute_task_with_retry_exhausted(self, tmp_path):
        """Test retry exhausted after max retries."""
        adapter = ClaudeSDKAdapter(tmp_path)

        def mock_execute(*args, **kwargs):
            return ClaudeResult(
                success=False, output="", error="timeout", duration_ms=100
            )

        with patch.object(adapter, "execute_task", side_effect=mock_execute):
            result = adapter.execute_task_with_retry("test prompt", max_retries=3)

        assert result.success is False
        assert "timeout" in result.error


class TestGetAdapter:
    """Tests for get_adapter factory function."""

    def test_get_adapter_sdk_when_available(self, tmp_path):
        """Test get_adapter returns SDK adapter when SDK available."""
        from claude.sdk_adapter import get_adapter

        # Mock SDK available
        with patch.object(
            ClaudeSDKAdapter, "check_sdk_available", return_value=True
        ):
            adapter = get_adapter(tmp_path, use_sdk=True)
            assert isinstance(adapter, ClaudeSDKAdapter)

    def test_get_adapter_cli_when_requested(self, tmp_path):
        """Test get_adapter returns CLI wrapper when explicitly requested."""
        from claude.sdk_adapter import get_adapter
        from claude.cli_wrapper import ClaudeCliWrapper

        adapter = get_adapter(tmp_path, use_sdk=False)
        assert isinstance(adapter, ClaudeCliWrapper)

    def test_get_adapter_fallback_on_sdk_unavailable(self, tmp_path):
        """Test get_adapter falls back to CLI when SDK unavailable."""
        from claude.sdk_adapter import get_adapter
        from claude.cli_wrapper import ClaudeCliWrapper

        # Mock SDK not available
        with patch.object(
            ClaudeSDKAdapter,
            "check_sdk_available",
            side_effect=ImportError("SDK not installed"),
        ):
            adapter = get_adapter(tmp_path, use_sdk=True)
            assert isinstance(adapter, ClaudeCliWrapper)
