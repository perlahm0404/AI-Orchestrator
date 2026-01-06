"""Tests for self-correction system"""

import pytest
from agents.self_correct import analyze_failure, FixStrategy
from ralph.fast_verify import VerifyResult


def test_analyze_lint_failure():
    """Test analysis of lint failures"""
    result = VerifyResult(
        status="FAIL",
        reason="Lint errors",
        lint_errors=["Missing semicolon", "Unused variable"]
    )

    strategy = analyze_failure(result)

    assert strategy.action == "run_autofix"
    assert strategy.command == "npm run lint:fix"
    assert strategy.retry_immediately is True


def test_analyze_type_failure():
    """Test analysis of type errors"""
    result = VerifyResult(
        status="FAIL",
        reason="Type errors",
        type_errors=["Type 'string' is not assignable to type 'number'"]
    )

    strategy = analyze_failure(result)

    assert strategy.action == "fix_types"
    assert "TypeScript type errors" in strategy.prompt
    assert strategy.retry_immediately is False


def test_analyze_test_failure():
    """Test analysis of test failures"""
    result = VerifyResult(
        status="FAIL",
        reason="Tests failed",
        test_failures=["Expected 42 but got 43"]
    )

    strategy = analyze_failure(result)

    assert strategy.action == "fix_implementation"
    assert "Tests failed" in strategy.prompt
    assert strategy.retry_immediately is False


def test_analyze_unknown_failure():
    """Test analysis of unknown failures"""
    result = VerifyResult(
        status="FAIL",
        reason="Unknown error"
    )

    strategy = analyze_failure(result)

    assert strategy.action == "escalate"
