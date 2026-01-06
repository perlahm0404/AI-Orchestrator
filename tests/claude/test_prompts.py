"""Tests for Claude prompt generation"""

import pytest
from claude.prompts import (
    generate_bugfix_prompt,
    generate_quality_prompt,
    generate_feature_prompt,
    detect_task_type,
    detect_quality_issue_type,
    generate_smart_prompt
)


def test_detect_task_type():
    """Test task type detection from ID"""
    assert detect_task_type("BUG-001") == "bug"
    assert detect_task_type("QUALITY-002") == "quality"
    assert detect_task_type("FEATURE-003") == "feature"
    assert detect_task_type("TEST-004") == "test"
    assert detect_task_type("UNKNOWN-005") == "unknown"
    assert detect_task_type("bug-001") == "bug"  # Case insensitive


def test_detect_quality_issue_type():
    """Test quality issue type detection"""
    assert detect_quality_issue_type("Remove console.error from file") == "console_error"
    assert detect_quality_issue_type("Fix unused import in auth.ts") == "unused_import"
    assert detect_quality_issue_type("Add type annotation to function") == "type_annotation"
    assert detect_quality_issue_type("Fix TypeScript error") == "type_annotation"
    assert detect_quality_issue_type("Fix linting issues") == "lint"
    assert detect_quality_issue_type("Fix failing test") == "test_failure"
    assert detect_quality_issue_type("Some other issue") == "general"


def test_generate_bugfix_prompt_basic():
    """Test basic bug fix prompt generation"""
    prompt = generate_bugfix_prompt(
        bug_description="Fix authentication timeout",
        file_path="src/auth/session.ts"
    )

    assert "Fix this bug: Fix authentication timeout" in prompt
    assert "src/auth/session.ts" in prompt
    assert "Read the file" in prompt
    assert "Fix the bug" in prompt
    assert "Ensure all existing tests still pass" in prompt


def test_generate_bugfix_prompt_with_tests():
    """Test bug fix prompt with test files"""
    prompt = generate_bugfix_prompt(
        bug_description="Fix login bug",
        file_path="src/auth.ts",
        test_files=["tests/auth.test.ts", "tests/login.test.ts"]
    )

    assert "tests/auth.test.ts" in prompt
    assert "tests/login.test.ts" in prompt


def test_generate_bugfix_prompt_with_context():
    """Test bug fix prompt with additional context"""
    prompt = generate_bugfix_prompt(
        bug_description="Fix bug",
        file_path="src/foo.ts",
        context="This bug only occurs in production"
    )

    assert "This bug only occurs in production" in prompt


def test_generate_quality_prompt_console_error():
    """Test quality prompt for console.error removal"""
    prompt = generate_quality_prompt(
        issue_description="Remove console.error",
        file_path="src/logger.ts",
        issue_type="console_error"
    )

    assert "console.error" in prompt
    assert "src/logger.ts" in prompt
    assert "Replace with proper error logging" in prompt


def test_generate_quality_prompt_unused_import():
    """Test quality prompt for unused import"""
    prompt = generate_quality_prompt(
        issue_description="Remove unused import",
        file_path="src/utils.ts",
        issue_type="unused_import"
    )

    assert "unused import" in prompt
    assert "src/utils.ts" in prompt
    assert "Remove it cleanly" in prompt


def test_generate_quality_prompt_type_annotation():
    """Test quality prompt for type annotation"""
    prompt = generate_quality_prompt(
        issue_description="Add type annotation",
        file_path="src/types.ts",
        issue_type="type_annotation"
    )

    assert "type annotation" in prompt
    assert "src/types.ts" in prompt
    assert "TypeScript types" in prompt


def test_generate_quality_prompt_lint():
    """Test quality prompt for linting"""
    prompt = generate_quality_prompt(
        issue_description="Fix linting issues",
        file_path="src/app.ts",
        issue_type="lint"
    )

    assert "linting issues" in prompt
    assert "src/app.ts" in prompt


def test_generate_quality_prompt_test_failure():
    """Test quality prompt for test failure"""
    prompt = generate_quality_prompt(
        issue_description="Fix failing test",
        file_path="tests/app.test.ts",
        issue_type="test_failure"
    )

    assert "failing test" in prompt
    assert "tests/app.test.ts" in prompt


def test_generate_feature_prompt_basic():
    """Test basic feature prompt"""
    prompt = generate_feature_prompt(
        feature_description="Add user authentication",
        files=["src/auth.ts", "src/user.ts"]
    )

    assert "Add user authentication" in prompt
    assert "src/auth.ts" in prompt
    assert "src/user.ts" in prompt
    assert "Read existing code" in prompt
    assert "Write tests" in prompt


def test_generate_feature_prompt_with_criteria():
    """Test feature prompt with acceptance criteria"""
    prompt = generate_feature_prompt(
        feature_description="Add login feature",
        files=["src/login.ts"],
        acceptance_criteria=[
            "User can log in with email",
            "User can log out",
            "Session is persisted"
        ]
    )

    assert "User can log in with email" in prompt
    assert "User can log out" in prompt
    assert "Session is persisted" in prompt


def test_generate_feature_prompt_with_context():
    """Test feature prompt with context"""
    prompt = generate_feature_prompt(
        feature_description="Add feature",
        files=["src/foo.ts"],
        context="Use OAuth 2.0 for authentication"
    )

    assert "Use OAuth 2.0" in prompt


def test_generate_smart_prompt_bug():
    """Test smart prompt for bug task"""
    prompt = generate_smart_prompt(
        task_id="BUG-001",
        description="Fix timeout issue",
        file_path="src/api.ts",
        test_files=["tests/api.test.ts"]
    )

    assert "Fix this bug" in prompt
    assert "Fix timeout issue" in prompt
    assert "src/api.ts" in prompt
    assert "tests/api.test.ts" in prompt


def test_generate_smart_prompt_quality():
    """Test smart prompt for quality task"""
    prompt = generate_smart_prompt(
        task_id="QUALITY-001",
        description="Remove console.error from logging",
        file_path="src/logger.ts"
    )

    assert "console.error" in prompt
    assert "src/logger.ts" in prompt


def test_generate_smart_prompt_feature():
    """Test smart prompt for feature task"""
    prompt = generate_smart_prompt(
        task_id="FEATURE-001",
        description="Add user dashboard",
        file_path="src/dashboard.ts"
    )

    assert "Add user dashboard" in prompt
    assert "src/dashboard.ts" in prompt
    assert "Read existing code" in prompt


def test_generate_smart_prompt_unknown():
    """Test smart prompt for unknown task type"""
    prompt = generate_smart_prompt(
        task_id="UNKNOWN-001",
        description="Do something",
        file_path="src/foo.ts"
    )

    assert "Do something" in prompt
    assert "src/foo.ts" in prompt
