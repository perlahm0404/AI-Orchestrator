"""
Wiggum Stop Hook for Claude Agent SDK

Implements iteration control for agents - decides whether the agent
can stop execution or must continue iterating.

Decision Logic:
1. Check completion signal (<promise>TEXT</promise>)
2. Check iteration budget (15-50 based on agent type)
3. Check Ralph verdict from PostToolUse hook
4. Decision tree:
   - PASS → allow stop
   - BLOCKED → require human, stop
   - FAIL + safe_to_merge → allow stop
   - FAIL + regression → block, continue iteration

Usage:
    from governance.hooks.sdk_stop_hook import wiggum_stop_hook

    options = ClaudeCodeOptions(
        hooks={
            "Stop": [wiggum_stop_hook]
        }
    )
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import subprocess


class StopDecision(Enum):
    """Decision on whether to allow agent to stop."""

    ALLOW = "allow"  # Let agent exit
    BLOCK = "block"  # Block exit, continue iteration
    ASK_HUMAN = "ask"  # Block and request human approval


@dataclass
class StopHookResult:
    """Result from stop hook evaluation."""

    allow_stop: bool
    require_human: bool = False
    message: Optional[str] = None
    decision: StopDecision = StopDecision.ALLOW
    verdict: Optional[Any] = None


async def wiggum_stop_hook(
    input_data: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    SDK Stop hook implementing Wiggum iteration control.

    This hook is called when the agent attempts to stop execution.
    It implements the Wiggum pattern:
    1. Check for completion signal
    2. Check iteration budget
    3. Check Ralph verdict
    4. Decide: ALLOW, BLOCK, or ASK_HUMAN

    Args:
        input_data: Hook input containing:
            - stop_hook_active: bool indicating stop was requested
            - content: Agent's final output (for completion signal)
        context: Execution context containing:
            - agent: BaseAgent instance
            - app_context: AppContext for Ralph
            - last_verdict: Ralph verdict from PostToolUse
            - session_id: Current session ID
            - changed_files: List of changed files

    Returns:
        Dict with stop decision:
        - {}: Allow stop
        - {"continue": True, "message": "..."}: Block stop, return message
        - {"decision": "ask_human"}: Require human approval
    """
    # Get agent from context
    agent = context.get("agent")
    if agent is None:
        # No agent context - allow stop by default
        return {}

    # Get agent output for completion signal checking
    output = input_data.get("content", "")
    if isinstance(output, dict):
        output = output.get("text", "")

    # Check 1: Completion signal (<promise>TEXT</promise>)
    promise = None
    if hasattr(agent, "config") and agent.config.expected_completion_signal:
        promise = agent.check_completion_signal(output)

    # Check 2: Iteration budget
    if hasattr(agent, "current_iteration"):
        agent.current_iteration += 1

    max_iterations = _get_max_iterations(agent)
    current_iteration = getattr(agent, "current_iteration", 0)

    if current_iteration >= max_iterations:
        # Budget exhausted - require human review
        return {
            "continue": False,
            "decision": "ask_human",
            "message": f"Iteration budget exhausted ({max_iterations} iterations). Human review required.",
        }

    # Check 3: Get Ralph verdict from PostToolUse hook
    verdict = context.get("last_verdict")

    # Check 4: Are there any changes?
    changed_files = context.get("changed_files", [])
    if not changed_files:
        # No changes made - task appears incomplete
        return {
            "continue": True,
            "message": "No file changes detected. Please make changes to complete the task.",
        }

    # Decision tree based on verdict
    if verdict is None:
        # No verdict yet - run verification now
        app_context = context.get("app_context")
        if app_context:
            verdict = _run_verification(
                project=app_context.project_name,
                changes=changed_files,
                session_id=context.get("session_id", "unknown"),
                app_context=app_context,
                baseline=context.get("baseline"),
            )
            context["last_verdict"] = verdict

    if verdict is None:
        # Still no verdict - allow stop (fail open for safety)
        return {}

    verdict_type = getattr(verdict, "type", None)
    verdict_value = getattr(verdict_type, "value", str(verdict_type))

    if verdict_value == "PASS":
        # All checks passed - allow stop
        completion_message = "All checks passed - task complete"
        if promise:
            completion_message = f"Task complete: <promise>{promise}</promise> (verified)"
        print(f"\n{completion_message}")
        return {}

    elif verdict_value == "BLOCKED":
        # Guardrail violation - handle based on mode
        return _handle_guardrail_violation(verdict, context)

    else:  # FAIL
        if getattr(verdict, "safe_to_merge", False):
            # Only pre-existing failures - allow stop
            print("\nPre-existing failures detected but no regressions - safe to proceed")
            return {}
        else:
            # New failures or regressions - block and retry
            iteration_msg = f"Iteration {current_iteration}/{max_iterations}"
            return {
                "continue": True,
                "message": f"{iteration_msg}: Fix the issues and retry:\n\n{verdict.summary()}",
            }


