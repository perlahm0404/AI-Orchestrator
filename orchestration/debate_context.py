"""
DebateContext - Shared state for council debates.

Thread-safe storage for question, evidence, arguments, and debate metadata.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class Position(Enum):
    """Agent's position on the debate topic."""
    SUPPORT = "SUPPORT"      # Recommends adoption/action
    OPPOSE = "OPPOSE"        # Recommends against
    NEUTRAL = "NEUTRAL"      # No clear recommendation, presents trade-offs


@dataclass
class Argument:
    """Single argument from a debate agent."""
    agent_id: str
    perspective: str  # "cost", "integration", "performance", etc.
    position: Position
    evidence: List[str]  # Supporting evidence (URLs, quotes, data)
    reasoning: str       # Core argument
    confidence: float    # 0.0-1.0
    round_number: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "perspective": self.perspective,
            "position": self.position.value,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "round_number": self.round_number,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EvidenceItem:
    """Single piece of evidence collected during research."""
    source: str          # URL, file path, or "internal_knowledge"
    content: str         # Relevant excerpt or summary
    collected_by: str    # Agent that found this
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "content": self.content,
            "collected_by": self.collected_by,
            "timestamp": self.timestamp.isoformat()
        }


class DebateContext:
    """
    Thread-safe shared state for council debates.

    All debate agents read from this context during analysis.
    Only CouncilOrchestrator writes to it (except argument posting).

    Usage:
        context = DebateContext(
            topic="Should we adopt LlamaIndex?",
            perspectives=["cost", "integration", "performance"]
        )
        await context.post_argument(argument)
        args = context.get_arguments(round_number=1)
    """

    def __init__(
        self,
        topic: str,
        perspectives: List[str],
        council_id: str,
        metadata: Optional[Dict] = None
    ):
        # Core debate question
        self.topic = topic
        self.perspectives = perspectives
        self.council_id = council_id
        self.metadata = metadata or {}

        # Debate state
        self._current_round = 1
        self._arguments: List[Argument] = []
        self._evidence: List[EvidenceItem] = []

        # Thread safety
        self._lock = asyncio.Lock()

        # Timestamps
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    async def post_argument(self, argument: Argument):
        """Post an argument to the debate (thread-safe)."""
        async with self._lock:
            self._arguments.append(argument)

    async def add_evidence(self, evidence: EvidenceItem):
        """Add evidence to the shared pool (thread-safe)."""
        async with self._lock:
            self._evidence.append(evidence)

    def get_arguments(
        self,
        round_number: Optional[int] = None,
        perspective: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[Argument]:
        """
        Get arguments matching filters.

        Args:
            round_number: Filter by round (None = all rounds)
            perspective: Filter by perspective (None = all perspectives)
            agent_id: Filter by agent (None = all agents)

        Returns:
            List of matching arguments (read-only)
        """
        results = list(self._arguments)

        if round_number is not None:
            results = [a for a in results if a.round_number == round_number]

        if perspective is not None:
            results = [a for a in results if a.perspective == perspective]

        if agent_id is not None:
            results = [a for a in results if a.agent_id == agent_id]

        return results

    def get_evidence(self, collected_by: Optional[str] = None) -> List[EvidenceItem]:
        """Get evidence items (optionally filtered by collector)."""
        if collected_by:
            return [e for e in self._evidence if e.collected_by == collected_by]
        return list(self._evidence)

    async def advance_round(self):
        """Advance to next debate round (orchestrator only)."""
        async with self._lock:
            self._current_round += 1

    @property
    def current_round(self) -> int:
        """Get current debate round (thread-safe read)."""
        return self._current_round

    async def mark_started(self):
        """Mark debate as started."""
        async with self._lock:
            if not self.started_at:
                self.started_at = datetime.utcnow()

    async def mark_completed(self):
        """Mark debate as completed."""
        async with self._lock:
            if not self.completed_at:
                self.completed_at = datetime.utcnow()

    def get_duration_seconds(self) -> Optional[float]:
        """Get debate duration in seconds (None if not completed)."""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def get_summary(self) -> dict:
        """Get debate summary statistics."""
        position_counts = {
            Position.SUPPORT: 0,
            Position.OPPOSE: 0,
            Position.NEUTRAL: 0
        }

        for arg in self._arguments:
            position_counts[arg.position] += 1

        return {
            "council_id": self.council_id,
            "topic": self.topic,
            "perspectives": self.perspectives,
            "current_round": self._current_round,
            "total_arguments": len(self._arguments),
            "total_evidence": len(self._evidence),
            "position_distribution": {
                pos.value: count for pos, count in position_counts.items()
            },
            "duration_seconds": self.get_duration_seconds(),
            "status": self._get_status()
        }

    def _get_status(self) -> str:
        """Get debate status."""
        if self.completed_at:
            return "COMPLETED"
        elif self.started_at:
            return "IN_PROGRESS"
        else:
            return "PENDING"

    def to_dict(self) -> dict:
        """Convert entire context to dictionary (for serialization)."""
        return {
            "council_id": self.council_id,
            "topic": self.topic,
            "perspectives": self.perspectives,
            "metadata": self.metadata,
            "current_round": self._current_round,
            "arguments": [arg.to_dict() for arg in self._arguments],
            "evidence": [ev.to_dict() for ev in self._evidence],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "summary": self.get_summary()
        }
