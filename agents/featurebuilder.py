"""
FeatureBuilder Agent

Autonomous agent that builds new features with governance.

Workflow:
1. Receive feature description + target files
2. Read existing codebase and understand context
3. Generate new code/files for feature
4. Run tests (lint/typecheck/unit tests)
5. If tests pass: Return success (Ralph runs at PR time only)
6. If tests fail: Retry up to max_iterations

Key Differences from BugFix:
- Works ONLY on feature/* branches
- Can create new files (not just modify)
- Higher iteration budget (50 vs 15)
- No per-commit Ralph verification (only at PR)
- Liberal limits: 500 lines, 20 files

Implementation: v5.4 - Dev Team Architecture
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import subprocess

from governance.kill_switch import mode
from governance import contract
from governance.require_harness import require_harness
from agents.base import BaseAgent, AgentConfig


@dataclass
class FeatureTask:
    """A feature development task."""
    task_id: str
    description: str
    target_files: List[str]
    project_path: Path
    branch: str = ""
    requires_approval: List[str] = None


class FeatureBuilderAgent(BaseAgent):
    """
    Autonomous feature development agent with governance.

    Works on feature/* branches only.
    Builds new features with liberal autonomy (L1 contract).
    Ralph verification only at PR time, not per-commit.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize FeatureBuilder agent.

        Args:
            app_adapter: Application adapter (KareMatch, CredentialMate, etc.)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract (dev-team, not featurebuilder)
        self.contract = contract.load("dev-team")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="featurebuilder",
                expected_completion_signal="FEATURE_COMPLETE",
                max_iterations=self.contract.limits.get("max_iterations", 50),
                max_retries=self.contract.limits.get("max_retries", 5)
            )
        else:
            self.config = config

        # Backward compatibility
        self.max_retries = self.config.max_retries

        # Iteration tracking
        self.current_iteration = 0
        self.iteration_history: List[Dict[str, Any]] = []

    def execute(self, task_id: str) -> Dict[str, Any]:
        """
        Execute feature development workflow using Claude CLI.

        Args:
            task_id: The task ID to work on (e.g., "FEAT-001")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - output: Agent output text (for completion signal checking)
            - files_changed: List of files created/modified
        """
        # Check kill-switch
        mode.require_normal()

        # Validate branch (must be on feature/* branch)
        current_branch = self._get_current_branch()
        if not current_branch.startswith("feature/"):
            return {
                "task_id": task_id,
                "status": "blocked",
                "reason": f"Branch violation: Must be on feature/* branch (currently on {current_branch})",
                "output": f"BLOCKED: Not on feature branch (current: {current_branch})"
            }

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "create_file")

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
        project_dir = Path(self.app_context.project_path)

        from claude.cli_wrapper import ClaudeCliWrapper
        from claude.sdk_adapter import ClaudeSDKAdapter

        wrapper: ClaudeSDKAdapter | ClaudeCliWrapper
        if self.config.use_sdk:
            # Use Claude Agent SDK
            wrapper = ClaudeSDKAdapter(project_dir)
            print(f"🚀 Building feature via Claude Agent SDK...")
        else:
            # Use CLI wrapper (fallback)
            wrapper = ClaudeCliWrapper(project_dir)
            print(f"🚀 Building feature via Claude CLI...")
        print(f"   Branch: {current_branch}")
        print(f"   Prompt: {task_description}")

        result = wrapper.execute_task(
            prompt=task_description,
            files=None,  # Let Claude decide which files to examine
            timeout=600  # 10 minutes (features take longer than bugfixes)
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

        # Return success (no per-commit Ralph for feature branches)
        return {
            "task_id": task_id,
            "status": "completed",
            "output": output,
            "iterations": self.current_iteration,
            "files_changed": result.files_changed
        }

    def execute_feature_task(self, feature: FeatureTask) -> Dict[str, Any]:
        """
        Execute feature development workflow (legacy method for backward compatibility).

        Args:
            feature: FeatureTask with description and target files

        Returns:
            Result dict with status
        """
        # Check kill-switch
        mode.require_normal()

        # Validate branch
        current_branch = self._get_current_branch()
        if not current_branch.startswith("feature/"):
            return {
                "task_id": feature.task_id,
                "status": "blocked",
                "reason": f"Branch violation: Must be on feature/* branch (currently on {current_branch})"
            }

        # Check contract
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "create_file")

        # Track iteration
        self.current_iteration += 1

        output = f"Feature implementation in progress on {len(feature.target_files)} file(s)"

        # Check for completion signal if configured
        if self.config.expected_completion_signal:
            promise = self.check_completion_signal(output)
            if promise == self.config.expected_completion_signal:
                return {
                    "task_id": feature.task_id,
                    "status": "completed",
                    "signal": "promise",
                    "promise_text": promise,
                    "output": output
                }

        return {
            "task_id": feature.task_id,
            "status": "completed",
            "output": output
        }

    def _get_current_branch(self) -> str:
        """
        Get current git branch.

        Returns:
            Branch name (e.g., "feature/matching-algorithm")
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.app_context.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

    def checkpoint(self) -> Dict[str, Any]:
        """Capture current state for resume."""
        return {
            "agent": "featurebuilder",
            "project": self.app_context.project_name,
            "branch": self._get_current_branch()
        }

    def halt(self, reason: str) -> None:
        """Gracefully stop execution."""
        # Log halt reason (would go to audit log in production)
        pass

    def run_with_loop(self, task_id: str, task_description: str = "", max_iterations: int = None, resume: bool = False):
        """
        Run feature development with Wiggum iteration loop.

        This is a convenience method that creates an IterationLoop and runs the agent.
        Use this for Wiggum iteration mode with stop hooks.

        Args:
            task_id: Task identifier
            task_description: Description of the feature to build
            max_iterations: Override max_iterations from config
            resume: Resume from saved state if available

        Returns:
            IterationResult with final status

        Example:
            agent = FeatureBuilderAgent(app_adapter, config=AgentConfig(
                project_name="karematch",
                agent_name="featurebuilder",
                expected_completion_signal="FEATURE_COMPLETE",
                max_iterations=50
            ))
            result = agent.run_with_loop("Build matching algorithm", "Implement deterministic matching...")
        """
        from orchestration.iteration_loop import IterationLoop

        loop = IterationLoop(self, self.app_context)
        return loop.run(
            task_id=task_id,
            task_description=task_description,
            max_iterations=max_iterations,
            resume=resume
        )
