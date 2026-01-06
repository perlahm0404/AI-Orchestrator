"""Tests for fast verification system"""

import pytest
from pathlib import Path
from ralph.fast_verify import (
    VerifyResult,
    find_related_tests,
    fast_verify
)


def test_verify_result_properties():
    """Test VerifyResult property methods"""
    result = VerifyResult(
        status="FAIL",
        lint_errors=["error 1"],
        type_errors=[],
        test_failures=[]
    )

    assert result.has_lint_errors is True
    assert result.has_type_errors is False
    assert result.has_test_failures is False


def test_find_related_tests(tmp_path):
    """Test finding related test files"""
    # Create fake project structure
    src_dir = tmp_path / "src" / "auth"
    src_dir.mkdir(parents=True)

    tests_dir = tmp_path / "tests" / "auth"
    tests_dir.mkdir(parents=True)

    # Create test file
    test_file = tests_dir / "session.test.ts"
    test_file.write_text("// test")

    # Find tests for src file
    changed_files = ["src/auth/session.ts"]
    related_tests = find_related_tests(tmp_path, changed_files)

    assert "tests/auth/session.test.ts" in related_tests


def test_verify_result_pass_status():
    """Test PASS status result"""
    result = VerifyResult(
        status="PASS",
        reason="All checks passed",
        duration_ms=1500
    )

    assert result.status == "PASS"
    assert result.has_lint_errors is False
    assert result.has_type_errors is False
    assert result.has_test_failures is False
