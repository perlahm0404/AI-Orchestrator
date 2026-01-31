"""
MessageBus - Async inter-agent communication for Council Pattern.

Handles message routing, @mentions, and audit logging for debate agents.
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


@dataclass
class Message:
    """Single message between debate agents."""
    from_agent: str
    to_agent: Optional[str]  # None = broadcast to all
    body: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default="")

    def __post_init__(self):
        if not self.message_id:
            self.message_id = f"MSG-{self.timestamp.strftime('%Y%m%d%H%M%S')}-{self.from_agent[:8]}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "body": self.body,
            "timestamp": self.timestamp.isoformat()
        }


class MessageBus:
    """
    Async message bus for debate agent communication.

    Features:
    - Thread-safe message delivery
    - @mention routing (e.g., "@cost_analyst your analysis missed X")
    - Broadcast messages (to_agent=None)
    - Message history for audit trails

    Usage:
        bus = MessageBus()
        await bus.post(Message(from_agent="integration", to_agent="cost", body="..."))
        messages = await bus.get_messages_for(agent_id="cost")
    """

    def __init__(self):
        # Agent-specific message queues
        self._queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

        # Complete message history (for audit/replay)
        self._history: List[Message] = []

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Registered agents (for broadcast validation)
        self._agents: set = set()

    def register_agent(self, agent_id: str):
        """Register an agent with the message bus."""
        self._agents.add(agent_id)
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()

    def unregister_agent(self, agent_id: str):
        """Unregister an agent (cleanup)."""
        if agent_id in self._agents:
            self._agents.remove(agent_id)

    async def post(self, message: Message):
        """
        Post a message to the bus.

        Routing logic:
        - If to_agent is specified, deliver to that agent only
        - If to_agent is None, broadcast to all registered agents
        - Also check body for @mentions and route accordingly
        """
        async with self._lock:
            # Add to history
            self._history.append(message)

            # Extract @mentions from message body
            mentions = self._extract_mentions(message.body)

            # Determine recipients
            recipients = set()
            if message.to_agent:
                recipients.add(message.to_agent)
            else:
                # Broadcast to all agents except sender
                recipients = self._agents - {message.from_agent}

            # Add @mentioned agents
            recipients.update(mentions)

            # Deliver to all recipients
            for agent_id in recipients:
                if agent_id in self._queues:
                    await self._queues[agent_id].put(message)

    async def get_messages_for(self, agent_id: str, timeout: float = 0.1) -> List[Message]:
        """
        Get all pending messages for an agent (non-blocking).

        Args:
            agent_id: Agent to fetch messages for
            timeout: How long to wait for messages (default 0.1s)

        Returns:
            List of messages (may be empty)
        """
        if agent_id not in self._queues:
            return []

        messages = []
        queue = self._queues[agent_id]

        try:
            # Get first message (may wait up to timeout)
            msg = await asyncio.wait_for(queue.get(), timeout=timeout)
            messages.append(msg)

            # Drain any additional messages (non-blocking)
            while not queue.empty():
                try:
                    msg = queue.get_nowait()
                    messages.append(msg)
                except asyncio.QueueEmpty:
                    break
        except asyncio.TimeoutError:
            pass

        return messages

    def get_history(self, since: Optional[datetime] = None) -> List[Message]:
        """
        Get message history.

        Args:
            since: Only return messages after this timestamp

        Returns:
            List of messages in chronological order
        """
        if since:
            return [m for m in self._history if m.timestamp >= since]
        return list(self._history)

    def get_conversation(self, agent1: str, agent2: str) -> List[Message]:
        """Get all messages between two agents."""
        return [
            m for m in self._history
            if (m.from_agent == agent1 and m.to_agent == agent2) or
               (m.from_agent == agent2 and m.to_agent == agent1)
        ]

    def clear(self):
        """Clear all messages and queues (for testing)."""
        self._history.clear()
        for queue in self._queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

    @staticmethod
    def _extract_mentions(text: str) -> set:
        """
        Extract @mentions from message body.

        Examples:
            "@cost_analyst your analysis missed X" -> {"cost_analyst"}
            "cc @integration @security" -> {"integration", "security"}
        """
        mention_pattern = r'@(\w+)'
        return set(re.findall(mention_pattern, text))

    def get_stats(self) -> dict:
        """Get message bus statistics."""
        return {
            "total_messages": len(self._history),
            "registered_agents": len(self._agents),
            "messages_per_agent": {
                agent: sum(1 for m in self._history if m.from_agent == agent)
                for agent in self._agents
            }
        }
