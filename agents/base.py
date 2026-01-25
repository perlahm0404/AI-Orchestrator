"""
Base Agent Protocol

All agents inherit from this base class which enforces:
- Stateless execution (no persistent memory)
- Contract compliance (check before every action)
- Evidence production (capture before/after state)
- Graceful halt on governance violations
- Session reflection (handoff generation)
- Iteration loop with completion signals (Ralph-Wiggum pattern)

Implementation: Phase 0, v5 enhancements
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from orchestration.reflection import SessionResult


@dataclass
class AgentConfig:
    """
    Configuration for agent behavior and limits.

    Fields are typically loaded from autonomy contracts and app adapters.
    """
    project_name: str
    agent_name: str
    expected_completion_signal: Optional[str] = None  # e.g., "COMPLETE", "DONE"
    max_iterations: int = 10  # Default, should be overridden by contract
    max_retries: int = 3  # Backward compatibility with existing agents
    use_sdk: bool = True  # Use Claude Agent SDK (True) or CLI wrapper (False)


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

    def check_completion_signal(self, output: str) -> Optional[str]:
        """
        Check if agent output contains completion promise.

        Returns promise text if found, None otherwise.

        Pattern: <promise>TEXT</promise>
        - Exact string matching (case-sensitive)
        - Multi-word promises supported
        - Whitespace normalized

        Example:
            output = "Task complete. <promise>DONE</promise>"
            result = agent.check_completion_signal(output)
            # result = "DONE"

        Returns:
            Promise text if found, None otherwise
        """
        match = re.search(r'<promise>(.*?)</promise>', output, re.DOTALL)
        if match:
            promise_text = match.group(1).strip()
            # Normalize whitespace
            promise_text = ' '.join(promise_text.split())
            return promise_text
        return None

    def record_iteration(self, verdict: Any, changes: list[str]) -> None:
        """
        Record iteration for budget tracking and analysis.

        Args:
            verdict: Ralph Verdict from this iteration
            changes: List of files changed in this iteration

        Note:
            Should be called by GovernedSession after each iteration.
            Verdict type should have .type attribute with .value property.
        """
        from datetime import datetime

        # Extract verdict info safely
        verdict_type = "UNKNOWN"
        safe_to_merge = False
        regression_detected = False

        if verdict:
            if hasattr(verdict, 'type'):
                verdict_type = verdict.type.value if hasattr(verdict.type, 'value') else str(verdict.type)
            if hasattr(verdict, 'safe_to_merge'):
                safe_to_merge = verdict.safe_to_merge
            if hasattr(verdict, 'regression_detected'):
                regression_detected = verdict.regression_detected

        # Get current iteration number from concrete agent
        iteration_num = getattr(self, 'current_iteration', 0)

        iteration_record = {
            "iteration": iteration_num,
            "timestamp": datetime.now().isoformat(),
            "verdict": verdict_type,
            "safe_to_merge": safe_to_merge,
            "changes": changes,
            "regression": regression_detected
        }

        # Store in iteration history (concrete agent should have this attribute)
        if not hasattr(self, 'iteration_history'):
            self.iteration_history = []
        self.iteration_history.append(iteration_record)

    def get_iteration_summary(self) -> dict[str, Any]:
        """
        Get summary of iteration attempts.

        Returns:
            Dict with:
            - total_iterations: Total number of iterations
            - max_iterations: Maximum allowed iterations
            - pass_count: Number of PASS verdicts
            - fail_count: Number of FAIL verdicts
            - blocked_count: Number of BLOCKED verdicts
            - history: Full iteration history
        """
        # Get config and history from concrete agent
        config = getattr(self, 'config', None)
        max_iters = config.max_iterations if config else 10
        current_iter = getattr(self, 'current_iteration', 0)
        history = getattr(self, 'iteration_history', [])

        return {
            "total_iterations": current_iter,
            "max_iterations": max_iters,
            "pass_count": sum(1 for i in history if i.get("verdict") == "PASS"),
            "fail_count": sum(1 for i in history if i.get("verdict") == "FAIL"),
            "blocked_count": sum(1 for i in history if i.get("verdict") == "BLOCKED"),
            "history": history
        }

    def finalize_session(self, result: dict[str, Any]) -> "SessionResult":
        """
        Create session reflection and handoff document.

        Called at the end of execution to generate handoff artifacts.
        Agents can override this to customize handoff generation.

        Args:
            result: Raw result dict from execute()

        Returns:
            SessionResult suitable for handoff generation

        Example:
            result = agent.execute("TASK-123")
            session_result = agent.finalize_session(result)
            handoff = create_session_handoff("session-id", "bugfix", session_result)
        """
        from orchestration.reflection import (
            SessionResult,
            SessionStatus,
            FileChange,
            SessionTestSummary
        )

        # Convert raw result to SessionResult
        # Default implementation - agents should override for custom behavior
        status_map = {
            "completed": SessionStatus.COMPLETED,
            "blocked": SessionStatus.BLOCKED,
            "failed": SessionStatus.FAILED,
            "partial": SessionStatus.PARTIAL
        }

        return SessionResult(
            task_id=result.get("task_id", "unknown"),
            status=status_map.get(result.get("status", "failed"), SessionStatus.FAILED),
            accomplished=result.get("accomplished", []),
            incomplete=result.get("incomplete", []),
            blockers=result.get("blockers", []),
            file_changes=result.get("file_changes", []),
            tests=result.get("tests"),
            verdict=result.get("verdict"),
            handoff_notes=result.get("handoff_notes", ""),
            next_steps=result.get("next_steps", []),
            regression_risk=result.get("regression_risk", "LOW"),
            merge_confidence=result.get("merge_confidence", "HIGH"),
            requires_review=result.get("requires_review", False)
        )
