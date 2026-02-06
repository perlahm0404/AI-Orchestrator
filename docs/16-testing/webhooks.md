# Webhook Notifications

**Status**: ✅ Production Ready
**Version**: v8.0 (Phase 4)
**Related**: KO-aio-005

## Overview

The AI Orchestrator webhook system provides real-time notifications for task lifecycle events during autonomous loop execution. Webhooks are sent to your configured endpoint with rich event data, enabling integration with Slack, Discord, N8N, and other notification platforms.

### Key Features

- **Async HTTP delivery** with httpx
- **Retry logic** with exponential backoff (3 attempts: 1s, 2s delays)
- **Event filtering** by type and severity
- **Configurable timeout** (3s default)
- **Rich formatting** for Slack with color-coded attachments
- **Severity-based alerting** (info, warning, error)

## Event Types

The webhook system sends four event types during autonomous loop execution:

| Event | When Fired | Severity | Description |
|-------|-----------|----------|-------------|
| `loop_start` | Loop begins | info | Autonomous loop initialization |
| `task_start` | Task begins | info | Task picked up for execution |
| `task_complete` | Task finishes | info/warning/error | Task completion with verdict |
| `loop_complete` | Loop ends | info | All tasks processed or max iterations reached |

### Event Payloads

#### loop_start

```json
{
  "event_type": "loop_start",
  "severity": "info",
  "timestamp": "2026-02-05T19:30:00.000Z",
  "data": {
    "project": "karematch",
    "max_iterations": 100,
    "queue_type": "bugs",
    "use_sqlite": true
  }
}
```

#### task_start

```json
{
  "event_type": "task_start",
  "severity": "info",
  "timestamp": "2026-02-05T19:30:15.000Z",
  "data": {
    "task_id": "TASK-ABC123",
    "description": "Fix authentication bug in login flow",
    "file": "src/auth/login.ts",
    "attempts": 0
  }
}
```

#### task_complete

```json
{
  "event_type": "task_complete",
  "severity": "info",
  "timestamp": "2026-02-05T19:35:00.000Z",
  "data": {
    "task_id": "TASK-ABC123",
    "verdict": "PASS",
    "iterations": 5,
    "files_changed": [
      "src/auth/login.ts",
      "tests/auth/test_login.py"
    ]
  }
}
```

**Severity Mapping**:
- `PASS` → `info` (green)
- `FAIL` → `warning` (yellow)
- `BLOCKED` → `error` (red)

#### loop_complete

```json
{
  "event_type": "loop_complete",
  "severity": "info",
  "timestamp": "2026-02-05T20:00:00.000Z",
  "data": {
    "tasks_processed": 25,
    "tasks_completed": 23,
    "tasks_failed": 2
  }
}
```

## Setup and Configuration

### Basic Setup

Enable webhooks by adding the `--webhook-url` flag to your autonomous loop command:

```bash
python autonomous_loop.py \
  --project karematch \
  --use-sqlite \
  --webhook-url https://hooks.example.com/webhook
```

### Event Filtering

Filter events by type or severity using the `WebhookHandler` directly in code:

```python
from orchestration.webhooks import WebhookHandler, WebhookEvent

# Filter by event type (only send task_complete and loop_complete)
handler = WebhookHandler(
    url="https://hooks.example.com/webhook",
    filter_event_types=["task_complete", "loop_complete"]
)

# Filter by minimum severity (only warning and error)
handler = WebhookHandler(
    url="https://hooks.example.com/webhook",
    min_severity="warning"
)

# Send event
event = WebhookEvent(
    event_type="task_complete",
    severity="error",
    data={"task_id": "TASK-123", "verdict": "BLOCKED"}
)
await handler.send(event)
```

## Slack Integration

### Setup

1. Create a Slack incoming webhook:
   - Go to https://api.slack.com/messaging/webhooks
   - Click "Create New App" → "From scratch"
   - Enable "Incoming Webhooks"
   - Click "Add New Webhook to Workspace"
   - Select a channel and authorize
   - Copy the webhook URL

2. Run autonomous loop with Slack webhook:

```bash
python autonomous_loop.py \
  --project karematch \
  --use-sqlite \
  --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Slack Message Formatting

Use the `SlackFormatter` for rich Slack messages with attachments:

```python
from orchestration.formatters.slack import SlackFormatter
from orchestration.webhooks import WebhookEvent
import requests

