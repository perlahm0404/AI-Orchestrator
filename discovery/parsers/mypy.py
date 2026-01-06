"""Mypy parser for extracting structured type errors from output.

Parses output from: mypy .
"""

import re
from dataclasses import dataclass


@dataclass
class MypyError:
    """Structured representation of a Mypy type error."""
    file: str
    line: int
    column: int
    error_type: str  # e.g., "assignment", "arg-type", "return-value"
    message: str
    priority: int  # P0/P1/P2 based on impact

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column} [{self.error_type}] {self.message}"


class MypyParser:
    """Parser for Mypy output."""

    # Critical error types (P0 priority)
    CRITICAL_ERRORS = {
        'assignment',     # Type mismatch in assignment
        'arg-type',       # Wrong argument type
        'return-value',   # Wrong return type
        'call-arg',       # Missing/extra arguments
        'override',       # Invalid method override
        'attr-defined',   # Attribute doesn't exist
    }

    # Missing annotation errors (P1 priority)
    ANNOTATION_ERRORS = {
        'no-untyped-def',
        'no-untyped-call',
        'var-annotated',
        'annotation-unchecked',
    }

    # Critical code paths for P0 priority
    CRITICAL_PATHS = [
        'app/auth/',
        'app/api/',
        'api/auth/',
        'api/routes/',
    ]

    def parse(self, mypy_output: str) -> list[MypyError]:
        """
        Parse Mypy output into structured MypyError list.

        Args:
            mypy_output: Raw text output from mypy

        Returns:
            List of MypyError objects

        Example input:
            app/auth/session.py:42:10: error: Argument 1 to "foo" has incompatible type "str"; expected "int"  [arg-type]
        """
        if not mypy_output or not mypy_output.strip():
            return []

        errors = []

        # Regex pattern for mypy errors:
        # path/to/file.py:line:column: error: message  [error-type]
        pattern = re.compile(
            r'^(.+?):(\d+):(\d+):\s+error:\s+(.+?)\s+\[([a-z-]+)\]$',
            re.MULTILINE
        )

        for match in pattern.finditer(mypy_output):
            file_path = match.group(1)
            line = int(match.group(2))
            column = int(match.group(3))
            message = match.group(4)
            error_type = match.group(5)

            error = MypyError(
                file=self._normalize_path(file_path),
                line=line,
                column=column,
                error_type=error_type,
                message=message,
                priority=self._compute_priority(error_type, file_path)
            )
            errors.append(error)

        return errors

    def _compute_priority(self, error_type: str, file_path: str) -> int:
        """
        Compute priority (P0/P1/P2) based on error type and file location.

        P0 (blocks users):
        - Type safety violations in critical paths (auth/, api/)
        - Critical error types (assignment, arg-type, etc.)

        P1 (degrades UX):
        - Missing type annotations
        - Type errors in non-critical code

        P2 (tech debt):
        - General type mismatches in utility code
        """
        # Check if file is in critical path
        is_critical_path = any(
            path in file_path
            for path in self.CRITICAL_PATHS
        )

        # P0: Critical errors in critical paths
        if error_type in self.CRITICAL_ERRORS and is_critical_path:
            return 0  # P0: Blocks users

        # P1: Critical errors anywhere, or missing annotations
        if error_type in self.CRITICAL_ERRORS or error_type in self.ANNOTATION_ERRORS:
            return 1  # P1: Degrades UX

        # P2: All other type errors
        return 2  # P2: Tech debt

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path (remove absolute prefix if present)."""
        markers = ['/app/', '/api/', '/tests/', '/src/']

        for marker in markers:
            if marker in file_path:
                parts = file_path.split(marker)
                if len(parts) > 1:
                    return marker.lstrip('/') + marker.join(parts[1:])

        return file_path
