"""
Iteration Loop Manager - Wiggum Pattern

Manages the iteration loop for agents with stop hook integration.

This implements the Wiggum iteration pattern:
1. Agent executes task
2. Stop hook evaluates if agent can exit (calls Ralph for verification)
3. If BLOCK → agent retries
4. If ALLOW → session complete
5. If ASK_HUMAN → pause for approval

Wiggum = Iteration control system (uses Ralph for verification)
Ralph = Code quality verification system (PASS/FAIL/BLOCKED)

Usage:
    from orchestration.iteration_loop import IterationLoop
    from agents.bugfix import BugFixAgent

    loop = IterationLoop(agent, app_context)
    result = loop.run(task_id="TASK-123", task_description="Fix bug")

Implementation: Wiggum System
"""

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING
from pathlib import Path
import subprocess

if TYPE_CHECKING:
    from agents.base import BaseAgent

from governance.hooks.stop_hook import agent_stop_hook, StopDecision
from ralph.baseline import BaselineRecorder
from orchestration.state_file import write_state_file, read_state_file, cleanup_state_file, LoopState
from datetime import datetime

# Knowledge Object integration
from knowledge.service import find_relevant, create_draft
from orchestration.ko_helpers import extract_tags_from_task, format_ko_for_display, extract_learning_from_iterations


@dataclass
class IterationResult:
    """Result of an iteration loop."""
    task_id: str
    status: str  # "completed", "failed", "blocked", "aborted"
    iterations: int
    verdict: Any = None
    reason: str = ""
    iteration_summary: dict = None