formatter = SlackFormatter()
event = WebhookEvent(
    event_type="task_complete",
    severity="info",
    data={
        "task_id": "TASK-ABC123",
        "verdict": "PASS",
        "iterations": 5,
        "files_changed": ["src/main.py", "tests/test_main.py"]
    }
)

slack_msg = formatter.format(event)
response = requests.post(
    "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    json=slack_msg
)
```

### Slack Message Format

Slack messages include:
- **Color coding**: Green (info), Yellow (warning), Red (error)
- **Emojis**: ✅ (success), ⚠️ (warning), ❌ (error), 🚀 (loop start), 🏁 (loop complete)
- **Rich fields**: Task ID, verdict, iterations, files changed, etc.
- **Formatted verdicts**: ✅ PASS, ⚠️ FAIL, ❌ BLOCKED

**Example Slack Message**:

```
✅ Task Complete

Task ID: TASK-ABC123
Verdict: ✅ PASS
Iterations: 5
Files Changed: 2

Changed Files:
• src/auth/login.ts
• tests/auth/test_login.py
```

## Discord Integration

### Setup

1. Create a Discord webhook:
   - Open your Discord server
   - Edit Channel → Integrations → Webhooks
   - Click "New Webhook"
   - Copy the webhook URL

2. Use the generic webhook handler (Discord uses similar JSON format):

```python
from orchestration.webhooks import WebhookHandler, WebhookEvent
import asyncio

handler = WebhookHandler(
    url="https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"
)

event = WebhookEvent(
    event_type="task_complete",
    severity="info",
    data={"task_id": "TASK-123", "verdict": "PASS"}
)

asyncio.run(handler.send(event))
```

### Discord Message Example

```python
# Example: Custom Discord formatting
import requests

def format_discord_message(event):
    """Format event for Discord."""
    emoji = {"info": "✅", "warning": "⚠️", "error": "❌"}

    return {
        "content": f"{emoji[event.severity]} **{event.event_type}**",
        "embeds": [{
            "title": "Task Details",
            "description": f"Task ID: {event.data.get('task_id')}",
            "color": {"info": 3066993, "warning": 16776960, "error": 15158332}[event.severity],
            "fields": [
                {"name": "Verdict", "value": event.data.get("verdict", "N/A"), "inline": True},
                {"name": "Iterations", "value": str(event.data.get("iterations", 0)), "inline": True}
            ],
            "timestamp": event.timestamp
        }]
    }

# Send to Discord
discord_msg = format_discord_message(event)
requests.post(
    "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL",
    json=discord_msg
)
```

## N8N Workflow Integration

N8N is a workflow automation tool that can receive webhooks and trigger complex workflows.

### Setup

1. Create an N8N workflow with a Webhook trigger node
2. Copy the webhook URL from the trigger node
3. Use the URL with autonomous loop

### Example N8N Workflow

See `examples/n8n_workflow.json` for a complete workflow that:
- Receives task completion webhooks
- Filters by severity (only errors)
- Sends Slack notification
- Creates Jira ticket for blocked tasks
- Logs to database

```json
{
  "name": "AI Orchestrator Webhook Handler",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "ai-orchestrator",
        "responseMode": "lastNode",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Filter Errors",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.severity}}",
              "operation": "equal",
              "value2": "error"
            }
          ]
        }
      }
    },
    {
      "name": "Send Slack Alert",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#ai-orchestrator-alerts",
        "text": "🚨 Task Blocked: {{$json.data.task_id}}",
        "attachments": [
          {
            "color": "danger",
            "fields": {
              "item": [
                {"short": true, "title": "Task ID", "value": "={{$json.data.task_id}}"},
                {"short": true, "title": "Verdict", "value": "={{$json.data.verdict}}"}
              ]
            }
          }
        ]
      }
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "Filter Errors"}]]},
    "Filter Errors": {"main": [[{"node": "Send Slack Alert"}]]}
  }
}
```

## Retry Logic

The webhook system includes automatic retry with exponential backoff:

- **Max retries**: 3 attempts
- **Backoff delays**: 1s, 2s, 4s (2^n)
- **Timeout**: 3s per attempt (configurable)
- **HTTP success codes**: 200, 201, 202, 204

```python
# Configure retry behavior
handler = WebhookHandler(
    url="https://hooks.example.com/webhook",
    timeout=5.0,      # 5 second timeout
    max_retries=5     # 5 retry attempts
)
```

## Troubleshooting

### Webhooks Not Sending

**Problem**: No webhooks received at endpoint

**Solutions**:
1. Verify `--webhook-url` is set correctly
2. Check endpoint is accessible (test with curl)
3. Check autonomous loop output for webhook initialization message:
   ```
   🔔 Webhook notifications enabled: https://...
   ```
4. Verify SSL certificate is valid (webhooks require HTTPS)

### Webhook Delivery Failures

**Problem**: Webhooks failing to deliver (check logs)

**Solutions**:
1. Check endpoint returns 200-level status code
2. Verify timeout is sufficient (default: 3s)
3. Check network connectivity from orchestrator to endpoint
4. Review retry logic in logs (3 attempts with exponential backoff)

### Slack Messages Not Formatted

**Problem**: Slack shows JSON instead of rich messages

**Solutions**:
1. Use `SlackFormatter` to format events before sending
2. Verify Slack webhook URL is correct (not Discord or other platform)
3. Check Slack webhook is enabled in your workspace
4. Test with simple message first:
   ```bash
   curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test message"}'
   ```

### High Volume Issues

**Problem**: Too many webhook notifications

**Solutions**:
1. Use event filtering to reduce volume:
   ```python
   handler = WebhookHandler(
       url="...",
       filter_event_types=["task_complete", "loop_complete"]
   )
   ```
2. Use severity filtering to only get errors:
   ```python
   handler = WebhookHandler(
       url="...",
       min_severity="error"  # Only errors
   )
   ```
3. Configure Slack notification preferences to reduce noise

### Timeout Errors

**Problem**: Webhook requests timing out

**Solutions**:
1. Increase timeout setting:
   ```python
   handler = WebhookHandler(url="...", timeout=10.0)
   ```
2. Check endpoint response time (should be < 3s)
3. Consider using async webhook endpoints
4. Reduce payload size by filtering unnecessary data

## Advanced Usage

### Custom Webhook Formatters

Create custom formatters for other platforms:

```python
from orchestration.webhooks import WebhookEvent
from typing import Dict, Any

