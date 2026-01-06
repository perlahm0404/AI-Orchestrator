"""TypeScript parser for extracting structured type errors from compiler output.

Parses output from: npm run check (or tsc --noEmit)
"""

import re
from dataclasses import dataclass


@dataclass
class TypeScriptError:
    """Structured representation of a TypeScript error."""
    file: str
    line: int
    column: int
    error_code: str  # e.g., "TS2345"
    message: str
    priority: int  # P0/P1/P2 based on impact

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column} [{self.error_code}] {self.message}"


class TypeScriptParser:
    """Parser for TypeScript compiler output."""

    # Critical error codes (P0 priority)
    CRITICAL_ERRORS = {
        'TS2345',  # Type mismatch in function call
        'TS2322',  # Type mismatch in assignment
        'TS2554',  # Wrong number of arguments
        'TS2339',  # Property does not exist
        'TS2341',  # Private property access
        'TS2351',  # Cannot use 'new' with expression
        'TS2352',  # Conversion may be a mistake
        'TS2365',  # Operator cannot be applied
        'TS2367',  # Comparison may be unintentional
        'TS2540',  # Cannot assign to readonly
        'TS2741',  # Missing properties
    }

    # Missing type annotations (P1 priority)
    MISSING_TYPE_ERRORS = {
        'TS7006',  # Parameter implicitly has 'any' type
        'TS7031',  # Binding element implicitly has 'any' type
        'TS7034',  # Variable implicitly has 'any' type
    }

    # Critical code paths for P0 priority
    CRITICAL_PATHS = [
        'auth/',
        'payment/',
        'api/',
        'session/',
        'security/',
    ]

    def parse(self, tsc_output: str) -> list[TypeScriptError]:
        """
        Parse TypeScript compiler output into structured TypeScriptError list.

        Args:
            tsc_output: Raw text output from tsc --noEmit

        Returns:
            List of TypeScriptError objects

        Example input:
            src/auth/session.ts(42,10): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.
        """
        if not tsc_output or not tsc_output.strip():
            return []

        errors = []

        # Regex pattern for TypeScript errors:
        # path/to/file.ts(line,column): error TSXXXX: message
        pattern = re.compile(
            r'^(.+?)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.+)$',
            re.MULTILINE
        )

        for match in pattern.finditer(tsc_output):
            file_path = match.group(1)
            line = int(match.group(2))
            column = int(match.group(3))
            error_code = match.group(4)
            message = match.group(5)

            error = TypeScriptError(
                file=self._normalize_path(file_path),
                line=line,
                column=column,
                error_code=error_code,
                message=message,
                priority=self._compute_priority(error_code, file_path)
            )
            errors.append(error)

        return errors

    def _compute_priority(self, error_code: str, file_path: str) -> int:
        """
        Compute priority (P0/P1/P2) based on error code and file location.

        P0 (blocks users):
        - Type safety violations in critical paths (auth/, payment/, api/)
        - Critical error codes (TS2345, TS2322, etc.)

        P1 (degrades UX):
        - Missing type annotations (TS7006, TS7031)
        - Type errors in non-critical code

        P2 (tech debt):
        - Implicit any, general type mismatches in non-critical areas
        """
        # Check if file is in critical path
        is_critical_path = any(
            path in file_path
            for path in self.CRITICAL_PATHS
        )

        # P0: Critical errors in critical paths
        if error_code in self.CRITICAL_ERRORS and is_critical_path:
            return 0  # P0: Blocks users

        # P1: Critical errors anywhere, or missing types
        if error_code in self.CRITICAL_ERRORS or error_code in self.MISSING_TYPE_ERRORS:
            return 1  # P1: Degrades UX

        # P2: All other type errors
        return 2  # P2: Tech debt

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path (remove absolute prefix if present)."""
        # TypeScript often returns relative paths already, but handle absolute paths
        # e.g., /Users/foo/karematch/src/auth.ts → src/auth.ts

        # Find common project markers
        markers = ['/services/', '/packages/', '/apps/', '/src/']

        for marker in markers:
            if marker in file_path:
                # Extract path from first marker onwards
                parts = file_path.split(marker)
                if len(parts) > 1:
                    return marker.lstrip('/') + marker.join(parts[1:])

        # If no marker found, return as-is (likely already relative)
        return file_path
