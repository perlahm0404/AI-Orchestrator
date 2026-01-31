"""
End-to-end integration tests for the autonomous loop.

Tests the full flow:
1. Load work queue
2. Execute tasks with SimplifiedLoop
3. Verify results with FastVerify
4. Track metrics
5. Generate dashboard

These tests use mocked Claude CLI to avoid actual LLM calls.
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import shutil

from orchestration.simplified_loop import SimplifiedLoop, LoopConfig, LoopResult
from orchestration.parallel_executor import ParallelExecutor, ExecutorConfig, CoordinationStrategy
from monitoring.metrics import MetricsCollector, generate_dashboard
from tasks.work_queue import WorkQueue, Task


class TestE2ESimplifiedLoop:
    """End-to-end tests for SimplifiedLoop."""

    @pytest.fixture
    def test_project(self, tmp_path: Path):
        """Create a test project directory with work queue."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create tasks directory
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()

        # Create a simple work queue
        work_queue = {
            "project": "test_project",
            "features": [
                {
                    "id": "TASK-001",
                    "description": "Fix import error in utils.py",
                    "file": "src/utils.py",
                    "status": "pending",
                    "priority": 1
                },
                {
                    "id": "TASK-002",
                    "description": "Add type hints to models.py",
                    "file": "src/models.py",
                    "status": "pending",
                    "priority": 2
                }
            ]
        }

        queue_path = tasks_dir / "work_queue_test.json"
        queue_path.write_text(json.dumps(work_queue, indent=2))

        # Create source files
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "utils.py").write_text("def helper(): pass\n")
        (src_dir / "models.py").write_text("class User: pass\n")

        return {
            "project_dir": project_dir,
            "queue_path": queue_path,
            "tasks_dir": tasks_dir,
        }

    @pytest.mark.asyncio
    async def test_full_loop_execution(self, test_project):
        """Test complete loop execution with mocked task execution."""
        config = LoopConfig(
            project_dir=test_project["project_dir"],
            max_iterations=10,
            auto_commit=False,
            work_queue_path=test_project["queue_path"],
            enable_metrics=True,
        )

        loop = SimplifiedLoop(config)

        # Mock the entire _execute_task_with_retries to return success
        from orchestration.simplified_loop import TaskResult

        async def mock_execute(task):
            return TaskResult(
                task_id=task.id,
                success=True,
                files_changed=[task.file],
                attempts=1
            )

        with patch.object(loop, '_execute_task_with_retries', side_effect=mock_execute):
            result = await loop.run()

        assert result.completed == 2
        assert result.failed == 0
        assert result.iterations == 2

    @pytest.mark.asyncio
    async def test_loop_with_failures(self, test_project):
        """Test loop handles failures correctly."""
        config = LoopConfig(
            project_dir=test_project["project_dir"],
            max_iterations=10,
            auto_commit=False,
            work_queue_path=test_project["queue_path"],
            enable_metrics=True,
        )

        loop = SimplifiedLoop(config)
        call_count = 0

        async def mock_claude_with_failure(task, context=None):
            nonlocal call_count
            call_count += 1
            # First task succeeds, second fails
            if "TASK-001" in task.id:
                return {"success": True, "files": ["src/utils.py"]}
            return {"success": False, "files": [], "error": "Simulated failure"}

        with patch.object(loop, '_run_claude_code', side_effect=mock_claude_with_failure), \
             patch.object(loop, '_fast_verify') as mock_verify:

            from ralph.fast_verify import VerifyResult, VerifyStatus, VerifyTier
            mock_verify.return_value = VerifyResult(
                status=VerifyStatus.FAIL,
                tier=VerifyTier.INSTANT,
                errors=["Test failure"]
            )

            result = await loop.run()

        # Both tasks attempted, both should fail (verify fails even for first)
        assert result.failed >= 1

    @pytest.mark.asyncio
    async def test_metrics_collection_during_loop(self, test_project):
        """Test that metrics are collected during loop execution."""
        config = LoopConfig(
            project_dir=test_project["project_dir"],
            max_iterations=10,
            auto_commit=False,
            work_queue_path=test_project["queue_path"],
            enable_metrics=True,
        )

        loop = SimplifiedLoop(config)

        from orchestration.simplified_loop import TaskResult

        async def mock_execute(task):
            return TaskResult(
                task_id=task.id,
                success=True,
                files_changed=[task.file],
                attempts=1
            )

        with patch.object(loop, '_execute_task_with_retries', side_effect=mock_execute):
            await loop.run()

        # Check metrics were collected
        metrics = loop.get_metrics_collector()
        assert metrics is not None

        dashboard = loop.get_dashboard()
        assert dashboard is not None
        assert dashboard.completed_tasks >= 1

    @pytest.mark.asyncio
    async def test_loop_respects_max_iterations(self, test_project):
        """Test that loop stops at max_iterations."""
        # Create a queue with many tasks
        work_queue = {
            "project": "test_project",
            "features": [
                {
                    "id": f"TASK-{i:03d}",
                    "description": f"Task {i}",
                    "file": "src/file.py",
                    "status": "pending",
                    "priority": 1
                }
                for i in range(20)
            ]
        }
        test_project["queue_path"].write_text(json.dumps(work_queue))

        config = LoopConfig(
            project_dir=test_project["project_dir"],
            max_iterations=5,  # Limit to 5
            auto_commit=False,
            work_queue_path=test_project["queue_path"],
            enable_metrics=False,
        )

        loop = SimplifiedLoop(config)

        from orchestration.simplified_loop import TaskResult

        async def mock_execute(task):
            return TaskResult(
                task_id=task.id,
                success=True,
                files_changed=[task.file],
                attempts=1
            )

        with patch.object(loop, '_execute_task_with_retries', side_effect=mock_execute):
            result = await loop.run()

        assert result.iterations == 5
        assert result.completed == 5


