"""
DebateManifest - JSONL audit logging for council debates.

Records all events during a debate for accountability and replay.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class DebateManifest:
    """
    JSONL audit logger for council debates.

    Each debate gets its own manifest file:
        .aibrain/councils/{COUNCIL_ID}/manifest.jsonl

    Events logged:
    - council_init: Debate started
    - agent_spawn: Agent created
    - round_start: New debate round
    - argument_posted: Agent posted argument
    - message: Inter-agent message
    - evidence_added: Research evidence collected
    - synthesis: Final recommendation
    - adr_created: ADR generated

    Usage:
        manifest = DebateManifest(council_id="COUNCIL-20260130-001")
        manifest.log_event("council_init", {"topic": "...", "perspectives": [...]})
        manifest.log_argument("cost_analyst", "SUPPORT", 0.8)
    """

    def __init__(self, council_id: str, manifest_dir: Optional[Path] = None):
        self.council_id = council_id

        # Default to .aibrain/councils/{council_id}/
        if manifest_dir is None:
            manifest_dir = Path(".aibrain/councils") / council_id

        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

        self.manifest_path = self.manifest_dir / "manifest.jsonl"

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """
        Log a debate event.

        Args:
            event_type: Type of event (council_init, agent_spawn, etc.)
            data: Event-specific data
        """
        entry = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "council_id": self.council_id,
            **data
        }

        with open(self.manifest_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_council_init(self, topic: str, perspectives: List[str], metadata: Optional[Dict] = None):
        """Log debate initialization."""
        self.log_event("council_init", {
            "topic": topic,
            "perspectives": perspectives,
            "metadata": metadata or {}
        })

    def log_agent_spawn(self, agent_id: str, agent_type: str, perspective: str):
        """Log agent creation."""
        self.log_event("agent_spawn", {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "perspective": perspective
        })

    def log_round_start(self, round_number: int):
        """Log debate round start."""
        self.log_event("round_start", {
            "round_number": round_number
        })

    def log_argument(
        self,
        agent_id: str,
        perspective: str,
        position: str,
        confidence: float,
        reasoning: str
    ):
        """Log argument posted by agent."""
        self.log_event("argument_posted", {
            "agent_id": agent_id,
            "perspective": perspective,
            "position": position,
            "confidence": confidence,
            "reasoning_preview": reasoning[:200]  # First 200 chars
        })

    def log_message(self, from_agent: str, to_agent: Optional[str], body: str):
        """Log inter-agent message."""
        self.log_event("message", {
            "from_agent": from_agent,
            "to_agent": to_agent or "ALL",
            "body_preview": body[:200]
        })

    def log_evidence(self, agent_id: str, source: str, content_preview: str):
        """Log evidence collection."""
        self.log_event("evidence_added", {
            "collected_by": agent_id,
            "source": source,
            "content_preview": content_preview[:200]
        })

    def log_synthesis(
        self,
        recommendation: str,
        confidence: float,
        vote_breakdown: Dict[str, int]
    ):
        """Log final synthesis."""
        self.log_event("synthesis", {
            "recommendation": recommendation,
            "confidence": confidence,
            "vote_breakdown": vote_breakdown
        })

    def log_adr_created(self, adr_path: str, approved: bool):
        """Log ADR generation."""
        self.log_event("adr_created", {
            "adr_path": adr_path,
            "human_approved": approved
        })

    def get_events(self, event_type: Optional[str] = None) -> List[Dict]:
        """
        Read events from manifest.

        Args:
            event_type: Filter by event type (None = all events)

        Returns:
            List of events in chronological order
        """
        if not self.manifest_path.exists():
            return []

        events = []
        with open(self.manifest_path) as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if event_type is None or event.get("event") == event_type:
                        events.append(event)

        return events

    def get_timeline(self) -> str:
        """
        Generate human-readable timeline of debate.

        Returns:
            Formatted timeline string
        """
        events = self.get_events()
        if not events:
            return "No events recorded."

        lines = [f"Debate Timeline: {self.council_id}", "=" * 60]

        for event in events:
            timestamp = event.get("timestamp", "")
            event_type = event.get("event", "unknown")

            # Format based on event type
            if event_type == "council_init":
                lines.append(f"[{timestamp}] INIT: {event.get('topic', 'N/A')}")
                lines.append(f"  Perspectives: {', '.join(event.get('perspectives', []))}")

            elif event_type == "agent_spawn":
                lines.append(f"[{timestamp}] SPAWN: {event.get('agent_id', 'N/A')} ({event.get('perspective', 'N/A')})")

            elif event_type == "round_start":
                lines.append(f"[{timestamp}] ROUND {event.get('round_number', '?')} START")

            elif event_type == "argument_posted":
                lines.append(f"[{timestamp}] ARGUMENT: {event.get('agent_id', 'N/A')} - {event.get('position', 'N/A')} (conf: {event.get('confidence', 0):.2f})")

            elif event_type == "synthesis":
                lines.append(f"[{timestamp}] SYNTHESIS: {event.get('recommendation', 'N/A')} (conf: {event.get('confidence', 0):.2f})")

            elif event_type == "adr_created":
                lines.append(f"[{timestamp}] ADR: {event.get('adr_path', 'N/A')} (approved: {event.get('human_approved', False)})")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get manifest statistics."""
        events = self.get_events()

        event_counts = {}
        for event in events:
            event_type = event.get("event", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "council_id": self.council_id,
            "total_events": len(events),
            "event_counts": event_counts,
            "manifest_path": str(self.manifest_path)
        }
