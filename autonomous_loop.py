#!/usr/bin/env python3
"""
Autonomous Agent Loop - Wiggum-Integrated Autonomous System (v5.1) + Monitoring UI (v6.1)

Fully autonomous work queue processing with Wiggum iteration control:

WORK DISCOVERY & EXECUTION:
1. Pull next task from work_queue.json
2. Create agent with task-specific config (completion promise, iteration budget)
3. Run Wiggum IterationLoop with self-correction (15-50 retries per task)
4. Fast verify with Ralph (30 seconds)
5. On BLOCKED: Ask human for Revert/Override/Abort decision
6. On COMPLETED: Commit to git and continue to next task
7. Repeat until queue empty or max iterations reached

WIGGUM INTEGRATION FEATURES:
- Completion signals: Agent outputs <promise>TEXT</promise> when done
- Iteration budgets: 15-50 retries per task (agent-specific)
- State persistence: Automatic resume from .aibrain/agent-loop.local.md
- Human escalation: Only on BLOCKED verdicts (guardrails)
- Iteration tracking: Full audit trail of attempts, verdicts, changes
- Ralph verification: PASS/FAIL/BLOCKED verdicts every iteration

MONITORING UI (v6.1):
- WebSocket streaming: Real-time task events to React dashboard
- Event types: loop_start, task_start, task_complete, ralph_verdict, loop_complete
- Dashboard: http://localhost:3000 (when UI is running)
- WebSocket server: ws://localhost:8080/ws (auto-started with --enable-monitoring)

AUTONOMY LEVEL: 87% (up from 60% without Wiggum)
- Self-correction: 15-50 retries (vs 3 before)
- Tasks per session: 30-50 (vs 10-15 before)
- Completion detection: Promise tags + verification (vs files only)
- Session resume: Automatic (vs manual before)
- KO approval: Auto (70% confidence-based) (vs 100% manual before)

Note: Uses Claude Code CLI (authenticated via claude.ai), not Anthropic API.

Based on: https://github.com/anthropics/claude-quickstarts/autonomous-coding
Wiggum integration: v5.1 (2026-01-06)
Monitoring UI: v6.1 (2026-02-05)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tasks.work_queue import WorkQueue, Task
from orchestration.queue_manager import WorkQueueManager
from orchestration.models import Feature as FeatureModel
from governance.kill_switch import mode
from governance.bypass_manager import BypassManager, BypassMode
from adapters.karematch import KareMatchAdapter
from adapters.credentialmate import CredentialMateAdapter
from agents.bugfix import BugFixAgent
from orchestration.advisor_integration import AutonomousAdvisorIntegration
from orchestration.circuit_breaker import (
    get_lambda_breaker,
    reset_lambda_breaker,
    CircuitBreakerTripped,
    KillSwitchActive,
)
from governance.resource_tracker import ResourceTracker, ResourceLimits
from governance.cost_estimator import estimate_iteration_cost, format_cost


def read_progress_file(project_dir: Path) -> str:
    """Read claude-progress.txt for session continuity"""
    progress_file = project_dir / "claude-progress.txt"
    if progress_file.exists():
        return progress_file.read_text()
    return ""


def update_progress_file(project_dir: Path, task: Task, status: str, details: str) -> None:
    """Update claude-progress.txt with latest status"""
    progress_file = project_dir / "claude-progress.txt"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {timestamp}\n\n"

    if status == "complete":
        entry += f"- [x] {task.id}: {task.description}\n"
        entry += f"  - Files: {task.file}\n"
        entry += f"  - Status: ✅ Complete\n"
        entry += f"  - {details}\n"
    elif status == "in_progress":
        entry += f"- [ ] {task.id}: {task.description}\n"
        entry += f"  - Status: 🔄 In Progress (attempt {task.attempts})\n"
        entry += f"  - {details}\n"
    elif status == "blocked":
        entry += f"- [ ] {task.id}: {task.description}\n"
        entry += f"  - Status: 🛑 Blocked\n"
        entry += f"  - Reason: {details}\n"

    # Append to file
    with progress_file.open("a") as f:
        f.write(entry)


def _get_git_changed_files(project_dir: Path) -> list[str]:
    """Get list of files changed in working directory (unstaged + staged)"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return []
    except Exception:
        return []


def git_commit(message: str, project_dir: Path) -> bool:
    """Create git commit for completed task"""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=project_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_dir,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e.stderr.decode()}")
        return False


