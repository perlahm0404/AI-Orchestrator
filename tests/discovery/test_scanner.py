"""Integration tests for bug discovery scanner.

Tests end-to-end workflow:
1. Scanner runs commands and collects results
2. Baseline manager tracks known vs. new bugs
3. Task generator creates grouped tasks
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from discovery.scanner import BugScanner, ScanResult
from discovery.baseline import BaselineManager
from discovery.task_generator import TaskGenerator
from discovery.parsers.eslint import LintError
from discovery.parsers.typescript import TypeScriptError


class TestScannerIntegration:
    """Integration tests for BugScanner."""

    def test_scan_result_by_file_grouping(self):
        """Test that scan results can be grouped by file."""
        # Create a scan result with mixed error types
        scan_result = ScanResult(
            timestamp=None,
            project="test",
            lint_errors=[
                LintError("src/auth.ts", 10, 5, "no-unused-vars", 2, "Unused var", 1),
                LintError("src/auth.ts", 15, 10, "no-console", 1, "Console log", 2),
                LintError("src/utils.ts", 20, 5, "indent", 1, "Indent error", 2),
            ],
            type_errors=[
                TypeScriptError("src/auth.ts", 42, 10, "TS2345", "Type mismatch", 1),
            ],
            test_failures=[],
            guardrail_violations=[]
        )

        # Group by file
        by_file = scan_result.by_file()

        # Verify grouping
        assert "src/auth.ts" in by_file
        assert "src/utils.ts" in by_file
        assert len(by_file["src/auth.ts"]) == 3  # 2 lint + 1 type
        assert len(by_file["src/utils.ts"]) == 1  # 1 lint

    def test_total_errors_count(self):
        """Test total error counting."""
        scan_result = ScanResult(
            timestamp=None,
            project="test",
            lint_errors=[Mock(), Mock()],  # 2 lint errors
            type_errors=[Mock()],  # 1 type error
            test_failures=[Mock()],  # 1 test failure
            guardrail_violations=[Mock(), Mock()]  # 2 guardrails
        )

        assert scan_result.total_errors() == 6


class TestBaselineIntegration:
    """Integration tests for BaselineManager."""

    def test_baseline_creation_and_comparison(self, tmp_path):
        """Test creating baseline and comparing with new scan."""
        # Create baseline manager with temp directory
        with patch.object(BaselineManager, '__init__', lambda self, project: None):
            baseline_mgr = BaselineManager("test")
            baseline_mgr.project_name = "test"
            baseline_mgr.baseline_dir = tmp_path
            baseline_mgr.baseline_file = tmp_path / "test-baseline.json"

            # Create initial scan result
            scan1 = ScanResult(
                timestamp=None,
                project="test",
                lint_errors=[
                    LintError("src/auth.ts", 10, 5, "no-unused-vars", 2, "Unused var", 1),
                ],
                type_errors=[],
                test_failures=[],
                guardrail_violations=[]
            )

            # Create baseline
            baseline_mgr.create_baseline(scan1)

            # Verify baseline file created
            assert baseline_mgr.baseline_file.exists()

            # Create new scan with additional error (regression)
            scan2 = ScanResult(
                timestamp=None,
                project="test",
                lint_errors=[
                    LintError("src/auth.ts", 10, 5, "no-unused-vars", 2, "Unused var", 1),  # Baseline
                    LintError("src/auth.ts", 20, 5, "no-console", 1, "Console", 2),  # NEW
                ],
                type_errors=[],
                test_failures=[],
                guardrail_violations=[]
            )

            # Compare with baseline
            new_bugs, baseline_bugs = baseline_mgr.compare_with_baseline(scan2)

            # Verify classification
            assert len(new_bugs) == 1  # New console error
            assert len(baseline_bugs) == 1  # Existing unused-vars error


class TestTaskGeneratorIntegration:
    """Integration tests for TaskGenerator."""

    def test_task_generation_groups_by_file(self):
        """Test that task generator groups bugs by file."""
        # Create scan result with bugs in 2 files
        scan_result = ScanResult(
            timestamp=None,
            project="test",
            lint_errors=[
                LintError("src/auth.ts", 10, 5, "no-unused-vars", 2, "Unused var", 1),
                LintError("src/auth.ts", 15, 10, "no-console", 1, "Console", 2),
                LintError("src/utils.ts", 20, 5, "indent", 1, "Indent", 2),
            ],
            type_errors=[],
            test_failures=[],
            guardrail_violations=[]
        )

        # Create bug dicts (simulating baseline comparison)
        bugs = [
            {'file': 'src/auth.ts', 'line': 10, 'type': 'lint', 'rule': 'no-unused-vars',
             'fingerprint': 'abc123', 'original_error': scan_result.lint_errors[0], 'is_new': False},
            {'file': 'src/auth.ts', 'line': 15, 'type': 'lint', 'rule': 'no-console',
             'fingerprint': 'def456', 'original_error': scan_result.lint_errors[1], 'is_new': False},
            {'file': 'src/utils.ts', 'line': 20, 'type': 'lint', 'rule': 'indent',
             'fingerprint': 'ghi789', 'original_error': scan_result.lint_errors[2], 'is_new': False},
        ]

        # Generate tasks
        task_gen = TaskGenerator("test")
        tasks = task_gen.generate_tasks(scan_result, [], bugs)

        # Verify grouping (2 files = 2 tasks)
        assert len(tasks) == 2

        # Verify file grouping
        auth_tasks = [t for t in tasks if t.file == 'src/auth.ts']
        utils_tasks = [t for t in tasks if t.file == 'src/utils.ts']

        assert len(auth_tasks) == 1
        assert len(utils_tasks) == 1

        # Verify bug counts
        assert auth_tasks[0].bug_count == 2
        assert utils_tasks[0].bug_count == 1

    def test_priority_assignment(self):
        """Test that priorities are assigned correctly."""
        scan_result = ScanResult(
            timestamp=None,
            project="test",
            lint_errors=[
                LintError("src/auth.ts", 10, 5, "no-eval", 2, "Eval detected", 0),  # Security (P0)
            ],
            type_errors=[],
            test_failures=[],
            guardrail_violations=[]
        )

        bugs = [
            {'file': 'src/auth.ts', 'line': 10, 'type': 'lint', 'rule': 'no-eval',
             'fingerprint': 'abc123', 'original_error': scan_result.lint_errors[0], 'is_new': True},
        ]

        task_gen = TaskGenerator("test")
        tasks = task_gen.generate_tasks(scan_result, bugs, [])

        assert len(tasks) == 1
        assert tasks[0].priority == 0  # P0 for security
        assert tasks[0].is_new is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