class IterationLoop:
    """
    Manages iteration loop for agents with stop hook integration.

    This orchestrator implements the Ralph-Wiggum pattern where agents
    can iterate multiple times to self-correct failures.
    """

    def __init__(self, agent: "BaseAgent", app_context, state_dir: Path = None):
        """
        Initialize iteration loop manager.

        Args:
            agent: The agent to run (must extend BaseAgent)
            app_context: Application context for Ralph verification
            state_dir: Directory for persistent state (default: .aibrain)
        """
        self.agent = agent
        self.app_context = app_context
        self.project_path = Path(app_context.project_path)
        self.state_dir = state_dir or (self.project_path / ".aibrain")

        # Record baseline for regression detection
        baseline_recorder = BaselineRecorder(self.project_path, app_context)
        self.agent.baseline = baseline_recorder.record()

    def _get_changed_files(self) -> list[str]:
        """Get list of files changed since baseline."""
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

    def run(self, task_id: str, task_description: str = "", max_iterations: int = None, resume: bool = False) -> IterationResult:
        """
        Run agent with iteration loop and stop hook.

        Args:
            task_id: Task identifier
            task_description: Description of the task (for state file)
            max_iterations: Override agent's max_iterations (optional)
            resume: Resume from saved state if available

        Returns:
            IterationResult with final status
        """
        # Try to resume from state file
        if resume:
            state = read_state_file(self.state_dir / "agent-loop.local.md")
            if state:
                print(f"\n♻️  Resuming from iteration {state.iteration}")
                self.agent.current_iteration = state.iteration
                if state.max_iterations:
                    self.agent.config.max_iterations = state.max_iterations
                if state.completion_promise:
                    self.agent.config.expected_completion_signal = state.completion_promise
                if state.task_description:
                    task_description = state.task_description

        # Override max_iterations if specified
        if max_iterations:
            self.agent.config.max_iterations = max_iterations

        # Store task description in agent for execute() to access
        self.agent.task_description = task_description

        print(f"\n{'='*60}")
        print(f"🔄 Starting iteration loop for {task_id}")
        print(f"   Agent: {self.agent.config.agent_name}")
        print(f"   Max iterations: {self.agent.config.max_iterations}")
        if self.agent.config.expected_completion_signal:
            print(f"   Completion signal: <promise>{self.agent.config.expected_completion_signal}</promise>")
        print(f"{'='*60}\n")

        # Save initial state
        state = LoopState(
            iteration=self.agent.current_iteration,
            max_iterations=self.agent.config.max_iterations,
            completion_promise=self.agent.config.expected_completion_signal,
            task_description=task_description or f"Task {task_id}",
            agent_name=self.agent.config.agent_name,
            session_id=task_id,
            started_at=datetime.now().isoformat(),
            project_name=self.agent.config.project_name,
            task_id=task_id
        )
        write_state_file(state, self.state_dir)

        # PRE-EXECUTION: Consult Knowledge Objects
        relevant_kos = self._consult_knowledge(task_description)
        if relevant_kos:
            self.agent.relevant_knowledge = relevant_kos

        # Iteration loop
        while True:
            iteration_num = self.agent.current_iteration + 1
            print(f"\n--- Iteration {iteration_num}/{self.agent.config.max_iterations} ---")

            # Execute agent task
            try:
                result = self.agent.execute(task_id)
            except Exception as e:
                print(f"❌ Agent execution failed: {e}")
                return IterationResult(
                    task_id=task_id,
                    status="failed",
                    iterations=self.agent.current_iteration,
                    reason=f"Agent execution error: {str(e)}",
                    iteration_summary=self.agent.get_iteration_summary()
                )

            # Get changed files
            changes = self._get_changed_files()
            output = result.get("output", "")

            # Run stop hook
            try:
                stop_result = agent_stop_hook(
                    agent=self.agent,
                    session_id=task_id,
                    changes=changes,
                    output=output,
                    app_context=self.app_context
                )
            except KeyboardInterrupt:
                # User aborted via stop hook
                print("\n⚠️  Session aborted by user")
                return IterationResult(
                    task_id=task_id,
                    status="aborted",
                    iterations=self.agent.current_iteration,
                    reason="User aborted session",
                    iteration_summary=self.agent.get_iteration_summary()
                )

            # Record iteration if we have a verdict
            if stop_result.verdict:
                self.agent.record_iteration(stop_result.verdict, changes)

            # Update state file after each iteration
            state.iteration = self.agent.current_iteration
            write_state_file(state, self.state_dir)

            # Print stop hook message
            if stop_result.system_message:
                print(f"\n{stop_result.system_message}")

            # Handle stop decision
            if stop_result.decision == StopDecision.ALLOW:
                # Agent can exit - cleanup state file
                cleanup_state_file(self.state_dir)
                print(f"\n✅ Task complete after {self.agent.current_iteration} iteration(s)")

                # POST-EXECUTION: Create draft KO if multi-iteration success
                if self.agent.current_iteration >= 2:
                    self._create_draft_ko(task_id, task_description, stop_result.verdict)

                return IterationResult(
                    task_id=task_id,
                    status="completed",
                    iterations=self.agent.current_iteration,
                    verdict=stop_result.verdict,
                    reason=stop_result.reason,
                    iteration_summary=self.agent.get_iteration_summary()
                )

            elif stop_result.decision == StopDecision.ASK_HUMAN:
                # Block and request human approval
                print(f"\n⚠️  Human approval required: {stop_result.reason}")
                print(f"Iteration summary: {self.agent.get_iteration_summary()}")

                # For now, halt (in future, implement approval workflow)
                return IterationResult(
                    task_id=task_id,
                    status="blocked",
                    iterations=self.agent.current_iteration,
                    verdict=stop_result.verdict,
                    reason=stop_result.reason,
                    iteration_summary=self.agent.get_iteration_summary()
                )

            else:  # StopDecision.BLOCK
                # Continue iteration - agent will retry
                print(f"🔄 Continuing to iteration {iteration_num + 1}...")
                continue

    def _consult_knowledge(self, task_description: str) -> list:
        """
        Consult Knowledge Objects before starting work.

        Extracts tags from task description, searches for relevant KOs,
        and displays them to the user. Fails gracefully if errors occur.

        Args:
            task_description: The task description to extract tags from

        Returns:
            List of relevant KnowledgeObject instances (empty if none found or error)
        """
        try:
            # Extract tags from task description
            tags = extract_tags_from_task(task_description)

            if not tags:
                return []

            # Search for relevant KOs
            relevant_kos = find_relevant(
                project=self.agent.config.project_name,
                tags=tags
            )

            if not relevant_kos:
                print(f"\n📚 Knowledge consultation: No relevant KOs found for tags: {tags}")
                return []

            # Display relevant KOs to user
            print(f"\n{'='*60}")
            print(f"📚 RELEVANT KNOWLEDGE OBJECTS ({len(relevant_kos)} found)")
            print(f"{'='*60}")

            for ko in relevant_kos:
                print(format_ko_for_display(ko))
                print()

            print(f"{'='*60}\n")

            return relevant_kos

        except Exception as e:
            # Fail gracefully - don't block agent startup
            print(f"\n⚠️  Knowledge consultation failed: {e}")
            print(f"   Continuing without knowledge context...\n")
            return []

    def _create_draft_ko(self, task_id: str, task_description: str, verdict: Any) -> None:
        """
        Create draft Knowledge Object after successful multi-iteration fix.

        Only creates KO if 2+ iterations (indicating learning occurred).
        Fails gracefully if errors occur - doesn't block agent completion.

        Args:
            task_id: Task identifier
            task_description: Task description
            verdict: Final Ralph verdict
        """
        try:
            # Extract learning from iteration history
            learning = extract_learning_from_iterations(
                task_description=task_description,
                iteration_history=self.agent.iteration_history,
                verdict=verdict,
                changes=self._get_changed_files()
            )

            # Create draft KO
            ko = create_draft(
                project=self.agent.config.project_name,
                title=learning['title'],
                what_was_learned=learning['what_was_learned'],
                why_it_matters=learning['why_it_matters'],
                prevention_rule=learning['prevention_rule'],
                tags=learning['tags'],
                detection_pattern=learning.get('detection_pattern', ''),
                file_patterns=learning.get('file_patterns', [])
            )

            print(f"\n📝 Created draft Knowledge Object: {ko.id}")
            print(f"   Title: {ko.title}")
            print(f"   Tags: {', '.join(ko.tags)}")
            print(f"   Review with: aibrain ko pending")
            print(f"   Approve with: aibrain ko approve {ko.id}\n")

        except Exception as e:
            # Fail gracefully - don't block agent completion
            print(f"\n⚠️  Failed to create draft KO: {e}")
            print(f"   (Task still completed successfully)\n")
