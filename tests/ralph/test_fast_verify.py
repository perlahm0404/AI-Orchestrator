"""
Tests for Fast Verification System (Phase 2)

TDD approach: Tests written first, then implementation.
Target: 30-second verification vs 5-minute full Ralph.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import List
from enum import Enum

# These imports will fail until we implement the modules
try:
    from ralph.fast_verify import (
        FastVerify,
        VerifyResult,
        VerifyStatus,
        VerifyTier,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

    # Placeholder classes for test definition
    class VerifyStatus(Enum):
        PASS = "PASS"
        FAIL = "FAIL"
        BLOCKED = "BLOCKED"

    class VerifyTier(Enum):
        INSTANT = "instant"
        QUICK = "quick"
        RELATED = "related"
        FULL = "full"

    @dataclass
    class VerifyResult:
        status: VerifyStatus
        tier: VerifyTier
        errors: List[str]
        duration_ms: int
        lint_passed: bool = True
        types_passed: bool = True
        tests_passed: bool = True


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestVerifyResult:
    """Test VerifyResult dataclass."""

    def test_pass_result(self):
        """PASS result has correct fields."""
        result = VerifyResult(
            status=VerifyStatus.PASS,
            tier=VerifyTier.QUICK,
            errors=[],
            duration_ms=1500,
        )
        assert result.status == VerifyStatus.PASS

    def test_fail_result_with_errors(self):
        """FAIL result contains error details."""
        result = VerifyResult(
            status=VerifyStatus.FAIL,
            tier=VerifyTier.INSTANT,
            errors=["Line 10: Missing semicolon"],
            duration_ms=500,
            lint_passed=False
        )
        assert result.status == VerifyStatus.FAIL
        assert "semicolon" in result.errors[0]


class TestFastVerifyInstantTier:
    """Test instant tier (<5s) - lint only."""

    @pytest.fixture
    def fast_verify(self, tmp_path: Path):
        return FastVerify(project_dir=tmp_path)

    def test_lint_pass(self, fast_verify, tmp_path: Path):
        """Lint passes for clean file."""
        test_file = tmp_path / "clean.ts"
        test_file.write_text("const x = 1;\n")

        with patch.object(fast_verify, '_run_lint') as mock_lint:
            mock_lint.return_value = (True, [])
            result = fast_verify.verify_instant([str(test_file)])

        assert result.status == VerifyStatus.PASS
        assert result.lint_passed is True

    def test_lint_fail(self, fast_verify, tmp_path: Path):
        """Lint fails for problematic file."""
        test_file = tmp_path / "bad.ts"
        test_file.write_text("const x = 1\n")

        with patch.object(fast_verify, '_run_lint') as mock_lint:
            mock_lint.return_value = (False, ["Missing semicolon"])
            result = fast_verify.verify_instant([str(test_file)])

        assert result.status == VerifyStatus.FAIL
        assert result.lint_passed is False


class TestFastVerifyQuickTier:
    """Test quick tier (<30s) - lint + types."""

    @pytest.fixture
    def fast_verify(self, tmp_path: Path):
        return FastVerify(project_dir=tmp_path)

    def test_quick_runs_lint_and_types(self, fast_verify, tmp_path: Path):
        """Quick tier runs both lint and type checking."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x: number = 1;\n")

        with patch.object(fast_verify, '_run_lint') as mock_lint:
            with patch.object(fast_verify, '_run_typecheck') as mock_types:
                mock_lint.return_value = (True, [])
                mock_types.return_value = (True, [])
                result = fast_verify.verify_quick([str(test_file)])

        assert result.status == VerifyStatus.PASS
        assert result.lint_passed is True
        assert result.types_passed is True

    def test_quick_fails_on_type_error(self, fast_verify, tmp_path: Path):
        """Quick tier fails on type error."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x: number = 'string';\n")

        with patch.object(fast_verify, '_run_lint') as mock_lint:
            with patch.object(fast_verify, '_run_typecheck') as mock_types:
                mock_lint.return_value = (True, [])
                mock_types.return_value = (False, ["Type error"])
                result = fast_verify.verify_quick([str(test_file)])

        assert result.status == VerifyStatus.FAIL
        assert result.types_passed is False


class TestFastVerifyRelatedTier:
    """Test related tier (<60s) - lint + types + related tests."""

    @pytest.fixture
    def fast_verify(self, tmp_path: Path):
        return FastVerify(project_dir=tmp_path)

    def test_related_runs_all_three(self, fast_verify, tmp_path: Path):
        """Related tier runs lint, types, and related tests."""
        src_file = tmp_path / "src" / "auth.ts"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("export function login() {}\n")

        with patch.object(fast_verify, '_run_lint') as mock_lint:
            with patch.object(fast_verify, '_run_typecheck') as mock_types:
                with patch.object(fast_verify, '_run_related_tests') as mock_tests:
                    mock_lint.return_value = (True, [])
                    mock_types.return_value = (True, [])
                    mock_tests.return_value = (True, [])
                    result = fast_verify.verify_related([str(src_file)])

        assert result.status == VerifyStatus.PASS
        assert result.tests_passed is True


class TestVerifyTierSelection:
    """Test automatic tier selection."""

    @pytest.fixture
    def fast_verify(self, tmp_path: Path):
        return FastVerify(project_dir=tmp_path)

    def test_selects_instant_for_small_change(self, fast_verify, tmp_path: Path):
        """Small changes get instant tier."""
        file = tmp_path / "small.ts"
        file.write_text("x\n")

        with patch.object(fast_verify, '_count_lines_changed', return_value=5):
            tier = fast_verify.select_tier([str(file)])

        assert tier == VerifyTier.INSTANT

    def test_selects_quick_for_medium_change(self, fast_verify, tmp_path: Path):
        """Medium changes get quick tier."""
        file = tmp_path / "medium.ts"
        file.write_text("x\n" * 50)

        with patch.object(fast_verify, '_count_lines_changed', return_value=50):
            tier = fast_verify.select_tier([str(file)])

        assert tier == VerifyTier.QUICK
