"""
Simplified Governance Enforcement - Single enforcement point

Replaces complex @require_harness decorator and fragmented checks
with a single, simple enforcement function.

Target: ~50 lines (vs 144 lines in require_harness.py)
"""

from pathlib import Path
from typing import Optional

from governance.contract import ContractViolation, Contract


class GovernanceEnforcement:
    """Single class for all governance enforcement"""

    def __init__(self, contract: Contract):
        self.contract = contract

    def check_action(self, action: str, context: Optional[dict] = None) -> bool:
        """
        Check if action is allowed by contract

        Args:
            action: Action to check (e.g., "write_file", "git_commit")
            context: Optional context dict with details

        Returns:
            True if allowed

        Raises:
            ContractViolation if not allowed
        """
        context = context or {}

        # Check if action is in allowed list
        if action not in self.contract.allowed_actions:
            raise ContractViolation(
                f"Action '{action}' not allowed by contract '{self.contract.agent}'"
            )

        # Check limits
        lines_changed = context.get("lines_changed", 0)
        files_changed = context.get("files_changed", 0)

        if lines_changed > self.contract.limits.get("max_lines_changed", float("inf")):
            raise ContractViolation(
                f"Too many lines changed: {lines_changed} > {self.contract.limits['max_lines_changed']}"
            )

        if files_changed > self.contract.limits.get("max_files_changed", float("inf")):
            raise ContractViolation(
                f"Too many files changed: {files_changed} > {self.contract.limits['max_files_changed']}"
            )

        return True

    def check_file_write(self, file_path: str, lines_added: int) -> bool:
        """Convenience method for file write checks"""
        return self.check_action("write_file", {
            "file_path": file_path,
            "lines_changed": lines_added,
            "files_changed": 1
        })

    def check_git_operation(self, operation: str) -> bool:
        """Convenience method for git operation checks"""
        # Check if operation is forbidden
        forbidden = self.contract.forbidden_actions or []
        if operation in forbidden:
            raise ContractViolation(
                f"Git operation '{operation}' is forbidden by contract"
            )
        return self.check_action("git_commit")
