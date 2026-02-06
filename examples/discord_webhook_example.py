#!/usr/bin/env python3
"""
Discord Webhook Integration Example

Demonstrates how to send AI Orchestrator events to Discord.

Usage:
    python examples/discord_webhook_example.py --webhook-url https://discord.com/api/webhooks/XXX

Requirements:
    - Discord webhook URL
    - httpx (pip install httpx)
"""

import asyncio
import argparse
from orchestration.webhooks import WebhookEvent
import httpx


def format_discord_message(event: WebhookEvent) -> dict:
    """Format webhook event for Discord."""
    # Emoji mapping
    emoji = {"info": "✅", "warning": "⚠️", "error": "❌"}

    # Color mapping (Discord uses decimal color codes)
    color = {
        "info": 3066993,    # Green
        "warning": 16776960, # Yellow
        "error": 15158332   # Red
    }

    # Create embed fields based on event type
    fields = []
    if event.event_type == "task_complete":
        fields = [
            {
                "name": "Task ID",
                "value": event.data.get("task_id", "Unknown"),
                "inline": True
            },
            {
                "name": "Verdict",
                "value": event.data.get("verdict", "N/A"),
                "inline": True
            },
            {
                "name": "Iterations",
                "value": str(event.data.get("iterations", 0)),
                "inline": True
            }
        ]

        files_changed = event.data.get("files_changed", [])
        if files_changed:
            fields.append({
                "name": "Files Changed",
                "value": f"{len(files_changed)} files",
                "inline": True
            })

    elif event.event_type == "loop_complete":
        fields = [
            {
                "name": "Tasks Processed",
                "value": str(event.data.get("tasks_processed", 0)),
                "inline": True
            },
            {
                "name": "Tasks Completed",
                "value": str(event.data.get("tasks_completed", 0)),
                "inline": True
            },
            {
                "name": "Tasks Failed",
                "value": str(event.data.get("tasks_failed", 0)),
                "inline": True
            }
        ]

    return {
        "content": f"{emoji[event.severity]} **{event.event_type.replace('_', ' ').title()}**",
        "embeds": [{
            "title": "AI Orchestrator Event",
            "color": color[event.severity],
            "fields": fields,
            "timestamp": event.timestamp,
            "footer": {
                "text": "AI Orchestrator"
            }
        }]
    }


async def send_discord_notification(webhook_url: str, event: WebhookEvent):
    """Send notification to Discord."""
    discord_msg = format_discord_message(event)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            webhook_url,
            json=discord_msg,
            timeout=5.0
        )

        if response.status_code in [200, 204]:
            print(f"✅ Sent {event.event_type} notification to Discord")
        else:
            print(f"❌ Failed to send notification: {response.status_code}")


async def demo_notifications(webhook_url: str):
    """Send demo notifications to Discord."""
    print(f"Sending demo notifications to Discord: {webhook_url}\n")

    # 1. Loop start
    print("1. Sending loop_start notification...")
    await send_discord_notification(
        webhook_url,
        WebhookEvent(
            event_type="loop_start",
            severity="info",
            data={
                "project": "karematch",
                "max_iterations": 100
            }
        )
    )
    await asyncio.sleep(1)

    # 2. Task complete (PASS)
    print("2. Sending task_complete (PASS) notification...")
    await send_discord_notification(
        webhook_url,
        WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={
                "task_id": "TASK-ABC123",
                "verdict": "PASS",
                "iterations": 5,
                "files_changed": ["src/main.py", "tests/test_main.py"]
            }
        )
    )
    await asyncio.sleep(1)

    # 3. Task complete (BLOCKED)
    print("3. Sending task_complete (BLOCKED) notification...")
    await send_discord_notification(
        webhook_url,
        WebhookEvent(
            event_type="task_complete",
            severity="error",
            data={
                "task_id": "TASK-ERROR456",
                "verdict": "BLOCKED",
                "iterations": 15
            }
        )
    )
    await asyncio.sleep(1)

    # 4. Loop complete
    print("4. Sending loop_complete notification...")
    await send_discord_notification(
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
        description="Send demo notifications to Discord"
    )
    parser.add_argument(
        "--webhook-url",
        required=True,
        help="Discord webhook URL"
    )

    args = parser.parse_args()

    # Run demo
    asyncio.run(demo_notifications(args.webhook_url))


if __name__ == "__main__":
    main()
