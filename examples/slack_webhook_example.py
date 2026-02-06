#!/usr/bin/env python3
"""
Slack Webhook Integration Example

Demonstrates how to send AI Orchestrator events to Slack with rich formatting.

Usage:
    python examples/slack_webhook_example.py --webhook-url https://hooks.slack.com/services/XXX

Requirements:
    - Slack incoming webhook URL
    - httpx (pip install httpx)
"""

import asyncio
import argparse
from orchestration.webhooks import WebhookHandler, WebhookEvent
from orchestration.formatters.slack import SlackFormatter
import httpx


async def send_slack_notification(webhook_url: str, event: WebhookEvent):
    """Send formatted Slack notification."""
    # Format event for Slack
    formatter = SlackFormatter()
    slack_msg = formatter.format(event)

    # Send to Slack
    async with httpx.AsyncClient() as client:
        response = await client.post(
            webhook_url,
            json=slack_msg,
            timeout=5.0
        )

        if response.status_code == 200:
            print(f"✅ Sent {event.event_type} notification to Slack")
        else:
            print(f"❌ Failed to send notification: {response.status_code}")


async def demo_notifications(webhook_url: str):
    """Send demo notifications to Slack."""
    print(f"Sending demo notifications to: {webhook_url}\n")

    # 1. Loop start notification
    print("1. Sending loop_start notification...")
    await send_slack_notification(
        webhook_url,
        WebhookEvent(
            event_type="loop_start",
            severity="info",
            data={
                "project": "karematch",
                "max_iterations": 100,
                "queue_type": "bugs",
                "use_sqlite": True
            }
        )
    )
    await asyncio.sleep(1)

    # 2. Task start notification
    print("2. Sending task_start notification...")
    await send_slack_notification(
        webhook_url,
        WebhookEvent(
            event_type="task_start",
            severity="info",
            data={
                "task_id": "TASK-ABC123",
                "description": "Fix authentication bug in login flow",
                "file": "src/auth/login.ts",
                "attempts": 0
            }
        )
    )
    await asyncio.sleep(1)

    # 3. Task complete (PASS) notification
    print("3. Sending task_complete (PASS) notification...")
    await send_slack_notification(
        webhook_url,
        WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={
                "task_id": "TASK-ABC123",
                "verdict": "PASS",
                "iterations": 5,
                "files_changed": [
                    "src/auth/login.ts",
                    "tests/auth/test_login.py"
                ]
            }
        )
    )
    await asyncio.sleep(1)

    # 4. Task complete (FAIL) notification
    print("4. Sending task_complete (FAIL) notification...")
    await send_slack_notification(
        webhook_url,
        WebhookEvent(
            event_type="task_complete",
            severity="warning",
            data={
                "task_id": "TASK-XYZ789",
                "verdict": "FAIL",
                "iterations": 10,
                "files_changed": ["src/utils/helper.ts"]
            }
        )
    )
    await asyncio.sleep(1)

    # 5. Task complete (BLOCKED) notification
    print("5. Sending task_complete (BLOCKED) notification...")
    await send_slack_notification(
        webhook_url,
        WebhookEvent(
            event_type="task_complete",
            severity="error",
            data={
                "task_id": "TASK-ERROR456",
                "verdict": "BLOCKED",
                "iterations": 15,
                "files_changed": []
            }
        )
    )
    await asyncio.sleep(1)

    # 6. Loop complete notification
    print("6. Sending loop_complete notification...")
    await send_slack_notification(
        webhook_url,
        WebhookEvent(
            event_type="loop_complete",
            severity="info",
            data={
                "tasks_processed": 25,
                "tasks_completed": 23,
                "tasks_failed": 2
            }
        )
    )

    print("\n✅ All demo notifications sent!")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Send demo notifications to Slack"
    )
    parser.add_argument(
        "--webhook-url",
        required=True,
        help="Slack incoming webhook URL"
    )

    args = parser.parse_args()

    # Run demo
    asyncio.run(demo_notifications(args.webhook_url))


if __name__ == "__main__":
    main()
