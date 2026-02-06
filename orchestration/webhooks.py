"""
WebhookHandler: Async HTTP webhook delivery with retry logic and filtering.

Features:
- Async HTTP POST with httpx
- Exponential backoff retry (3 attempts by default)
- Event type and severity filtering
- Configurable timeout (3s default)
- Support for severity levels: info, warning, error

Reference: KO-aio-005 (Webhook notifications)
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx


@dataclass
class WebhookEvent:
    """
    Webhook event data structure.

    Attributes:
        event_type: Type of event (e.g., "task_complete", "loop_start")
        severity: Severity level ("info", "warning", "error")
        data: Event payload data
        timestamp: ISO timestamp (auto-generated)
    """
    event_type: str
    severity: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type,
            "severity": self.severity,
            "data": self.data,
            "timestamp": self.timestamp
        }


class WebhookHandler:
    """
    Async webhook handler with retry logic and event filtering.

    Example:
        handler = WebhookHandler(
            url="https://hooks.slack.com/services/XXX",
            filter_event_types=["task_complete", "loop_complete"],
            min_severity="warning"
        )

        event = WebhookEvent(
            event_type="task_complete",
            severity="info",
            data={"task_id": "TASK-123", "status": "completed"}
        )

        success = await handler.send(event)
    """

    # Severity levels (in order of importance)
    SEVERITY_LEVELS = ["info", "warning", "error"]

    def __init__(
        self,
        url: str,
        timeout: float = 3.0,
        max_retries: int = 3,
        filter_event_types: Optional[List[str]] = None,
        min_severity: Optional[str] = None
    ):
        """
        Initialize webhook handler.

        Args:
            url: Webhook endpoint URL
            timeout: Request timeout in seconds (default: 3.0)
            max_retries: Maximum retry attempts (default: 3)
            filter_event_types: Only send these event types (None = all)
            min_severity: Minimum severity level to send (None = all)
        """
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries
        self.filter_event_types = filter_event_types
        self.min_severity = min_severity

    def _should_send(self, event: WebhookEvent) -> bool:
        """
        Check if event should be sent based on filters.

        Args:
            event: Event to check

        Returns:
            True if event passes filters, False otherwise
        """
        # Filter by event type
        if self.filter_event_types and event.event_type not in self.filter_event_types:
            return False

        # Filter by severity level
        if self.min_severity:
            try:
                min_level = self.SEVERITY_LEVELS.index(self.min_severity)
                event_level = self.SEVERITY_LEVELS.index(event.severity)
                if event_level < min_level:
                    return False
            except ValueError:
                # Invalid severity level - allow it through
                pass

        return True

    async def send(self, event: WebhookEvent) -> bool:
        """
        Send webhook event with retry logic.

        Args:
            event: Event to send

        Returns:
            True if sent successfully (or filtered), False if all retries failed
        """
        # Check filters
        if not self._should_send(event):
            # Event filtered - return True (not an error)
            return True

        # Retry with exponential backoff
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.url,
                        json=event.to_dict(),
                        timeout=self.timeout
                    )

                    if response.status_code in [200, 201, 202, 204]:
                        # Success
                        return True
                    else:
                        # Non-success status code - will retry
                        if attempt < self.max_retries - 1:
                            # Exponential backoff: 1s, 2s, 4s
                            await asyncio.sleep(2 ** attempt)

            except Exception as e:
                # Network error, timeout, etc. - will retry
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    await asyncio.sleep(2 ** attempt)
                else:
                    # Last attempt failed
                    return False

        # All retries exhausted
        return False
