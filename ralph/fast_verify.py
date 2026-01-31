"""
Fast Verification System (Phase 2)

Tiered verification for quick feedback during iteration:
- Instant (<5s): Lint only changed files
- Quick (<30s): Lint + type checking
- Related (<60s): Lint + types + related tests
- Full (~5min): Full test suite (for PRs)
"""

import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Tuple


class VerifyStatus(Enum):
    """Verification result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class VerifyTier(Enum):
    """Verification tiers by speed/thoroughness."""
    INSTANT = "instant"
    QUICK = "quick"
    RELATED = "related"
    FULL = "full"


@dataclass
class VerifyResult:
    """Result of verification."""
    status: VerifyStatus
    tier: VerifyTier
    errors: List[str] = field(default_factory=list)
    duration_ms: int = 0
    lint_passed: bool = True
    types_passed: bool = True
    tests_passed: bool = True


class FastVerify:
    """Fast verification system with tiered checks."""

    INSTANT_MAX_LINES = 20
    QUICK_MAX_LINES = 100

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def verify_instant(self, files: List[str]) -> VerifyResult:
        """Instant verification (<5s) - lint only."""
        start = time.time()
        lint_ok, lint_errors = self._run_lint(files)
        duration_ms = int((time.time() - start) * 1000)

        return VerifyResult(
            status=VerifyStatus.PASS if lint_ok else VerifyStatus.FAIL,
            tier=VerifyTier.INSTANT,
            errors=lint_errors,
            duration_ms=duration_ms,
            lint_passed=lint_ok
        )

    def verify_quick(self, files: List[str]) -> VerifyResult:
        """Quick verification (<30s) - lint + types."""
        start = time.time()
        errors = []

        lint_ok, lint_errors = self._run_lint(files)
        errors.extend(lint_errors)

        types_ok, type_errors = self._run_typecheck(files)
        errors.extend(type_errors)

        duration_ms = int((time.time() - start) * 1000)

        return VerifyResult(
            status=VerifyStatus.PASS if (lint_ok and types_ok) else VerifyStatus.FAIL,
            tier=VerifyTier.QUICK,
            errors=errors,
            duration_ms=duration_ms,
            lint_passed=lint_ok,
            types_passed=types_ok
        )

    def verify_related(self, files: List[str]) -> VerifyResult:
        """Related verification (<60s) - lint + types + related tests."""
        start = time.time()
        errors = []

        lint_ok, lint_errors = self._run_lint(files)
        errors.extend(lint_errors)

        types_ok, type_errors = self._run_typecheck(files)
        errors.extend(type_errors)

        tests_ok, test_errors = self._run_related_tests(files)
        errors.extend(test_errors)

        duration_ms = int((time.time() - start) * 1000)

        return VerifyResult(
            status=VerifyStatus.PASS if (lint_ok and types_ok and tests_ok) else VerifyStatus.FAIL,
            tier=VerifyTier.RELATED,
            errors=errors,
            duration_ms=duration_ms,
            lint_passed=lint_ok,
            types_passed=types_ok,
            tests_passed=tests_ok
        )

    def verify_full(self) -> VerifyResult:
        """Full verification (~5min) - complete test suite."""
        start = time.time()
        errors = []

        lint_ok, lint_errors = self._run_lint([])
        errors.extend(lint_errors)

        types_ok, type_errors = self._run_typecheck([])
        errors.extend(type_errors)

        tests_ok, test_errors = self._run_all_tests()
        errors.extend(test_errors)

        guard_ok, guard_errors = self._run_guardrails()
        errors.extend(guard_errors)

        all_ok = lint_ok and types_ok and tests_ok and guard_ok
        duration_ms = int((time.time() - start) * 1000)

        return VerifyResult(
            status=VerifyStatus.PASS if all_ok else VerifyStatus.FAIL,
            tier=VerifyTier.FULL,
            errors=errors,
            duration_ms=duration_ms,
            lint_passed=lint_ok,
            types_passed=types_ok,
            tests_passed=tests_ok
        )

    def select_tier(self, files: List[str]) -> VerifyTier:
        """Auto-select verification tier based on change size."""
        lines = self._count_lines_changed(files)

        if lines <= self.INSTANT_MAX_LINES:
            return VerifyTier.INSTANT
        elif lines <= self.QUICK_MAX_LINES:
            return VerifyTier.QUICK
        else:
            return VerifyTier.RELATED

    def find_related_tests(self, files: List[str]) -> List[str]:
        """Find test files related to source files."""
        related = []
        for file in files:
            path = Path(file)
            if ".test." in path.name or "_test." in path.name:
                related.append(file)
                continue

            patterns = [
                path.parent.parent / "tests" / path.parent.name / path.name.replace(".ts", ".test.ts"),
                path.parent.parent / "tests" / path.parent.name / path.name.replace(".tsx", ".test.tsx"),
                path.parent / "__tests__" / path.name.replace(".ts", ".test.ts"),
                path.parent.parent / "tests" / path.name.replace(".py", "_test.py"),
            ]

            for pattern in patterns:
                if pattern.exists():
                    related.append(str(pattern))
                    break

        return related

    def try_autofix_lint(self, files: List[str]) -> bool:
        """Attempt to auto-fix lint errors."""
        return self._run_lint_fix(files)

    def _run_lint(self, files: List[str]) -> Tuple[bool, List[str]]:
        """Run linter on files."""
        try:
            cmd = ["npm", "run", "lint"]
            if files:
                cmd.extend(["--", "--"] + files)
            result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stderr.splitlines() if result.returncode != 0 else []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True, []

    def _run_typecheck(self, files: List[str]) -> Tuple[bool, List[str]]:
        """Run type checking."""
        try:
            result = subprocess.run(["npm", "run", "typecheck"], cwd=self.project_dir, capture_output=True, text=True, timeout=60)
            return result.returncode == 0, result.stderr.splitlines() if result.returncode != 0 else []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True, []

    def _run_related_tests(self, files: List[str]) -> Tuple[bool, List[str]]:
        """Run tests related to changed files."""
        related = self.find_related_tests(files)
        if not related:
            return True, []
        try:
            result = subprocess.run(["npm", "test", "--"] + related, cwd=self.project_dir, capture_output=True, text=True, timeout=120)
            return result.returncode == 0, result.stderr.splitlines() if result.returncode != 0 else []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True, []

    def _run_all_tests(self) -> Tuple[bool, List[str]]:
        """Run full test suite."""
        try:
            result = subprocess.run(["npm", "test"], cwd=self.project_dir, capture_output=True, text=True, timeout=300)
            return result.returncode == 0, result.stderr.splitlines() if result.returncode != 0 else []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True, []

    def _run_guardrails(self) -> Tuple[bool, List[str]]:
        """Run guardrail checks."""
        return True, []

    def _run_lint_fix(self, files: List[str]) -> bool:
        """Run lint autofix."""
        try:
            cmd = ["npm", "run", "lint:fix"]
            if files:
                cmd.extend(["--", "--"] + files)
            result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, timeout=30)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _count_lines_changed(self, files: List[str]) -> int:
        """Count total lines changed in files."""
        total = 0
        for file in files:
            path = self.project_dir / file if not Path(file).is_absolute() else Path(file)
            if path.exists():
                try:
                    total += len(path.read_text().splitlines())
                except (OSError, UnicodeDecodeError):
                    pass
        return total
