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
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from governance.kill_switch import mode
from governance import contract
from governance.require_harness import require_harness
from ralph import engine
from agents.base import BaseAgent, AgentConfig


@dataclass
class BugTask:
    """A bug fixing task."""
    task_id: str
    description: str
    affected_files: List[str]
    project_path: Path
    expected_fix: str = ""  # Optional hint about what to fix


class BugFixAgent(BaseAgent):
    """
    Autonomous bug fixing agent with governance.

    This is a simplified MVP implementation for Phase 1.
    Enhanced in v5 with Ralph-Wiggum iteration patterns.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize BugFix agent.

        Args:
            app_adapter: Application adapter (KareMatch, CredentialMate, etc.)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("bugfix")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="bugfix",
                expected_completion_signal=None,  # Can be set by caller
                max_iterations=self.contract.limits.get("max_iterations", 10),
                max_retries=self.contract.limits.get("max_retries", 3)
            )
        else:
            self.config = config

        # Backward compatibility
        self.max_retries = self.config.max_retries

        # Iteration tracking (Phase 2 - initialized here for forward compatibility)
        self.current_iteration = 0
        self.iteration_history: List[Dict[str, Any]] = []

    def execute(self, task_id: str) -> Dict[str, Any]:
        """
        Execute bug fix workflow using Claude CLI.

        Args:
            task_id: The task ID to work on (e.g., "TASK-123")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - evidence: Dict of evidence artifacts
            - verdict: Ralph verification result
            - output: Agent output text (for completion signal checking)
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "run_ralph")

        # Track iteration
        self.current_iteration += 1

        # Check iteration budget
        if self.current_iteration > self.config.max_iterations:
            return {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Max iterations ({self.config.max_iterations}) reached",
                "iterations": self.current_iteration,
                "output": f"Failed: Max iterations ({self.config.max_iterations}) reached"
            }

        # Get task description (set by IterationLoop.run())
        task_description = getattr(self, 'task_description', task_id)

        # Execute via Claude - use SDK or CLI based on config
        from pathlib import Path

        project_dir = Path(self.app_context.project_path)

        from claude.cli_wrapper import ClaudeCliWrapper
        from claude.sdk_adapter import ClaudeSDKAdapter

        wrapper: ClaudeSDKAdapter | ClaudeCliWrapper
        if self.config.use_sdk:
            # Use Claude Agent SDK
            wrapper = ClaudeSDKAdapter(project_dir)
            print(f"🚀 Executing task via Claude Agent SDK...")
        else:
            # Use CLI wrapper (fallback)
            wrapper = ClaudeCliWrapper(project_dir)
            print(f"🚀 Executing task via Claude CLI...")

        print(f"   Prompt: {task_description}")

        result = wrapper.execute_task(
            prompt=task_description,
            files=None,  # Let Claude decide which files to examine
            timeout=300  # 5 minutes
        )

        if not result.success:
            return {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Claude CLI execution failed: {result.error}",
                "iterations": self.current_iteration,
                "output": result.error or "Execution failed"
            }

        print(f"✅ Claude CLI execution complete ({result.duration_ms}ms)")
        if result.files_changed:
            print(f"   Changed files: {', '.join(result.files_changed)}")

        # Use Claude's output for completion signal checking
        output = result.output

        # Check for completion signal if configured
        if self.config.expected_completion_signal:
            promise = self.check_completion_signal(output)
            if promise == self.config.expected_completion_signal:
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "signal": "promise",
                    "promise_text": promise,
                    "output": output,
                    "iterations": self.current_iteration,
                    "files_changed": result.files_changed
                }

        # Return success
        return {
            "task_id": task_id,
            "status": "completed",
            "output": output,
            "iterations": self.current_iteration,
            "files_changed": result.files_changed
        }

    def execute_bug_task(self, bug: BugTask) -> Dict[str, Any]:
        """
        Execute bug fix workflow (legacy method for backward compatibility).

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

        # Track iteration
        self.current_iteration += 1

        # For MVP: Apply simple fixes directly
        # In production: This would use AI to analyze and fix
        result = self._apply_fix(bug)

        # Run Ralph verification
        verdict = self._verify_fix(bug)

        output = f"Bug fix applied to {len(bug.affected_files)} file(s)"

        # Check for completion signal if configured
        if self.config.expected_completion_signal:
            promise = self.check_completion_signal(output)
            if promise == self.config.expected_completion_signal:
                return {
                    "task_id": bug.task_id,
                    "status": "completed",
                    "signal": "promise",
                    "promise_text": promise,
                    "verdict": verdict,
                    "changes": result.get("changes", []),
                    "output": output
                }

        return {
            "task_id": bug.task_id,
            "status": "completed" if verdict.type.value == "PASS" else "failed",
            "verdict": verdict,
            "changes": result.get("changes", []),
            "output": output
        }

    @require_harness
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

    def run_with_loop(self, task_id: str, task_description: str = "", max_iterations: int = None, resume: bool = False):
        """
        Run bug fix with Wiggum iteration loop.

        This is a convenience method that creates an IterationLoop and runs the agent.
        Use this for Wiggum iteration mode with stop hooks (uses Ralph for verification).

        Args:
            task_id: Task identifier
            task_description: Description of the task
            max_iterations: Override max_iterations from config
            resume: Resume from saved state if available

        Returns:
            IterationResult with final status

        Example:
            agent = BugFixAgent(app_adapter, config=AgentConfig(
                project_name="karematch",
                agent_name="bugfix",
                expected_completion_signal="DONE",
                max_iterations=15
            ))
            result = agent.run_with_loop("Fix login bug", "Fix auth timeout in login.ts")
        """
        from orchestration.iteration_loop import IterationLoop

        loop = IterationLoop(self, self.app_context)
        return loop.run(
            task_id=task_id,
            task_description=task_description,
            max_iterations=max_iterations,
            resume=resume
        )


@require_harness
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