class TestE2EParallelExecution:
    """End-to-end tests for parallel execution."""

    @pytest.fixture
    def test_tasks(self):
        """Create test tasks."""
        return [
            Task(id=f"TASK-{i:03d}", description=f"Task {i}",
                 file=f"src/file{i}.py", status="pending")
            for i in range(6)
        ]

    @pytest.mark.asyncio
    async def test_parallel_execution_with_metrics(self, tmp_path: Path, test_tasks):
        """Test parallel execution with metrics collection."""
        config = ExecutorConfig(
            max_parallel=3,
            strategy=CoordinationStrategy.INDEPENDENT
        )

        executor = ParallelExecutor(project_dir=tmp_path, config=config)

        with patch.object(executor, '_run_agent') as mock_run:
            async def mock_agent(task, slot):
                await asyncio.sleep(0.01)
                return {"success": True, "files": [task.file]}

            mock_run.side_effect = mock_agent

            result = await executor.execute(test_tasks)

        assert result.completed == 6
        assert result.failed == 0
        assert result.total_time_ms > 0

    @pytest.mark.asyncio
    async def test_parallel_with_file_lock(self, tmp_path: Path):
        """Test file lock prevents concurrent access."""
        # Tasks that touch the same file
        tasks = [
            Task(id="TASK-001", description="Edit shared file 1",
                 file="src/shared.py", status="pending"),
            Task(id="TASK-002", description="Edit shared file 2",
                 file="src/shared.py", status="pending"),
        ]

        config = ExecutorConfig(
            max_parallel=3,
            strategy=CoordinationStrategy.FILE_LOCK
        )

        executor = ParallelExecutor(project_dir=tmp_path, config=config)

        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrency(task, slot):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return {"success": True, "files": [task.file]}

        with patch.object(executor, '_run_agent', side_effect=track_concurrency):
            await executor.execute(tasks)

        # File lock should serialize access
        assert max_concurrent == 1


