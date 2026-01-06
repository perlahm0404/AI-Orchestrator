"""
Fast Verification - Tiered verification for iteration loops

Replaces 5-minute full Ralph with 30-second fast checks:
- Tier 1: Lint (changed files only) - <5s
- Tier 2: Typecheck (incremental) - <30s
- Tier 3: Related tests only - <60s

Full Ralph verification still runs on PR creation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional
import subprocess
import time


VerifyStatus = Literal["PASS", "FAIL"]


@dataclass
class VerifyResult:
    """Fast verification result"""
    status: VerifyStatus
    reason: Optional[str] = None
    duration_ms: int = 0
    lint_errors: list[str] = None
    type_errors: list[str] = None
    test_failures: list[str] = None

    def __post_init__(self):
        if self.lint_errors is None:
            self.lint_errors = []
        if self.type_errors is None:
            self.type_errors = []
        if self.test_failures is None:
            self.test_failures = []

    @property
    def has_lint_errors(self) -> bool:
        return len(self.lint_errors) > 0

    @property
    def has_type_errors(self) -> bool:
        return len(self.type_errors) > 0

    @property
    def has_test_failures(self) -> bool:
        return len(self.test_failures) > 0


def run_lint(project_dir: Path, changed_files: list[str]) -> VerifyResult:
    """
    Tier 1: Run linter on changed files only

    Args:
        project_dir: Project directory
        changed_files: List of files that changed

    Returns:
        VerifyResult with lint status
    """
    start = time.time()

    # Filter for lintable files
    lintable = [f for f in changed_files if f.endswith(('.ts', '.tsx', '.js', '.jsx'))]
    if not lintable:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(status="PASS", reason="No lintable files", duration_ms=duration)

    try:
        # Run eslint on specific files
        result = subprocess.run(
            ["npm", "run", "lint", "--", *lintable],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout
        )

        duration = int((time.time() - start) * 1000)

        if result.returncode == 0:
            return VerifyResult(status="PASS", reason="Lint passed", duration_ms=duration)
        else:
            # Parse errors from output
            errors = result.stdout.split('\n') if result.stdout else []
            return VerifyResult(
                status="FAIL",
                reason="Lint errors found",
                lint_errors=errors[:10],  # First 10 errors
                duration_ms=duration
            )

    except subprocess.TimeoutExpired:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(
            status="FAIL",
            reason="Lint timeout",
            duration_ms=duration
        )
    except Exception as e:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(
            status="FAIL",
            reason=f"Lint error: {str(e)}",
            duration_ms=duration
        )


def run_typecheck(project_dir: Path, changed_files: list[str]) -> VerifyResult:
    """
    Tier 2: Run TypeScript incremental typecheck

    Args:
        project_dir: Project directory
        changed_files: List of files that changed

    Returns:
        VerifyResult with typecheck status
    """
    start = time.time()

    # Filter for TypeScript files
    ts_files = [f for f in changed_files if f.endswith(('.ts', '.tsx'))]
    if not ts_files:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(status="PASS", reason="No TypeScript files", duration_ms=duration)

    try:
        # Run tsc with --incremental
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--incremental"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )

        duration = int((time.time() - start) * 1000)

        if result.returncode == 0:
            return VerifyResult(status="PASS", reason="Typecheck passed", duration_ms=duration)
        else:
            # Parse type errors
            errors = result.stdout.split('\n') if result.stdout else []
            return VerifyResult(
                status="FAIL",
                reason="Type errors found",
                type_errors=errors[:10],  # First 10 errors
                duration_ms=duration
            )

    except subprocess.TimeoutExpired:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(
            status="FAIL",
            reason="Typecheck timeout",
            duration_ms=duration
        )
    except Exception as e:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(
            status="FAIL",
            reason=f"Typecheck error: {str(e)}",
            duration_ms=duration
        )


def find_related_tests(project_dir: Path, changed_files: list[str]) -> list[str]:
    """
    Find tests related to changed files

    Args:
        project_dir: Project directory
        changed_files: List of files that changed

    Returns:
        List of test file paths
    """
    tests = []

    for file in changed_files:
        # Convention: src/foo/bar.ts → tests/foo/bar.test.ts
        if file.startswith('src/'):
            # Remove src/ prefix and extension
            relative = file[4:]  # Remove 'src/'
            base = relative.rsplit('.', 1)[0]  # Remove extension

            # Add .test.ts
            test_file = f"tests/{base}.test.ts"
            test_path = project_dir / test_file

            if test_path.exists():
                tests.append(test_file)

    return tests


def run_tests(project_dir: Path, test_files: list[str]) -> VerifyResult:
    """
    Tier 3: Run related tests only

    Args:
        project_dir: Project directory
        test_files: List of test files to run

    Returns:
        VerifyResult with test status
    """
    start = time.time()

    if not test_files:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(status="PASS", reason="No tests to run", duration_ms=duration)

    try:
        # Run vitest on specific files
        result = subprocess.run(
            ["npx", "vitest", "run", *test_files],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )

        duration = int((time.time() - start) * 1000)

        if result.returncode == 0:
            return VerifyResult(status="PASS", reason="Tests passed", duration_ms=duration)
        else:
            # Parse test failures
            failures = result.stdout.split('\n') if result.stdout else []
            return VerifyResult(
                status="FAIL",
                reason="Tests failed",
                test_failures=failures[:20],  # First 20 lines
                duration_ms=duration
            )

    except subprocess.TimeoutExpired:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(
            status="FAIL",
            reason="Test timeout",
            duration_ms=duration
        )
    except Exception as e:
        duration = int((time.time() - start) * 1000)
        return VerifyResult(
            status="FAIL",
            reason=f"Test error: {str(e)}",
            duration_ms=duration
        )


def fast_verify(project_dir: Path, changed_files: list[str]) -> VerifyResult:
    """
    Fast verification for iteration loop (~30-60 seconds total)

    Runs three tiers:
    1. Lint (changed files only) - <5s
    2. Typecheck (incremental) - <30s
    3. Related tests only - <60s

    Args:
        project_dir: Project directory
        changed_files: List of files that changed

    Returns:
        VerifyResult with combined status
    """
    overall_start = time.time()

    # Tier 1: Lint
    print("  🔍 Tier 1: Running lint...")
    lint_result = run_lint(project_dir, changed_files)
    print(f"     {lint_result.status} ({lint_result.duration_ms}ms)")

    if lint_result.status == "FAIL":
        return lint_result

    # Tier 2: Typecheck
    print("  🔍 Tier 2: Running typecheck...")
    type_result = run_typecheck(project_dir, changed_files)
    print(f"     {type_result.status} ({type_result.duration_ms}ms)")

    if type_result.status == "FAIL":
        return type_result

    # Tier 3: Related tests
    print("  🔍 Tier 3: Running related tests...")
    test_files = find_related_tests(project_dir, changed_files)
    test_result = run_tests(project_dir, test_files)
    print(f"     {test_result.status} ({test_result.duration_ms}ms)")

    if test_result.status == "FAIL":
        return test_result

    # All passed
    overall_duration = int((time.time() - overall_start) * 1000)
    return VerifyResult(
        status="PASS",
        reason="All verifications passed",
        duration_ms=overall_duration
    )
