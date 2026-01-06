"""ESLint parser for extracting structured lint errors from JSON output.

Parses output from: npm run lint -- --format=json
"""

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class LintError:
    """Structured representation of an ESLint error."""
    file: str
    line: int
    column: int
    rule_id: str
    severity: int  # 1=warning, 2=error
    message: str
    priority: int  # P0/P1/P2 based on impact

    def __str__(self) -> str:
        severity_label = 'error' if self.severity == 2 else 'warning'
        return f"{self.file}:{self.line}:{self.column} [{severity_label}] {self.rule_id}: {self.message}"


class ESLintParser:
    """Parser for ESLint JSON output."""

    # Security-related rules (P0 priority)
    SECURITY_RULES = {
        'no-eval',
        'no-implied-eval',
        'no-new-func',
        'no-script-url',
        'react/no-danger',
        'react/no-danger-with-children',
        'security/detect-eval-with-expression',
        'security/detect-non-literal-regexp',
        'security/detect-unsafe-regex',
    }

    # Correctness rules (P1 priority)
    CORRECTNESS_RULES = {
        'unused-imports/no-unused-imports',
        'no-unused-vars',
        '@typescript-eslint/no-unused-vars',
        'no-console',
        'no-debugger',
        'no-unreachable',
        'no-constant-condition',
        'no-duplicate-case',
        'no-empty',
        'no-extra-semi',
        'no-func-assign',
        'no-inner-declarations',
        'no-invalid-regexp',
        'no-irregular-whitespace',
        'no-obj-calls',
        'no-sparse-arrays',
        'no-unexpected-multiline',
        'use-isnan',
        'valid-typeof',
        '@typescript-eslint/no-explicit-any',
        '@typescript-eslint/no-non-null-assertion',
    }

    # All other rules default to P2 (style/formatting)

    def parse(self, json_output: str) -> list[LintError]:
        """
        Parse ESLint JSON output into structured LintError list.

        Args:
            json_output: Raw JSON string from eslint --format=json

        Returns:
            List of LintError objects
        """
        if not json_output or not json_output.strip():
            return []

        # Extract only the JSON array (filter out warnings/logs)
        # Look for the start of the JSON array
        try:
            json_start = json_output.index('[')
            json_output = json_output[json_start:]

            # Find the matching closing bracket
            # Use a simple approach: find the last ] that makes valid JSON
            decoder = json.JSONDecoder()
            data, end_idx = decoder.raw_decode(json_output)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  Failed to parse ESLint JSON: {e}")
            return []

        errors = []

        # ESLint JSON format: array of file results
        for file_result in data:
            file_path = file_result.get('filePath', '')
            messages = file_result.get('messages', [])

            for msg in messages:
                rule_id = msg.get('ruleId')
                if not rule_id:
                    # Skip messages without rule ID (e.g., parsing errors)
                    continue

                error = LintError(
                    file=self._normalize_path(file_path),
                    line=msg.get('line', 0),
                    column=msg.get('column', 0),
                    rule_id=rule_id,
                    severity=msg.get('severity', 1),
                    message=msg.get('message', ''),
                    priority=self._compute_priority(rule_id, msg.get('severity', 1))
                )
                errors.append(error)

        return errors

    def _compute_priority(self, rule_id: str, severity: int) -> int:
        """
        Compute priority (P0/P1/P2) based on rule type and severity.

        P0 (blocks users):
        - Security rules (eval, XSS, etc.)

        P1 (degrades UX):
        - Correctness rules (unused vars, console.error, etc.)
        - Errors (severity=2) that aren't style-only

        P2 (tech debt):
        - Style/formatting rules
        - Warnings (severity=1)
        """
        if rule_id in self.SECURITY_RULES:
            return 0  # P0: Security issues

        if rule_id in self.CORRECTNESS_RULES:
            return 1  # P1: Correctness issues

        # Errors in non-style rules get P1, warnings/style get P2
        if severity == 2 and not self._is_style_rule(rule_id):
            return 1  # P1: Non-style errors

        return 2  # P2: Style/formatting

    def _is_style_rule(self, rule_id: str) -> bool:
        """Check if rule is purely style/formatting."""
        style_keywords = [
            'indent',
            'quotes',
            'semi',
            'comma',
            'spacing',
            'whitespace',
            'newline',
            'brace-style',
            'import/order',
            'import/newline-after-import',
            'prettier',
        ]
        return any(keyword in rule_id.lower() for keyword in style_keywords)

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path (remove absolute prefix if present)."""
        # ESLint often returns absolute paths, convert to relative
        # e.g., /Users/foo/karematch/src/auth.ts → src/auth.ts

        # Find common project markers
        markers = ['/services/', '/packages/', '/apps/', '/src/']

        for marker in markers:
            if marker in file_path:
                # Extract path from first marker onwards
                parts = file_path.split(marker)
                if len(parts) > 1:
                    return marker.lstrip('/') + marker.join(parts[1:])

        # If no marker found, return as-is (might already be relative)
        return file_path
