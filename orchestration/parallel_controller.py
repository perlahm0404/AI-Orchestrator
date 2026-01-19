#!/usr/bin/env python3
"""
Parallel Execution Controller - Manages parallel worker execution

Spawns and coordinates multiple workers executing tasks concurrently.
"""

import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import subprocess


@dataclass
class SubagentTask:
    """Represents a task assigned to a subagent worker"""
    subagent_id: str                # "worker-0", "worker-1"
    task_id: str                    # Task ID from work queue
    task: Dict                      # Full task data
    agent_type: str                 # Agent type to use
    state_dir: Path                 # Isolated state directory
    status: str                     # "pending" | "running" | "completed" | "escalated" | "failed"
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[Dict]          # Result from iteration loop
    escalation: Optional[Dict]      # Escalation data if escalated
    error: Optional[str]            # Error message if failed


class ParallelController:
    """Manages parallel execution of tasks across multiple workers"""

    def __init__(
        self,
        max_workers: int = 2,
        project_dir: Path = None,
        cito_interface=None
    ):
        """
        Initialize parallel controller

        Args:
            max_workers: Maximum number of parallel workers (default: 2)
            project_dir: Root directory of the project
            cito_interface: CITO interface for escalation handling (optional)
        """
        self.max_workers = max_workers
        self.project_dir = project_dir or Path.cwd()
        self.cito_interface = cito_interface

        # Worker tracking
        self.workers: Dict[str, SubagentTask] = {}
        self.worker_lock = threading.Lock()

        # Executor
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # State directory
        self.aibrain_dir = self.project_dir / ".aibrain"
        self.aibrain_dir.mkdir(parents=True, exist_ok=True)

    def spawn_subagent(
        self,
        task: Dict,
        worker_id: str,
        agent_type: str,
        app_context: Optional[Dict] = None
    ) -> Future:
        """
        Spawn a subagent worker to execute a task

        Args:
            task: Task data from work queue
            worker_id: Worker identifier (e.g., "worker-0")
            agent_type: Agent type to use (e.g., "bugfix", "featurebuilder")
            app_context: Application context for agent

        Returns:
            Future object for the worker execution
        """
        # Create isolated state directory
        state_dir = self.aibrain_dir / worker_id
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create subagent task
        subagent_task = SubagentTask(
            subagent_id=worker_id,
            task_id=task.get("id", "unknown"),
            task=task,
            agent_type=agent_type,
            state_dir=state_dir,
            status="pending",
            started_at=None,
            completed_at=None,
            result=None,
            escalation=None,
            error=None
        )

        # Register worker
        with self.worker_lock:
            self.workers[worker_id] = subagent_task

        # Submit to executor
        future = self.executor.submit(
            self._run_subagent,
            subagent_task,
            app_context
        )

        return future

    def wait_for_workers(
        self,
        futures: Dict[str, Future],
        timeout: Optional[int] = None
    ) -> Dict[str, SubagentTask]:
        """
        Wait for all workers to complete

        Args:
            futures: Dict mapping worker_id to Future
            timeout: Optional timeout in seconds

        Returns:
            Dict mapping worker_id to completed SubagentTask
        """
        results = {}

        for future in as_completed(futures.values(), timeout=timeout):
            worker_id, result = future.result()
            results[worker_id] = result

        return results

    def _run_subagent(
        self,
        subagent_task: SubagentTask,
        app_context: Optional[Dict]
    ) -> tuple[str, SubagentTask]:
        """
        Run subagent worker (executed in thread pool)

        Args:
            subagent_task: Subagent task to execute
            app_context: Application context

        Returns:
            Tuple of (worker_id, completed SubagentTask)
        """
        worker_id = subagent_task.subagent_id

        try:
            # Update status to running
            with self.worker_lock:
                self.workers[worker_id].status = "running"
                self.workers[worker_id].started_at = datetime.now().isoformat()

            # Save worker state
            self._save_worker_state(subagent_task)

            # Execute iteration loop
            result = self._execute_iteration_loop(subagent_task, app_context)

            # Update with result
            with self.worker_lock:
                if result.get("status") == "escalated":
                    self.workers[worker_id].status = "escalated"
                    self.workers[worker_id].escalation = result.get("escalation")
                elif result.get("status") == "completed":
                    self.workers[worker_id].status = "completed"
                else:
                    self.workers[worker_id].status = "failed"
                    self.workers[worker_id].error = result.get("error")

                self.workers[worker_id].result = result
                self.workers[worker_id].completed_at = datetime.now().isoformat()

                # Save final state
                self._save_worker_state(self.workers[worker_id])

                return worker_id, self.workers[worker_id]

        except Exception as e:
            # Handle worker failure
            with self.worker_lock:
                self.workers[worker_id].status = "failed"
                self.workers[worker_id].error = str(e)
                self.workers[worker_id].completed_at = datetime.now().isoformat()

                self._save_worker_state(self.workers[worker_id])

                return worker_id, self.workers[worker_id]

    def _execute_iteration_loop(
        self,
        subagent_task: SubagentTask,
        app_context: Optional[Dict]
    ) -> Dict:
        """
        Execute iteration loop for task

        This is a placeholder that would normally call the IterationLoop class.
        For now, it simulates execution.

        Args:
            subagent_task: Task to execute
            app_context: Application context

        Returns:
            Result dictionary
        """
        # In real implementation, this would:
        # 1. Initialize IterationLoop with task and agent
        # 2. Run iterations until completion or escalation
        # 3. Return iteration result

        # Placeholder simulation
        task = subagent_task.task
        agent_type = subagent_task.agent_type

        # Simulate work
        import time
        time.sleep(1)

        # Simulate result based on task complexity
        if "hipaa" in task.get("description", "").lower():
            # High-risk task - escalate
            return {
                "status": "escalated",
                "reason": "HIPAA-sensitive changes require CITO review",
                "iterations": 5,
                "escalation": {
                    "type": "high_risk",
                    "confidence": 0.7,
                    "recommendation": "Approve with audit logging"
                }
            }
        elif "bug" in task.get("title", "").lower():
            # Simple bug fix - complete
            return {
                "status": "completed",
                "iterations": 3,
                "ralph_verdict": "PASS"
            }
        else:
            # Feature work - complete
            return {
                "status": "completed",
                "iterations": 8,
                "ralph_verdict": "PASS"
            }

    def _save_worker_state(self, subagent_task: SubagentTask):
        """Save worker state to disk"""
        state_file = subagent_task.state_dir / "worker-state.json"

        state = {
            "subagent_id": subagent_task.subagent_id,
            "task_id": subagent_task.task_id,
            "agent_type": subagent_task.agent_type,
            "status": subagent_task.status,
            "started_at": subagent_task.started_at,
            "completed_at": subagent_task.completed_at,
            "result": subagent_task.result,
            "escalation": subagent_task.escalation,
            "error": subagent_task.error
        }

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def get_worker_status(self, worker_id: str) -> Optional[SubagentTask]:
        """Get current status of a worker"""
        with self.worker_lock:
            return self.workers.get(worker_id)

    def list_active_workers(self) -> List[SubagentTask]:
        """List all active workers"""
        with self.worker_lock:
            return [
                worker for worker in self.workers.values()
                if worker.status in ["pending", "running"]
            ]

    def shutdown(self, wait: bool = True):
        """Shutdown the executor"""
        self.executor.shutdown(wait=wait)