class CustomFormatter:
    """Custom webhook formatter for your platform."""

    def format(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format event for custom platform."""
        return {
            "title": event.event_type,
            "severity": event.severity,
            "timestamp": event.timestamp,
            "details": event.data
        }

# Usage
formatter = CustomFormatter()
formatted = formatter.format(event)
```

### Webhook with Circuit Breaker

Implement circuit breaker pattern for webhook resilience:

```python
from orchestration.circuit_breaker import CircuitBreaker

webhook_breaker = CircuitBreaker(
    max_failures=5,
    timeout=60  # 60 second cooldown
)

async def send_with_breaker(handler, event):
    """Send webhook with circuit breaker protection."""
    if webhook_breaker.is_open():
        print("⚡ Circuit breaker open - skipping webhook")
        return False

    try:
        result = await handler.send(event)
        if result:
            webhook_breaker.record_success()
        else:
            webhook_breaker.record_failure()
        return result
    except Exception as e:
        webhook_breaker.record_failure()
        raise
```

## Examples

See `examples/` directory for complete examples:

- `examples/slack_webhook_example.py` - Slack integration with SlackFormatter
- `examples/discord_webhook_example.py` - Discord integration
- `examples/n8n_workflow.json` - N8N workflow for webhook automation

## API Reference

### WebhookHandler

```python
class WebhookHandler:
    """Async webhook handler with retry logic and event filtering."""

    def __init__(
        self,
        url: str,
        timeout: float = 3.0,
        max_retries: int = 3,
        filter_event_types: Optional[List[str]] = None,
        min_severity: Optional[str] = None
    )

    async def send(self, event: WebhookEvent) -> bool:
        """Send webhook event. Returns True on success."""
```

### WebhookEvent

```python
@dataclass
class WebhookEvent:
    """Webhook event data structure."""

    event_type: str  # "loop_start", "task_start", etc.
    severity: str    # "info", "warning", "error"
    data: Dict[str, Any]
    timestamp: str   # ISO 8601 format

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
```

### SlackFormatter

```python
class SlackFormatter:
    """Format webhook events for Slack incoming webhooks."""

    def format(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format event as Slack message with attachments."""
```

## Related Documentation

- [Autonomous Loop](../14-orchestration/autonomous-loop.md) - Main execution loop
- [Monitoring UI](./monitoring-ui.md) - Real-time WebSocket monitoring
- [Feature Hierarchy](./feature-hierarchy.md) - SQLite work queue with epic→feature→task
- [KO-aio-005](../../knowledge/approved/KO-aio-005.md) - Webhook notifications knowledge object
