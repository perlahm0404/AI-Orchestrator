"""Ruff parser for extracting structured lint errors from JSON output.

Parses output from: ruff check --output-format=json
"""

import json
from dataclasses import dataclass


@dataclass
class RuffError:
    """Structured representation of a Ruff lint error."""
    file: str
    line: int
    column: int
    rule_id: str
    severity: str  # "error" or "warning"
    message: str
    priority: int  # P0/P1/P2 based on impact

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column} [{self.severity}] {self.rule_id}: {self.message}"


class RuffParser:
    """Parser for Ruff JSON output."""

    # Security-related rules (P0 priority)
    SECURITY_RULES = {
        'S', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7',  # Security rules
        'E501',  # SQL injection patterns
    }

    # Correctness rules (P1 priority)
    CORRECTNESS_RULES = {
        'F',  # Pyflakes (undefined names, unused imports)
        'E',  # pycodestyle errors
        'W',  # pycodestyle warnings
        'B',  # flake8-bugbear (likely bugs)
        'N',  # pep8-naming
        'UP',  # pyupgrade
    }

    def parse(self, json_output: str) -> list[RuffError]:
        """
        Parse Ruff JSON output into structured RuffError list.

        Args:
            json_output: Raw JSON string from ruff check --format=json

        Returns:
            List of RuffError objects
        """
        if not json_output or not json_output.strip():
            return []

        # Extract only the JSON array (filter out warnings/logs)
        try:
            json_start = json_output.index('[')
            json_output = json_output[json_start:]

            # Use JSONDecoder to extract valid JSON
            decoder = json.JSONDecoder()
            data, end_idx = decoder.raw_decode(json_output)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  Failed to parse Ruff JSON: {e}")
            return []

        errors = []

        # Ruff JSON format: array of violation objects
        for violation in data:
            code = violation.get('code', '')
            if not code:
                continue

            error = RuffError(
                file=self._normalize_path(violation.get('filename', '')),
                line=violation.get('location', {}).get('row', 0),
                column=violation.get('location', {}).get('column', 0),
                rule_id=code,
                severity='error',  # Ruff treats everything as error by default
                message=violation.get('message', ''),
                priority=self._compute_priority(code)
            )
            errors.append(error)

        return errors

    def _compute_priority(self, rule_id: str) -> int:
        """
        Compute priority (P0/P1/P2) based on rule type.

        P0 (blocks users):
        - Security rules (S*)

        P1 (degrades UX):
        - Correctness rules (F*, E*, W*, B*)
        - Undefined names, unused imports

        P2 (tech debt):
        - Style/formatting rules
        """
        # Get rule prefix (e.g., 'S' from 'S101', 'F' from 'F401')
        rule_prefix = ''.join(c for c in rule_id if c.isalpha())

        if any(rule_id.startswith(sec) for sec in self.SECURITY_RULES):
            return 0  # P0: Security issues

        if any(rule_id.startswith(cor) for cor in self.CORRECTNESS_RULES):
            return 1  # P1: Correctness issues

        return 2  # P2: Style/formatting

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path (remove absolute prefix if present)."""
        # Ruff returns relative paths by default
        # But handle absolute paths just in case
        markers = ['/app/', '/api/', '/tests/', '/src/']

        for marker in markers:
            if marker in file_path:
                parts = file_path.split(marker)
                if len(parts) > 1:
                    return marker.lstrip('/') + marker.join(parts[1:])

        return file_path
