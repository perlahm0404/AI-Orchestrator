"""
CodeQuality Agent

Improves code quality in safe, reversible batches.

Workflow:
1. ESTABLISH baseline (test count, lint errors, type errors)
2. SCAN for safe auto-fix issues
3. PROCESS in batches (max 20)
4. VALIDATE test count unchanged after each batch
5. ROLLBACK if tests fail
6. GENERATE batch REVIEW.md
7. MARK batch as pending_review
8. HALT and wait for human approval

Constraints:
- Test count must remain unchanged (no behavior changes)
- Cannot add new features
- Cannot remove tests
- Rollback on any test failure

Implementation: Phase 1
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import subprocess
import re

from governance.kill_switch import mode
from governance import contract
from ralph import engine
from agents.base import BaseAgent, AgentConfig


@dataclass
class QualityBaseline:
    """Baseline metrics before quality improvements."""
    test_count: int
    lint_errors: int
    type_errors: int
    test_output: str


@dataclass
class QualityIssue:
    """A code quality issue that can be auto-fixed."""
    file: str
    line: int
    rule: str
    message: str
    fix_type: str  # "unused_import", "import_order", "console_statement", etc.


@dataclass
class QualityBatch:
    """A batch of quality fixes to apply together."""
    batch_id: int
    issues: List[QualityIssue]
    files_affected: List[str]


class CodeQualityAgent(BaseAgent):
    """
    Autonomous code quality improvement agent.

    Fixes lint, type, and style issues in safe batches with rollback.
    Enhanced in v5 with Ralph-Wiggum iteration patterns.
    """

    def __init__(self, app_adapter, config: Optional[AgentConfig] = None):
        """
        Initialize CodeQuality agent.

        Args:
            app_adapter: Application adapter (KareMatch, CredentialMate, etc.)
            config: Optional AgentConfig (will be created from contract if not provided)
        """
        self.app_adapter = app_adapter
        self.app_context = app_adapter.get_context()

        # Load autonomy contract
        self.contract = contract.load("codequality")

        # Create or use provided config
        if config is None:
            self.config = AgentConfig(
                project_name=self.app_context.project_name,
                agent_name="codequality",
                expected_completion_signal=None,  # Can be set by caller
                max_iterations=self.contract.limits.get("max_iterations", 10),
                max_retries=self.contract.limits.get("max_retries", 3)
            )
        else:
            self.config = config

        # Batch limits from contract
        self.max_batch_size = self.contract.limits.get("max_batch_size", 20)
        self.max_files_per_batch = self.contract.limits.get("max_files_per_batch", 10)

        # State
        self.baseline: Optional[QualityBaseline] = None
        self.batches_processed = 0
        self.total_fixes = 0

        # Iteration tracking (Phase 2 - initialized here for forward compatibility)
        self.current_iteration = 0
        self.iteration_history: List[Dict[str, Any]] = []

    def execute(self, task_id: str) -> Dict[str, Any]:
        """
        Execute code quality improvement task using Claude CLI.

        Args:
            task_id: Task identifier

        Returns:
            Execution result dict
        """
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
            print(f"🔧 Executing code quality task via Claude Agent SDK...")
        else:
            # Use CLI wrapper (fallback)
            wrapper = ClaudeCliWrapper(project_dir)
            print(f"🔧 Executing code quality task via Claude CLI...")
        print(f"   Prompt: {task_description}")

        # For code quality, add specific instructions
        quality_prompt = f"""
{task_description}

Focus on code quality improvements:
- Remove unused imports and variables
- Fix linting issues
- Improve type annotations
- Refactor for clarity
- Follow project style guide

