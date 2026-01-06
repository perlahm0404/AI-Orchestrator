"""Tests for Claude CLI wrapper"""

import pytest
from pathlib import Path
from claude.cli_wrapper import ClaudeCliWrapper, ClaudeResult


def test_cli_wrapper_init(tmp_path):
    """Test wrapper initialization"""
    wrapper = ClaudeCliWrapper(tmp_path)
    assert wrapper.project_dir == tmp_path


def test_parse_changed_files():
    """Test parsing changed files from output"""
    wrapper = ClaudeCliWrapper(Path("/tmp"))

    output = """
Modified: src/auth.ts
Created: tests/auth.test.ts
Some other output
Updated: src/utils.ts
Random text here
Modified: components/Header.tsx
"""

    files = wrapper._parse_changed_files(output)
    assert len(files) == 4
    assert "src/auth.ts" in files
    assert "tests/auth.test.ts" in files
    assert "src/utils.ts" in files
    assert "components/Header.tsx" in files


def test_parse_changed_files_empty():
    """Test parsing with no changed files"""
    wrapper = ClaudeCliWrapper(Path("/tmp"))

    output = """
Some output
No file changes here
Just regular text
"""

    files = wrapper._parse_changed_files(output)
    assert len(files) == 0


def test_parse_changed_files_with_paths():
    """Test parsing with full paths"""
    wrapper = ClaudeCliWrapper(Path("/tmp"))

    output = """
Modified: src/services/auth/session.ts
Created: tests/integration/auth.test.ts
Updated: packages/api/src/routes.ts
"""

    files = wrapper._parse_changed_files(output)
    assert len(files) == 3
    assert "src/services/auth/session.ts" in files
    assert "tests/integration/auth.test.ts" in files
    assert "packages/api/src/routes.ts" in files


def test_result_dataclass():
    """Test ClaudeResult dataclass"""
    result = ClaudeResult(
        success=True,
        output="Task complete",
        files_changed=["src/test.ts"]
    )

    assert result.success is True
    assert result.error is None
    assert len(result.files_changed) == 1
    assert result.files_changed[0] == "src/test.ts"


def test_result_dataclass_with_error():
    """Test ClaudeResult with error"""
    result = ClaudeResult(
        success=False,
        output="",
        error="Timeout occurred",
        duration_ms=5000
    )

    assert result.success is False
    assert result.error == "Timeout occurred"
    assert result.duration_ms == 5000
    assert len(result.files_changed) == 0


def test_result_dataclass_defaults():
    """Test ClaudeResult with minimal initialization"""
    result = ClaudeResult(
        success=True,
        output="Done"
    )

    assert result.success is True
    assert result.output == "Done"
    assert result.error is None
    assert result.files_changed == []
    assert result.duration_ms == 0
