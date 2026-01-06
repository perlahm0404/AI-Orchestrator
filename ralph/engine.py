"""
Ralph Core Verification Engine

Entry point for all verification requests.

Usage:
    from ralph import engine

    verdict = engine.verify(
        project="karematch",
        changes=["src/auth.ts", "tests/auth.test.ts"],
        session_id="abc-123"
    )

    if verdict.type == VerdictType.BLOCKED:
        # Halt immediately, cannot proceed
        agent.halt(verdict.reason)
    elif verdict.type == VerdictType.FAIL:
        # Can retry after fixing issues
        handle_failures(verdict.failures)
    else:
        # PASS - safe to proceed
        proceed_with_merge()

Implementation: Phase 0
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class VerdictType(Enum):
    """Verification outcome types."""
    PASS = "PASS"       # All steps succeeded
    FAIL = "FAIL"       # One or more steps failed (fixable)
    BLOCKED = "BLOCKED" # Guardrail violation (not fixable)


@dataclass
class StepResult:
    """Result of a single verification step."""
    step: str           # e.g., "guardrails", "lint", "typecheck"
    passed: bool
    output: str
    duration_ms: int


@dataclass
class Verdict:
    """
    Complete verification result.

    This is the canonical output of Ralph verification.
    """
    type: VerdictType
    steps: list[StepResult]
    reason: str | None = None  # For BLOCKED/FAIL
    evidence: dict[str, Any] | None = None


def verify(
    project: str,
    changes: list[str],
    session_id: str,
    policy_version: str = "v1"
) -> Verdict:
    """
    Run full verification pipeline.

    Args:
        project: Target project (e.g., "karematch")
        changes: List of changed file paths
        session_id: Current session ID for audit
        policy_version: Policy version to use (default "v1")

    Returns:
        Verdict with PASS/FAIL/BLOCKED and evidence
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Ralph engine not yet implemented")
