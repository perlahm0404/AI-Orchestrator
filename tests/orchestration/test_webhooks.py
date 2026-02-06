"""
Test WebhookHandler with retry logic and event filtering.

TDD: These tests verify webhook delivery, retries, and filtering.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from orchestration.webhooks import WebhookHandler, WebhookEvent


@pytest.fixture
def webhook_handler():
    """Create WebhookHandler instance."""
    return WebhookHandler(
        url="https://hooks.example.com/webhook",
        timeout=3.0,
        max_retries=3
    )


@pytest.fixture
def sample_event():
    """Create sample webhook event."""
    return WebhookEvent(
        event_type="task_complete",
        severity="info",
        data={
            "task_id": "TASK-123",
            "status": "completed",
            "iterations": 5
        }
    )


class TestWebhookHandler:
    """Test WebhookHandler basic functionality."""

    @pytest.mark.asyncio
    async def test_send_successful(self, webhook_handler, sample_event):
        """Should send webhook successfully on first attempt."""
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=200)

            result = await webhook_handler.send(sample_event)

            assert result is True
            assert mock_post.call_count == 1
            # Verify payload structure
            call_args = mock_post.call_args
            assert call_args[1]['json']['event_type'] == 'task_complete'
            assert call_args[1]['json']['severity'] == 'info'

    @pytest.mark.asyncio
    async def test_send_timeout(self, webhook_handler, sample_event):
        """Should respect timeout setting."""
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=200)

            await webhook_handler.send(sample_event)

            # Verify timeout was set
            call_args = mock_post.call_args
            assert call_args[1]['timeout'] == 3.0


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, webhook_handler, sample_event):
        """Should retry 3 times on failure."""
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            # Simulate failures
            mock_post.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                MagicMock(status_code=200)  # Success on 3rd attempt
            ]

            result = await webhook_handler.send(sample_event)

            assert result is True
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, webhook_handler, sample_event):
        """Should return False after exhausting retries."""
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            # Simulate continuous failures
            mock_post.side_effect = Exception("Network error")

            result = await webhook_handler.send(sample_event)

            assert result is False
            assert mock_post.call_count == 3  # max_retries

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, webhook_handler, sample_event):
        """Should use exponential backoff between retries."""
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                mock_post.side_effect = [
                    Exception("Network error"),
                    Exception("Network error"),
                    MagicMock(status_code=200)
                ]

                await webhook_handler.send(sample_event)

                # Verify exponential backoff: 1s, 2s
                sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert len(sleep_calls) == 2
                assert sleep_calls[0] == 1.0  # 2^0
                assert sleep_calls[1] == 2.0  # 2^1


class TestEventFiltering:
    """Test event filtering by type and severity."""

    @pytest.mark.asyncio
    async def test_filter_by_event_type(self):
        """Should filter events by type."""
        handler = WebhookHandler(
            url="https://hooks.example.com/webhook",
            filter_event_types=["task_complete", "loop_complete"]
        )

        # Allowed event
        allowed_event = WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={}
        )

        # Filtered event
        filtered_event = WebhookEvent(
            event_type="task_start",
            severity="info",
            data={}
        )

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=200)

            # Send allowed event
            result1 = await handler.send(allowed_event)
            assert result1 is True
            assert mock_post.call_count == 1

            # Send filtered event
            result2 = await handler.send(filtered_event)
            assert result2 is True  # Returns True but doesn't send
            assert mock_post.call_count == 1  # Still 1 (no new call)

    @pytest.mark.asyncio
    async def test_filter_by_severity(self):
        """Should filter events by severity level."""
        handler = WebhookHandler(
            url="https://hooks.example.com/webhook",
            min_severity="warning"  # Only warning and error
        )

        info_event = WebhookEvent(event_type="test", severity="info", data={})
        warning_event = WebhookEvent(event_type="test", severity="warning", data={})
        error_event = WebhookEvent(event_type="test", severity="error", data={})

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(status_code=200)

            # Info should be filtered
            await handler.send(info_event)
            assert mock_post.call_count == 0

            # Warning should pass
            await handler.send(warning_event)
            assert mock_post.call_count == 1

            # Error should pass
            await handler.send(error_event)
            assert mock_post.call_count == 2


class TestWebhookEvent:
    """Test WebhookEvent data class."""

    def test_event_to_dict(self, sample_event):
        """Should convert event to dict."""
        event_dict = sample_event.to_dict()

        assert event_dict['event_type'] == 'task_complete'
        assert event_dict['severity'] == 'info'
        assert event_dict['data']['task_id'] == 'TASK-123'
        assert 'timestamp' in event_dict

    def test_event_severity_levels(self):
        """Should support all severity levels."""
        for severity in ['info', 'warning', 'error']:
            event = WebhookEvent(
                event_type="test",
                severity=severity,
                data={}
            )
            assert event.severity == severity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
