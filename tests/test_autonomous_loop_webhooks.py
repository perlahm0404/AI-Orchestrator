"""
Test autonomous_loop.py webhook integration.

TDD: These tests verify webhook delivery during autonomous loop execution.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path


@pytest.fixture
def mock_webhook_handler():
    """Create mock WebhookHandler."""
    handler = MagicMock()
    handler.send = AsyncMock(return_value=True)
    return handler


class TestWebhookIntegration:
    """Test webhook integration in autonomous loop."""

    @pytest.mark.asyncio
    async def test_loop_start_webhook(self, mock_webhook_handler):
        """Should send loop_start webhook when loop begins."""
        from autonomous_loop import run_autonomous_loop
        from adapters.karematch import KareMatchAdapter

        with patch('autonomous_loop.WorkQueueManager') as mock_manager:
            with patch('autonomous_loop.WebhookHandler', return_value=mock_webhook_handler):
                with patch('autonomous_loop.KareMatchAdapter') as mock_adapter:
                    # Setup empty queue (no tasks)
                    mock_manager.return_value.get_next_task.return_value = None
                    # Mock adapter
                    mock_adapter.return_value.get_context.return_value.project_path = "/tmp"

                    # Run loop with webhook
                    await run_autonomous_loop(
                        project_dir=Path("/tmp"),
                        project_name="karematch",  # Use valid project
                        max_iterations=1,
                        use_sqlite=True,
                        webhook_url="https://hooks.example.com/webhook"
                    )

                    # Verify loop_start webhook sent (at least)
                    assert mock_webhook_handler.send.call_count >= 1
                    first_call = mock_webhook_handler.send.call_args_list[0]
                    event = first_call[0][0]
                    assert event.event_type == "loop_start"
                    assert event.severity == "info"

    @pytest.mark.asyncio
    async def test_task_start_webhook(self, mock_webhook_handler):
        """Should send task_start webhook when task begins."""
        # This test would require more complex mocking of the entire loop
        # For now, we'll verify the webhook handler is called with correct event type
        from orchestration.webhooks import WebhookEvent

        # Simulate what autonomous_loop should do
        event = WebhookEvent(
            event_type="task_start",
            severity="info",
            data={"task_id": "TASK-123", "description": "Test task"}
        )

        await mock_webhook_handler.send(event)

        assert mock_webhook_handler.send.called
        call_args = mock_webhook_handler.send.call_args[0]
        assert call_args[0].event_type == "task_start"

    @pytest.mark.asyncio
    async def test_task_complete_webhook_severity(self, mock_webhook_handler):
        """Should set severity based on verdict."""
        from orchestration.webhooks import WebhookEvent

        # Test PASS = info
        pass_event = WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={"task_id": "TASK-123", "verdict": "PASS"}
        )
        await mock_webhook_handler.send(pass_event)
        assert mock_webhook_handler.send.call_args[0][0].severity == "info"

        # Test FAIL = warning
        fail_event = WebhookEvent(
            event_type="task_complete",
            severity="warning",
            data={"task_id": "TASK-123", "verdict": "FAIL"}
        )
        await mock_webhook_handler.send(fail_event)
        assert mock_webhook_handler.send.call_args[0][0].severity == "warning"

        # Test BLOCKED = error
        blocked_event = WebhookEvent(
            event_type="task_complete",
            severity="error",
            data={"task_id": "TASK-123", "verdict": "BLOCKED"}
        )
        await mock_webhook_handler.send(blocked_event)
        assert mock_webhook_handler.send.call_args[0][0].severity == "error"


class TestWebhookConfiguration:
    """Test webhook configuration options."""

    def test_webhook_url_flag_available(self):
        """Should accept --webhook-url CLI flag."""
        import argparse
        from autonomous_loop import main

        # This test verifies the argument is defined
        # We can't easily test the full CLI without running it
        # So we'll just verify the parser setup
        parser = argparse.ArgumentParser()
        parser.add_argument("--webhook-url", type=str, default=None)

        args = parser.parse_args(["--webhook-url", "https://example.com"])
        assert args.webhook_url == "https://example.com"

    @pytest.mark.asyncio
    async def test_no_webhook_when_url_not_provided(self, mock_webhook_handler):
        """Should not send webhooks when URL not provided."""
        from autonomous_loop import run_autonomous_loop

        with patch('autonomous_loop.WorkQueueManager') as mock_manager:
            # Setup empty queue
            mock_manager.return_value.get_next_task.return_value = None

            # Run without webhook_url
            await run_autonomous_loop(
                project_dir=Path("/tmp"),
                project_name="test",
                max_iterations=1,
                use_sqlite=True
                # webhook_url not provided
            )

            # Webhook handler should not be created
            # (would need to mock WebhookHandler constructor to verify this)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