class TestE2EMetricsDashboard:
    """End-to-end tests for metrics dashboard."""

    @pytest.fixture
    def populated_metrics(self, tmp_path: Path):
        """Create a metrics collector with realistic data."""
        collector = MetricsCollector(storage_dir=tmp_path / ".metrics")

        # Simulate a realistic session using the counter names that generate_dashboard expects
        for i in range(8):
            collector.record("tasks.completed", 1)
            collector.record("task.duration_ms", 5000 + i * 100)

        for i in range(2):
            collector.record("tasks.failed", 1, tags={"error_type": "lint" if i == 0 else "test"})

        collector.set_gauge("agent.active", 3)
        collector.set_gauge("agent.total", 4)
        collector.flush()

        return collector

    def test_dashboard_generation(self, populated_metrics):
        """Test dashboard generates correct statistics."""
        dashboard = generate_dashboard(populated_metrics)

        assert dashboard.total_tasks == 10
        assert dashboard.completed_tasks == 8
        assert dashboard.failed_tasks == 2
        assert 0.79 <= dashboard.success_rate <= 0.81
        assert dashboard.avg_task_duration_ms > 5000

    def test_dashboard_error_breakdown(self, populated_metrics):
        """Test dashboard includes error breakdown."""
        dashboard = generate_dashboard(populated_metrics)

        assert "lint" in dashboard.error_breakdown
        assert "test" in dashboard.error_breakdown
        assert dashboard.error_breakdown["lint"] == 1
        assert dashboard.error_breakdown["test"] == 1

    def test_dashboard_agent_utilization(self, populated_metrics):
        """Test dashboard calculates agent utilization."""
        dashboard = generate_dashboard(populated_metrics)

        # 3 active out of 4 = 75%
        assert 0.74 <= dashboard.agent_utilization <= 0.76

    def test_metrics_persistence(self, tmp_path: Path):
        """Test metrics persist across collector instances."""
        metrics_dir = tmp_path / ".metrics"

        # First collector
        collector1 = MetricsCollector(storage_dir=metrics_dir)
        collector1.increment("tasks.completed")
        collector1.increment("tasks.completed")
        collector1.flush()

        # Second collector loads existing data
        collector2 = MetricsCollector(storage_dir=metrics_dir)
        total = collector2.get_total("tasks.completed")

        assert total == 2


class TestE2EFullPipeline:
    """Test the complete pipeline from queue to dashboard."""

    @pytest.fixture
    def full_test_env(self, tmp_path: Path):
        """Create a complete test environment."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()

        work_queue = {
            "project": "e2e_test",
            "features": [
                {
                    "id": "E2E-001",
                    "description": "E2E test task 1",
                    "file": "src/main.py",
                    "status": "pending",
                    "priority": 1
                },
                {
                    "id": "E2E-002",
                    "description": "E2E test task 2",
                    "file": "src/utils.py",
                    "status": "pending",
                    "priority": 2
                },
            ]
        }

        queue_path = tasks_dir / "work_queue_e2e.json"
        queue_path.write_text(json.dumps(work_queue))

        return {
            "project_dir": project_dir,
            "queue_path": queue_path,
        }

    @pytest.mark.asyncio
    async def test_full_pipeline(self, full_test_env):
        """Test complete pipeline: queue -> loop -> metrics -> dashboard."""
        # 1. Load queue
        queue = WorkQueue.load(full_test_env["queue_path"])
        assert queue.get_stats()["pending"] == 2

        # 2. Create and run loop
        config = LoopConfig(
            project_dir=full_test_env["project_dir"],
            max_iterations=10,
            auto_commit=False,
            work_queue_path=full_test_env["queue_path"],
            enable_metrics=True,
        )

        loop = SimplifiedLoop(config)

        from orchestration.simplified_loop import TaskResult

        async def mock_execute(task):
            return TaskResult(
                task_id=task.id,
                success=True,
                files_changed=[task.file],
                attempts=1
            )

        with patch.object(loop, '_execute_task_with_retries', side_effect=mock_execute):
            result = await loop.run()

        # 3. Verify results
        assert result.completed == 2
        assert result.failed == 0

        # 4. Check metrics
        metrics = loop.get_metrics_collector()
        assert metrics is not None

        # 5. Generate dashboard
        dashboard = loop.get_dashboard()
        assert dashboard is not None
        assert dashboard.completed_tasks == 2
        assert dashboard.success_rate == 1.0

        # 6. Verify queue updated
        updated_queue = WorkQueue.load(full_test_env["queue_path"])
        assert updated_queue.get_stats()["complete"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
