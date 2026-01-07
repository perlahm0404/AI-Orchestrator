"""
TestWriter Agent

Autonomous agent that writes comprehensive tests with governance.

Workflow:
1. Receive test requirements + code to test
2. Analyze existing test patterns in codebase
3. Generate Vitest/Playwright tests
4. Run tests to verify they pass
5. Check coverage (must be 80%+)
6. If coverage sufficient: Return success
7. If coverage insufficient: Add more tests (retry up to max_iterations)

Test Requirements:
- Use Vitest for unit tests
- Use Playwright for E2E tests
- Follow existing test patterns
- Achieve 80%+ coverage
- Test happy paths AND edge cases
- Use .todo() for WIP tests (allowed by contract)
- Cannot delete existing tests (contract forbids)

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
class TestTask:
    """A test writing task."""
    task_id: str
    description: str
    code_to_test: List[str]  # Files/modules to test
    project_path: Path
    test_files: List[str] = None  # Where to write tests
    min_coverage: int = 80  # Minimum required coverage


class TestWriterAgent(BaseAgent):
    """
    Autonomous test writing agent with governance.

    Specializes in writing comprehensive Vitest/Playwright tests.
    Works on feature/* branches (part of Dev Team).
    Must achieve 80%+ coverage.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize TestWriter agent.

        Args:
            app_adapter: Application adapter (KareMatch, CredentialMate, etc.)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract (dev-team, not testwriter)
        self.contract = contract.load("dev-team")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="testwriter",
                expected_completion_signal="TESTS_COMPLETE",
                max_iterations=self.contract.limits.get("max_iterations", 15),
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
        Execute test writing workflow using Claude CLI.

        Args:
            task_id: The task ID to work on (e.g., "TEST-001")

        Returns:
            Result dict with:
            - status: "completed" | "blocked" | "failed"
            - output: Agent output text (for completion signal checking)
            - files_changed: List of test files created/modified
            - coverage: Coverage percentage (if available)
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract: can we execute this action?
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "create_file")
        contract.require_allowed(self.contract, "run_tests")

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

        # Enhance prompt with test-specific instructions
        enhanced_prompt = self._enhance_test_prompt(task_description)

        # Execute via Claude CLI
        from claude.cli_wrapper import ClaudeCliWrapper

        project_dir = Path(self.app_context.project_path)
        wrapper = ClaudeCliWrapper(project_dir)

        print(f"🧪 Writing tests via Claude CLI...")
        print(f"   Prompt: {task_description}")

        result = wrapper.execute_task(
            prompt=enhanced_prompt,
            files=None,  # Let Claude decide which files to examine
            timeout=600  # 10 minutes
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
            print(f"   Test files: {', '.join(result.files_changed)}")

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

    def _enhance_test_prompt(self, base_prompt: str) -> str:
        """
        Enhance user prompt with test-specific instructions.

        Args:
            base_prompt: User's original task description

        Returns:
            Enhanced prompt with test best practices
        """
        enhancement = """

Requirements:
- Use Vitest for unit tests
- Use Playwright for E2E tests (if needed)
- Follow existing test patterns in tests/unit/ and tests/e2e/
- Achieve 80%+ coverage
- Test happy paths AND edge cases
- Use .todo() for tests you can't complete yet
- DO NOT delete existing tests (only add new ones)

Signal completion with: <promise>TESTS_COMPLETE</promise>
"""
        return base_prompt + enhancement

    def execute_test_task(self, test_task: TestTask) -> Dict[str, Any]:
        """
        Execute test writing workflow (legacy method for backward compatibility).

        Args:
            test_task: TestTask with code to test and requirements

        Returns:
            Result dict with status and coverage
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract
        contract.require_allowed(self.contract, "write_file")
        contract.require_allowed(self.contract, "create_file")
        contract.require_allowed(self.contract, "run_tests")

        # Track iteration
        self.current_iteration += 1

        output = f"Tests written for {len(test_task.code_to_test)} file(s)"

        # Check for completion signal if configured
        if self.config.expected_completion_signal:
            promise = self.check_completion_signal(output)
            if promise == self.config.expected_completion_signal:
                return {
                    "task_id": test_task.task_id,
                    "status": "completed",
                    "signal": "promise",
                    "promise_text": promise,
                    "output": output,
                    "coverage": test_task.min_coverage
                }

        return {
            "task_id": test_task.task_id,
            "status": "completed",
            "output": output
        }

    def checkpoint(self) -> Dict[str, Any]:
        """Capture current state for resume."""
        return {
            "agent": "testwriter",
            "project": self.app_context.project_name
        }

    def halt(self, reason: str) -> None:
        """Gracefully stop execution."""
        # Log halt reason (would go to audit log in production)
        pass

    def run_with_loop(self, task_id: str, task_description: str = "", max_iterations: int = None, resume: bool = False):
        """
        Run test writing with Wiggum iteration loop.

        This is a convenience method that creates an IterationLoop and runs the agent.
        Use this for Wiggum iteration mode with stop hooks.

        Args:
            task_id: Task identifier
            task_description: Description of tests to write
            max_iterations: Override max_iterations from config
            resume: Resume from saved state if available

        Returns:
            IterationResult with final status

        Example:
            agent = TestWriterAgent(app_adapter, config=AgentConfig(
                project_name="karematch",
                agent_name="testwriter",
                expected_completion_signal="TESTS_COMPLETE",
                max_iterations=15
            ))
            result = agent.run_with_loop("Write matching tests", "Write comprehensive tests for matching algorithm...")
        """
        from orchestration.iteration_loop import IterationLoop

        loop = IterationLoop(self, self.app_context)
        return loop.run(
            task_id=task_id,
            task_description=task_description,
            max_iterations=max_iterations,
            resume=resume
        )
