#!/usr/bin/env python3
"""
Parallel Autonomous Agent Loop - Multi-Agent Execution (v6.0)

Enables multiple agents to run in parallel on independent tasks:

PARALLEL EXECUTION:
1. Load work queue and group non-conflicting tasks into waves
2. Execute waves sequentially, tasks within each wave in parallel
3. Use ThreadPoolExecutor for I/O-bound agent work (CLI, git, API calls)
4. Serialize git commits via GitCommitQueue to prevent merge conflicts
5. Isolate worker state via per-worker directories (.aibrain/worker-{N}/)

ARCHITECTURE:
┌──────────────────────────────────────────────────────────────┐
│                  parallel_autonomous_loop.py                  │
│                                                              │
│   WaveOrchestrator                                           │
│   ├─ Uses ParallelExecutor.coordinate_execution()            │
│   ├─ Groups non-conflicting tasks into waves                 │
│   └─ Executes waves sequentially, tasks within wave parallel │
│                                                              │
│   ThreadPoolExecutor (max_parallel workers)                  │
│   ├─ Worker 1: Task A (files: src/auth/*)                   │
│   ├─ Worker 2: Task B (files: src/utils/*)                  │
│   └─ Worker 3: Task C (files: src/matching/*)               │
│                                                              │
│   GitCommitQueue (serialized)                                │
│   └─ Commits in order as tasks complete                      │
└──────────────────────────────────────────────────────────────┘

USAGE:
    # Run up to 3 agents in parallel
    python parallel_autonomous_loop.py --project karematch --max-parallel 3

    # Sequential fallback (same as autonomous_loop.py)
    python parallel_autonomous_loop.py --project karematch --max-parallel 1

Based on: autonomous_loop.py (v5.1)
Parallel execution: v6.0 (2026-01-16)
"""

import asyncio
import sys
import time
import queue
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from pathlib import Path
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tasks.work_queue import WorkQueue, Task
from governance.kill_switch import mode
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
from agents.coordinator.parallel_executor import ParallelExecutor


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER CONTEXT - Per-worker state isolation
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WorkerContext:
    """Per-worker state and configuration for isolation."""
    worker_id: int
    state_dir: Path
    lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        """Ensure state directory exists."""
        self.state_dir.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GIT COMMIT QUEUE - Serialized commits to prevent merge conflicts
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(slots=True)
class CommitRequest:
    """Request to commit changes after task completion."""
    task_id: str
    message: str
    project_dir: Path
    worker_id: int
    files_changed: list[str] = field(default_factory=list)


