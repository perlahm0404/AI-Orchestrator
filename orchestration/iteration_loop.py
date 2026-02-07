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
from orchestration.session_state import SessionState, format_session_markdown
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Knowledge Object integration
from knowledge.service import find_relevant, create_draft
from orchestration.ko_helpers import extract_tags_from_task, format_ko_for_display, extract_learning_from_iterations
from knowledge.metrics import record_consultation, record_outcome
from knowledge.config import get_config

# Signal template integration
from orchestration.signal_templates import infer_task_type, get_template, build_prompt_with_signal

# Circuit breaker integration (ADR-003)
from orchestration.circuit_breaker import (
    get_lambda_breaker,
    record_lambda_call,
    CircuitBreakerTripped,
    KillSwitchActive,
)


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

        # SessionState for stateless memory (v9.0)
        self.session: SessionState = None
        self.session_enabled = True  # Can be disabled for testing

        # Record baseline for regression detection
        baseline_recorder = BaselineRecorder(self.project_path, app_context)
        self.agent.baseline = baseline_recorder.record()

    def _get_changed_files(self) -> list[str]:
        """Get list of files changed since baseline."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return []
            return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        except (FileNotFoundError, OSError):
            # Git not available in environment - return empty list
            # This is expected in sandboxed environments
            return []

    def _extract_next_steps(self, output: str) -> list[str]:
        """
        Extract next steps from agent output.

        Looks for common patterns like:
        - "Next steps:" followed by bullet points
        - "TODO:" items
        - Numbered lists after completion statements
        """
        if not output:
            return []

        next_steps = []
        lines = output.split('\n')

        in_next_steps_section = False
        for line in lines:
            line_lower = line.lower().strip()

            # Detect next steps section
            if 'next step' in line_lower or 'todo:' in line_lower:
                in_next_steps_section = True
                continue

            # Extract bullet points or numbered items
            if in_next_steps_section:
                if line.strip().startswith(('-', '*', '•')) or (len(line.strip()) > 2 and line.strip()[0].isdigit() and line.strip()[1] in '.):'):
                    step = line.strip().lstrip('-*•0123456789.): ').strip()
                    if step and len(step) > 5:  # Avoid very short items
                        next_steps.append(step[:200])  # Limit length
                elif line.strip() == '':
                    in_next_steps_section = False

            # Limit to 5 next steps
            if len(next_steps) >= 5:
                break

        return next_steps

    def _summarize_output(self, output: str) -> str:
        """
        Create a brief summary of agent output.

        Extracts key information like:
        - Completion status
        - Files modified
        - Key actions taken
        """
        if not output:
            return ""

        # Truncate to reasonable length
        max_length = 500
        if len(output) > max_length:
            # Try to find a good break point
            summary = output[:max_length]
            last_period = summary.rfind('.')
            if last_period > max_length // 2:
                summary = summary[:last_period + 1]
            else:
                summary = summary + "..."
            return summary

        return output

    def _determine_phase(self) -> str:
        """
        Determine current phase based on agent type and iteration.

        Returns a human-readable phase name.
        """
        agent_name = self.agent.config.agent_name.lower()
        iteration = self.agent.current_iteration

        if 'bugfix' in agent_name:
            if iteration <= 2:
                return "diagnosis"
            elif iteration <= 5:
                return "fix_implementation"
            else:
                return "verification"
        elif 'feature' in agent_name:
            if iteration <= 3:
                return "design"
            elif iteration <= 10:
                return "implementation"
            else:
                return "testing"
        elif 'test' in agent_name:
            if iteration <= 2:
                return "test_design"
            else:
                return "test_implementation"
        elif 'quality' in agent_name or 'refactor' in agent_name:
            if iteration <= 2:
                return "analysis"
            else:
                return "refactoring"
        else:
            return f"iteration_{iteration}"

    def _build_iteration_log(self) -> list[dict]:
        """
        Build iteration log from agent's iteration history.

        Returns list of iteration entries for session markdown.
        """
        if not hasattr(self.agent, 'iteration_history'):
            return []

        log = []
        for entry in self.agent.iteration_history:
            log_entry = {
                "num": entry.get('iteration', len(log) + 1),
                "task": entry.get('task', 'Unknown'),
                "result": entry.get('verdict', 'Unknown'),
            }
            if entry.get('notes'):
                log_entry["notes"] = entry['notes']
            log.append(log_entry)

        return log

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

        # Auto-detect task type and apply completion signal template if not configured
        if task_description and not self.agent.config.expected_completion_signal:
            task_type = infer_task_type(task_description)
            template = get_template(task_type)

            if template:
                self.agent.config.expected_completion_signal = template.promise
                print(f"📋 Auto-detected task type: {task_type}")
                print(f"   Using completion signal: <promise>{template.promise}</promise>")

                # Enhance task description with signal instructions
                task_description = build_prompt_with_signal(task_description, task_type)

        # Store task description in agent for execute() to access
        self.agent.task_description = task_description

        # Initialize SessionState for stateless memory (v9.0)
        if self.session_enabled:
            self.session = SessionState(
                task_id=task_id,
                project=self.agent.config.project_name or "unknown"
            )
            # Try to load existing session for additional context
            try:
                existing_session = self.session.get_latest()
                if existing_session and not resume:
                    # Session exists but not explicitly resuming - inform user
                    logger.info(f"Found existing session for {task_id} at iteration {existing_session.get('iteration_count', 0)}")
            except FileNotFoundError:
                pass  # No existing session, starting fresh

        print(f"\n{'='*60}")
        print(f"🔄 Starting iteration loop for {task_id}")
        print(f"   Agent: {self.agent.config.agent_name}")
        print(f"   Max iterations: {self.agent.config.max_iterations}")
        if self.agent.config.expected_completion_signal:
            print(f"   Completion signal: <promise>{self.agent.config.expected_completion_signal}</promise>")
        if self.session_enabled:
            print(f"   Session state: Enabled (stateless memory v9.0)")
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
        relevant_kos = self._consult_knowledge(task_description, task_id)
        if relevant_kos:
            self.agent.relevant_knowledge = relevant_kos
            # Track which KOs were consulted for this task
            self.agent.consulted_ko_ids = [ko.id for ko in relevant_kos]
        else:
            self.agent.consulted_ko_ids = []

        # Iteration loop
        while True:
            iteration_num = self.agent.current_iteration + 1
            print(f"\n--- Iteration {iteration_num}/{self.agent.config.max_iterations} ---")

            # Execute agent task
            try:
                result = self.agent.execute(task_id)
            except CircuitBreakerTripped as e:
                print(f"⚡ Circuit breaker tripped during iteration: {e}")
                return IterationResult(
                    task_id=task_id,
                    status="failed",
                    iterations=self.agent.current_iteration,
                    reason=f"Circuit breaker tripped: {e.reason}",
                    iteration_summary=self.agent.get_iteration_summary()
                )
            except KillSwitchActive as e:
                print(f"🛑 Kill switch activated: {e}")
                return IterationResult(
                    task_id=task_id,
                    status="aborted",
                    iterations=self.agent.current_iteration,
                    reason=f"Kill switch active: {e.mode}",
                    iteration_summary=self.agent.get_iteration_summary()
                )
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

            # Update SessionState with rich iteration data (v9.0 stateless memory)
            if self.session_enabled and self.session:
                try:
                    # Determine status based on stop decision
                    if stop_result.decision == StopDecision.ALLOW:
                        session_status = "completed"
                    elif stop_result.decision == StopDecision.ASK_HUMAN:
                        session_status = "blocked"
                    else:
                        session_status = "in_progress"

                    # Extract next steps from output if available
                    next_steps = self._extract_next_steps(output) if output else []

                    # Build session data
                    session_data = {
                        "iteration_count": self.agent.current_iteration,
                        "phase": self._determine_phase(),
                        "status": session_status,
                        "last_output": self._summarize_output(output),
                        "next_steps": next_steps,
                        "agent_type": self.agent.config.agent_name,
                        "max_iterations": self.agent.config.max_iterations,
                        "context_window": 1,  # Will be tracked by AutonomousLoop
                        "tokens_used": 0,  # Will be tracked by AutonomousLoop
                    }

                    # Add error if blocked
                    if stop_result.decision == StopDecision.ASK_HUMAN:
                        session_data["error"] = stop_result.reason

                    # Add verdict info if available
                    if stop_result.verdict:
                        verdict_str = getattr(stop_result.verdict, 'type', stop_result.verdict)
                        session_data["last_output"] = f"Verdict: {verdict_str}. {session_data['last_output']}"

                    # Generate markdown content
                    session_data["markdown_content"] = format_session_markdown(
                        session_data,
                        iteration_log=self._build_iteration_log()
                    )

                    self.session.save(session_data)
                    logger.debug(f"SessionState saved for iteration {self.agent.current_iteration}")
                except Exception as e:
                    logger.warning(f"Failed to save SessionState: {e}")
                    # Don't block execution on SessionState failures

            # Print stop hook message
            if stop_result.system_message:
                print(f"\n{stop_result.system_message}")

            # Handle stop decision
            if stop_result.decision == StopDecision.ALLOW:
                # Agent can exit - cleanup state file
                cleanup_state_file(self.state_dir)

                # Archive SessionState on completion (v9.0)
                if self.session_enabled and self.session:
                    try:
                        self.session.archive()
                        logger.info(f"SessionState archived for completed task {task_id}")
                    except Exception as e:
                        logger.warning(f"Failed to archive SessionState: {e}")

                print(f"\n✅ Task complete after {self.agent.current_iteration} iteration(s)")

                # Record outcome metrics if KOs were consulted
                if hasattr(self.agent, 'consulted_ko_ids') and self.agent.consulted_ko_ids:
                    try:
                        record_outcome(
                            task_id=task_id,
                            success=True,
                            iterations=self.agent.current_iteration,
                            consulted_ko_ids=self.agent.consulted_ko_ids
                        )
                    except Exception as e:
                        print(f"⚠️  Failed to record outcome metrics: {e}")

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

    def _consult_knowledge(self, task_description: str, task_id: str) -> list:
        """
        Consult Knowledge Objects before starting work.

        Extracts tags from task description, searches for relevant KOs,
        displays them to the user, and records consultation metrics.
        Fails gracefully if errors occur.

        Args:
            task_description: The task description to extract tags from
            task_id: The task ID (for metrics tracking)

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

            # Record consultation metrics
            for ko in relevant_kos:
                record_consultation(ko.id, task_id)

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

        AUTO-APPROVAL: High-confidence KOs are auto-approved based on:
        - Ralph PASS verdict (successful fix)
        - 2-10 iteration range (meaningful learning, not trivial or too complex)

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

            # AUTO-APPROVAL LOGIC: Confidence-based auto-approval
            # Uses configurable thresholds from knowledge/config.py
            ko_config = get_config(self.agent.config.project_name)

            should_auto_approve = False
            if ko_config.auto_approve_enabled:
                # Check verdict requirement
                verdict_ok = verdict.type.value == "PASS" if ko_config.auto_approve_require_pass else True

                # Check iteration range
                iterations_ok = (
                    ko_config.auto_approve_min_iterations <=
                    self.agent.current_iteration <=
                    ko_config.auto_approve_max_iterations
                )

                should_auto_approve = verdict_ok and iterations_ok

            if should_auto_approve:
                # Auto-approve high-confidence KO
                from knowledge.service import approve
                approve(ko.id)

                print(f"\n✅ Auto-approved Knowledge Object: {ko.id}")
                print(f"   Title: {ko.title}")
                print(f"   Tags: {', '.join(ko.tags)}")
                print(f"   Confidence: HIGH (PASS verdict, {self.agent.current_iteration} iterations)")
                print(f"   Status: Approved and ready for use\n")
            else:
                # Low confidence - needs human review
                reason = []
                if ko_config.auto_approve_require_pass and verdict.type.value != "PASS":
                    reason.append(f"verdict={verdict.type.value}")
                if self.agent.current_iteration < ko_config.auto_approve_min_iterations:
                    reason.append(f"iterations<{ko_config.auto_approve_min_iterations} (trivial)")
                elif self.agent.current_iteration > ko_config.auto_approve_max_iterations:
                    reason.append(f"iterations>{ko_config.auto_approve_max_iterations} (too complex)")
                if not ko_config.auto_approve_enabled:
                    reason.append("auto-approval disabled")

                print(f"\n📋 Created draft Knowledge Object: {ko.id}")
                print(f"   Title: {ko.title}")
                print(f"   Tags: {', '.join(ko.tags)}")
                print(f"   Confidence: LOW ({', '.join(reason)})")
                print(f"   Status: Needs human review")
                print(f"   Review with: aibrain ko pending")
                print(f"   Approve with: aibrain ko approve {ko.id}\n")

        except Exception as e:
            # Fail gracefully - don't block agent completion
            print(f"\n⚠️  Failed to create draft KO: {e}")
            print(f"   (Task still completed successfully)\n")

    async def run_async(
        self,
        task_id: str,
        task_description: str = "",
        max_iterations: int = None,
        resume: bool = False,
    ) -> IterationResult:
        """
        Run agent with SDK adapter and async hooks.

        This is the SDK-based implementation that uses:
        - ClaudeSDKAdapter instead of ClaudeCliWrapper
        - PostToolUse hooks for Ralph verification
        - Stop hooks for Wiggum iteration control

        Args:
            task_id: Task identifier
            task_description: Description of the task
            max_iterations: Override agent's max_iterations
            resume: Resume from saved state if available

        Returns:
            IterationResult with final status
        """
        import asyncio

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

        # Auto-detect task type and apply completion signal template
        if task_description and not self.agent.config.expected_completion_signal:
            task_type = infer_task_type(task_description)
            template = get_template(task_type)

            if template:
                self.agent.config.expected_completion_signal = template.promise
                print(f"📋 Auto-detected task type: {task_type}")
                print(f"   Using completion signal: <promise>{template.promise}</promise>")
                task_description = build_prompt_with_signal(task_description, task_type)

        # Store task description in agent
        self.agent.task_description = task_description

        # Initialize SessionState for stateless memory (v9.0)
        if self.session_enabled:
            self.session = SessionState(
                task_id=task_id,
                project=self.agent.config.project_name or "unknown"
            )

        # Determine execution mode for display
        use_sdk = getattr(self.agent.config, 'use_sdk', True)
        mode_str = "Claude Agent SDK (async)" if use_sdk else "Claude CLI Wrapper (OAuth)"

        print(f"\n{'='*60}")
        print(f"🔄 Starting iteration loop for {task_id}")
        print(f"   Agent: {self.agent.config.agent_name}")
        print(f"   Max iterations: {self.agent.config.max_iterations}")
        print(f"   Mode: {mode_str}")
        if self.agent.config.expected_completion_signal:
            print(f"   Completion signal: <promise>{self.agent.config.expected_completion_signal}</promise>")
        if self.session_enabled:
            print(f"   Session state: Enabled (stateless memory v9.0)")
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
            task_id=task_id,
        )
        write_state_file(state, self.state_dir)

        # PRE-EXECUTION: Consult Knowledge Objects
        relevant_kos = self._consult_knowledge(task_description, task_id)
        if relevant_kos:
            self.agent.relevant_knowledge = relevant_kos
            self.agent.consulted_ko_ids = [ko.id for ko in relevant_kos]
        else:
            self.agent.consulted_ko_ids = []

        # Check use_sdk config to determine execution path
        use_sdk = getattr(self.agent.config, 'use_sdk', True)

        # Import SDK context (used by both paths)
        from claude.sdk_adapter import SDKExecutionContext

        # Create execution context for hooks
        context = SDKExecutionContext(
            agent=self.agent,
            app_context=self.app_context,
            baseline=self.agent.baseline,
            session_id=task_id,
            changed_files=[],
            max_iterations=self.agent.config.max_iterations,
        )

        # Execute via SDK or CLI wrapper
        try:
            if use_sdk:
                # Import SDK adapter
                from claude.sdk_adapter import ClaudeSDKAdapter

                # Create SDK adapter
                adapter = ClaudeSDKAdapter(self.project_path)

                # Execute via SDK with hooks
                result = await adapter.execute_task_async(
                    prompt=task_description,
                    files=None,
                    timeout=300,
                    task_type=self.agent.config.agent_name,
                    context=context,
                )
            else:
                # Use CLI wrapper (OAuth authentication via claude login)
                from claude.cli_wrapper import ClaudeCliWrapper

                # Create CLI wrapper (startup protocol disabled - causes timeout issues)
                cli_wrapper = ClaudeCliWrapper(
                    self.project_path,
                    repo_name=self.agent.config.project_name,
                    enable_startup_protocol=False,
                )

                # Execute via CLI wrapper
                result = cli_wrapper.execute_task(
                    prompt=task_description,
                    files=None,
                    timeout=300,
                    allow_dangerous_permissions=True,
                    task_type=self.agent.config.agent_name,
                )
        except CircuitBreakerTripped as e:
            print(f"⚡ Circuit breaker tripped: {e}")
            return IterationResult(
                task_id=task_id,
                status="failed",
                iterations=self.agent.current_iteration,
                reason=f"Circuit breaker tripped: {e.reason}",
                iteration_summary=self.agent.get_iteration_summary(),
            )
        except KillSwitchActive as e:
            print(f"🛑 Kill switch activated: {e}")
            return IterationResult(
                task_id=task_id,
                status="aborted",
                iterations=self.agent.current_iteration,
                reason=f"Kill switch active: {e.mode}",
                iteration_summary=self.agent.get_iteration_summary(),
            )
        except KeyboardInterrupt:
            print("\n⚠️  Session aborted by user")
            return IterationResult(
                task_id=task_id,
                status="aborted",
                iterations=self.agent.current_iteration,
                reason="User aborted session",
                iteration_summary=self.agent.get_iteration_summary(),
            )
        except Exception as e:
            print(f"❌ SDK execution failed: {e}")
            return IterationResult(
                task_id=task_id,
                status="failed",
                iterations=self.agent.current_iteration,
                reason=f"SDK execution error: {str(e)}",
                iteration_summary=self.agent.get_iteration_summary(),
            )

        # Process result
        if not result.success:
            return IterationResult(
                task_id=task_id,
                status="failed",
                iterations=self.agent.current_iteration,
                reason=result.error or "Unknown error",
                iteration_summary=self.agent.get_iteration_summary(),
            )

        # Get final verdict from context
        verdict = context.last_verdict

        # Update iteration count from context
        self.agent.current_iteration = context.current_iteration

        # Record iteration if we have a verdict
        if verdict:
            self.agent.record_iteration(verdict, context.changed_files)

        # Save final SessionState and archive on completion (v9.0)
        if self.session_enabled and self.session:
            try:
                session_data = {
                    "iteration_count": self.agent.current_iteration,
                    "phase": "completed",
                    "status": "completed",
                    "last_output": f"Task completed successfully. Verdict: {verdict}",
                    "next_steps": [],
                    "agent_type": self.agent.config.agent_name,
                    "max_iterations": self.agent.config.max_iterations,
                    "context_window": 1,
                    "tokens_used": 0,
                    "markdown_content": format_session_markdown(
                        {"iteration_count": self.agent.current_iteration, "phase": "completed", "status": "completed"},
                        iteration_log=self._build_iteration_log()
                    ),
                }
                self.session.save(session_data)
                self.session.archive()
                logger.info(f"SessionState archived for completed task {task_id}")
            except Exception as e:
                logger.warning(f"Failed to save/archive SessionState: {e}")

        # Cleanup state file on success
        cleanup_state_file(self.state_dir)
        print(f"\n✅ Task complete after {self.agent.current_iteration} iteration(s)")

        # Record outcome metrics
        if hasattr(self.agent, "consulted_ko_ids") and self.agent.consulted_ko_ids:
            try:
                record_outcome(
                    task_id=task_id,
                    success=True,
                    iterations=self.agent.current_iteration,
                    consulted_ko_ids=self.agent.consulted_ko_ids,
                )
            except Exception as e:
                print(f"⚠️  Failed to record outcome metrics: {e}")

        # POST-EXECUTION: Create draft KO if multi-iteration
        if self.agent.current_iteration >= 2 and verdict:
            self._create_draft_ko(task_id, task_description, verdict)

        return IterationResult(
            task_id=task_id,
            status="completed",
            iterations=self.agent.current_iteration,
            verdict=verdict,
            reason="SDK execution completed successfully",
            iteration_summary=self.agent.get_iteration_summary(),
        )

    def run_with_sdk(
        self,
        task_id: str,
        task_description: str = "",
        max_iterations: int = None,
        resume: bool = False,
    ) -> IterationResult:
        """
        Sync wrapper for run_async (SDK-based execution).

        Use this method for SDK-based execution when you don't need
        async context.

        Args:
            task_id: Task identifier
            task_description: Description of the task
            max_iterations: Override agent's max_iterations
            resume: Resume from saved state if available

        Returns:
            IterationResult with final status
        """
        import asyncio

        return asyncio.run(
            self.run_async(
                task_id=task_id,
                task_description=task_description,
                max_iterations=max_iterations,
                resume=resume,
            )
        )
