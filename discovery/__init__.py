"""Bug discovery and work queue generation system.

This module provides automated bug discovery for TypeScript/Node.js projects by:
1. Scanning multiple bug sources (ESLint, TypeScript, tests, guardrails)
2. Tracking baseline bugs vs. new regressions
3. Generating prioritized work queue tasks grouped by file
4. CLI integration via `aibrain discover-bugs`

Autonomy Impact: +2% (automates bug triaging and work queue creation)
"""

from .scanner import BugScanner, ScanResult
from .baseline import BaselineManager
from .task_generator import TaskGenerator

__all__ = [
    'BugScanner',
    'ScanResult',
    'BaselineManager',
    'TaskGenerator',
]
