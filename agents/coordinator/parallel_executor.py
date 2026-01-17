"""
Parallel Execution Tracker

Manages concurrent agent execution with:
1. Active agent tracking
2. File lock mechanism to prevent collision
3. Coordination across parallel tasks

Integration: Phase 3 of Governance Harmonization
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# Paths
VIBE_KANBAN_ROOT = Path("/Users/tmac/1_REPOS/AI_Orchestrator/vibe-kanban")
BOARD_STATE_PATH = VIBE_KANBAN_ROOT / "board-state.json"
LOCKS_DIR = VIBE_KANBAN_ROOT / "locks"


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class AgentExecution:
    """Tracks a single agent execution."""
    agent_id: str
    task_id: str
    repo: str
    branch_lane: str
    files_locked: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: utc_now().isoformat())
    status: str = "running"  # running, completed, blocked, failed
    last_heartbeat: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "repo": self.repo,
            "branch_lane": self.branch_lane,
            "files_locked": self.files_locked,
            "started_at": self.started_at,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentExecution":
        return cls(
            agent_id=data.get("agent_id", ""),
            task_id=data.get("task_id", ""),
            repo=data.get("repo", ""),
            branch_lane=data.get("branch_lane", ""),
            files_locked=data.get("files_locked", []),
            started_at=data.get("started_at", ""),
            status=data.get("status", "running"),
            last_heartbeat=data.get("last_heartbeat", ""),
        )


@dataclass
class FileLock:
    """Represents a lock on a file."""
    file_path: str
    agent_id: str
    task_id: str
    acquired_at: str = field(default_factory=lambda: utc_now().isoformat())
    lock_type: str = "exclusive"  # exclusive, shared

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "acquired_at": self.acquired_at,
            "lock_type": self.lock_type,
        }


class ParallelExecutor:
    """
    Manages parallel agent execution with file locking.

    Key features:
    1. Agent Registration - Track which agents are active
    2. File Locking - Prevent multiple agents from modifying same file
    3. Conflict Detection - Identify potential conflicts before they happen
    4. Heartbeat - Detect stale agents
    """

    def __init__(self):
        self._ensure_directories()
        self.active_agents: Dict[str, AgentExecution] = {}
        self.file_locks: Dict[str, FileLock] = {}
        self._load_state()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        LOCKS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> None:
        """Load state from board-state.json."""
        if BOARD_STATE_PATH.exists():
            try:
                with open(BOARD_STATE_PATH, 'r') as f:
                    state = json.load(f)

                # Load active agents
                for agent_data in state.get("agents_active", []):
                    if isinstance(agent_data, dict):
                        agent = AgentExecution.from_dict(agent_data)
                        self.active_agents[agent.agent_id] = agent

                # Load file locks
                for lock_data in state.get("file_locks", []):
                    if isinstance(lock_data, dict):
                        lock = FileLock(**lock_data)
                        self.file_locks[lock.file_path] = lock
            except Exception as e:
                print(f"Error loading state: {e}")

    def _save_state(self) -> None:
        """Save state to board-state.json."""
        try:
            if BOARD_STATE_PATH.exists():
                with open(BOARD_STATE_PATH, 'r') as f:
                    state = json.load(f)
            else:
                state = {"version": "1.0"}

            # Save active agents
            state["agents_active"] = [
                agent.to_dict() for agent in self.active_agents.values()
            ]

            # Save file locks
            state["file_locks"] = [
                lock.to_dict() for lock in self.file_locks.values()
            ]

            state["last_updated"] = utc_now().isoformat()

            with open(BOARD_STATE_PATH, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            print(f"Error saving state: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def register_agent(
        self,
        agent_id: str,
        task_id: str,
        repo: str,
        branch_lane: str,
    ) -> AgentExecution:
        """
        Register an agent for execution.

        Args:
            agent_id: Unique agent identifier
            task_id: Task being executed
            repo: Repository being worked on
            branch_lane: Branch lane for this work

        Returns:
            AgentExecution record
        """
        execution = AgentExecution(
            agent_id=agent_id,
            task_id=task_id,
            repo=repo,
            branch_lane=branch_lane,
        )

        self.active_agents[agent_id] = execution
        self._save_state()

        return execution

    def unregister_agent(self, agent_id: str, status: str = "completed") -> None:
        """
        Unregister an agent and release its locks.

        Args:
            agent_id: Agent to unregister
            status: Final status (completed, failed, blocked)
        """
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            agent.status = status

            # Release all file locks held by this agent
            locks_to_remove = [
                fp for fp, lock in self.file_locks.items()
                if lock.agent_id == agent_id
            ]
            for fp in locks_to_remove:
                self._release_file_lock(fp)

            del self.active_agents[agent_id]
            self._save_state()

    def heartbeat(self, agent_id: str) -> bool:
        """
        Update agent heartbeat timestamp.

        Args:
            agent_id: Agent to update

        Returns:
            True if agent exists and was updated
        """
        if agent_id in self.active_agents:
            self.active_agents[agent_id].last_heartbeat = utc_now().isoformat()
            self._save_state()
            return True
        return False

    def get_active_agents(self) -> List[AgentExecution]:
        """Get all active agents."""
        return list(self.active_agents.values())

    def get_stale_agents(self, timeout_seconds: int = 300) -> List[AgentExecution]:
        """
        Get agents that haven't sent heartbeat within timeout.

        Args:
            timeout_seconds: Heartbeat timeout (default 5 minutes)

        Returns:
            List of stale agents
        """
        now = utc_now()
        stale = []

        for agent in self.active_agents.values():
            try:
                last_hb = datetime.fromisoformat(agent.last_heartbeat.replace('Z', '+00:00'))
                if (now - last_hb).total_seconds() > timeout_seconds:
                    stale.append(agent)
            except Exception:
                # If we can't parse the timestamp, consider it stale
                stale.append(agent)

        return stale

    def cleanup_stale_agents(self, timeout_seconds: int = 300) -> List[str]:
        """
        Clean up stale agents and their locks.

        Args:
            timeout_seconds: Heartbeat timeout

        Returns:
            List of cleaned up agent IDs
        """
        stale = self.get_stale_agents(timeout_seconds)
        cleaned = []

        for agent in stale:
            self.unregister_agent(agent.agent_id, status="stale")
            cleaned.append(agent.agent_id)

        return cleaned

    # ═══════════════════════════════════════════════════════════════════════════
    # FILE LOCKING
    # ═══════════════════════════════════════════════════════════════════════════

    def acquire_lock(
        self,
        agent_id: str,
        task_id: str,
        file_path: str,
        lock_type: str = "exclusive"
    ) -> bool:
        """
        Acquire a lock on a file.

        Args:
            agent_id: Agent requesting lock
            task_id: Task the agent is working on
            file_path: Path to file to lock
            lock_type: Type of lock (exclusive, shared)

        Returns:
            True if lock acquired, False if file already locked
        """
        # Normalize path
        normalized_path = str(Path(file_path).resolve())

        # Check if already locked
        if normalized_path in self.file_locks:
            existing_lock = self.file_locks[normalized_path]

            # Same agent can re-acquire its own lock
            if existing_lock.agent_id == agent_id:
                return True

            # Shared locks allow multiple readers
            if lock_type == "shared" and existing_lock.lock_type == "shared":
                return True

            # Otherwise, conflict
            return False

        # Create lock
        lock = FileLock(
            file_path=normalized_path,
            agent_id=agent_id,
            task_id=task_id,
            lock_type=lock_type,
        )

        self.file_locks[normalized_path] = lock

        # Update agent's locked files
        if agent_id in self.active_agents:
            self.active_agents[agent_id].files_locked.append(normalized_path)

        # Create physical lock file
        self._create_lock_file(normalized_path, lock)

        self._save_state()
        return True

    def release_lock(self, agent_id: str, file_path: str) -> bool:
        """
        Release a lock on a file.

        Args:
            agent_id: Agent releasing lock
            file_path: Path to file to unlock

        Returns:
            True if lock released, False if not held by this agent
        """
        normalized_path = str(Path(file_path).resolve())

        if normalized_path not in self.file_locks:
            return True  # Not locked

        lock = self.file_locks[normalized_path]

        if lock.agent_id != agent_id:
            return False  # Not this agent's lock

        return self._release_file_lock(normalized_path)

    def _release_file_lock(self, file_path: str) -> bool:
        """Internal method to release a lock."""
        if file_path in self.file_locks:
            lock = self.file_locks[file_path]

            # Update agent's locked files
            if lock.agent_id in self.active_agents:
                agent = self.active_agents[lock.agent_id]
                if file_path in agent.files_locked:
                    agent.files_locked.remove(file_path)

            # Remove lock
            del self.file_locks[file_path]

            # Remove physical lock file
            self._remove_lock_file(file_path)

            self._save_state()
            return True

        return False

    def is_locked(self, file_path: str) -> Optional[FileLock]:
        """
        Check if a file is locked.

        Args:
            file_path: Path to check

        Returns:
            FileLock if locked, None otherwise
        """
        normalized_path = str(Path(file_path).resolve())
        return self.file_locks.get(normalized_path)

    def get_locks_for_agent(self, agent_id: str) -> List[FileLock]:
        """Get all locks held by an agent."""
        return [
            lock for lock in self.file_locks.values()
            if lock.agent_id == agent_id
        ]

    def _create_lock_file(self, file_path: str, lock: FileLock) -> None:
        """Create a physical lock file."""
        lock_file = LOCKS_DIR / f"{hash(file_path)}.lock"
        try:
            with open(lock_file, 'w') as f:
                json.dump(lock.to_dict(), f)
        except Exception as e:
            print(f"Error creating lock file: {e}")

    def _remove_lock_file(self, file_path: str) -> None:
        """Remove a physical lock file."""
        lock_file = LOCKS_DIR / f"{hash(file_path)}.lock"
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception as e:
            print(f"Error removing lock file: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFLICT DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def check_conflicts(
        self,
        agent_id: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """
        Check for potential conflicts before an agent starts work.

        Args:
            agent_id: Agent that wants to work on files
            files: List of files agent wants to modify

        Returns:
            Conflict report
        """
        conflicts = []
        warnings = []

        for file_path in files:
            normalized_path = str(Path(file_path).resolve())

            if normalized_path in self.file_locks:
                lock = self.file_locks[normalized_path]
                if lock.agent_id != agent_id:
                    conflicts.append({
                        "file": file_path,
                        "locked_by": lock.agent_id,
                        "task": lock.task_id,
                        "since": lock.acquired_at,
                    })

            # Check if any agent is working in the same directory
            file_dir = str(Path(file_path).parent)
            for lock in self.file_locks.values():
                if lock.agent_id != agent_id:
                    lock_dir = str(Path(lock.file_path).parent)
                    if file_dir == lock_dir:
                        warnings.append({
                            "file": file_path,
                            "nearby_lock": lock.file_path,
                            "locked_by": lock.agent_id,
                        })

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "warnings": warnings,
            "can_proceed": len(conflicts) == 0,
        }

    def get_repo_activity(self, repo: str) -> Dict[str, Any]:
        """
        Get activity summary for a repository.

        Args:
            repo: Repository name

        Returns:
            Activity summary
        """
        agents_in_repo = [
            a for a in self.active_agents.values()
            if a.repo == repo
        ]

        locks_in_repo = [
            l for l in self.file_locks.values()
            if repo in l.file_path
        ]

        return {
            "repo": repo,
            "active_agents": len(agents_in_repo),
            "agents": [a.to_dict() for a in agents_in_repo],
            "locked_files": len(locks_in_repo),
            "locks": [l.to_dict() for l in locks_in_repo],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # PARALLEL EXECUTION HELPERS (v6.0)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_available_slots(self, max_parallel: int) -> int:
        """
        Get number of available worker slots.

        Args:
            max_parallel: Maximum parallel workers allowed

        Returns:
            Number of free worker slots (0 if at capacity)
        """
        active_count = len([a for a in self.active_agents.values() if a.status == "running"])
        return max(0, max_parallel - active_count)

    def wait_for_completion(self, agent_id: str, timeout_seconds: int = 300) -> bool:
        """
        Block until an agent completes or timeout expires.

        Args:
            agent_id: Agent to wait for
            timeout_seconds: Maximum wait time (default 5 minutes)

        Returns:
            True if agent completed, False if timeout or not found
        """
        import time
        start = time.time()

        while (time.time() - start) < timeout_seconds:
            if agent_id not in self.active_agents:
                return True  # Agent unregistered (completed)

            agent = self.active_agents[agent_id]
            if agent.status != "running":
                return True  # Agent finished

            time.sleep(0.5)  # Poll every 500ms

        return False  # Timeout

    def can_acquire_files(self, agent_id: str, files: list[str]) -> bool:
        """
        Check if all files can be acquired without blocking.

        Args:
            agent_id: Agent that wants to lock files
            files: List of files to check

        Returns:
            True if all files can be locked, False if any would block
        """
        for file_path in files:
            lock = self.is_locked(file_path)
            if lock and lock.agent_id != agent_id:
                return False
        return True

    def get_worker_stats(self) -> dict:
        """
        Get statistics about current parallel execution.

        Returns:
            Dict with running/total agents, locked files, stale agents
        """
        running = len([a for a in self.active_agents.values() if a.status == "running"])
        total = len(self.active_agents)
        stale = len(self.get_stale_agents())
        locked_files = len(self.file_locks)

        return {
            "running_agents": running,
            "total_agents": total,
            "stale_agents": stale,
            "locked_files": locked_files,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # COORDINATION
    # ═══════════════════════════════════════════════════════════════════════════

    def coordinate_execution(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Plan coordinated execution of multiple tasks.

        Analyzes tasks for dependencies and file conflicts,
        then assigns execution order.

        Args:
            tasks: List of task dicts with 'id', 'files', 'repo'

        Returns:
            Execution plan with waves and conflicts
        """
        waves: List[List[Dict[str, Any]]] = []
        remaining = list(tasks)
        used_files: Set[str] = set()

        while remaining:
            wave = []
            wave_files: Set[str] = set()

            for task in remaining[:]:
                task_files = set(task.get('files', []))

                # Check if any files conflict with this wave
                if task_files.intersection(wave_files):
                    continue  # Skip to next wave

                # Check dependencies
                deps = task.get('dependencies', [])
                deps_satisfied = all(
                    any(t.get('id') == dep and t in (item for w in waves for item in w)
                        for t in tasks)
                    for dep in deps
                ) if deps else True

                if not deps_satisfied:
                    continue

                # Add to this wave
                wave.append(task)
                wave_files.update(task_files)
                remaining.remove(task)

            if wave:
                waves.append(wave)
                used_files.update(wave_files)
            else:
                # No progress - circular dependency or unresolvable conflict
                break

        return {
            "waves": [
                [t.get('id') for t in wave]
                for wave in waves
            ],
            "wave_count": len(waves),
            "unscheduled": [t.get('id') for t in remaining],
            "has_unscheduled": len(remaining) > 0,
        }


