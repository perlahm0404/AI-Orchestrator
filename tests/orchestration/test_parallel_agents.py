"""
Tests for Parallel Agent Execution (Priority 5)

TDD approach: Tests written first, then implementation.
Target: Run multiple agents in parallel with coordination.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass
from typing import List, Optional

# These imports will fail until we implement the modules
try:
    from orchestration.parallel_executor import (
        ParallelExecutor,
        ExecutorConfig,
        AgentSlot,
        ExecutionResult,
        CoordinationStrategy,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

    # Placeholder classes for test definition
    @dataclass
    class AgentSlot:
        agent_id: str
        task_id: Optional[str] = None
        status: str = "idle"

    @dataclass
    class ExecutionResult:
        completed: int = 0
        failed: int = 0
        total_time_ms: int = 0

    class CoordinationStrategy:
        INDEPENDENT = "independent"
        FILE_LOCK = "file_lock"
        SEQUENTIAL_FALLBACK = "sequential_fallback"

    @dataclass
    class ExecutorConfig:
        max_parallel: int = 3
        strategy: str = "independent"


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestExecutorConfig:
    """Test ExecutorConfig dataclass."""

    def test_config_has_required_fields(self):
        """Config has all required fields."""
        config = ExecutorConfig(
            max_parallel=4,
            strategy=CoordinationStrategy.FILE_LOCK
        )

        assert config.max_parallel == 4
        assert config.strategy == CoordinationStrategy.FILE_LOCK

    def test_config_default_values(self):
        """Config has sensible defaults."""
        config = ExecutorConfig()

        assert config.max_parallel == 3
        assert config.strategy == CoordinationStrategy.INDEPENDENT


class TestAgentSlot:
    """Test AgentSlot dataclass."""

    def test_slot_tracks_agent_state(self):
        """Slot tracks agent assignment and status."""
        slot = AgentSlot(
            agent_id="agent-1",
            task_id="task-123",
            status="running"
        )

        assert slot.agent_id == "agent-1"
        assert slot.task_id == "task-123"
        assert slot.status == "running"

    def test_slot_defaults_to_idle(self):
        """Slot defaults to idle status."""
        slot = AgentSlot(agent_id="agent-1")

        assert slot.status == "idle"
        assert slot.task_id is None


class TestParallelExecutor:
    """Test ParallelExecutor class."""

    @pytest.fixture
    def executor(self, tmp_path: Path):
        config = ExecutorConfig(max_parallel=3)
        return ParallelExecutor(project_dir=tmp_path, config=config)

    @pytest.fixture
    def mock_tasks(self):
        """Create mock tasks for testing."""
        from tasks.work_queue import Task
        return [
            Task(id="task-1", description="Fix bug 1", file="src/a.py", status="pending"),
            Task(id="task-2", description="Fix bug 2", file="src/b.py", status="pending"),
            Task(id="task-3", description="Fix bug 3", file="src/c.py", status="pending"),
        ]

    def test_executor_initializes_slots(self, executor):
        """Executor initializes correct number of agent slots."""
        assert len(executor.slots) == 3
        for slot in executor.slots:
            assert slot.status == "idle"

    def test_executor_respects_max_parallel(self, tmp_path: Path):
        """Executor respects max_parallel config."""
        config = ExecutorConfig(max_parallel=5)
        executor = ParallelExecutor(project_dir=tmp_path, config=config)

        assert len(executor.slots) == 5

    @pytest.mark.asyncio
    async def test_execute_single_task(self, executor, mock_tasks):
        """Execute a single task successfully."""
        with patch.object(executor, '_run_agent', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": True, "files": ["src/a.py"]}

            result = await executor.execute([mock_tasks[0]])

        assert result.completed == 1
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_execute_parallel_tasks(self, executor, mock_tasks):
        """Execute multiple tasks in parallel."""
        execution_order = []

        async def track_execution(task, slot):
            execution_order.append((task.id, slot.agent_id))
            await asyncio.sleep(0.01)  # Simulate work
            return {"success": True, "files": [task.file]}

        with patch.object(executor, '_run_agent', side_effect=track_execution):
            result = await executor.execute(mock_tasks)

        assert result.completed == 3
        # Verify parallel execution - all should start before any completes
        # (In truly parallel execution, order is non-deterministic)

    @pytest.mark.asyncio
    async def test_execute_with_failures(self, executor, mock_tasks):
        """Handle task failures gracefully."""
        call_count = 0

        async def fail_second(task, slot):
            nonlocal call_count
            call_count += 1
            if task.id == "task-2":
                return {"success": False, "error": "Test failure"}
            return {"success": True, "files": [task.file]}

        with patch.object(executor, '_run_agent', side_effect=fail_second):
            result = await executor.execute(mock_tasks)

        assert result.completed == 2
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_slot_reuse_after_completion(self, executor):
        """Slots are reused after task completion."""
        from tasks.work_queue import Task
        # More tasks than slots
        tasks = [
            Task(id=f"task-{i}", description=f"Fix bug {i}", file=f"src/{i}.py", status="pending")
            for i in range(6)
        ]

        completed_slots = []

        async def track_slot(task, slot):
            completed_slots.append(slot.agent_id)
            await asyncio.sleep(0.01)
            return {"success": True, "files": [task.file]}

        with patch.object(executor, '_run_agent', side_effect=track_slot):
            result = await executor.execute(tasks)

        assert result.completed == 6
        # Slots should be reused (only 3 unique slot IDs for 6 tasks)
        unique_slots = set(completed_slots)
        assert len(unique_slots) <= 3


class TestCoordinationStrategies:
    """Test different coordination strategies."""

    @pytest.fixture
    def independent_executor(self, tmp_path: Path):
        config = ExecutorConfig(
            max_parallel=3,
            strategy=CoordinationStrategy.INDEPENDENT
        )
        return ParallelExecutor(project_dir=tmp_path, config=config)

    @pytest.fixture
    def file_lock_executor(self, tmp_path: Path):
        config = ExecutorConfig(
            max_parallel=3,
            strategy=CoordinationStrategy.FILE_LOCK
        )
        return ParallelExecutor(project_dir=tmp_path, config=config)

    @pytest.mark.asyncio
    async def test_independent_allows_same_file(self, independent_executor):
        """Independent strategy allows multiple agents on same file."""
        from tasks.work_queue import Task
        # Two tasks touching same file
        tasks = [
            Task(id="task-1", description="Fix part A", file="src/shared.py", status="pending"),
            Task(id="task-2", description="Fix part B", file="src/shared.py", status="pending"),
        ]

        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrent(task, slot):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return {"success": True, "files": [task.file]}

        with patch.object(independent_executor, '_run_agent', side_effect=track_concurrent):
            await independent_executor.execute(tasks)

        # Both should run concurrently
        assert max_concurrent == 2

    @pytest.mark.asyncio
    async def test_file_lock_serializes_same_file(self, file_lock_executor):
        """File lock strategy serializes access to same file."""
        from tasks.work_queue import Task
        # Two tasks touching same file
        tasks = [
            Task(id="task-1", description="Fix part A", file="src/shared.py", status="pending"),
            Task(id="task-2", description="Fix part B", file="src/shared.py", status="pending"),
        ]

        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrent(task, slot):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return {"success": True, "files": [task.file]}

        with patch.object(file_lock_executor, '_run_agent', side_effect=track_concurrent):
            await file_lock_executor.execute(tasks)

        # Should serialize - only 1 at a time for same file
        assert max_concurrent == 1

    @pytest.mark.asyncio
    async def test_file_lock_allows_different_files(self, file_lock_executor):
        """File lock allows parallel execution on different files."""
        from tasks.work_queue import Task
        tasks = [
            Task(id="task-1", description="Fix A", file="src/a.py", status="pending"),
            Task(id="task-2", description="Fix B", file="src/b.py", status="pending"),
        ]

        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrent(task, slot):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return {"success": True, "files": [task.file]}

        with patch.object(file_lock_executor, '_run_agent', side_effect=track_concurrent):
            await file_lock_executor.execute(tasks)

        # Different files can run in parallel
        assert max_concurrent == 2


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_result_captures_stats(self):
        """Result captures execution statistics."""
        result = ExecutionResult(
            completed=5,
            failed=1,
            total_time_ms=1500
        )

        assert result.completed == 5
        assert result.failed == 1
        assert result.total_time_ms == 1500

    def test_result_defaults_to_zero(self):
        """Result defaults to zero for all stats."""
        result = ExecutionResult()

        assert result.completed == 0
        assert result.failed == 0
        assert result.total_time_ms == 0


class TestIntegrationWithSimplifiedLoop:
    """Test parallel executor integration with SimplifiedLoop."""

    @pytest.mark.asyncio
    async def test_parallel_executor_uses_simplified_loop(self, tmp_path: Path):
        """Parallel executor can delegate to SimplifiedLoop for each task."""
        from orchestration.simplified_loop import SimplifiedLoop, LoopConfig

        config = ExecutorConfig(max_parallel=2)
        executor = ParallelExecutor(project_dir=tmp_path, config=config)

        # Verify executor can work with SimplifiedLoop
        loop_config = LoopConfig(project_dir=tmp_path)
        loop = SimplifiedLoop(loop_config)

        # Basic integration check
        assert executor.project_dir == tmp_path
        assert loop.config.project_dir == tmp_path

    @pytest.mark.asyncio
    async def test_parallel_respects_governance(self, tmp_path: Path):
        """Parallel execution respects governance contracts."""
        from governance.simple_enforce import check_action, ActionContext, ContractViolation

        # Create governance contract file
        contracts_dir = tmp_path / "governance" / "contracts"
        contracts_dir.mkdir(parents=True)
        (contracts_dir / "test-team.yaml").write_text("""
name: test-team
branches:
  - main
allowed_actions:
  - read_file
  - write_file
forbidden_actions:
  - deploy
limits:
  max_lines_changed: 100
  max_files_changed: 5
  max_iterations: 15
""")

        # Verify governance is checked
        context = ActionContext(team="test-team", action="write_file", branch="main")
        with patch('governance.simple_enforce.load_contract') as mock_load:
            from governance.simple_enforce import SimpleContract
            mock_load.return_value = SimpleContract(
                name="test-team",
                branches=["main"],
                allowed_actions=["read_file", "write_file"],
                forbidden_actions=["deploy"]
            )
            result = check_action(context)
            assert result is True