def get_current_branch(project_dir: Path) -> str:
    """Get current git branch"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def create_and_checkout_branch(branch_name: str, project_dir: Path, from_branch: str = "main") -> bool:
    """Create and checkout a new branch"""
    try:
        # Check if branch already exists
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.stdout.strip():
            # Branch exists, just checkout
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=project_dir,
                check=True,
                capture_output=True,
                timeout=10
            )
            print(f"✓ Checked out existing branch: {branch_name}\n")
            return True
        else:
            # Branch doesn't exist, create from base branch
            subprocess.run(
                ["git", "checkout", from_branch],
                cwd=project_dir,
                check=True,
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=project_dir,
                check=True,
                capture_output=True,
                timeout=10
            )
            print(f"✓ Created and checked out new branch: {branch_name}\n")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create/checkout branch {branch_name}: {e}")
        return False


def check_requires_approval(task: Task) -> bool:
    """
    Check if task requires human approval before proceeding.

    Args:
        task: Task to check

    Returns:
        True if approved (or no approval needed), False if rejected
    """
    if not hasattr(task, 'requires_approval') or not task.requires_approval:
        return True  # No approval needed

    print(f"\n{'='*80}")
    print(f"⚠️  APPROVAL REQUIRED")
    print(f"{'='*80}\n")
    print(f"Task {task.id} requires approval for the following items:\n")
    for item in task.requires_approval:
        print(f"  - {item}")
    print()

    response = input("Approve this task? [y/N]: ").strip().lower()
    return response == 'y'


async def run_autonomous_loop(
    project_dir: Path,
    max_iterations: int = 50,
    project_name: str = "karematch",
    enable_self_correction: bool = True,
    queue_type: str = "bugs",
    non_interactive: bool = False,
    bypass_mode: str = "safe",
    enable_monitoring: bool = False,
    use_sqlite: bool = False,
    epic_id: Optional[str] = None
) -> None:
    """
    Main autonomous loop with Wiggum integration (v5.1).

    Processes work queue with full Wiggum iteration control:
    - Pulls tasks from work_queue.json automatically
    - Creates agents with task-specific configs (completion promises, iteration budgets)
    - Runs IterationLoop with 15-50 retries per task (agent-specific)
    - Ralph verification every iteration (30 seconds, not 5 minutes)
    - Human escalation only on BLOCKED verdicts (R/O/A prompt in interactive mode)
    - Automatic session resume from state files
    - Git commit on COMPLETED, continue on BLOCKED

    Args:
        project_dir: Path to project directory (used for progress file)
        max_iterations: Maximum global iterations before stopping (default: 50)
        project_name: Project to work on (karematch or credentialmate)
        enable_self_correction: Deprecated - Wiggum always enables self-correction
        queue_type: Queue type to process ("bugs" or "features", default: "bugs")
        non_interactive: If True, auto-revert on guardrail violations instead of prompting (default: False)
        bypass_mode: Bypass mode for governance checks (safe/normal/fast/dangerous/yolo)
        enable_monitoring: If True, start WebSocket server for real-time monitoring UI

    Returns:
        None - Runs until queue empty, max iterations, or user abort

    Example:
        # Process bugfix work queue
        await run_autonomous_loop(
            project_dir=Path("/Users/tmac/karematch"),
            max_iterations=100,
            project_name="karematch",
            queue_type="bugs"
        )

        # Process feature work queue with monitoring
        await run_autonomous_loop(
            project_dir=Path("/Users/tmac/karematch"),
            max_iterations=100,
            project_name="karematch",
            queue_type="features",
            enable_monitoring=True
        )

        # After interruption (Ctrl+C), simply run again to resume
        await run_autonomous_loop(...)  # Automatically resumes from state file
    """
    # Initialize monitoring (Phase 1 - WebSocket streaming)
    from orchestration.monitoring_integration import MonitoringIntegration

    monitoring = MonitoringIntegration(enabled=enable_monitoring)
    await monitoring.start()

    print(f"\n{'='*80}")
    print(f"🤖 Starting Autonomous Agent Loop")
    print(f"{'='*80}\n")
    print(f"Project: {project_name}")
    print(f"Queue type: {queue_type}")
    print(f"Max iterations: {max_iterations}\n")

    # Stream loop start event
    await monitoring.loop_start(
        project=project_name,
        max_iterations=max_iterations,
        queue_type=queue_type
    )

    # Load work queue (JSON or SQLite mode)
    if use_sqlite:
        # SQLite mode: Use WorkQueueManager with feature hierarchy
        print(f"📊 Using SQLite work queue with feature hierarchy")
        if epic_id:
            print(f"   Filtering to epic: {epic_id}")

        queue_manager = WorkQueueManager(project=project_name, use_db=True)

        # Get stats from SQLite
        print(f"\n📋 Work Queue Stats (SQLite):")
        with queue_manager._get_session() as session:
            from orchestration.models import Epic, Task as TaskModel
            epics = session.query(Epic).all()
            all_tasks = session.query(TaskModel).all()
            pending_tasks = [t for t in all_tasks if t.status == "pending"]
            completed_tasks = [t for t in all_tasks if t.status == "completed"]

            print(f"   Epics: {len(epics)}")
            print(f"   Total tasks: {len(all_tasks)}")
            print(f"   Pending: {len(pending_tasks)}")
            print(f"   Completed: {len(completed_tasks)}")
        print()
    else:
        # JSON mode: Use legacy WorkQueue
        if queue_type == "features":
            queue_path = Path(__file__).parent / "tasks" / f"work_queue_{project_name}_features.json"
        else:
            queue_path = Path(__file__).parent / "tasks" / f"work_queue_{project_name}.json"
        queue = WorkQueue.load(queue_path)

        print(f"📋 Work Queue Stats:")
        stats = queue.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print()

    # Helper functions to abstract queue operations (SQLite vs JSON)
    def save_queue():
        """Save queue state (only for JSON mode)."""
        if not use_sqlite:
            queue.save(queue_path)

    def mark_in_progress_helper(task_id: str):
        """Mark task as in_progress in either SQLite or JSON mode."""
        if use_sqlite:
            # SQLite: status update via WorkQueueManager
            queue_manager.update_status(task_id, "in_progress")
        else:
            queue.mark_in_progress(task_id)
            save_queue()

    def mark_complete_helper(task_id: str, verdict: Optional[str] = None, files_changed: list = []):
        """Mark task as complete in either SQLite or JSON mode."""
        if use_sqlite:
            # SQLite: just update status (triggers handle feature/epic rollup)
            queue_manager.update_status(task_id, "completed")

            # TODO: Stream feature_complete event when all tasks in feature are done
            # This requires monitoring.feature_complete() method to be implemented
        else:
            mark_complete_helper(task_id, verdict=verdict, files_changed=files_changed)
            save_queue()

    def mark_blocked_helper(task_id: str, reason: str):
        """Mark task as blocked in either SQLite or JSON mode."""
        if use_sqlite:
            # For SQLite, we could set status to 'blocked' but the schema doesn't have that
            # For now, keep as pending and rely on manual intervention
            # In production, you'd add a 'blocked' status to the schema
            pass  # TODO: Add blocked status to schema
        else:
            mark_blocked_helper(task_id, reason)
            save_queue()

    # Load adapter
    if project_name == "karematch":
        adapter = KareMatchAdapter()  # type: ignore
    elif project_name == "credentialmate":
        adapter = CredentialMateAdapter()  # type: ignore
    else:
        print(f"❌ Unknown project: {project_name}")
        return

    app_context = adapter.get_context()
    app_context.non_interactive = non_interactive  # Set execution mode
    actual_project_dir = Path(app_context.project_path)

    # Initialize bypass manager (Phase 1 - Dangerous Mode Bypass System)
    bypass_mode_enum = BypassMode(bypass_mode)
    bypass_manager = BypassManager(
        mode=bypass_mode_enum,
        audit_log=actual_project_dir / ".aibrain" / "bypass-audit.log"
    )
    app_context.bypass_manager = bypass_manager  # type: ignore  # Make available to agents
    print(f"🚦 Bypass mode: {bypass_mode.upper()} - {bypass_mode_enum.value}")

    # Initialize advisor integration
    advisor_integration = AutonomousAdvisorIntegration(actual_project_dir)
    print("🧠 Advisor integration enabled")

    # Initialize circuit breaker for Lambda/API cost control (ADR-003)
    # Adjust limits based on bypass mode (YOLO gets higher limits)
    max_calls = 100 if bypass_mode in ["safe", "normal"] else 500
    circuit_breaker = reset_lambda_breaker(max_calls=max_calls)
    app_context.circuit_breaker = circuit_breaker  # type: ignore  # Make available to agents
    print(f"⚡ Circuit breaker initialized: max {circuit_breaker.max_calls_per_session} calls/session")

    # Initialize resource tracker for cost guardian (ADR-004)
    resource_tracker = ResourceTracker(
        project=project_name,
        limits=ResourceLimits(
            max_iterations=max_iterations,
            retry_escalation_threshold=10,
        ),
    )
    print(f"💰 Resource tracker initialized: max {max_iterations} iterations, ${resource_tracker.limits.max_cost_daily_usd:.2f}/day budget")

    # Show execution mode
    if non_interactive:
        print("🤖 Non-interactive mode: Auto-reverting guardrail violations")

    # Validate work queue tasks
    print("🔍 Validating work queue tasks...")
    validation_errors = queue.validate_tasks(actual_project_dir)
    if validation_errors:
        print(f"⚠️  Found {len(validation_errors)} validation error(s):")
        for error in validation_errors:
            print(f"   - {error}")

        # Mark tasks with missing files as blocked (except feature tasks which CREATE files)
        for task in queue.features:
            if task.status == "pending":
                # Feature tasks are allowed to CREATE files, so skip existence check
                is_feature_task = (
                    (hasattr(task, 'type') and task.type == "feature") or
                    (hasattr(task, 'agent') and task.agent == "FeatureBuilder") or
                    task.id.startswith("FEAT-")
                )

                # Check if this task has validation errors (non-feature tasks only)
                task_file_path = actual_project_dir / task.file
                if not task_file_path.exists() and not is_feature_task:
                    print(f"   🚫 Blocking {task.id} - target file not found")
                    mark_blocked_helper(task.id, f"Target file not found: {task.file}")
                elif not task_file_path.exists() and is_feature_task:
                    print(f"   ✨ Feature task {task.id} - will create new file: {task.file}")

        queue.save(queue_path)
        print(f"\n⚠️  {len([e for e in validation_errors if 'not found' in e])} tasks blocked due to missing files\n")
    else:
        print("✅ All tasks validated successfully\n")

    # Main loop
    for iteration in range(max_iterations):
        print(f"\n{'─'*80}")
        print(f"Iteration {iteration + 1}/{max_iterations}")
        print(f"{'─'*80}\n")

        # 1. Check kill-switch, circuit breaker, and resource limits
        try:
            mode.require_normal()
            circuit_breaker.check()  # Check both kill switch and call limits
        except KillSwitchActive as e:
            print(f"🛑 Kill-switch activated: {e}")
            break
        except CircuitBreakerTripped as e:
            print(f"⚡ Circuit breaker tripped: {e}")
            print(f"   Calls made: {e.call_count}/{e.limit}")
            print(f"   Session terminating cleanly to prevent runaway costs")
            break
        except Exception as e:
            print(f"🛑 System check failed: {e}")
            break

        # 1b. Check resource limits (ADR-004)
        resource_check = resource_tracker.record_iteration()
        if resource_check.exceeded:
            print(f"\n🛑 RESOURCE LIMIT EXCEEDED")
            for reason in resource_check.reasons:
                print(f"   - {reason}")
            print(f"\n   Estimated session cost: {format_cost(resource_tracker.usage.estimated_cost_usd)}")
            print("   Resume with: python autonomous_loop.py --project <name> --max-iterations <n>")
            break
        elif resource_check.warnings:
            print(f"\n⚠️  APPROACHING RESOURCE LIMITS")
            for warning in resource_check.warnings:
                print(f"   - {warning}")

        # 2. Get next task (SQLite or JSON mode)
        if use_sqlite:
            # SQLite mode: Get next task from WorkQueueManager
            task_dict = queue_manager.get_next_task()
            if not task_dict:
                print("✅ All tasks complete!")

                # Stream loop complete event
                with queue_manager._get_session() as session:
                    from orchestration.models import Task as TaskModel
                    all_tasks = session.query(TaskModel).all()
                    completed = len([t for t in all_tasks if t.status == "completed"])
                    blocked = len([t for t in all_tasks if t.status == "blocked"])

                await monitoring.loop_complete(
                    tasks_processed=len(all_tasks),
                    tasks_completed=completed,
                    tasks_failed=blocked
                )

                # Cleanup monitoring
                await monitoring.stop()
                break

            # Convert dict to Task-like object for compatibility
            task = type('Task', (), {
                'id': task_dict['id'],
                'description': task_dict['description'],
                'file': task_dict.get('file', ''),
                'feature_id': task_dict['feature_id'],
                'status': task_dict['status'],
                'attempts': task_dict.get('retries_used', 0),
                'tests': [],
                'completion_promise': 'FEATURE_COMPLETE',
                'max_iterations': 50
            })()
        else:
            # JSON mode: Use legacy WorkQueue
            current_task: Optional[Task] = queue.get_in_progress() or queue.get_next_pending()
            if not current_task:
                print("✅ All tasks complete!")

                # Stream loop complete event
                stats = queue.get_stats()
                await monitoring.loop_complete(
                    tasks_processed=stats.get("total", 0),
                    tasks_completed=stats.get("complete", 0),
                    tasks_failed=stats.get("blocked", 0)
                )

                # Cleanup monitoring
                await monitoring.stop()
                break

            task = current_task  # Assign to task for backward compatibility

        print(f"📌 Current Task: {task.id}")
        print(f"   Description: {task.description}")
        print(f"   File: {task.file}")
        print(f"   Attempts: {task.attempts}\n")

        # Stream task start event to monitoring UI (agent_type determined later)
        await monitoring.task_start(
            task_id=task.id,
            description=task.description,
            file=task.file,
            attempts=task.attempts,
            agent_type="unknown"  # Will be determined after factory import
        )

        # 2b. Check retry escalation (ADR-004)
        if resource_tracker.check_retry_escalation(task.attempts):
            print(f"\n🚨 RETRY ESCALATION: Task {task.id} exceeded {resource_tracker.limits.retry_escalation_threshold} attempts")
            # Register escalation task for human review
            escalation_id = queue.register_discovered_task(
                source=f"RETRY-{task.id}",
                description=f"ESCALATED: {task.description} - failed {task.attempts} times",
                file=task.file,
                discovered_by="cost-guardian",
                priority=0,  # P0 - needs human attention
            )
            if escalation_id:
                print(f"   Created escalation task: {escalation_id}")
            mark_blocked_helper(task.id, f"Retry limit exceeded ({task.attempts} attempts) - escalated to human review")
            queue.save(queue_path)
            update_progress_file(actual_project_dir, task, "blocked", f"Exceeded {task.attempts} retries - escalated")
            continue

        # 3. Handle feature tasks - check branch and approval
        if hasattr(task, 'type') and task.type == "feature":
            # Check if task has branch specified
            if hasattr(task, 'branch') and task.branch:
                current_branch = get_current_branch(actual_project_dir)
                if current_branch != task.branch:
                    print(f"🔀 Switching to feature branch: {task.branch}")
                    if not create_and_checkout_branch(task.branch, actual_project_dir):
                        mark_blocked_helper(task.id, f"Failed to create/checkout branch: {task.branch}")
                        queue.save(queue_path)
                        continue

            # Check if task requires approval
            if not check_requires_approval(task):
                print(f"❌ Task {task.id} rejected by user\n")
                mark_blocked_helper(task.id, "Rejected by user (approval denied)")
                queue.save(queue_path)
                update_progress_file(actual_project_dir, task, "blocked", "Rejected by user")
                continue

        # 4. Mark as in progress
        mark_in_progress_helper(task.id)
        update_progress_file(actual_project_dir, task, "in_progress", "Starting work")

        # 5. Consult advisors for domain-specific guidance
        advisor_result = advisor_integration.pre_task_analysis(
            task_id=task.id,
            description=task.description,
            file_path=task.file,
        )

        if advisor_result["needs_advisor"]:
            print(f"🧠 Advisor Analysis:")
            print(f"   Suggested: {advisor_result['analysis']['suggested_advisors']}")
            print(f"   Priority: {advisor_result['analysis']['priority']}")

            if advisor_result["escalations"]:
                print(f"\n⚠️  ESCALATIONS DETECTED:")
                for esc in advisor_result["escalations"]:
                    print(f"   - {esc}")

                # For required escalations, prompt human (unless non-interactive)
                if advisor_result["analysis"]["priority"] == "required":
                    if non_interactive:
                        print("\n⚙️  Non-interactive mode: Auto-approving strategic domain task")
                    else:
                        print("\n🚨 This task requires human review due to strategic domain.")
                        response = input("Continue anyway? [y/N]: ").strip().lower()
                        if response != 'y':
                            mark_blocked_helper(task.id, "Escalated for human review")
                            queue.save(queue_path)
                            update_progress_file(
                                actual_project_dir, task, "blocked",
                                "Escalated: " + "; ".join(advisor_result["escalations"])
                            )
                            continue

            if advisor_result["recommendations"]:
                print(f"\n📋 Advisor Recommendations Applied")

        # Store advisor context for agent
        advisor_context = advisor_result.get("context_enrichment", "")

        # 5b. Run meta-agent gates (v6.0 - Conditional gates, not sequential)
        # TEMPORARILY DISABLED: Meta-agent gates not yet implemented
        # TODO: Implement GovernanceAgent, ProductManagerAgent, CMOAgent
        # print(f"🛡️  Running meta-agent gates...")
        print(f"⚙️  Meta-agent gates disabled (not yet implemented)\n")

        # 6. Create agent with Wiggum integration
        from orchestration.iteration_loop import IterationLoop
        from agents.factory import create_agent, infer_agent_type

        # Determine agent type from task ID
        agent_type = infer_agent_type(task.id)
        print(f"🤖 Agent type: {agent_type}\n")

        # EDITORIAL TASK DETECTION: Use ContentPipeline for editorial tasks
        if agent_type == "editorial":
            # Editorial tasks use ContentPipeline orchestrator
            from orchestration.content_pipeline import ContentPipeline
            from agents.editorial.editorial_agent import EditorialTask

            print("📝 Editorial task detected - using ContentPipeline\n")

            # Parse EditorialTask from task object
            editorial_task = EditorialTask(
                task_id=task.id,
                category=getattr(task, 'category', "general"),
                topic=getattr(task, 'title', task.description.replace(' ', '-').lower()),
                keywords=getattr(task, 'keywords', []),
                research_sources=getattr(task, 'research_sources', []),
                target_audience=getattr(task, 'target_audience', "general"),
                target_word_count=getattr(task, 'target_word_count', 2000),
                min_seo_score=getattr(task, 'min_seo_score', 60)
            )

            # Load keyword strategy if available
            keyword_strategy = None
            keyword_strategy_path = Path("knowledge/seo/keyword-strategy.yaml")
            if keyword_strategy_path.exists():
                import yaml
                with open(keyword_strategy_path, 'r') as f:
                    keyword_strategy = yaml.safe_load(f)

            # Run with ContentPipeline
            try:
                pipeline = ContentPipeline(adapter=adapter, keyword_strategy=keyword_strategy)
                pipeline_result = pipeline.run(
                    editorial_task,
                    resume=True,
                    non_interactive=False,  # Allow human approval gates
                    max_iterations=50
                )

                # Convert PipelineResult to IterationResult format for consistency
                result = type('obj', (object,), {
                    'status': pipeline_result.status,
                    'iterations': pipeline_result.iterations,
                    'verdict': pipeline_result.verdict,
                    'reason': pipeline_result.reason
                })()

            except Exception as e:
                print(f"❌ Editorial pipeline failed: {e}\n")
                result = type('obj', (object,), {
                    'status': 'failed',
                    'iterations': 0,
                    'verdict': None,
                    'reason': f"Pipeline error: {e}"
                })()

        else:
            # Non-editorial tasks use standard IterationLoop
            # Create agent with task-specific config
            agent = create_agent(
                task_type=agent_type,
                project_name=project_name,
                completion_promise=task.completion_promise if hasattr(task, 'completion_promise') and task.completion_promise else None,
                max_iterations=task.max_iterations if hasattr(task, 'max_iterations') and task.max_iterations else None
            )

            # Set task context on agent for execute() to access
            agent.task_description = task.description
            agent.task_file = task.file
            agent.task_tests = task.tests if hasattr(task, 'tests') else []
            agent.advisor_context = advisor_context  # Inject advisor recommendations

            # 7. Run Wiggum iteration loop
            loop = IterationLoop(
                agent=agent,
                app_context=app_context,
                state_dir=actual_project_dir / ".aibrain"
            )

            result = await loop.run_async(
                task_id=task.id,
                task_description=task.description,
                max_iterations=50,  # Use reasonable default budget
                resume=True  # Enable automatic resume
            )

        # 8. Handle iteration loop result (common for both editorial and non-editorial)
        try:
            if getattr(result, 'status', None) == "completed":  # type: ignore
                # Task completed successfully - get changed files and verdict
                changed_files = _get_git_changed_files(actual_project_dir)
                verdict_str = None
                if hasattr(result, 'verdict') and result.verdict:  # type: ignore
                    verdict_str = str(result.verdict.type.value).upper()  # type: ignore  # "PASS", "FAIL", or "BLOCKED"

                mark_complete_helper(task.id, verdict=verdict_str, files_changed=changed_files)
                queue.save(queue_path)

                # Stream task complete event to monitoring UI
                await monitoring.task_complete(
                    task_id=task.id,
                    verdict=verdict_str or "PASS",
                    iterations=result.iterations,  # type: ignore
                    files_changed=changed_files
                )

                # Track advisor consultation outcome
                advisor_integration.on_task_complete(task.id, success=True)

                # Check if ADR creation is warranted (Phase 5 - ADR Automation Integration)
                from orchestration.advisor_to_adr import should_create_adr, register_adr_creation_task

                if should_create_adr(task, result, advisor_result, changed_files):
                    adr_task_id = register_adr_creation_task(
                        task=task,
                        result=result,
                        advisor_result=advisor_result,
                        changed_files=changed_files,
                        work_queue=queue,
                        project_root=Path(__file__).parent
                    )
                    if adr_task_id:
                        print(f"📋 ADR creation task registered: {adr_task_id}")
                        queue.save(queue_path)

                # Git commit
                task_prefix = task.id.split('-')[0].lower()
                commit_type = "fix" if task_prefix in ["bug", "bugfix", "fix"] else "feat"
                commit_msg = f"{commit_type}: {task.description}\n\nTask ID: {task.id}\nIterations: {result.iterations}"  # type: ignore

                if git_commit(commit_msg, actual_project_dir):
                    print("✅ Changes committed to git\n")
                    update_progress_file(
                        actual_project_dir,
                        task,
                        "complete",
                        f"Completed after {result.iterations} iteration(s)"  # type: ignore
                    )
                else:
                    print("⚠️  Git commit failed, but task marked complete\n")
                    update_progress_file(
                        actual_project_dir,
                        task,
                        "complete",
                        f"Completed after {result.iterations} iteration(s) (commit failed)"  # type: ignore
                    )

            elif result.status == "blocked":  # type: ignore
                # Task blocked (budget exhausted or BLOCKED verdict)
                mark_blocked_helper(task.id, result.reason)  # type: ignore
                queue.save(queue_path)

                # Stream task blocked event to monitoring UI
                await monitoring.task_complete(
                    task_id=task.id,
                    verdict="BLOCKED",
                    iterations=result.iterations,  # type: ignore
                    files_changed=[]
                )

                update_progress_file(
                    actual_project_dir,
                    task,
                    "blocked",
                    f"{result.reason} (after {result.iterations} iterations)"  # type: ignore
                )
                # Track advisor consultation outcome
                advisor_integration.on_task_complete(task.id, success=False)

            elif result.status == "aborted":  # type: ignore
                # User aborted - stop the entire loop
                print("\n🛑 User aborted session - stopping autonomous loop")
                mark_blocked_helper(task.id, "Session aborted by user")
                queue.save(queue_path)
                update_progress_file(
                    actual_project_dir,
                    task,
                    "blocked",
                    "Session aborted by user"
                )
                break  # Exit the main loop

            else:  # "failed"
                # Task failed for other reasons
                mark_blocked_helper(task.id, result.reason or "Task failed")  # type: ignore
                queue.save(queue_path)
                update_progress_file(
                    actual_project_dir,
                    task,
                    "blocked",
                    result.reason or "Task failed"
                )

        except Exception as e:
            print(f"❌ Exception during iteration loop: {e}\n")
            import traceback
            traceback.print_exc()
            mark_blocked_helper(task.id, str(e))
            queue.save(queue_path)
            update_progress_file(actual_project_dir, task, "blocked", str(e))
            continue

        # Brief pause for rate limiting
        await asyncio.sleep(3)

    # Final stats
    print(f"\n{'='*80}")
    print(f"📊 Final Work Queue Stats")
    print(f"{'='*80}\n")
    stats = queue.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Circuit breaker stats (ADR-003)
    cb_stats = circuit_breaker.get_stats()
    print(f"\n⚡ Circuit Breaker Stats:")
    print(f"   Session: {cb_stats['session_id']}")
    print(f"   Calls: {cb_stats['call_count']}/{cb_stats['max_calls']}")
    print(f"   State: {cb_stats['state']}")

    # Resource tracker stats (ADR-004)
    resource_summary = resource_tracker.get_summary()
    print(f"\n💰 Resource Usage (ADR-004):")
    print(f"   Iterations: {resource_summary['session']['iterations']}/{resource_tracker.limits.max_iterations}")
    print(f"   API Calls: {resource_summary['session']['api_calls']}")
    print(f"   Lambda Deploys: {resource_summary['session']['lambda_deploys']}")
    print(f"   Estimated Cost: {format_cost(resource_summary['session']['cost_usd'])}")
    print(f"   Session Duration: {resource_summary['session']['duration_hours']:.2f} hours")

    # Bypass manager stats (Phase 1 - Dangerous Mode Bypass System)
    bypass_stats = bypass_manager.get_stats()
    bypass_audit = bypass_manager.get_audit_summary()
    print(f"\n🚦 Bypass Manager Stats:")
    print(f"   Mode: {bypass_mode.upper()}")
    print(f"   Total Checks: {bypass_stats['total_checks']}")
    print(f"   Ralph Skipped: {bypass_stats['ralph_skipped']} ({bypass_stats['skip_rate']})")
    print(f"   Governance Skipped: {bypass_stats['governance_skipped']}")
    print(f"   Critical Checks: {bypass_stats['critical_checks_run']}")
    print(f"   Critical Violations: {bypass_stats['critical_violations_found']}")
    if bypass_stats['critical_violations_found'] > 0:
        print(f"   ⚠️  Review audit log: .aibrain/bypass-audit.log")

    # Check final status
    final_check = resource_tracker.check_limits()
    if final_check.exceeded:
        print(f"\n   ⚠️  LIMITS EXCEEDED:")
        for reason in final_check.reasons:
            print(f"      - {reason}")
    elif final_check.warnings:
        print(f"\n   ⚠️  APPROACHING LIMITS:")
        for warning in final_check.warnings:
            print(f"      - {warning}")
    else:
        print(f"\n   ✅ All resource limits OK")
    print()


def main() -> None:
    """
    CLI entry point for Wiggum-integrated autonomous loop (v5.1).

    Usage:
        # Start autonomous loop
        python autonomous_loop.py --project karematch --max-iterations 100

        # After interruption, run same command to resume
        python autonomous_loop.py --project karematch --max-iterations 100

    Features:
        - Wiggum iteration control (15-50 retries per task)
        - Completion signal detection (<promise> tags)
        - Ralph verification every iteration
        - Human escalation on BLOCKED (R/O/A prompt)
        - Automatic session resume from state files
        - Full iteration audit trail
        - Git commit on success, continue on blocked
        - KO auto-approval (70% confidence-based)
        - 87% autonomy (30-50 tasks per session)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Autonomous Agent Loop with Wiggum Integration (v5.1)",
        epilog="""
Examples:
  # Process KareMatch work queue
  python autonomous_loop.py --project karematch --max-iterations 100

  # Process CredentialMate work queue
  python autonomous_loop.py --project credentialmate --max-iterations 50

  # Resume after interruption (Ctrl+C)
  python autonomous_loop.py --project karematch --max-iterations 100

Features:
  - Work queue: Pulls tasks from tasks/work_queue.json
  - Wiggum: 15-50 retries per task (agent-specific budgets)
  - Completion: Detects <promise>TEXT</promise> tags
  - Verification: Ralph PASS/FAIL/BLOCKED every iteration
  - Human escalation: Only on BLOCKED (R/O/A prompt)
  - Session resume: Automatic from .aibrain/agent-loop.local.md
  - KO auto-approval: 70%% (confidence-based, PASS + 2-10 iterations)
  - Autonomy: 87%% (30-50 tasks per session)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project",
        default="karematch",
        choices=["karematch", "credentialmate"],
        help="Project to work on (default: karematch)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Maximum global iterations before stopping (default: 50). Each task also has its own iteration budget (15-50)."
    )
    parser.add_argument(
        "--queue",
        default="bugs",
        choices=["bugs", "features"],
        help="Queue type to process: bugs (bugfix/quality) or features (development) (default: bugs)"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode. On guardrail violations (BLOCKED), automatically revert changes and continue with next task instead of prompting."
    )
    parser.add_argument(
        "--bypass-mode",
        type=str,
        default="safe",
        choices=["safe", "normal", "fast", "dangerous", "yolo"],
        help="Bypass mode for governance checks. SAFE: full checks (default), NORMAL: skip Ralph on low-risk, FAST: skip Ralph on all non-critical, DANGEROUS: skip most governance, YOLO: maximum autonomy. Critical checks (DB deletes, prod deploys, secrets) always run."
    )
    parser.add_argument(
        "--enable-monitoring",
        action="store_true",
        help="Enable real-time monitoring UI with WebSocket streaming. Starts server at ws://localhost:8080/ws for dashboard at http://localhost:3000"
    )
    parser.add_argument(
        "--use-sqlite",
        action="store_true",
        help="Use SQLite work queue with epic→feature→task hierarchy instead of JSON work queue. Tasks are automatically processed by feature priority."
    )
    parser.add_argument(
        "--epic",
        type=str,
        default=None,
        help="Filter tasks to specific epic ID when using --use-sqlite mode. Example: --epic EPIC-12AB34CD"
    )

    args = parser.parse_args()

    # Determine project directory
    # For now, using adapter to get path
    if args.project == "karematch":
        adapter = KareMatchAdapter()  # type: ignore
    else:
        adapter = CredentialMateAdapter()  # type: ignore

    project_dir = Path(adapter.get_context().project_path)

    # Run loop
    try:
        asyncio.run(run_autonomous_loop(
            project_dir=project_dir,
            max_iterations=args.max_iterations,
            project_name=args.project,
            queue_type=args.queue,
            non_interactive=args.non_interactive,
            bypass_mode=args.bypass_mode,
            enable_monitoring=args.enable_monitoring,
            use_sqlite=args.use_sqlite,
            epic_id=args.epic
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   To resume, run the same command again")


if __name__ == "__main__":
    main()
