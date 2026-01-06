"""Test parser for extracting structured test failures from test runner output.

Parses output from: npm test -- --reporter=json (Vitest JSON reporter)
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestFailure:
    """Structured representation of a test failure."""
    test_file: str
    test_name: str
    failure_message: str
    source_file: str  # Inferred from test file name
    priority: int  # P0/P1/P2 based on impact

    def __str__(self) -> str:
        return f"{self.test_file} - {self.test_name}: {self.failure_message[:100]}"


class TestParser:
    """Parser for Vitest JSON output."""

    # Critical test file patterns (P0 priority)
    CRITICAL_TEST_PATHS = [
        'auth',
        'login',
        'session',
        'payment',
        'checkout',
        'security',
    ]

    # Feature test patterns (P1 priority)
    FEATURE_TEST_PATHS = [
        'matching',
        'credentialing',
        'wizard',
        'appointments',
        'profile',
        'onboarding',
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

    def parse(self, json_output: str) -> list[TestFailure]:
        """
        Parse Vitest JSON output into structured TestFailure list.

        Args:
            json_output: Raw JSON string from vitest --reporter=json

        Returns:
            List of TestFailure objects

        Vitest JSON format:
        {
          "testResults": [{
            "name": "services/auth/tests/login.test.ts",
            "status": "failed",
            "assertionResults": [{
              "title": "should authenticate valid user",
              "status": "failed",
              "failureMessages": ["Expected 200, got 401"]
            }]
          }]
        }
        """
        if not json_output or not json_output.strip():
            return []

        # Extract only the JSON object (filter out log messages)
        # Vitest with JSON reporter outputs logs first, then JSON at the end
        try:
            # Look for the start of JSON object
            json_start = json_output.index('{')
            json_output = json_output[json_start:]

            # Use JSONDecoder to extract valid JSON
            decoder = json.JSONDecoder()
            data, end_idx = decoder.raw_decode(json_output)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  Failed to parse test JSON: {e}")
            return []

        failures = []

        # Handle Vitest JSON format
        test_results = data.get('testResults', [])

        for test_result in test_results:
            test_file = test_result.get('name', '')
            status = test_result.get('status', '')

            if status != 'failed':
                continue

            assertion_results = test_result.get('assertionResults', [])

            for assertion in assertion_results:
                if assertion.get('status') == 'failed':
                    test_name = assertion.get('title', '')
                    failure_messages = assertion.get('failureMessages', [])
                    failure_message = '\n'.join(failure_messages) if failure_messages else ''

                    source_file = self._infer_source_file(test_file)

                    failure = TestFailure(
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
            services/auth/tests/login.test.ts → services/auth/src/login.ts
            packages/utils/__tests__/index.test.ts → packages/utils/index.ts
            apps/web/src/components/__tests__/Button.test.tsx → apps/web/src/components/Button.tsx
        """
        # Remove .test.* extension
        source = test_file.replace('.test.ts', '.ts').replace('.test.tsx', '.tsx')

        # Replace test directory patterns with src
        if '/tests/' in source:
            source = source.replace('/tests/', '/src/')
        elif '/__tests__/' in source:
            source = source.replace('/__tests__/', '/')
        elif '/test/' in source:
            source = source.replace('/test/', '/src/')

        return source

    def _compute_priority(self, test_file: str, failure_message: str) -> int:
        """
        Compute priority (P0/P1/P2) based on test file path and failure message.

        P0 (blocks users):
        - Auth/payment/security test failures (blocks core functionality)

        P1 (degrades UX):
        - Feature test failures (degrades UX but not blocking)
        - New test failures (regressions)

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
        # Find common project markers
        markers = ['/services/', '/packages/', '/apps/', '/src/', '/tests/']

        for marker in markers:
            if marker in file_path:
                # Extract path from first marker onwards
                parts = file_path.split(marker)
                if len(parts) > 1:
                    return marker.lstrip('/') + marker.join(parts[1:])

        # If no marker found, return as-is (likely already relative)
        return file_path
