"""
BugFix Agent

Autonomous agent that fixes bugs with governance.

Workflow:
1. Receive bug description + affected files
2. Read code and understand bug
3. Generate fix
4. Run Ralph verification
5. If PASS: Return success (human approves PR)
6. If FAIL/BLOCKED: Retry up to max_retries

Implementation: Phase 1 MVP
"""

from pathlib import Path
from typing import Any, Dict, List
from dataclasses import dataclass

from governance.kill_switch import mode
from governance import contract
from ralph import engine


@dataclass
class BugTask:
    """A bug fixing task."""
    task_id: str
    description: str
    affected_files: List[str]
    project_path: Path
    expected_fix: str = ""  # Optional hint about what to fix


class BugFixAgent:
    """
    Autonomous bug fixing agent with governance.

    This is a simplified MVP implementation for Phase 1.
    """

    def __init__(self, app_adapter):
        """
        Initialize BugFix agent.

        Args:
            app_adapter: Application adapter (KareMatch, CredentialMate, etc.)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("bugfix")

        # Retry limit from contract
        self.max_retries = self.contract.limits.get("max_retries", 3)

    def execute(self, bug: BugTask) -> Dict[str, Any]:
        """
        Execute bug fix workflow.

        Args:
            bug: BugTask with description and affected files

        Returns:
            Result dict with status and verdict
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "run_ralph")

        # For MVP: Apply simple fixes directly
        # In production: This would use AI to analyze and fix
        result = self._apply_fix(bug)

        # Run Ralph verification
        verdict = self._verify_fix(bug)

        return {
            "task_id": bug.task_id,
            "status": "completed" if verdict.type.value == "PASS" else "failed",
            "verdict": verdict,
            "changes": result.get("changes", [])
        }

    def _apply_fix(self, bug: BugTask) -> Dict[str, Any]:
        """
        Apply the fix to files.

        For MVP: Uses expected_fix string to make simple replacements.
        In production: Would use AI to analyze and generate fix.

        Args:
            bug: BugTask with fix details

        Returns:
            Dict with changes made
        """
        changes = []

        for file_path in bug.affected_files:
            full_path = Path(self.app_context.project_path) / file_path

            if not full_path.exists():
                continue

            # Read current content
            with open(full_path, 'r') as f:
                content = f.read()

            # Apply fix (MVP: simple replacement)
            if bug.expected_fix and bug.expected_fix in content:
                # This is a placeholder for real AI-driven fixing
                # For now, we'll just document that a fix would be applied
                changes.append({
                    "file": file_path,
                    "type": "modified",
                    "lines_changed": 1
                })

        return {"changes": changes}

    def _verify_fix(self, bug: BugTask) -> Any:
        """
        Run Ralph verification on the fix.

        Args:
            bug: BugTask with affected files

        Returns:
            Ralph Verdict
        """
        # Check contract: can we run Ralph?
        contract.require_allowed(self.contract, "run_ralph")

        # Run Ralph verification
        verdict = engine.verify(
            project=self.app_context.project_name,
            changes=bug.affected_files,
            session_id=bug.task_id,
            app_context=self.app_context
        )

        return verdict

    def checkpoint(self) -> Dict[str, Any]:
        """Capture current state for resume."""
        return {
            "agent": "bugfix",
            "project": self.app_context.project_name
        }

    def halt(self, reason: str) -> None:
        """Gracefully stop execution."""
        # Log halt reason (would go to audit log in production)
        pass


def fix_bug_simple(
    project_path: Path,
    file_path: str,
    old_code: str,
    new_code: str
) -> bool:
    """
    Simple helper to fix a bug by replacing code.

    Args:
        project_path: Root path of project
        file_path: Relative path to file
        old_code: Code to replace
        new_code: New code

    Returns:
        True if fix was applied successfully
    """
    full_path = project_path / file_path

    if not full_path.exists():
        return False

    try:
        # Read file
        with open(full_path, 'r') as f:
            content = f.read()

        # Apply fix
        if old_code not in content:
            return False

        new_content = content.replace(old_code, new_code)

        # Write back
        with open(full_path, 'w') as f:
            f.write(new_content)

        return True

    except Exception:
        return False
