"""Parsers for extracting structured bug data from tool outputs.

TypeScript/Node.js Parsers:
- ESLintParser: Parse npm run lint --format=json
- TypeScriptParser: Parse npm run check output
- TestParser: Parse npm test --reporter=json (Vitest)

Python Parsers:
- RuffParser: Parse ruff check --format=json
- MypyParser: Parse mypy . output
- PytestParser: Parse pytest --json-report or pytest -v

Universal Parsers:
- GuardrailParser: Parse rg --json output for suppression patterns
"""

from .eslint import ESLintParser, LintError
from .typescript import TypeScriptParser, TypeScriptError
from .test import TestParser, TestFailure
from .guardrails import GuardrailParser, GuardrailViolation
from .ruff import RuffParser, RuffError
from .mypy import MypyParser, MypyError
from .pytest import PytestParser, PytestFailure

__all__ = [
    # TypeScript/Node.js
    'ESLintParser',
    'LintError',
    'TypeScriptParser',
    'TypeScriptError',
    'TestParser',
    'TestFailure',
    # Python
    'RuffParser',
    'RuffError',
    'MypyParser',
    'MypyError',
    'PytestParser',
    'PytestFailure',
    # Universal
    'GuardrailParser',
    'GuardrailViolation',
]
