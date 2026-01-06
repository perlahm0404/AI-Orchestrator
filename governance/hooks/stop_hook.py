"""
Stop Hook System - Blocks agent exit until governance approval.

Based on anthropics/claude-code Ralph-Wiggum stop hook pattern.

Decision Logic:
1. Check completion signal → ALLOW if matches expected
2. Check iteration budget → ASK_HUMAN if exhausted
3. Run Ralph verification
4. PASS → ALLOW
5. BLOCKED → ASK_HUMAN (cannot auto-fix, requires human decision)
6. FAIL + safe_to_merge → ALLOW (pre-existing failures only)
7. FAIL + regression → BLOCK (give agent chance to fix)

Implementation: Phase 3 - Ralph-Wiggum Integration
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base import BaseAgent
    from ralph.verdict import Verdict


class StopDecision(Enum):
    """Decision on whether to allow agent to stop."""
    ALLOW = "allow"      # Let agent exit
    BLOCK = "block"      # Block exit, continue iteration
    ASK_HUMAN = "ask"    # Block and request human approval


@dataclass
class StopHookResult:
    """Result of stop hook evaluation."""
    decision: StopDecision
    reason: str
    system_message: Optional[str] = None
    verdict: Optional["Verdict"] = None


def agent_stop_hook(
    agent: "BaseAgent",
    session_id: str,
    changes: list[str],
    output: str,
    app_context
) -> StopHookResult:
    """
    Evaluate if agent should be allowed to stop.

    Decision logic:
    1. Check completion signal → ALLOW if matches expected
    2. Check iteration budget → ASK_HUMAN if exhausted
    3. Run Ralph verification
    4. If PASS → ALLOW
    5. If BLOCKED → ASK_HUMAN (cannot auto-fix)
    6. If FAIL + safe_to_merge → ALLOW (pre-existing only)
    7. If FAIL + regression → BLOCK (give agent chance to fix)

    Args:
        agent: BaseAgent instance
        session_id: Current session ID
        changes: List of changed files
        output: Agent's output text
        app_context: Application context

    Returns:
        StopHookResult with decision and context
    """
    from ralph.engine import verify
    from ralph.verdict import VerdictType

    # Check 1: Completion signal
    if agent.config.expected_completion_signal:
        promise = agent.check_completion_signal(output)
        if promise == agent.config.expected_completion_signal:
            # Agent explicitly signaled completion
            return StopHookResult(
                decision=StopDecision.ALLOW,
                reason="Completion signal detected",
                system_message=f"✅ Task complete: <promise>{promise}</promise>"
            )

    # Check 2: Iteration budget exhausted
    if agent.current_iteration >= agent.config.max_iterations:
        return StopHookResult(
            decision=StopDecision.ASK_HUMAN,
            reason=f"Max iterations ({agent.config.max_iterations}) reached",
            system_message="⚠️  Iteration budget exhausted - human review required"
        )

    # Check 3: Ralph verification
    if not changes:
        # No changes made - task appears incomplete, block and retry
        return StopHookResult(
            decision=StopDecision.BLOCK,
            reason="No changes detected - agent may have failed silently",
            system_message="⚠️  No file changes detected. Agent should modify files to complete the task."
        )

    # Get baseline if agent has one
    baseline = getattr(agent, 'baseline', None)

    verdict = verify(
        project=app_context.project_name,
        changes=changes,
        session_id=session_id,
        app_context=app_context,
        baseline=baseline
    )

    # Decision tree based on verdict
    if verdict.type == VerdictType.PASS:
        return StopHookResult(
            decision=StopDecision.ALLOW,
            reason="Ralph verification PASSED",
            system_message="✅ All checks passed - safe to proceed",
            verdict=verdict
        )

    elif verdict.type == VerdictType.BLOCKED:
        # Guardrail violation - ask human for approval/override
        print("\n" + "="*60)
        print("🚫 GUARDRAIL VIOLATION DETECTED")
        print("="*60)
        print(verdict.summary())
        print("\n" + "="*60)
        print("OPTIONS:")
        print("  [R] Revert changes and exit")
        print("  [O] Override guardrail and continue")
        print("  [A] Abort session immediately")
        print("="*60)

        while True:
            response = input("Your choice [R/O/A]: ").strip().upper()
            if response in ['R', 'O', 'A']:
                break
            print("Invalid choice. Please enter R, O, or A.")

        if response == 'R':
            # Revert changes
            return StopHookResult(
                decision=StopDecision.ALLOW,  # Exit after revert
                reason="Human chose to revert guardrail violation",
                system_message="↩️  Changes reverted by human decision",
                verdict=verdict
            )
        elif response == 'O':
            # Override - continue with warning
            return StopHookResult(
                decision=StopDecision.ALLOW,  # Continue despite BLOCKED
                reason="Human override of guardrail violation",
                system_message="⚠️  WARNING: Guardrail overridden by human. Proceeding with caution.",
                verdict=verdict
            )
        else:  # 'A'
            # Abort immediately
            raise KeyboardInterrupt("Session aborted by human decision")

    else:  # VerdictType.FAIL
        if verdict.safe_to_merge:
            # Only pre-existing failures - allow
            return StopHookResult(
                decision=StopDecision.ALLOW,
                reason="Ralph FAIL but safe to merge (pre-existing failures only)",
                system_message="⚠️  Pre-existing failures detected but no regressions",
                verdict=verdict
            )
        else:
            # New failures or regressions - block and let agent retry
            iteration_num = agent.current_iteration + 1
            return StopHookResult(
                decision=StopDecision.BLOCK,
                reason="Ralph FAIL - new failures or regressions detected",
                system_message=f"🔄 Iteration {iteration_num}: Fix the issues and retry:\n\n" + verdict.summary(),
                verdict=verdict
            )
