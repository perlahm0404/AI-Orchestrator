"""Bug scanner orchestrates all parsers to collect bugs from multiple sources.

TypeScript/Node.js commands (standard projects):
- npm run lint -- --format=json (ESLint)
- npm run check (TypeScript)
- npm test -- --reporter=json (Vitest)
- rg --json (Guardrails)

TypeScript/Node.js commands (Turborepo monorepos):
- npx eslint . --format=json (ESLint - direct invocation)
- npx tsc --noEmit (TypeScript - direct invocation)
- npx vitest run --reporter=json --outputFile=.vitest-results.json (Vitest - direct invocation)
- rg --json (Guardrails)

Python commands:
- ruff check . --output-format=json (Ruff)
- mypy . (MyPy)
- pytest -v (Pytest)
- rg --json --type=python (Guardrails)

Notes:
- Turborepo detection: Automatically detects turbo.json and bypasses npm scripts
- Direct tool invocation avoids Turborepo argument passing issues
- Vitest uses --outputFile to avoid verbose console logging
"""

import subprocess
import shlex
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

from .parsers import (
    ESLintParser,
    TypeScriptParser,
    TestParser,
    GuardrailParser,
    RuffParser,
    MypyParser,
    PytestParser,
    LintError,
    TypeScriptError,
    TestFailure,
    GuardrailViolation,
    RuffError,
    MypyError,
    PytestFailure,
)


@dataclass
class ScanResult:
    """Complete scan result from all bug sources."""
    timestamp: datetime
    project: str
    lint_errors: list[LintError]
    type_errors: list[TypeScriptError]
    test_failures: list[TestFailure]
    guardrail_violations: list[GuardrailViolation]

    def total_errors(self) -> int:
        """Total count across all error types."""
        return (
            len(self.lint_errors) +
            len(self.type_errors) +
            len(self.test_failures) +
            len(self.guardrail_violations)
        )

    def by_file(self) -> dict[str, list]:
        """Group all errors by file path."""
        grouped = defaultdict(list)

        for error in self.lint_errors:
            grouped[error.file].append(error)
        for error in self.type_errors:
            grouped[error.file].append(error)
        for failure in self.test_failures:
            # Use source file (inferred from test file)
            grouped[failure.source_file].append(failure)
        for violation in self.guardrail_violations:
            grouped[violation.file].append(violation)

        return grouped


class BugScanner:
    """Orchestrates all bug discovery sources."""

    def __init__(self, project_path: Path, project_name: str, language: str = 'typescript', scanner_commands: Optional[dict] = None):
        """
        Initialize scanner.

        Args:
            project_path: Path to project root directory
            project_name: Project name (e.g., 'karematch')
            language: Project language ('typescript' or 'python')
            scanner_commands: Optional project-specific scanner commands (overrides defaults)
        """
        self.project_path = project_path
        self.project_name = project_name
        self.language = language
        self.scanner_commands = scanner_commands or {}

        # Detect if project uses Turborepo (monorepo)
        self.uses_turborepo = (project_path / "turbo.json").exists()
        if self.uses_turborepo:
            print("📦 Turborepo detected - using direct tool invocation")

        # Configure parsers based on language
        if language == 'python':
            self.parsers = {
                'lint': RuffParser(),
                'typecheck': MypyParser(),
                'test': PytestParser(),
                'guardrails': GuardrailParser(),
            }
        else:  # typescript (default)
            self.parsers = {
                'lint': ESLintParser(),
                'typecheck': TypeScriptParser(),
                'test': TestParser(),
                'guardrails': GuardrailParser(),
            }

    def scan(self, sources: Optional[list[str]] = None) -> ScanResult:
        """
        Run all scanners and return structured bugs.

        Args:
            sources: Which sources to scan (default: all)
                     ['lint', 'typecheck', 'test', 'guardrails']

        Returns:
            ScanResult with all discovered bugs
        """
        sources = sources or ['lint', 'typecheck', 'test', 'guardrails']

        results = {
            'lint': [],
            'typecheck': [],
            'test': [],
            'guardrails': [],
        }

        for source in sources:
            if source not in self.parsers:
                print(f"⚠️  Unknown source: {source}, skipping")
                continue

            print(f"🔍 Scanning {source}...")

            try:
                raw_output = self._run_scanner(source)
                errors = self.parsers[source].parse(raw_output)
                results[source] = errors
                print(f"   Found {len(errors)} issues")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Timeout (> 10 minutes), skipping")
            except Exception as e:
                print(f"   ⚠️  Error: {e}, skipping")

        return ScanResult(
            timestamp=datetime.now(),
            project=self.project_name,
            lint_errors=results['lint'],
            type_errors=results['typecheck'],
            test_failures=results['test'],
            guardrail_violations=results['guardrails']
        )

    def _run_scanner(self, source: str) -> str:
        """
        Execute scanner command and return output.

        Args:
            source: Scanner type ('lint', 'typecheck', 'test', 'guardrails')

        Returns:
            Raw command output (stdout + stderr)
        """
        # Check for project-specific scanner commands first
        if source in self.scanner_commands:
            cmd_str = self.scanner_commands[source]
            cmd = shlex.split(cmd_str)
        else:
            # Fall back to default commands
            # Python commands
            if self.language == 'python':
                commands = {
                    'lint': ['ruff', 'check', '.', '--output-format=json'],
                    'typecheck': ['mypy', '.'],
                    'test': ['pytest', '-v'],  # Use verbose output (JSON report requires plugin)
                    'guardrails': [
                        'rg',
                        '# type: ignore|# noqa|@pytest.mark.skip',
                        '--json',
                        '--type', 'python',
                    ]
                }
            else:  # TypeScript/Node.js commands (default)
                if self.uses_turborepo:
                    # Turborepo projects: bypass npm scripts, call tools directly
                    commands = {
                        'lint': ['npx', 'eslint', '.', '--format=json'],
                        'typecheck': ['npx', 'tsc', '--noEmit'],
                        'test': ['npx', 'vitest', 'run', '--reporter=json', '--outputFile=.vitest-results.json'],
                        'guardrails': [
                            'rg',
                            '@ts-ignore|@ts-nocheck|eslint-disable|\\.skip\\(|\\.only\\(',
                            '--json',
                            '--type', 'typescript',
                            '--type', 'typescriptreact',
                        ]
                    }
                else:
                    # Standard npm projects: use npm scripts
                    commands = {
                        'lint': ['npm', 'run', 'lint', '--', '--format=json'],
                        'typecheck': ['npm', 'run', 'check'],
                        'test': ['npm', 'test', '--', '--reporter=json'],
                        'guardrails': [
                            'rg',
                            '@ts-ignore|@ts-nocheck|eslint-disable|\\.skip\\(|\\.only\\(',
                            '--json',
                            '--type', 'typescript',
                            '--type', 'typescriptreact',
                        ]
                    }

            if source not in commands:
                raise ValueError(f"Unknown scanner source: {source}")

            cmd = commands[source]

        # Run command with timeout
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            # Special handling for Vitest with outputFile
            if source == 'test' and self.uses_turborepo and self.language == 'typescript':
                # Read from the output file instead of stdout
                output_file = self.project_path / '.vitest-results.json'
                if output_file.exists():
                    output = output_file.read_text()
                    # Clean up the temporary file
                    output_file.unlink()
                else:
                    # Fallback to stdout/stderr if file wasn't created
                    output = result.stdout + result.stderr
            else:
                # Combine stdout and stderr
                # Note: Many tools (like tsc) write errors to stderr
                output = result.stdout + result.stderr

            return output

        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Command timed out after 10 minutes")
            raise