class GitCommitQueue:
    """
    Thread-safe queue for serialized git commits.

    Prevents merge conflicts by processing commits one at a time,
    even when multiple workers complete tasks simultaneously.
    """

    def __init__(self):
        self._queue: queue.Queue[CommitRequest] = queue.Queue()
        self._lock = threading.Lock()
        self._running = True
        self._worker_thread: threading.Thread | None = None
        self._commit_results: dict[str, bool] = {}

    def start(self):
        """Start the commit worker thread."""
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._commit_worker,
            daemon=True,
            name="GitCommitWorker"
        )
        self._worker_thread.start()

    def stop(self):
        """Stop the commit worker thread."""
        self._running = False
        if self._worker_thread:
            self._queue.put(None)  # Sentinel to unblock queue.get()
            self._worker_thread.join(timeout=5)

    def submit(self, request: CommitRequest) -> None:
        """Submit a commit request to the queue."""
        self._queue.put(request)

    def wait_for_commit(self, task_id: str, timeout: float = 30.0) -> bool:
        """Wait for a specific commit to complete."""
        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            with self._lock:
                if task_id in self._commit_results:
                    return self._commit_results.pop(task_id)
            time.sleep(0.1)
        return False

    def _commit_worker(self):
        """Worker thread that processes commits sequentially."""
        while self._running:
            try:
                request = self._queue.get(timeout=1.0)
                if request is None:
                    break  # Sentinel received

                success = self._do_commit(request)

                with self._lock:
                    self._commit_results[request.task_id] = success

            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️  Commit worker error: {e}")

    def _do_commit(self, request: CommitRequest) -> bool:
        """Execute a git commit."""
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=request.project_dir,
                check=True,
                capture_output=True
            )

            # Commit with message
            subprocess.run(
                ["git", "commit", "-m", request.message],
                cwd=request.project_dir,
                check=True,
                capture_output=True
            )

            print(f"✅ [Worker {request.worker_id}] Committed: {request.task_id}")
            return True

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            # Empty commits are OK (no changes)
            if "nothing to commit" in stderr.lower():
                print(f"⚪ [Worker {request.worker_id}] No changes to commit: {request.task_id}")
                return True
            print(f"❌ [Worker {request.worker_id}] Commit failed: {stderr}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE ORCHESTRATOR - Plans and executes parallel task waves
# ═══════════════════════════════════════════════════════════════════════════════

class WaveOrchestrator:
    """
    Orchestrates parallel task execution using waves.

    Waves are groups of non-conflicting tasks that can run in parallel.
    Tasks conflict if they modify the same files.
    """

    def __init__(
        self,
        work_queue: WorkQueue,
        project_dir: Path,
        app_context: Any,
        max_parallel: int = 3,
        non_interactive: bool = False
    ):
        self.work_queue = work_queue
        self.project_dir = project_dir
        self.app_context = app_context
        self.max_parallel = max_parallel
        self.non_interactive = non_interactive

        # Initialize components
        self.parallel_executor = ParallelExecutor()
        self.commit_queue = GitCommitQueue()

        # Worker contexts (one per parallel slot)
        self.workers: dict[int, WorkerContext] = {
            i: WorkerContext(
                worker_id=i,
                state_dir=project_dir / ".aibrain" / f"worker-{i}"
            )
            for i in range(max_parallel)
        }

    def plan_waves(self) -> list[list[Task]]:
        """
        Plan execution waves from pending tasks.

        Uses ParallelExecutor.coordinate_execution() to group tasks
        that don't have file conflicts.

        Returns:
            List of waves, where each wave is a list of non-conflicting tasks
        """
        # Get all pending tasks
        pending_tasks = [t for t in self.work_queue.features if t.status == "pending"]

        if not pending_tasks:
            return []

        # Convert tasks to format expected by coordinate_execution
        task_dicts = []
        for task in pending_tasks:
            # Infer files touched from task.file (could expand to include test files)
            files = [task.file]
            if task.tests:
                files.extend(task.tests)

            task_dicts.append({
                'id': task.id,
                'files': files,
                'repo': self.work_queue.project,
                'task': task  # Store original task for later
            })

        # Get execution plan
        plan = self.parallel_executor.coordinate_execution(task_dicts)

        # Convert wave IDs back to Task objects
        waves = []
        task_by_id = {t.id: t for t in pending_tasks}

        for wave_ids in plan['waves']:
            wave_tasks = [task_by_id[tid] for tid in wave_ids if tid in task_by_id]
            if wave_tasks:
                waves.append(wave_tasks)

        # Log unscheduled tasks
        if plan['has_unscheduled']:
            print(f"⚠️  {len(plan['unscheduled'])} tasks could not be scheduled (circular deps)")
            for tid in plan['unscheduled']:
                print(f"   - {tid}")

        return waves

    def execute_wave(self, wave: list[Task]) -> dict[str, Any]:
        """
        Execute a wave of tasks in parallel.

        Args:
            wave: List of non-conflicting tasks to execute in parallel

        Returns:
            Results dict with per-task status
        """
        results = {}

        # Limit wave size to max_parallel
        wave_tasks = wave[:self.max_parallel]

        if len(wave) > self.max_parallel:
            print(f"⚠️  Wave has {len(wave)} tasks but max_parallel={self.max_parallel}")
            print(f"   Remaining {len(wave) - self.max_parallel} tasks deferred to next wave")

        print(f"\n{'─'*80}")
        print(f"🌊 Executing wave with {len(wave_tasks)} parallel task(s)")
        print(f"{'─'*80}")
        for i, task in enumerate(wave_tasks):
            print(f"   [{i}] {task.id}: {task.description[:50]}...")

        # Execute tasks in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            # Submit all tasks
            future_to_task: dict[Future[dict[str, Any]], Task] = {}

            for i, task in enumerate(wave_tasks):
                worker = self.workers[i]
                future = executor.submit(
                    self._execute_single_task,
                    task,
                    worker
                )
                future_to_task[future] = task

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.id] = result
                except Exception as e:
                    print(f"❌ [Task {task.id}] Exception: {e}")
                    results[task.id] = {
                        'status': 'failed',
                        'error': str(e)
                    }

        return results

    def _execute_single_task(self, task: Task, worker: WorkerContext) -> dict[str, Any]:
        """
        Execute a single task in a worker thread.

        This is the core task execution logic, adapted from autonomous_loop.py.
        """
        from orchestration.iteration_loop import IterationLoop
        from agents.factory import create_agent, infer_agent_type

        print(f"\n🔧 [Worker {worker.worker_id}] Starting {task.id}")

        # Acquire file lock via ParallelExecutor
        agent_id = f"worker-{worker.worker_id}-{task.id}"

        # Register agent with file locks
        self.parallel_executor.register_agent(
            agent_id=agent_id,
            task_id=task.id,
            repo=self.work_queue.project,
            branch_lane="parallel"
        )

        # Acquire lock on task file
        if not self.parallel_executor.acquire_lock(agent_id, task.id, task.file):
            print(f"⚠️  [Worker {worker.worker_id}] Could not acquire lock on {task.file}")
            self.parallel_executor.unregister_agent(agent_id, status="blocked")
            return {'status': 'blocked', 'reason': f'File locked: {task.file}'}

        try:
            # Mark task in progress (thread-safe via work_queue lock)
            self.work_queue.mark_in_progress(task.id)

            # Determine agent type
            agent_type = infer_agent_type(task.id)

            # Create agent with task-specific config
            agent = create_agent(
                task_type=agent_type,
                project_name=self.work_queue.project,
                completion_promise=task.completion_promise if hasattr(task, 'completion_promise') and task.completion_promise else None,
                max_iterations=task.max_iterations if hasattr(task, 'max_iterations') and task.max_iterations else None
            )

            # Set task context
            agent.task_description = task.description
            agent.task_file = task.file
            agent.task_tests = task.tests if hasattr(task, 'tests') else []

            # Run iteration loop with worker-specific state dir
            loop = IterationLoop(
                agent=agent,
                app_context=self.app_context,
                state_dir=worker.state_dir  # Worker-isolated state
            )

            result = loop.run(
                task_id=task.id,
                task_description=task.description,
                max_iterations=None,
                resume=True
            )

            # Process result
            if result.status == "completed":
                # Get changed files
                changed_files = self._get_git_changed_files()
                verdict_str = None
                if result.verdict:
                    verdict_str = str(result.verdict.type.value).upper()

                # Mark complete (thread-safe)
                self.work_queue.mark_complete(
                    task.id,
                    verdict=verdict_str,
                    files_changed=changed_files
                )

                # Submit commit to serialized queue
                task_prefix = task.id.split('-')[0].lower()
                commit_type = "fix" if task_prefix in ["bug", "bugfix", "fix"] else "feat"
                commit_msg = f"{commit_type}: {task.description}\n\nTask ID: {task.id}\nIterations: {result.iterations}\nWorker: {worker.worker_id}"

                self.commit_queue.submit(CommitRequest(
                    task_id=task.id,
                    message=commit_msg,
                    project_dir=self.project_dir,
                    worker_id=worker.worker_id,
                    files_changed=changed_files
                ))

                print(f"✅ [Worker {worker.worker_id}] Completed {task.id} ({result.iterations} iterations)")

                return {
                    'status': 'completed',
                    'iterations': result.iterations,
                    'verdict': verdict_str
                }

            elif result.status == "blocked":
                self.work_queue.mark_blocked(task.id, result.reason)
                print(f"🚫 [Worker {worker.worker_id}] Blocked {task.id}: {result.reason}")
                return {
                    'status': 'blocked',
                    'reason': result.reason
                }

            else:  # failed or aborted
                self.work_queue.mark_blocked(task.id, result.reason or "Task failed")
                print(f"❌ [Worker {worker.worker_id}] Failed {task.id}: {result.reason}")
                return {
                    'status': 'failed',
                    'reason': result.reason
                }

        except Exception as e:
            traceback.print_exc()
            self.work_queue.mark_blocked(task.id, str(e))
            return {
                'status': 'failed',
                'error': str(e)
            }

        finally:
            # Always release locks and unregister agent
            self.parallel_executor.release_lock(agent_id, task.file)
            self.parallel_executor.unregister_agent(agent_id, status="completed")

    def _get_git_changed_files(self) -> list[str]:
        """Get list of files changed in working directory."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return []
        except Exception:
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PARALLEL LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def run_parallel_loop(
    project_dir: Path,
    max_iterations: int = 50,
    project_name: str = "karematch",
    max_parallel: int = 3,
    queue_type: str = "bugs",
    non_interactive: bool = False
) -> None:
    """
    Main parallel autonomous loop.

    Processes work queue with parallel agent execution:
    - Groups non-conflicting tasks into waves
    - Executes waves sequentially, tasks within wave in parallel
    - Uses ThreadPoolExecutor for I/O-bound agent work
    - Serializes git commits to prevent merge conflicts

    Args:
        project_dir: Path to project directory
        max_iterations: Maximum global iterations (across all waves)
        project_name: Project to work on (karematch or credentialmate)
        max_parallel: Maximum parallel agents (default: 3)
        queue_type: Queue type to process ("bugs" or "features")
        non_interactive: If True, auto-revert on guardrail violations
    """
    print(f"\n{'='*80}")
    print(f"🚀 Starting Parallel Autonomous Agent Loop (v6.0)")
    print(f"{'='*80}\n")
    print(f"Project: {project_name}")
    print(f"Queue type: {queue_type}")
    print(f"Max parallel: {max_parallel}")
    print(f"Max iterations: {max_iterations}\n")

    # Load work queue
    if queue_type == "features":
        queue_path = Path(__file__).parent / "tasks" / f"work_queue_{project_name}_features.json"
    else:
        queue_path = Path(__file__).parent / "tasks" / f"work_queue_{project_name}.json"
    work_queue = WorkQueue.load(queue_path)

    print(f"📋 Work Queue Stats:")
    stats = work_queue.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()

    # Load adapter
    if project_name == "karematch":
        adapter = KareMatchAdapter()
    elif project_name == "credentialmate":
        adapter = CredentialMateAdapter()
    else:
        print(f"❌ Unknown project: {project_name}")
        return

    app_context = adapter.get_context()
    app_context.non_interactive = non_interactive
    actual_project_dir = Path(app_context.project_path)

    # Initialize circuit breaker
    circuit_breaker = reset_lambda_breaker(max_calls=100 * max_parallel)
    app_context.circuit_breaker = circuit_breaker
    print(f"⚡ Circuit breaker: max {circuit_breaker.max_calls_per_session} calls")

    # Initialize resource tracker
    resource_tracker = ResourceTracker(
        project=project_name,
        limits=ResourceLimits(
            max_iterations=max_iterations,
            retry_escalation_threshold=10,
        ),
    )
    print(f"💰 Resource tracker: max {max_iterations} iterations")

    # Initialize wave orchestrator
    orchestrator = WaveOrchestrator(
        work_queue=work_queue,
        project_dir=actual_project_dir,
        app_context=app_context,
        max_parallel=max_parallel,
        non_interactive=non_interactive
    )

    # Start commit queue worker
    orchestrator.commit_queue.start()

    # Initialize counters before try block to ensure they're always bound
    total_completed = 0
    total_blocked = 0

    try:
        # Check kill-switch
        mode.require_normal()
        circuit_breaker.check()

        # Plan waves
        waves = orchestrator.plan_waves()

        if not waves:
            print("✅ No pending tasks - queue is empty!")
            return

        print(f"\n📊 Execution Plan:")
        print(f"   Total waves: {len(waves)}")
        for i, wave in enumerate(waves):
            print(f"   Wave {i+1}: {len(wave)} task(s) - {[t.id for t in wave]}")
        print()

        # Execute waves
        iteration = 0

        for wave_num, wave in enumerate(waves):
            # Check limits before each wave
            try:
                mode.require_normal()
                circuit_breaker.check()
            except (KillSwitchActive, CircuitBreakerTripped) as e:
                print(f"\n🛑 Execution halted: {e}")
                break

            resource_check = resource_tracker.record_iteration()
            if resource_check.exceeded:
                print(f"\n🛑 Resource limit exceeded")
                for reason in resource_check.reasons:
                    print(f"   - {reason}")
                break

            print(f"\n{'═'*80}")
            print(f"🌊 WAVE {wave_num + 1}/{len(waves)}")
            print(f"{'═'*80}")

            # Execute wave
            results = orchestrator.execute_wave(wave)

            # Save queue after each wave
            work_queue.save(queue_path)

            # Tally results
            for task_id, result in results.items():
                if result.get('status') == 'completed':
                    total_completed += 1
                else:
                    total_blocked += 1

            iteration += len(wave)

            if iteration >= max_iterations:
                print(f"\n⚠️  Max iterations ({max_iterations}) reached")
                break

            # Brief pause between waves
            await asyncio.sleep(2)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")

    finally:
        # Stop commit queue
        orchestrator.commit_queue.stop()

        # Clean up stale agents
        cleaned = orchestrator.parallel_executor.cleanup_stale_agents()
        if cleaned:
            print(f"\n🧹 Cleaned up {len(cleaned)} stale agents")

        # Final stats
        print(f"\n{'='*80}")
        print(f"📊 Final Stats")
        print(f"{'='*80}\n")
        final_stats = work_queue.get_stats()
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
        print(f"\n   Total completed this run: {total_completed}")
        print(f"   Total blocked this run: {total_blocked}")

        # Circuit breaker stats
        cb_stats = circuit_breaker.get_stats()
        print(f"\n⚡ Circuit Breaker:")
        print(f"   Calls: {cb_stats['call_count']}/{cb_stats['max_calls']}")
        print(f"   State: {cb_stats['state']}")


def main():
    """
    CLI entry point for parallel autonomous loop.

    Usage:
        # Run 3 parallel agents
        python parallel_autonomous_loop.py --project karematch --max-parallel 3

        # Sequential mode (like autonomous_loop.py)
        python parallel_autonomous_loop.py --project karematch --max-parallel 1
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Parallel Autonomous Agent Loop (v6.0)",
        epilog="""
Examples:
  # Run 3 parallel agents on KareMatch
  python parallel_autonomous_loop.py --project karematch --max-parallel 3

  # Sequential mode (backwards compatible)
  python parallel_autonomous_loop.py --project karematch --max-parallel 1

  # Multi-repo parallel (run separately)
  python parallel_autonomous_loop.py --project karematch &
  python parallel_autonomous_loop.py --project credentialmate &

Features:
  - Wave-based scheduling: Non-conflicting tasks run in parallel
  - File locking: ParallelExecutor prevents collision
  - Serialized commits: GitCommitQueue prevents merge conflicts
  - Worker isolation: Per-worker state directories
  - ThreadPoolExecutor: True parallelism for I/O-bound agents
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
        help="Maximum global iterations (default: 50)"
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=3,
        help="Maximum parallel agents (default: 3)"
    )
    parser.add_argument(
        "--queue",
        default="bugs",
        choices=["bugs", "features"],
        help="Queue type: bugs or features (default: bugs)"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Auto-revert guardrail violations instead of prompting"
    )

    args = parser.parse_args()

    # Determine project directory
    if args.project == "karematch":
        adapter = KareMatchAdapter()
    else:
        adapter = CredentialMateAdapter()

    project_dir = Path(adapter.get_context().project_path)

    # Run loop
    try:
        asyncio.run(run_parallel_loop(
            project_dir=project_dir,
            max_iterations=args.max_iterations,
            project_name=args.project,
            max_parallel=args.max_parallel,
            queue_type=args.queue,
            non_interactive=args.non_interactive
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   To resume, run the same command again")


if __name__ == "__main__":
    main()