# CLI interface
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Parallel Executor")
    parser.add_argument('command', choices=[
        'status',
        'agents',
        'locks',
        'cleanup',
        'repo-activity',
    ])
    parser.add_argument('--repo', '-r', help='Repository name')
    parser.add_argument('--timeout', type=int, default=300, help='Stale timeout in seconds')
    args = parser.parse_args()

    executor = ParallelExecutor()

    if args.command == 'status':
        agents = executor.get_active_agents()
        locks = list(executor.file_locks.values())
        print(f"Parallel Executor Status:")
        print(f"  Active Agents: {len(agents)}")
        print(f"  File Locks: {len(locks)}")
        stale = executor.get_stale_agents(args.timeout)
        print(f"  Stale Agents: {len(stale)}")

    elif args.command == 'agents':
        agents = executor.get_active_agents()
        print(f"Active Agents ({len(agents)}):")
        for agent in agents:
            print(f"  {agent.agent_id}:")
            print(f"    Task: {agent.task_id}")
            print(f"    Repo: {agent.repo}")
            print(f"    Lane: {agent.branch_lane}")
            print(f"    Locks: {len(agent.files_locked)}")
            print(f"    Status: {agent.status}")

    elif args.command == 'locks':
        locks = list(executor.file_locks.values())
        print(f"File Locks ({len(locks)}):")
        for lock in locks:
            print(f"  {lock.file_path}:")
            print(f"    Agent: {lock.agent_id}")
            print(f"    Task: {lock.task_id}")
            print(f"    Type: {lock.lock_type}")

    elif args.command == 'cleanup':
        cleaned = executor.cleanup_stale_agents(args.timeout)
        print(f"Cleaned up {len(cleaned)} stale agents:")
        for agent_id in cleaned:
            print(f"  - {agent_id}")

    elif args.command == 'repo-activity':
        if not args.repo:
            print("--repo required")
            return
        activity = executor.get_repo_activity(args.repo)
        print(json.dumps(activity, indent=2))


if __name__ == "__main__":
    main()
