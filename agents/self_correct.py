"""
Self-Correction System (Phase 3)

Analyzes verification failures and applies fixes with bounded retries.

Usage:
    from agents.self_correct import SelfCorrector, analyze_failure

    corrector = SelfCorrector(project_dir=Path("/path/to/project"))
    result = await corrector.fix_with_retries(task, max_retries=5)
"""

import asyncio
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List, Any


class FixAction(Enum):
    """Types of fix actions."""
    RUN_AUTOFIX = "run_autofix"
    FIX_TYPES = "fix_types"
    FIX_IMPLEMENTATION = "fix_implementation"
    ESCALATE = "escalate"


@dataclass
class FixStrategy:
    """Strategy for fixing a verification failure."""
    action: FixAction
    command: Optional[str] = None
    prompt: Optional[str] = None
    retry_immediately: bool = False
    reason: Optional[str] = None


@dataclass
class FixResult:
    """Result of fix attempt."""
    success: bool
    attempts: int
    last_error: Optional[str] = None


def analyze_failure(verify_result: Any) -> FixStrategy:
    """
    Analyze a verification failure and determine fix strategy.

    Args:
        verify_result: Result from FastVerify

    Returns:
        FixStrategy with action to take
    """
    # Lint errors - try autofix
    if not getattr(verify_result, 'lint_passed', True):
        return FixStrategy(
            action=FixAction.RUN_AUTOFIX,
            command="npm run lint:fix",
            retry_immediately=True
        )

    # Type errors - need Claude to fix
    if not getattr(verify_result, 'types_passed', True):
        errors = getattr(verify_result, 'errors', [])
        error_text = '\n'.join(errors[:5])  # First 5 errors
        return FixStrategy(
            action=FixAction.FIX_TYPES,
            prompt=f"Fix these type errors:\n{error_text}",
            retry_immediately=False
        )

    # Test failures - need implementation fix
    if not getattr(verify_result, 'tests_passed', True):
        errors = getattr(verify_result, 'errors', [])
        error_text = '\n'.join(errors[:5])
        return FixStrategy(
            action=FixAction.FIX_IMPLEMENTATION,
            prompt=f"Tests failed. Either fix the implementation or update tests if spec changed:\n{error_text}",
            retry_immediately=False
        )

    # Unknown failure - escalate
    return FixStrategy(
        action=FixAction.ESCALATE,
        reason="Unknown failure type"
    )


def _run_command(command: Optional[str], project_dir: Path) -> bool:
    """Run a shell command in the project directory."""
    if not command:
        return False
    try:
        result = subprocess.run(
            command.split(),
            cwd=project_dir,
            capture_output=True,
            timeout=60
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return False


def apply_fix(strategy: FixStrategy, files: List[str], project_dir: Path) -> bool:
    """
    Apply a fix strategy synchronously.

    Returns True if fix was applied successfully.
    """
    if strategy.action == FixAction.RUN_AUTOFIX:
        return _run_command(strategy.command, project_dir)

    # Other actions need async handling
    _ = files  # Will be used when integration is complete
    return False


class SelfCorrector:
    """
    Self-correction system with bounded retries.

    Analyzes failures and attempts automatic fixes,
    escalating to humans when retries are exhausted.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    async def fix_with_retries(self, task: Any, max_retries: int = 5) -> FixResult:
        """
        Attempt to fix a task with bounded retries.

        Args:
            task: Task to fix
            max_retries: Maximum retry attempts

        Returns:
            FixResult with success status
        """
        attempts = 0
        last_error = None

        for attempt in range(max_retries):
            attempts = attempt + 1

            try:
                success = await self._attempt_fix(task, context_level=attempt)
                if success:
                    return FixResult(success=True, attempts=attempts)
            except Exception as e:
                last_error = str(e)

        # Exhausted retries - escalate
        self._escalate(task, last_error)
        return FixResult(success=False, attempts=attempts, last_error=last_error)

    async def _attempt_fix(self, task: Any, context_level: int = 0) -> bool:
        """
        Single fix attempt.

        Args:
            task: Task to fix
            context_level: Amount of context to include (increases with retries)

        Returns:
            True if fix succeeded
        """
        # Placeholder - would invoke Claude Code
        return False

    async def _analyze_and_fix(self, task: Any, attempt: int = 0) -> bool:
        """Analyze failure and apply fix."""
        return False

    def _escalate(self, task: Any, error: Optional[str]) -> None:
        """Escalate to human when retries exhausted."""
        print(f"ESCALATE: Task {getattr(task, 'id', 'unknown')} failed after max retries")
        if error:
            print(f"Last error: {error}")

    def apply_fix(self, strategy: FixStrategy, files: List[str]) -> bool:
        """Apply a fix strategy synchronously."""
        if strategy.action == FixAction.RUN_AUTOFIX:
            return self._run_command(strategy.command or "")

        return False

    async def apply_fix_async(self, strategy: FixStrategy, files: List[str]) -> bool:
        """Apply a fix strategy asynchronously."""
        if strategy.action == FixAction.RUN_AUTOFIX:
            return self._run_command(strategy.command or "")

        if strategy.action in (FixAction.FIX_TYPES, FixAction.FIX_IMPLEMENTATION):
            return await self._send_to_claude(strategy.prompt or "", files)

        return False

    def _run_command(self, command: str) -> bool:
        """Run a shell command."""
        try:
            result = subprocess.run(
                command.split(),
                cwd=self.project_dir,
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            return False

    async def _send_to_claude(self, prompt: str, files: List[str]) -> bool:
        """Send fix request to Claude Code."""
        # Placeholder - would invoke Claude Code CLI
        return True
