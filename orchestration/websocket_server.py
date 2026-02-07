"""
WebSocket server for real-time autonomous loop monitoring.

Provides live updates to React dashboard showing:
- Task start/complete events
- Ralph verdict results
- Agent iteration counts
- Full execution history
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from typing import Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Orchestrator Monitoring")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API router for dashboard data
from orchestration.api import api as api_router
app.include_router(api_router)

# Event queue (shared between autonomous loop and WebSocket clients)
event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

# Active WebSocket connections
active_connections: list[WebSocket] = []


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_connections": len(active_connections),
        "events_queued": event_queue.qsize()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time event streaming.

    Accepts connections from React dashboard and streams events
    from the autonomous loop (task starts, completions, Ralph verdicts, etc.).
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"✅ WebSocket client connected (total: {len(active_connections)})")

    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Connected to AI Orchestrator monitoring",
                "active_connections": len(active_connections)
            }
        }))

        # Main event loop - wait for events and send to client
        while True:
            # Wait for event from autonomous loop
            event = await event_queue.get()

            # Send to all connected clients
            for connection in active_connections:
                try:
                    await connection.send_text(json.dumps(event))
                except Exception as e:
                    logger.error(f"Failed to send event to client: {e}")

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket client disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        # Clean up connection
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"Connections remaining: {len(active_connections)}")


async def stream_event(
    event_type: str,
    data: dict[str, Any],
    severity: str = "info"
) -> None:
    """
    Stream event to all connected WebSocket clients.

    Called by autonomous_loop.py to send events to monitoring dashboard.

    Args:
        event_type: Type of event (task_start, task_complete, ralph_verdict, etc.)
        data: Event payload (task_id, description, verdict, etc.)
        severity: Event severity level (info, warning, error)

    Example:
        await stream_event("task_start", {
            "task_id": "task-001",
            "description": "Fix TypeScript errors",
            "priority": 0
        })
    """
    event = {
        "type": event_type,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    # Add to event queue
    await event_queue.put(event)
    logger.debug(f"Event queued: {event_type}")


async def broadcast_event(event: dict[str, Any]) -> None:
    """
    Broadcast event to all connected WebSocket clients immediately.

    Alternative to stream_event() when you already have a formatted event dict.
    """
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(event))
        except Exception as e:
            logger.error(f"Failed to broadcast to client: {e}")


def get_active_connections_count() -> int:
    """Get number of active WebSocket connections."""
    return len(active_connections)


def get_event_queue_size() -> int:
    """Get number of events waiting in queue."""
    return event_queue.qsize()


# Server startup/shutdown hooks
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize server on startup."""
    logger.info("🚀 WebSocket server starting...")
    logger.info("Listening for connections at ws://localhost:8080/ws")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up on server shutdown."""
    logger.info("🛑 WebSocket server shutting down...")

    # Close all active connections
    for connection in active_connections:
        try:
            await connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    active_connections.clear()
    logger.info("All connections closed")


if __name__ == "__main__":
    """
    Run WebSocket server standalone for testing.

    In production, this is started by autonomous_loop.py.
    """
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
