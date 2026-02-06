"""
Test Slack webhook formatter.

TDD: These tests verify Slack message formatting with attachments and color coding.
"""

import pytest
from orchestration.webhooks import WebhookEvent
from orchestration.formatters.slack import SlackFormatter


@pytest.fixture
def slack_formatter():
    """Create SlackFormatter instance."""
    return SlackFormatter()


@pytest.fixture
def task_complete_event():
    """Create task_complete webhook event."""
    return WebhookEvent(
        event_type="task_complete",
        severity="info",
        data={
            "task_id": "TASK-ABC123",
            "verdict": "PASS",
            "iterations": 5,
            "files_changed": ["src/main.py", "tests/test_main.py"]
        }
    )


class TestSlackFormatter:
    """Test basic Slack message formatting."""

    def test_format_creates_slack_message(self, slack_formatter, task_complete_event):
        """Should create Slack message structure."""
        slack_msg = slack_formatter.format(task_complete_event)

        assert "text" in slack_msg
        assert "attachments" in slack_msg
        assert isinstance(slack_msg["attachments"], list)
        assert len(slack_msg["attachments"]) > 0

    def test_message_includes_event_type(self, slack_formatter, task_complete_event):
        """Should include event type in message text."""
        slack_msg = slack_formatter.format(task_complete_event)

        # Accept either "task_complete" or "task complete" (formatted version)
        text_lower = slack_msg["text"].lower()
        assert "task" in text_lower and "complete" in text_lower

    def test_attachment_has_required_fields(self, slack_formatter, task_complete_event):
        """Should have color, fields, and timestamp in attachment."""
        slack_msg = slack_formatter.format(task_complete_event)
        attachment = slack_msg["attachments"][0]

        assert "color" in attachment
        assert "fields" in attachment
        assert "ts" in attachment or "timestamp" in attachment


class TestColorCoding:
    """Test color coding by severity."""

    def test_info_severity_green_color(self, slack_formatter):
        """Info severity should use green color."""
        event = WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={"verdict": "PASS"}
        )
        slack_msg = slack_formatter.format(event)

        # Green color for success/info
        assert slack_msg["attachments"][0]["color"] in ["good", "#36a64f", "green"]

    def test_warning_severity_yellow_color(self, slack_formatter):
        """Warning severity should use yellow/orange color."""
        event = WebhookEvent(
            event_type="task_complete",
            severity="warning",
            data={"verdict": "FAIL"}
        )
        slack_msg = slack_formatter.format(event)

        # Yellow/orange color for warnings
        assert slack_msg["attachments"][0]["color"] in ["warning", "#ff9900", "yellow", "orange"]

    def test_error_severity_red_color(self, slack_formatter):
        """Error severity should use red color."""
        event = WebhookEvent(
            event_type="task_complete",
            severity="error",
            data={"verdict": "BLOCKED"}
        )
        slack_msg = slack_formatter.format(event)

        # Red color for errors
        assert slack_msg["attachments"][0]["color"] in ["danger", "#ff0000", "red"]


class TestEmojiMapping:
    """Test emoji based on severity and event type."""

    def test_success_emoji_for_info(self, slack_formatter):
        """Info/success events should have success emoji."""
        event = WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={"verdict": "PASS"}
        )
        slack_msg = slack_formatter.format(event)

        # Success emoji in text
        assert any(emoji in slack_msg["text"] for emoji in ["✅", ":white_check_mark:", "✓"])

    def test_warning_emoji_for_warning(self, slack_formatter):
        """Warning events should have warning emoji."""
        event = WebhookEvent(
            event_type="task_complete",
            severity="warning",
            data={"verdict": "FAIL"}
        )
        slack_msg = slack_formatter.format(event)

        # Warning emoji in text
        assert any(emoji in slack_msg["text"] for emoji in ["⚠️", ":warning:", "⚠"])

    def test_error_emoji_for_error(self, slack_formatter):
        """Error events should have error emoji."""
        event = WebhookEvent(
            event_type="task_complete",
            severity="error",
            data={"verdict": "BLOCKED"}
        )
        slack_msg = slack_formatter.format(event)

        # Error emoji in text
        assert any(emoji in slack_msg["text"] for emoji in ["❌", ":x:", "🚫", ":no_entry_sign:"])


class TestFieldFormatting:
    """Test field formatting for task details."""

    def test_task_id_field(self, slack_formatter, task_complete_event):
        """Should include task_id field."""
        slack_msg = slack_formatter.format(task_complete_event)
        fields = slack_msg["attachments"][0]["fields"]

        task_id_field = next((f for f in fields if "task" in f.get("title", "").lower()), None)
        assert task_id_field is not None
        assert "TASK-ABC123" in task_id_field["value"]

    def test_verdict_field(self, slack_formatter, task_complete_event):
        """Should include verdict field."""
        slack_msg = slack_formatter.format(task_complete_event)
        fields = slack_msg["attachments"][0]["fields"]

        verdict_field = next((f for f in fields if "verdict" in f.get("title", "").lower()), None)
        assert verdict_field is not None
        assert "PASS" in verdict_field["value"]

    def test_iterations_field(self, slack_formatter, task_complete_event):
        """Should include iterations field."""
        slack_msg = slack_formatter.format(task_complete_event)
        fields = slack_msg["attachments"][0]["fields"]

        iter_field = next((f for f in fields if "iteration" in f.get("title", "").lower()), None)
        assert iter_field is not None
        assert "5" in str(iter_field["value"])

    def test_files_changed_field(self, slack_formatter, task_complete_event):
        """Should include files changed field."""
        slack_msg = slack_formatter.format(task_complete_event)
        fields = slack_msg["attachments"][0]["fields"]

        files_field = next((f for f in fields if "file" in f.get("title", "").lower()), None)
        assert files_field is not None
        assert "2" in str(files_field["value"])  # 2 files changed


class TestEventTypeHandling:
    """Test handling of different event types."""

    def test_loop_start_event(self, slack_formatter):
        """Should format loop_start event."""
        event = WebhookEvent(
            event_type="loop_start",
            severity="info",
            data={"project": "karematch", "max_iterations": 100}
        )
        slack_msg = slack_formatter.format(event)

        assert "loop_start" in slack_msg["text"].lower() or "started" in slack_msg["text"].lower()
        assert slack_msg["attachments"][0]["color"] in ["good", "#36a64f", "green"]

    def test_task_start_event(self, slack_formatter):
        """Should format task_start event."""
        event = WebhookEvent(
            event_type="task_start",
            severity="info",
            data={"task_id": "TASK-XYZ", "description": "Fix bug"}
        )
        slack_msg = slack_formatter.format(event)

        assert "TASK-XYZ" in str(slack_msg)

    def test_loop_complete_event(self, slack_formatter):
        """Should format loop_complete event."""
        event = WebhookEvent(
            event_type="loop_complete",
            severity="info",
            data={"tasks_processed": 10, "tasks_completed": 8}
        )
        slack_msg = slack_formatter.format(event)

        assert "complete" in slack_msg["text"].lower()
        # Should show stats
        assert "10" in str(slack_msg) or "8" in str(slack_msg)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
