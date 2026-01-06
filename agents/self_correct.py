"""
Self-Correction Loop - Agent error analysis and automatic fixes

Enables agents to analyze verification failures and fix automatically:
- Lint errors → run autofix
- Type errors → analyze and fix types
- Test failures → fix implementation or update tests

Based on Anthropic's proven patterns for autonomous agents.
"""

from dataclasses import dataclass
from typing import Literal, Optional
from pathlib import Path
import subprocess

from ralph.fast_verify import VerifyResult


FixAction = Literal["run_autofix", "fix_types", "fix_implementation", "escalate"]


@dataclass
class FixStrategy:
    """Strategy for fixing a verification failure"""
    action: FixAction
    command: Optional[str] = None
    prompt: Optional[str] = None
    retry_immediately: bool = False


def analyze_failure(verify_result: VerifyResult) -> FixStrategy:
    """
    Determine fix strategy from verification failure

    Args:
        verify_result: Failed VerifyResult

    Returns:
        FixStrategy describing how to fix the issue
    """
    # Lint errors - can auto-fix
    if verify_result.has_lint_errors:
        return FixStrategy(
            action="run_autofix",
            command="npm run lint:fix",
            retry_immediately=True  # Autofix is deterministic
        )

    # Type errors - need Claude to analyze
    if verify_result.has_type_errors:
        error_summary = '\n'.join(verify_result.type_errors[:5])
        return FixStrategy(
            action="fix_types",
            prompt=f"""Fix these TypeScript type errors:

{error_summary}

Analyze the errors and update type annotations to resolve them.
Do not use 'any' unless absolutely necessary.""",
            retry_immediately=False  # Let Claude think
        )

    # Test failures - need implementation fix
    if verify_result.has_test_failures:
        failure_summary = '\n'.join(verify_result.test_failures[:10])
        return FixStrategy(
            action="fix_implementation",
            prompt=f"""Tests failed with these errors:

{failure_summary}

Analyze the test failures and either:
1. Fix the implementation to make tests pass, OR
2. Update tests if the specification changed

Prefer fixing implementation over changing tests unless requirements changed.""",
            retry_immediately=False  # Needs analysis
        )

    # Unknown failure
    return FixStrategy(
        action="escalate",
        prompt=f"Unknown verification failure: {verify_result.reason}"
    )


def apply_autofix(project_dir: Path, command: str) -> bool:
    """
    Apply automatic fix command (e.g., lint:fix)

    Args:
        project_dir: Project directory
        command: Command to run (e.g., "npm run lint:fix")

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            command.split(),
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Autofix failed: {e}")
        return False


async def implement_with_retries(
    task_id: str,
    task_description: str,
    changed_files: list[str],
    project_dir: Path,
    max_retries: int = 5
) -> dict:
    """
    Implement task with automatic retry on failures

    Args:
        task_id: Task identifier
        task_description: What to implement
        changed_files: Files that will be changed
        project_dir: Project directory
        max_retries: Maximum retry attempts

    Returns:
        Result dict with status and details
    """
    from ralph.fast_verify import fast_verify

    print(f"\n🔄 Implementing {task_id} with up to {max_retries} retries")

    for attempt in range(max_retries):
        print(f"\n{'─'*60}")
        print(f"Attempt {attempt + 1}/{max_retries}")
        print(f"{'─'*60}\n")

        # TODO: This is where Claude Code CLI would execute
        # For now, placeholder
        # subprocess.run(["claude", "--prompt", task_description])
        print(f"⚠️  Claude Code CLI execution not yet implemented")
        print(f"   Task: {task_description}")
        print(f"   Files: {changed_files}\n")

        # Verify the changes
        print("🔍 Running fast verification...")
        verify_result = fast_verify(project_dir, changed_files)

        if verify_result.status == "PASS":
            print(f"\n✅ Verification passed!")
            return {
                "status": "success",
                "attempts": attempt + 1,
                "verify_result": verify_result
            }

        # Failed - analyze and retry
        print(f"\n❌ Verification failed: {verify_result.reason}")

        if attempt < max_retries - 1:
            # Analyze failure and determine strategy
            strategy = analyze_failure(verify_result)
            print(f"\n📋 Fix Strategy: {strategy.action}")

            if strategy.action == "escalate":
                print("   Cannot auto-fix - escalating to human")
                break

            # Apply fix strategy
            if strategy.action == "run_autofix":
                print(f"   Running: {strategy.command}")
                success = apply_autofix(project_dir, strategy.command)
                if not success:
                    print("   Autofix failed")
                    continue
                print("   Autofix applied - retrying verification")

            elif strategy.action in ["fix_types", "fix_implementation"]:
                print(f"   Prompt for Claude:\n{strategy.prompt[:200]}...")
                # TODO: Send prompt to Claude Code CLI
                # subprocess.run(["claude", "--prompt", strategy.prompt])
                print("   ⚠️  Claude Code CLI not yet integrated")

            continue

    # Max retries exceeded
    return {
        "status": "failed",
        "attempts": max_retries,
        "reason": "Max retries exceeded",
        "last_error": verify_result.reason if 'verify_result' in locals() else "Unknown"
    }
