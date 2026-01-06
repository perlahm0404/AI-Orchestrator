"""Guardrails parser for detecting code quality suppression patterns.

Parses output from: rg --json (ripgrep JSON output)
Detects: @ts-ignore, @ts-nocheck, eslint-disable, .skip(), .only()
"""

import json
from dataclasses import dataclass


@dataclass
class GuardrailViolation:
    """Structured representation of a guardrail violation."""
    file: str
    line: int
    pattern: str  # "@ts-ignore", "eslint-disable", etc.
    context: str  # Surrounding code
    priority: int  # P0/P1/P2 based on impact

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.pattern}] {self.context[:50]}"


class GuardrailParser:
    """Parser for ripgrep JSON output to detect suppression patterns."""

    # Patterns to detect (in priority order)
    PATTERNS = {
        '.only(': 0,        # P0: Blocks comprehensive testing
        '.skip(': 0,        # P0: Blocks comprehensive testing
        'it.only': 0,       # P0: Vitest exclusive test
        'describe.only': 0, # P0: Vitest exclusive suite
        '@ts-ignore': 1,    # P1: Suppresses type errors
        'eslint-disable': 1,  # P1: Suppresses lint errors
        '@ts-nocheck': 2,   # P2: File-level suppression (tech debt)
        '// @ts-expect-error': 2,  # P2: Intentional suppression
    }

    def parse(self, rg_output: str) -> list[GuardrailViolation]:
        """
        Parse ripgrep JSON output into structured GuardrailViolation list.

        Args:
            rg_output: Raw JSON string from rg --json

        Returns:
            List of GuardrailViolation objects

        Ripgrep JSON format (newline-delimited JSON):
        {"type":"match","data":{"path":{"text":"src/auth.ts"},"lines":{"text":"// @ts-ignore\n"},"line_number":42}}
        """
        if not rg_output or not rg_output.strip():
            return []

        violations = []

        # Parse newline-delimited JSON (each line is a separate JSON object)
        for line in rg_output.strip().split('\n'):
            if not line.strip():
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Only process match objects
            if obj.get('type') != 'match':
                continue

            data = obj.get('data', {})
            path_info = data.get('path', {})
            lines_info = data.get('lines', {})

            file_path = path_info.get('text', '')
            line_number = data.get('line_number', 0)
            line_text = lines_info.get('text', '').strip()

            # Detect which pattern matched
            pattern = self._detect_pattern(line_text)
            if not pattern:
                continue

            violation = GuardrailViolation(
                file=self._normalize_path(file_path),
                line=line_number,
                pattern=pattern,
                context=line_text,
                priority=self.PATTERNS.get(pattern, 2)
            )
            violations.append(violation)

        return violations

    def _detect_pattern(self, line_text: str) -> str:
        """Detect which guardrail pattern is present in the line."""
        line_lower = line_text.lower()

        # Check each pattern (in order of specificity)
        if 'it.only' in line_lower or 'describe.only' in line_lower:
            return 'it.only' if 'it.only' in line_lower else 'describe.only'

        if '.only(' in line_text:
            return '.only('

        if '.skip(' in line_text:
            return '.skip('

        if '@ts-ignore' in line_text:
            return '@ts-ignore'

        if '@ts-expect-error' in line_text:
            return '// @ts-expect-error'

        if 'eslint-disable' in line_lower:
            return 'eslint-disable'

        if '@ts-nocheck' in line_text:
            return '@ts-nocheck'

        return ''

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
