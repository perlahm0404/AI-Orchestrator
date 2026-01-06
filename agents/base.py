"""
Base Agent Protocol

All agents inherit from this base class which enforces:
- Stateless execution (no persistent memory)
- Contract compliance (check before every action)
- Evidence production (capture before/after state)
- Graceful halt on governance violations

Implementation: Phase 0
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Abstract base class for all AI Orchestrator agents.

    Lifecycle:
    1. __init__: Load contract, connect to services
    2. execute(): Main entry point, runs the agent workflow
    3. checkpoint(): Save state for resume capability
    4. halt(): Graceful shutdown on violation or completion

    Invariants:
    - No state persists between execute() calls
    - All memory comes from external artifacts (DB, files)
    - Every action is logged to audit_log
    - Contract is checked before every write action
    """

    @abstractmethod
    def execute(self, task_id: str) -> dict[str, Any]:
        """
        Execute the agent's workflow for a given task.

        Args:
            task_id: The task to work on (e.g., "TASK-123")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - evidence: Dict of evidence artifacts
            - verdict: Ralph verification result
        """
        pass

    @abstractmethod
    def checkpoint(self) -> dict[str, Any]:
        """
        Capture current state for session resume.

        Returns:
            Checkpoint dict that can reconstruct agent state
        """
        pass

    @abstractmethod
    def halt(self, reason: str) -> None:
        """
        Gracefully stop execution.

        Args:
            reason: Why the agent is halting
        """
        pass
