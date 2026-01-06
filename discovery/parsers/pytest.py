"""Pytest parser for extracting structured test failures from JSON output.

Parses output from: pytest --json-report or pytest -v
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PytestFailure:
    """Structured representation of a pytest failure."""
    test_file: str
    test_name: str
    failure_message: str
    source_file: str  # Inferred from test file name
    priority: int  # P0/P1/P2 based on impact

    def __str__(self) -> str:
        return f"{self.test_file} - {self.test_name}: {self.failure_message[:100]}"


class PytestParser:
    """Parser for pytest output."""

    # Critical test file patterns (P0 priority)
    CRITICAL_TEST_PATHS = [
        'auth',
        'login',
        'session',
        'security',
    ]

    # Feature test patterns (P1 priority)
    FEATURE_TEST_PATHS = [
        'api',
        'routes',
        'models',
        'services',
    ]

    # Flaky test indicators (P2 priority)
    FLAKY_INDICATORS = [
        'timeout',
        'timing',
        'race condition',
        'intermittent',
        'sometimes fails',
        'flaky',
    ]

    def parse(self, pytest_output: str) -> list[PytestFailure]:
        """
        Parse pytest output into structured PytestFailure list.

        Supports both:
        - Verbose output (pytest -v)
        - JSON output (pytest --json-report)

        Args:
            pytest_output: Raw output from pytest

        Returns:
            List of PytestFailure objects
        """
        if not pytest_output or not pytest_output.strip():
            return []

        # Try JSON format first
        try:
            return self._parse_json(pytest_output)
        except (json.JSONDecodeError, KeyError):
            # Fall back to verbose output parsing
            return self._parse_verbose(pytest_output)

    def _parse_json(self, json_output: str) -> list[PytestFailure]:
        """Parse pytest JSON report format."""
        data = json.loads(json_output)
        failures = []

        tests = data.get('tests', [])
        for test in tests:
            if test.get('outcome') != 'failed':
                continue

            test_name = test.get('nodeid', '')
            # Split nodeid: "tests/test_auth.py::test_login"
            parts = test_name.split('::')
            test_file = parts[0] if parts else ''
            test_func = parts[1] if len(parts) > 1 else test_name

            call_info = test.get('call', {})
            longrepr = call_info.get('longrepr', '')

            source_file = self._infer_source_file(test_file)

            failure = PytestFailure(
                test_file=self._normalize_path(test_file),
                test_name=test_func,
                failure_message=longrepr,
                source_file=source_file,
                priority=self._compute_priority(test_file, longrepr)
            )
            failures.append(failure)

        return failures

    def _parse_verbose(self, verbose_output: str) -> list[PytestFailure]:
        """Parse pytest verbose output format."""
        failures = []

        # Pattern for FAILED lines:
        # tests/test_auth.py::test_login FAILED
        failed_pattern = re.compile(r'^(.+?)::(.+?)\s+FAILED', re.MULTILINE)

        for match in failed_pattern.finditer(verbose_output):
            test_file = match.group(1)
            test_name = match.group(2)

            # Try to extract failure message from surrounding context
            # This is approximate - JSON format is more reliable
            failure_message = "Test failed (run with --json-report for details)"

            source_file = self._infer_source_file(test_file)

            failure = PytestFailure(
                test_file=self._normalize_path(test_file),
                test_name=test_name,
                failure_message=failure_message,
                source_file=source_file,
                priority=self._compute_priority(test_file, failure_message)
            )
            failures.append(failure)

        return failures

    def _infer_source_file(self, test_file: str) -> str:
        """
        Infer source file path from test file path.

        Examples:
            tests/test_auth.py → app/auth.py
            tests/auth/test_session.py → app/auth/session.py
            tests/api/test_routes.py → api/routes.py
        """
        # Remove test_ prefix from filename
        if '/test_' in test_file:
            source = test_file.replace('/test_', '/')
        elif test_file.startswith('test_'):
            source = test_file[5:]  # Remove 'test_' prefix
        else:
            source = test_file

        # Replace tests/ with app/ or api/
        if source.startswith('tests/'):
            # Try to infer if it's app/ or api/ based on path
            if 'api' in source:
                source = source.replace('tests/', 'api/')
            else:
                source = source.replace('tests/', 'app/')

        return source

    def _compute_priority(self, test_file: str, failure_message: str) -> int:
        """
        Compute priority (P0/P1/P2) based on test file path and failure message.

        P0 (blocks users):
        - Auth/security test failures (blocks core functionality)

        P1 (degrades UX):
        - Feature test failures (degrades UX but not blocking)
        - API test failures

        P2 (tech debt):
        - Flaky tests (timing, race conditions)
        - Low-impact areas
        """
        test_file_lower = test_file.lower()
        failure_lower = failure_message.lower()

        # Check for flaky test indicators (lowest priority)
        if any(indicator in failure_lower for indicator in self.FLAKY_INDICATORS):
            return 2  # P2: Flaky tests

        # Check for critical paths (highest priority)
        if any(path in test_file_lower for path in self.CRITICAL_TEST_PATHS):
            return 0  # P0: Critical path failures

        # Check for feature paths (medium priority)
        if any(path in test_file_lower for path in self.FEATURE_TEST_PATHS):
            return 1  # P1: Feature failures

        # Default to P1 (unknown tests assumed important until proven otherwise)
        return 1  # P1: Unknown test failures

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path (remove absolute prefix if present)."""
        markers = ['/tests/', '/app/', '/api/']

        for marker in markers:
            if marker in file_path:
                parts = file_path.split(marker)
                if len(parts) > 1:
                    return marker.lstrip('/') + marker.join(parts[1:])

        return file_path
