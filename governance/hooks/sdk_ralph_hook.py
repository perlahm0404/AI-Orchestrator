"""
Ralph PostToolUse Hook for Claude Agent SDK

Runs Ralph verification after Edit/Write operations to detect:
- Guardrail violations (BLOCKED)
- Regressions (FAIL + regression_detected)
- Pre-existing failures (FAIL + safe_to_merge)
- Clean changes (PASS)

The hook injects instructions back into the agent when issues are detected,
allowing the agent to self-correct within the Wiggum iteration loop.

Usage:
    from governance.hooks.sdk_ralph_hook import ralph_post_tool_hook

    options = ClaudeCodeOptions(
        hooks={
            "PostToolUse": [
                HookMatcher(matcher="Edit|Write", hooks=[ralph_post_tool_hook])
            ]
        }
    )
"""

from typing import Any, Optional
import subprocess
from pathlib import Path


async def ralph_post_tool_hook(
    input_data: dict[str, Any],
    tool_use_id: str,  # noqa: ARG001
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Run Ralph verification after Edit/Write operations.

    This hook is called by the Claude Agent SDK after tool execution.
    It runs Ralph verification and returns instructions to the agent
    if issues are detected.

    Args:
        input_data: Hook input containing:
            - tool_name: Name of the tool (Edit, Write, etc.)
            - tool_input: Tool input parameters
            - tool_response: Tool response/output
        tool_use_id: Unique ID for this tool use
        context: Execution context containing:
            - agent: BaseAgent instance
            - app_context: AppContext for Ralph
            - baseline: Baseline for regression detection
            - session_id: Current session ID
            - changed_files: List of changed files

    Returns:
        Dict with optional instruction to return to agent:
        - Empty dict: Continue normally
        - {"instruction": "..."}: Return message to agent
        - {"decision": "stop"}: Force agent to stop
    """
    tool_name = input_data.get("tool_name", "")

    # Only run Ralph verification for Edit/Write operations
    if tool_name not in ("Edit", "Write"):
        return {}

    # Get context values
    app_context = context.get("app_context")
    if app_context is None:
        # No app context - skip verification
        return {}

    # Track the changed file
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if file_path:
        changed_files = context.get("changed_files", [])
        if file_path not in changed_files:
            changed_files.append(file_path)
            context["changed_files"] = changed_files

    # Get all changed files for this session
    changes = context.get("changed_files", [])
    if not changes:
        # No changes to verify yet
        return {}

    # Get session ID and baseline
    session_id = context.get("session_id", "unknown")
    baseline = context.get("baseline")

    # Run Ralph verification
    try:
        verdict = _run_ralph_verification(
            project=app_context.project_name,
            changes=changes,
            session_id=session_id,
            app_context=app_context,
            baseline=baseline,
        )
    except Exception as e:
        # Ralph verification failed - log and continue
        print(f"Warning: Ralph verification failed: {e}")
        return {}

    # Store verdict in context for Stop hook
    context["last_verdict"] = verdict

    # Handle verdict
    verdict_type = getattr(verdict, "type", None)
    verdict_value = getattr(verdict_type, "value", str(verdict_type))

    if verdict_value == "BLOCKED":
        # Guardrail violation - STOP immediately
        return {
            "instruction": _format_blocked_instruction(verdict),
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "decision": "stop",
                "reason": "Guardrail violation detected",
            },
        }

    elif verdict_value == "FAIL":
        if getattr(verdict, "regression_detected", False):
            # Regression detected - return warning to agent
            return {
                "instruction": _format_regression_warning(verdict),
            }
        elif getattr(verdict, "safe_to_merge", False):
            # Pre-existing failures only - continue
            return {}
        else:
            # New failures - return warning to agent
            return {
                "instruction": _format_failure_warning(verdict),
            }

    # PASS - continue normally
    return {}


def _run_ralph_verification(
    project: str,
    changes: list[str],
    session_id: str,
    app_context: Any,
    baseline: Optional[Any] = None,
) -> Any:
    """
    Run Ralph verification on changed files.

    Args:
        project: Project name (karematch, credentialmate)
        changes: List of changed file paths
        session_id: Current session ID
        app_context: AppContext with project config
        baseline: Optional baseline for regression detection

    Returns:
        Ralph Verdict
    """
    from ralph.engine import verify

    return verify(
        project=project,
        changes=changes,
        session_id=session_id,
        app_context=app_context,
        baseline=baseline,
    )


def _format_blocked_instruction(verdict: Any) -> str:
    """Format instruction for BLOCKED verdict (guardrail violation)."""
    summary = verdict.summary() if hasattr(verdict, "summary") else str(verdict)

    return f"""
STOP: GUARDRAIL VIOLATION DETECTED

{summary}

You must IMMEDIATELY revert the changes that caused this violation.
Do NOT proceed with any further modifications until the guardrail issue is resolved.

Required action:
1. Identify which change triggered the guardrail
2. Revert that specific change
3. Find an alternative approach that doesn't violate guardrails
"""


def _format_regression_warning(verdict: Any) -> str:
    """Format warning for regression detected."""
    summary = verdict.summary() if hasattr(verdict, "summary") else str(verdict)

    return f"""
WARNING: REGRESSION DETECTED

{summary}

Your changes have broken something that was previously working.
Please fix the regression before proceeding.

Required action:
1. Review the failing tests/checks
2. Fix the code to restore previous functionality
3. Ensure all tests pass before continuing
"""


def _format_failure_warning(verdict: Any) -> str:
    """Format warning for new failures."""
    summary = verdict.summary() if hasattr(verdict, "summary") else str(verdict)

    return f"""
WARNING: NEW FAILURES DETECTED

{summary}

Your changes have introduced new failures.
Please review and fix before proceeding.

Required action:
1. Review the failing checks
2. Fix the issues in your code
3. Verify the fixes resolve the failures
"""


def get_changed_files_from_git(project_path: Path) -> list[str]:
    """
    Get list of files changed since HEAD (uncommitted changes).

    Args:
        project_path: Path to git repository

    Returns:
        List of changed file paths
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