def _get_max_iterations(agent: Any) -> int:
    """Get max iterations from agent config."""
    if hasattr(agent, "config") and hasattr(agent.config, "max_iterations"):
        max_iter: int = agent.config.max_iterations
        return max_iter

    # Fallback to defaults based on agent type
    agent_name = getattr(agent.config, "agent_name", "unknown") if hasattr(agent, "config") else "unknown"

    defaults: dict[str, int] = {
        "bugfix": 15,
        "codequality": 20,
        "feature": 50,
        "test": 15,
        "editorial": 20,
    }

    return defaults.get(agent_name, 10)


def _run_verification(
    project: str,
    changes: list[str],
    session_id: str,
    app_context: Any,
    baseline: Optional[Any] = None,
) -> Any:
    """Run Ralph verification."""
    try:
        from ralph.engine import verify

        return verify(
            project=project,
            changes=changes,
            session_id=session_id,
            app_context=app_context,
            baseline=baseline,
        )
    except Exception as e:
        print(f"Warning: Ralph verification failed: {e}")
        return None


def _handle_guardrail_violation(
    verdict: Any,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Handle guardrail violation (BLOCKED verdict).

    In non-interactive mode: auto-revert and continue
    In interactive mode: prompt for R/O/A decision
    """
    import os

    print("\n" + "=" * 60)
    print("GUARDRAIL VIOLATION DETECTED")
    print("=" * 60)
    if hasattr(verdict, "summary"):
        print(verdict.summary())

    # Check for non-interactive mode
    app_context = context.get("app_context")
    non_interactive = getattr(app_context, "non_interactive", False) if app_context else False

    if non_interactive:
        # Auto-revert in non-interactive mode
        print("\nNON-INTERACTIVE MODE: Auto-reverting changes...")
        changed_files = context.get("changed_files", [])
        project_path = getattr(app_context, "project_path", ".") if app_context else "."
        _revert_changes(project_path, changed_files)

        return {
            "continue": False,
            "decision": "ask_human",
            "message": "Guardrail violation auto-reverted in non-interactive mode.",
        }

    # Check for auto-override environment variable
    auto_response = os.environ.get("AUTO_GUARDRAIL_OVERRIDE", "").strip().upper()

    if auto_response == "R":
        # Auto-revert
        changed_files = context.get("changed_files", [])
        project_path = getattr(app_context, "project_path", ".") if app_context else "."
        _revert_changes(project_path, changed_files)
        return {
            "continue": False,
            "decision": "ask_human",
            "message": "Guardrail violation reverted (AUTO_GUARDRAIL_OVERRIDE=R).",
        }

    elif auto_response == "O":
        # Auto-override
        print("WARNING: Guardrail overridden (AUTO_GUARDRAIL_OVERRIDE=O)")
        return {}

    elif auto_response == "A":
        # Auto-abort
        raise KeyboardInterrupt("Session aborted (AUTO_GUARDRAIL_OVERRIDE=A)")

    # Interactive mode - require human decision
    print("\n" + "=" * 60)
    print("OPTIONS:")
    print("  [R] Revert changes and exit")
    print("  [O] Override guardrail and continue")
    print("  [A] Abort session immediately")
    print("=" * 60)

    while True:
        response = input("Your choice [R/O/A]: ").strip().upper()
        if response in ["R", "O", "A"]:
            break
        print("Invalid choice. Please enter R, O, or A.")

    if response == "R":
        changed_files = context.get("changed_files", [])
        project_path = getattr(app_context, "project_path", ".") if app_context else "."
        _revert_changes(project_path, changed_files)
        return {
            "continue": False,
            "decision": "ask_human",
            "message": "Guardrail violation reverted by human choice.",
        }

    elif response == "O":
        print("WARNING: Guardrail overridden by human. Proceeding with caution.")
        return {}

    else:  # A
        raise KeyboardInterrupt("Session aborted by human decision")


def _revert_changes(project_path: str, changes: list[str]) -> tuple[bool, list[str]]:
    """Best-effort revert of tracked files."""
    failed = []

    for file_path in changes:
        try:
            result = subprocess.run(
                ["git", "checkout", "HEAD", "--", file_path],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                failed.append(file_path)
        except Exception:
            failed.append(file_path)

    if failed:
        print(f"Warning: Failed to revert: {', '.join(failed)}")

    return (not failed, failed)
