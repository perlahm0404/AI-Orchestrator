"""
Base Adapter Interface

All adapters implement this interface.

Usage:
    from adapters.karematch import KareMatchAdapter

    adapter = KareMatchAdapter()
    context = adapter.get_context()
    verdict = adapter.run_ralph(changed_files=["src/auth.ts"])
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AppContext:
    """
    Application context provided to Ralph.

    This tells Ralph HOW to verify, not WHAT rules to apply.
    Rules come from ralph/policy/v1.yaml.
    """
    project_name: str
    project_path: str
    language: str  # "typescript" | "python"

    # Commands to run
    lint_command: str
    typecheck_command: str
    test_command: str
    coverage_command: str

    # Paths
    source_paths: list[str]
    test_paths: list[str]
    coverage_report_path: str

    # Autonomy level
    autonomy_level: str  # "L1" | "L2"


class BaseAdapter(ABC):
    """Abstract base class for application adapters."""

    @abstractmethod
    def get_context(self) -> AppContext:
        """
        Get application context for Ralph.

        Returns:
            AppContext with project-specific configuration
        """
        pass

    @abstractmethod
    def run_ralph(
        self,
        changed_files: list[str],
        session_id: str
    ) -> dict[str, Any]:
        """
        Run Ralph verification for this project.

        Args:
            changed_files: Files that changed
            session_id: Current session ID

        Returns:
            Ralph verdict dict
        """
        pass
