"""
DebateAgent - Base class for perspective-specific council agents.

Each debate agent analyzes the topic from a specific perspective and posts arguments.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional

from orchestration.debate_context import Argument, DebateContext, EvidenceItem, Position
from orchestration.message_bus import Message, MessageBus


class DebateAgent(ABC):
    """
    Base class for debate agents in Council Pattern.

    Each agent:
    1. Analyzes the debate topic from their perspective
    2. Researches evidence
    3. Posts arguments to DebateContext
    4. Reads other agents' arguments (rounds 2+)
    5. Provides rebuttals or synthesis

    Subclasses must implement:
    - perspective: str (e.g., "cost", "integration")
    - analyze(): Research and form initial position
    - rebuttal(): Respond to other agents' arguments
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        perspective: str
    ):
        self.agent_id = agent_id
        self.context = context
        self.message_bus = message_bus
        self.perspective = perspective

        # Register with message bus
        self.message_bus.register_agent(agent_id)

        # Internal state
        self._my_arguments: List[Argument] = []
        self._evidence_collected: List[EvidenceItem] = []

    @abstractmethod
    async def analyze(self) -> Argument:
        """
        Analyze the debate topic from this agent's perspective.

        Called in Round 1. Should:
        1. Research the topic
        2. Collect evidence
        3. Form a position (SUPPORT/OPPOSE/NEUTRAL)
        4. Return initial argument

        Returns:
            Initial argument with position and evidence
        """
        pass

    async def rebuttal(self, other_arguments: List[Argument]) -> Optional[Argument]:
        """
        Respond to other agents' arguments (Round 2+).

        Args:
            other_arguments: Arguments from other agents

        Returns:
            Rebuttal argument, or None if nothing to add
        """
        # Default: no rebuttal (agents can override)
        return None

    async def synthesize(self, all_arguments: List[Argument]) -> str:
        """
        Provide synthesis/final thoughts (Round 3).

        Args:
            all_arguments: All arguments from all agents

        Returns:
            Final synthesis text
        """
        # Default: summarize own position
        return self._default_synthesis()

    async def post_argument(
        self,
        position: Position,
        reasoning: str,
        evidence: List[str],
        confidence: float
    ):
        """
        Post an argument to the debate context.

        Args:
            position: SUPPORT/OPPOSE/NEUTRAL
            reasoning: Core argument text
            evidence: Supporting evidence (URLs, quotes, data)
            confidence: 0.0-1.0
        """
        argument = Argument(
            agent_id=self.agent_id,
            perspective=self.perspective,
            position=position,
            evidence=evidence,
            reasoning=reasoning,
            confidence=confidence,
            round_number=self.context.current_round
        )

        await self.context.post_argument(argument)
        self._my_arguments.append(argument)

    async def add_evidence(self, source: str, content: str):
        """
        Add evidence to shared pool.

        Args:
            source: URL, file path, or description
            content: Relevant excerpt or summary
        """
        evidence = EvidenceItem(
            source=source,
            content=content,
            collected_by=self.agent_id
        )

        await self.context.add_evidence(evidence)
        self._evidence_collected.append(evidence)

    async def send_message(
        self,
        to_agent: Optional[str],
        body: str
    ):
        """
        Send a message to another agent (or broadcast).

        Args:
            to_agent: Target agent ID (None = broadcast)
            body: Message content (can include @mentions)
        """
        message = Message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            body=body
        )
        await self.message_bus.post(message)

    async def read_messages(self, timeout: float = 0.1) -> List[Message]:
        """
        Read pending messages for this agent.

        Args:
            timeout: How long to wait for messages

        Returns:
            List of messages (may be empty)
        """
        return await self.message_bus.get_messages_for(self.agent_id, timeout)

    def get_other_arguments(
        self,
        round_number: Optional[int] = None
    ) -> List[Argument]:
        """
        Get arguments from other agents (excluding self).

        Args:
            round_number: Filter by round (None = all rounds)

        Returns:
            List of arguments from other agents
        """
        all_args = self.context.get_arguments(round_number=round_number)
        return [arg for arg in all_args if arg.agent_id != self.agent_id]

    def get_my_arguments(self) -> List[Argument]:
        """Get this agent's arguments."""
        return list(self._my_arguments)

    def _default_synthesis(self) -> str:
        """Default synthesis: summarize own position."""
        if not self._my_arguments:
            return f"{self.perspective.title()} analysis: No arguments posted."

        latest = self._my_arguments[-1]
        return (
            f"{self.perspective.title()} perspective: {latest.position.value} "
            f"(confidence: {latest.confidence:.2f}). "
            f"Key reasoning: {latest.reasoning[:200]}..."
        )

    def __repr__(self):
        return f"<DebateAgent {self.agent_id} ({self.perspective})>"


class SimpleDebateAgent(DebateAgent):
    """
    Simple debate agent for testing.

    Takes a pre-determined position and reasoning.
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        perspective: str,
        position: Position,
        reasoning: str,
        evidence: List[str],
        confidence: float = 0.7
    ):
        super().__init__(agent_id, context, message_bus, perspective)
        self._position = position
        self._reasoning = reasoning
        self._evidence = evidence
        self._confidence = confidence

    async def analyze(self) -> Argument:
        """Post pre-determined argument."""
        await self.post_argument(
            position=self._position,
            reasoning=self._reasoning,
            evidence=self._evidence,
            confidence=self._confidence
        )
        return self._my_arguments[-1]