Do NOT change functionality or add new features.
Run lint and type checks after changes.
Output <promise>CODEQUALITY_COMPLETE</promise> when done.
"""

        result = wrapper.execute_task(
            prompt=quality_prompt,
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

        # No completion signal yet, will iterate again
        return {
            "task_id": task_id,
            "status": "in_progress",
            "output": output,
            "iterations": self.current_iteration,
            "files_changed": result.files_changed
        }

    def execute_quality_workflow(self, target_count: int = 50) -> Dict[str, Any]:
        """
        Execute code quality improvement workflow (legacy method for backward compatibility).

        Args:
            target_count: Number of issues to fix (default: 50)

        Returns:
            Result dict with status, batches processed, and fixes applied
        """
        # Check kill-switch
        mode.require_normal()

        # Check contract permissions
        contract.require_allowed(self.contract, "run_lint_fix")
        contract.require_allowed(self.contract, "run_tests")

        # Step 1: Establish baseline
        self.baseline = self._establish_baseline()

        # Step 2: Scan for issues
        issues = self._scan_for_issues()

        if not issues:
            return {
                "status": "completed",
                "message": "No quality issues found",
                "fixes_applied": 0,
                "batches_processed": 0
            }

        # Step 3: Process in batches
        batches = self._create_batches(issues, target_count)

        for batch in batches:
            try:
                # Apply batch fixes
                self._apply_batch(batch)

                # Validate test count unchanged
                if not self._validate_test_count():
                    self._rollback()
                    return {
                        "status": "halted",
                        "reason": "test_count_changed",
                        "fixes_applied": self.total_fixes,
                        "batches_processed": self.batches_processed
                    }

                # Run Ralph verification
                verdict = self._verify_batch(batch)

                if verdict.type.value == "BLOCKED":
                    self._rollback()
                    return {
                        "status": "halted",
                        "reason": "guardrails_violated",
                        "fixes_applied": self.total_fixes,
                        "batches_processed": self.batches_processed
                    }

                # Batch successful
                self.batches_processed += 1
                self.total_fixes += len(batch.issues)

                # Commit batch (in production, would create separate commits)
                # For now, we accumulate changes

            except Exception as e:
                self._rollback()
                return {
                    "status": "failed",
                    "reason": str(e),
                    "fixes_applied": self.total_fixes,
                    "batches_processed": self.batches_processed
                }

        return {
            "status": "completed",
            "fixes_applied": self.total_fixes,
            "batches_processed": self.batches_processed,
            "baseline": {
                "test_count": self.baseline.test_count,
                "lint_errors_before": self.baseline.lint_errors,
                "type_errors_before": self.baseline.type_errors
            }
        }

    def _establish_baseline(self) -> QualityBaseline:
        """
        Establish baseline metrics.

        Returns:
            QualityBaseline with test count and error counts
        """
        project_path = Path(self.app_context.project_path)

        # Count tests
        test_output = self._run_command(
            ["npx", "vitest", "run", "--reporter=verbose"],
            cwd=project_path,
            timeout=300
        )

        # Extract test count from output
        test_count = self._extract_test_count(test_output)

        # Count lint errors
        lint_output = self._run_command(
            ["npm", "run", "lint"],
            cwd=project_path,
            capture_errors=True
        )
        lint_errors = self._count_lint_errors(lint_output)

        # Count type errors
        type_output = self._run_command(
            ["npm", "run", "check"],
            cwd=project_path,
            capture_errors=True
        )
        type_errors = self._count_type_errors(type_output)

        return QualityBaseline(
            test_count=test_count,
            lint_errors=lint_errors,
            type_errors=type_errors,
            test_output=test_output
        )

    def _scan_for_issues(self) -> List[QualityIssue]:
        """
        Scan codebase for auto-fixable quality issues.

        Returns:
            List of QualityIssue objects
        """
        project_path = Path(self.app_context.project_path)
        issues = []

        # Scan for lint issues that can be auto-fixed
        lint_output = self._run_command(
            ["npm", "run", "lint"],
            cwd=project_path,
            capture_errors=True
        )

        # Parse lint output for issues
        # Format: /path/to/file.ts:line:col  error/warning  message  rule
        lint_pattern = r'(.+?):(\d+):\d+\s+(error|warning)\s+(.+?)\s+([\w/-]+)'
        for match in re.finditer(lint_pattern, lint_output):
            file_path, line, severity, message, rule = match.groups()

            # Only include auto-fixable issues
            if self._is_auto_fixable(rule):
                issues.append(QualityIssue(
                    file=file_path,
                    line=int(line),
                    rule=rule,
                    message=message,
                    fix_type=self._get_fix_type(rule)
                ))

        return issues

    def _is_auto_fixable(self, rule: str) -> bool:
        """Check if a lint rule can be auto-fixed safely."""
        auto_fixable_rules = [
            "unused-imports/no-unused-imports",
            "import/order",
            "@typescript-eslint/no-unused-vars",
            "no-console",  # Can remove debug console statements
        ]
        return rule in auto_fixable_rules

    def _get_fix_type(self, rule: str) -> str:
        """Get the type of fix needed for a rule."""
        fix_types = {
            "unused-imports/no-unused-imports": "unused_import",
            "import/order": "import_order",
            "@typescript-eslint/no-unused-vars": "unused_var",
            "no-console": "console_statement",
        }
        return fix_types.get(rule, "other")

    def _create_batches(
        self,
        issues: List[QualityIssue],
        target_count: int
    ) -> List[QualityBatch]:
        """
        Group issues into batches.

        Args:
            issues: All quality issues found
            target_count: How many fixes to target

        Returns:
            List of QualityBatch objects
        """
        batches = []
        batch_id = 0

        # Take only up to target_count issues
        issues_to_fix = issues[:target_count]

        # Group by fix type for easier processing
        i = 0
        while i < len(issues_to_fix):
            batch_issues = issues_to_fix[i:i + self.max_batch_size]
            batch_files = list(set(issue.file for issue in batch_issues))

            # Ensure we don't exceed file limit
            if len(batch_files) > self.max_files_per_batch:
                # Reduce batch size
                batch_issues = batch_issues[:self.max_files_per_batch]
                batch_files = list(set(issue.file for issue in batch_issues))

            batches.append(QualityBatch(
                batch_id=batch_id,
                issues=batch_issues,
                files_affected=batch_files
            ))

            batch_id += 1
            i += len(batch_issues)

        return batches

    def _apply_batch(self, batch: QualityBatch) -> None:
        """
        Apply fixes for a batch of issues.

        Args:
            batch: QualityBatch to process
        """
        # Check contract
        contract.require_allowed(self.contract, "write_file")

        project_path = Path(self.app_context.project_path)

        # For MVP: Use eslint --fix to apply fixes
        self._run_command(
            ["npm", "run", "lint", "--", "--fix"],
            cwd=project_path,
            capture_errors=True
        )

    def _validate_test_count(self) -> bool:
        """
        Validate that test count hasn't changed.

        Returns:
            True if test count unchanged, False otherwise
        """
        project_path = Path(self.app_context.project_path)

        test_output = self._run_command(
            ["npx", "vitest", "run", "--reporter=verbose"],
            cwd=project_path,
            timeout=300
        )

        current_test_count = self._extract_test_count(test_output)

        return current_test_count == self.baseline.test_count

    def _verify_batch(self, batch: QualityBatch) -> Any:
        """
        Run Ralph verification on batch changes.

        Args:
            batch: QualityBatch that was applied

        Returns:
            Ralph Verdict
        """
        contract.require_allowed(self.contract, "run_ralph")

        verdict = engine.verify(
            project=self.app_context.project_name,
            changes=batch.files_affected,
            session_id=f"codequality-batch-{batch.batch_id}",
            app_context=self.app_context
        )

        return verdict

    def _rollback(self) -> None:
        """Rollback changes in current batch."""
        project_path = Path(self.app_context.project_path)

        # Git reset to undo changes
        self._run_command(
            ["git", "checkout", "."],
            cwd=project_path
        )

    def _run_command(
        self,
        cmd: List[str],
        cwd: Path,
        timeout: int = 120,
        capture_errors: bool = False
    ) -> str:
        """
        Run a shell command and return output.

        Args:
            cmd: Command and arguments
            cwd: Working directory
            timeout: Command timeout in seconds
            capture_errors: If True, capture stderr with stdout

        Returns:
            Command output as string
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if capture_errors:
                return result.stdout + result.stderr
            return result.stdout

        except subprocess.TimeoutExpired:
            return ""
        except Exception:
            return ""

    def _extract_test_count(self, test_output: str) -> int:
        """Extract test count from vitest output."""
        # Pattern: "Test Files  X passed"
        match = re.search(r'Test Files\s+(\d+)\s+passed', test_output)
        if match:
            return int(match.group(1))

        # Pattern: "Tests  X passed"
        match = re.search(r'Tests\s+(\d+)\s+passed', test_output)
        if match:
            return int(match.group(1))

        return 0

    def _count_lint_errors(self, lint_output: str) -> int:
        """Count lint errors in output."""
        # Pattern: "✖ X problems (Y errors, Z warnings)"
        match = re.search(r'✖ (\d+) problems', lint_output)
        if match:
            return int(match.group(1))
        return 0

    def _count_type_errors(self, type_output: str) -> int:
        """Count TypeScript errors in output."""
        # Pattern: "error TS" appears for each error
        return type_output.count("error TS")

    def checkpoint(self) -> Dict[str, Any]:
        """Capture current state for resume."""
        return {
            "agent": "codequality",
            "project": self.app_context.project_name,
            "batches_processed": self.batches_processed,
            "total_fixes": self.total_fixes
        }

    def halt(self, reason: str) -> None:
        """Gracefully stop execution."""
        # Rollback current batch
        self._rollback()

    def run_with_loop(self, task_id: str, task_description: str = "", max_iterations: int = None, resume: bool = False):
        """
        Run code quality improvement with Wiggum iteration loop.

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
            agent = CodeQualityAgent(app_adapter, config=AgentConfig(
                project_name="karematch",
                agent_name="codequality",
                expected_completion_signal="CLEANUP_COMPLETE",
                max_iterations=20
            ))
            result = agent.run_with_loop("Remove console.log", "Clean up debug statements")
        """
        from orchestration.iteration_loop import IterationLoop

        loop = IterationLoop(self, self.app_context)
        return loop.run(
            task_id=task_id,
            task_description=task_description,
            max_iterations=max_iterations,
            resume=resume
        )