# CLI for testing
if __name__ == "__main__":
    import sys

    controller = ParallelController(max_workers=2)

    # Test tasks
    test_tasks = [
        {
            "id": "TASK-001",
            "title": "Fix button bug",
            "description": "Update button click handler"
        },
        {
            "id": "TASK-002",
            "title": "HIPAA audit log enhancement",
            "description": "Add HIPAA compliance logging for PHI access"
        }
    ]

    print("🚀 Spawning parallel workers...")

    futures = {}
    for i, task in enumerate(test_tasks):
        worker_id = f"worker-{i}"
        agent_type = "bugfix" if "bug" in task["title"].lower() else "featurebuilder"

        future = controller.spawn_subagent(task, worker_id, agent_type)
        futures[worker_id] = future

        print(f"   Spawned {worker_id} for {task['id']} ({agent_type})")

    print("\n⏳ Waiting for workers to complete...")

    results = controller.wait_for_workers(futures)

    print("\n✅ All workers completed\n")

    for worker_id, result in results.items():
        print(f"{worker_id}:")
        print(f"  Task: {result.task_id}")
        print(f"  Status: {result.status}")
        print(f"  Agent: {result.agent_type}")
        if result.result:
            print(f"  Iterations: {result.result.get('iterations', 'N/A')}")
        if result.escalation:
            print(f"  Escalation: {result.escalation.get('type', 'N/A')}")
        print()

    controller.shutdown()
