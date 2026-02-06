"""
Tests for WebSocket server.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from orchestration.websocket_server import (
    app,
    stream_event,
    event_queue,
    active_connections
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "active_connections" in data
    assert "events_queued" in data


@pytest.mark.asyncio
async def test_stream_event():
    """Test stream_event() adds event to queue."""
    # Clear queue first
    while not event_queue.empty():
        event_queue.get_nowait()

    # Stream event
    await stream_event("test_event", {"foo": "bar"}, severity="info")

    # Verify event in queue
    assert event_queue.qsize() == 1

    # Get event and verify structure
    event = await event_queue.get()
    assert event["type"] == "test_event"
    assert event["severity"] == "info"
    assert event["data"]["foo"] == "bar"
    assert "timestamp" in event


@pytest.mark.asyncio
async def test_stream_event_severity_levels():
    """Test different severity levels."""
    # Clear queue
    while not event_queue.empty():
        event_queue.get_nowait()

    # Test all severity levels
    await stream_event("info_event", {}, severity="info")
    await stream_event("warning_event", {}, severity="warning")
    await stream_event("error_event", {}, severity="error")

    assert event_queue.qsize() == 3

    # Verify severities
    event1 = await event_queue.get()
    assert event1["severity"] == "info"

    event2 = await event_queue.get()
    assert event2["severity"] == "warning"

    event3 = await event_queue.get()
    assert event3["severity"] == "error"


def test_websocket_connection():
    """Test WebSocket connection establishment."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            # Receive connection confirmation
            data = websocket.receive_text()
            message = json.loads(data)

            assert message["type"] == "connection_established"
            assert "timestamp" in message
            assert message["data"]["message"] == "Connected to AI Orchestrator monitoring"


def test_websocket_event_delivery():
    """Test events are queued for delivery to WebSocket clients."""
    # Note: Full end-to-end WebSocket event delivery is tested in integration tests
    # This test verifies the event queuing mechanism works correctly

    # Clear queue
    while not event_queue.empty():
        try:
            event_queue.get_nowait()
        except:
            break

    # Create event and verify structure
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(stream_event("task_start", {
            "task_id": "test-001",
            "description": "Test task"
        }))

        # Verify event was queued
        assert event_queue.qsize() == 1

        # Get event and verify
        event = loop.run_until_complete(event_queue.get())
        assert event["type"] == "task_start"
        assert event["data"]["task_id"] == "test-001"
        assert event["data"]["description"] == "Test task"
    finally:
        loop.close()


def test_cors_headers(client):
    """Test CORS headers are set correctly."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )

    assert response.status_code == 200
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_multiple_events_queued():
    """Test multiple events are queued correctly."""
    # Clear queue
    while not event_queue.empty():
        event_queue.get_nowait()

    # Queue multiple events
    for i in range(5):
        await stream_event(f"event_{i}", {"index": i})

    assert event_queue.qsize() == 5

    # Verify events in order
    for i in range(5):
        event = await event_queue.get()
        assert event["type"] == f"event_{i}"
        assert event["data"]["index"] == i


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
