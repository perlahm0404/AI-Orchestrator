"""
SlackFormatter: Transform generic webhook events to Slack message format.

Features:
- Slack attachments with color coding
- Emoji based on severity
- Field formatting for task details
- Supports all event types (loop_start, task_start, task_complete, loop_complete)

Reference: KO-aio-005 (Webhook notifications)
"""

from typing import Dict, Any, List
from orchestration.webhooks import WebhookEvent


class SlackFormatter:
    """
    Formats webhook events for Slack incoming webhooks.

    Example:
        formatter = SlackFormatter()
        event = WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={"task_id": "TASK-123", "verdict": "PASS"}
        )
        slack_message = formatter.format(event)

        # Send to Slack
        requests.post(webhook_url, json=slack_message)
    """

    # Color mapping by severity
    SEVERITY_COLORS = {
        "info": "good",      # Green
        "warning": "warning", # Yellow/Orange
        "error": "danger"    # Red
    }

    # Emoji mapping by severity
    SEVERITY_EMOJIS = {
        "info": "✅",
        "warning": "⚠️",
        "error": "❌"
    }

    # Event type emojis
    EVENT_EMOJIS = {
        "loop_start": "🚀",
        "task_start": "▶️",
        "task_complete": None,  # Use severity emoji
        "loop_complete": "🏁"
    }

    def format(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Format webhook event as Slack message.

        Args:
            event: Webhook event to format

        Returns:
            Slack message dict with text and attachments
        """
        # Get emoji for event
        emoji = self._get_emoji(event)

        # Create main message text
        text = f"{emoji} *{self._get_event_title(event)}*"

        # Create attachment with details
        attachment = {
            "color": self.SEVERITY_COLORS.get(event.severity, "good"),
            "fields": self._create_fields(event),
            "ts": event.timestamp,
            "footer": "AI Orchestrator",
            "footer_icon": "https://www.anthropic.com/images/icons/apple-touch-icon.png"
        }

        return {
            "text": text,
            "attachments": [attachment]
        }

    def _get_emoji(self, event: WebhookEvent) -> str:
        """Get emoji for event."""
        # Event-specific emoji takes precedence
        event_emoji = self.EVENT_EMOJIS.get(event.event_type)
        if event_emoji:
            return event_emoji

        # Otherwise use severity emoji
        return self.SEVERITY_EMOJIS.get(event.severity, "ℹ️")

    def _get_event_title(self, event: WebhookEvent) -> str:
        """Get human-readable event title."""
        titles = {
            "loop_start": "Loop Started",
            "task_start": "Task Started",
            "task_complete": "Task Complete",
            "loop_complete": "Loop Complete"
        }
        return titles.get(event.event_type, event.event_type.replace("_", " ").title())

    def _create_fields(self, event: WebhookEvent) -> List[Dict[str, Any]]:
        """Create Slack attachment fields from event data."""
        fields = []

        # Event type specific fields
        if event.event_type == "loop_start":
            fields.extend(self._loop_start_fields(event))
        elif event.event_type == "task_start":
            fields.extend(self._task_start_fields(event))
        elif event.event_type == "task_complete":
            fields.extend(self._task_complete_fields(event))
        elif event.event_type == "loop_complete":
            fields.extend(self._loop_complete_fields(event))

        return fields

    def _loop_start_fields(self, event: WebhookEvent) -> List[Dict[str, Any]]:
        """Create fields for loop_start event."""
        data = event.data
        return [
            {
                "title": "Project",
                "value": data.get("project", "Unknown"),
                "short": True
            },
            {
                "title": "Max Iterations",
                "value": str(data.get("max_iterations", "N/A")),
                "short": True
            },
            {
                "title": "Queue Type",
                "value": data.get("queue_type", "Unknown"),
                "short": True
            },
            {
                "title": "Mode",
                "value": "SQLite" if data.get("use_sqlite") else "JSON",
                "short": True
            }
        ]

    def _task_start_fields(self, event: WebhookEvent) -> List[Dict[str, Any]]:
        """Create fields for task_start event."""
        data = event.data
        return [
            {
                "title": "Task ID",
                "value": data.get("task_id", "Unknown"),
                "short": True
            },
            {
                "title": "Attempts",
                "value": str(data.get("attempts", 0)),
                "short": True
            },
            {
                "title": "Description",
                "value": data.get("description", "N/A"),
                "short": False
            },
            {
                "title": "File",
                "value": f"`{data.get('file', 'N/A')}`",
                "short": False
            }
        ]

    def _task_complete_fields(self, event: WebhookEvent) -> List[Dict[str, Any]]:
        """Create fields for task_complete event."""
        data = event.data
        files_changed = data.get("files_changed", [])

        fields = [
            {
                "title": "Task ID",
                "value": data.get("task_id", "Unknown"),
                "short": True
            },
            {
                "title": "Verdict",
                "value": self._format_verdict(data.get("verdict", "UNKNOWN")),
                "short": True
            },
            {
                "title": "Iterations",
                "value": str(data.get("iterations", "N/A")),
                "short": True
            },
            {
                "title": "Files Changed",
                "value": str(len(files_changed)) if files_changed else "0",
                "short": True
            }
        ]

        # Add file list if present
        if files_changed:
            files_list = "\n".join([f"• `{f}`" for f in files_changed[:5]])
            if len(files_changed) > 5:
                files_list += f"\n• ... and {len(files_changed) - 5} more"
            fields.append({
                "title": "Changed Files",
                "value": files_list,
                "short": False
            })

        return fields

    def _loop_complete_fields(self, event: WebhookEvent) -> List[Dict[str, Any]]:
        """Create fields for loop_complete event."""
        data = event.data
        return [
            {
                "title": "Tasks Processed",
                "value": str(data.get("tasks_processed", 0)),
                "short": True
            },
            {
                "title": "Tasks Completed",
                "value": str(data.get("tasks_completed", 0)),
                "short": True
            },
            {
                "title": "Tasks Failed",
                "value": str(data.get("tasks_failed", 0)),
                "short": True
            },
            {
                "title": "Success Rate",
                "value": self._calculate_success_rate(
                    data.get("tasks_completed", 0),
                    data.get("tasks_processed", 0)
                ),
                "short": True
            }
        ]

    def _format_verdict(self, verdict: str) -> str:
        """Format verdict with emoji."""
        verdict_emojis = {
            "PASS": "✅ PASS",
            "FAIL": "⚠️ FAIL",
            "BLOCKED": "❌ BLOCKED"
        }
        return verdict_emojis.get(verdict, verdict)

    def _calculate_success_rate(self, completed: int, total: int) -> str:
        """Calculate success rate percentage."""
        if total == 0:
            return "N/A"
        rate = (completed / total) * 100
        return f"{rate:.1f}%"
