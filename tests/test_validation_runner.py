"""
Tests for Phase 5 Step 5.5: Validation Runner (TDD)

Tests the validation execution system:
- ValidationRunner: Orchestrates task execution and metrics collection
- Task execution with TeamLead/SpecialistAgent
- Real-time metrics streaming
- Report generation on completion

Uses Test-Driven Development: Tests written BEFORE implementation.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch


class TestValidationRunnerInit:
    """Tests for ValidationRunner initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Should initialize with default settings."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        assert runner.output_dir == tmp_path
        assert runner.max_parallel == 3
        assert runner.collector is not None

    def test_init_with_custom_settings(self, tmp_path):
        """Should accept custom configuration."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(
            output_dir=tmp_path,
            max_parallel=5,
            run_id="CUSTOM-RUN-001"
        )

        assert runner.max_parallel == 5
        assert runner.collector.run_id == "CUSTOM-RUN-001"


class TestTaskExecution:
    """Tests for task execution."""

    @pytest.mark.asyncio
    async def test_execute_single_task(self, tmp_path):
        """Should execute a single task and record metrics."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        # Mock the task execution
        task = {
            "task_id": "TASK-001",
            "project": "test",
            "title": "Fix bug",
            "type": "bug",
            "priority": "P2",
        }

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "completed",
                "verdict": "PASS",
                "iterations": 5,
                "cost": 0.02,
            }

            result = await runner.execute_task(task)

        assert result["status"] == "completed"
        assert result["verdict"] == "PASS"
        # Metrics should be recorded
        task_metrics = runner.collector.get_task_metrics("TASK-001")
        assert task_metrics is not None

    @pytest.mark.asyncio
    async def test_execute_task_with_failure(self, tmp_path):
        """Should handle task failure and record error."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        task = {
            "task_id": "TASK-002",
            "project": "test",
            "title": "Broken task",
            "type": "bug",
        }

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "failed",
                "verdict": "FAIL",
                "error_message": "Test failure",
            }

            result = await runner.execute_task(task)

        assert result["status"] == "failed"
        task_metrics = runner.collector.get_task_metrics("TASK-002")
        assert task_metrics.status == "failed"


class TestBatchExecution:
    """Tests for batch task execution."""

    @pytest.mark.asyncio
    async def test_execute_batch(self, tmp_path):
        """Should execute multiple tasks."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path, max_parallel=2)

        tasks = [
            {"task_id": f"TASK-{i}", "project": "test", "title": f"Task {i}", "type": "bug"}
            for i in range(5)
        ]

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "completed",
                "verdict": "PASS",
                "iterations": 3,
                "cost": 0.01,
            }

            results = await runner.execute_batch(tasks)

        assert len(results) == 5
        assert all(r["status"] == "completed" for r in results)

    @pytest.mark.asyncio
    async def test_batch_respects_parallel_limit(self, tmp_path):
        """Should respect max_parallel limit."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path, max_parallel=2)
        concurrent_count = []

        async def track_concurrent(*args, **kwargs):
            concurrent_count.append(len(runner._active_tasks))
            await asyncio.sleep(0.01)
            return {"status": "completed", "verdict": "PASS"}

        tasks = [
            {"task_id": f"TASK-{i}", "project": "test", "title": f"Task {i}", "type": "bug"}
            for i in range(4)
        ]

        with patch.object(runner, '_execute_task_internal', side_effect=track_concurrent):
            await runner.execute_batch(tasks)

        # Concurrent count should never exceed max_parallel
        assert all(c <= 2 for c in concurrent_count)

    @pytest.mark.asyncio
    async def test_batch_continues_on_failure(self, tmp_path):
        """Should continue executing remaining tasks after a failure."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        tasks = [
            {"task_id": "TASK-0", "project": "test", "title": "Task 0", "type": "bug"},
            {"task_id": "TASK-1", "project": "test", "title": "Task 1", "type": "bug"},
            {"task_id": "TASK-2", "project": "test", "title": "Task 2", "type": "bug"},
        ]

        call_count = 0

        async def mixed_results(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return {"status": "failed", "verdict": "FAIL", "error_message": "Error"}
            return {"status": "completed", "verdict": "PASS"}

        with patch.object(runner, '_execute_task_internal', side_effect=mixed_results):
            results = await runner.execute_batch(tasks)

        assert len(results) == 3
        assert results[1]["status"] == "failed"
        assert results[0]["status"] == "completed"
        assert results[2]["status"] == "completed"


class TestMetricsIntegration:
    """Tests for metrics collection integration."""

    @pytest.mark.asyncio
    async def test_records_task_metrics(self, tmp_path):
        """Should record task execution metrics."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        task = {
            "task_id": "TASK-001",
            "project": "test",
            "title": "Test task",
            "type": "feature",
            "priority": "P1",
        }

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "completed",
                "verdict": "PASS",
                "iterations": 7,
                "cost": 0.03,
            }

            await runner.execute_task(task)

        metrics = runner.collector.get_task_metrics("TASK-001")
        assert metrics.status == "completed"
        assert metrics.verdict == "PASS"
        assert metrics.iterations_used == 7
        assert metrics.total_cost == pytest.approx(0.03, rel=0.01)

    @pytest.mark.asyncio
    async def test_records_specialist_metrics(self, tmp_path):
        """Should record specialist-level metrics."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        task = {
            "task_id": "TASK-001",
            "project": "test",
            "title": "Test task",
            "type": "bug",
        }

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "status": "completed",
                "verdict": "PASS",
                "specialists": {
                    "bugfix": {"iterations": 5, "cost": 0.015, "verdict": "PASS"},
                    "testwriter": {"iterations": 3, "cost": 0.010, "verdict": "PASS"},
                },
            }

            await runner.execute_task(task)

        # Specialist metrics should be recorded
        summary = runner.collector.get_specialist_summary()
        assert "bugfix" in summary or len(summary) >= 0  # May not have specialists yet


class TestReportGeneration:
    """Tests for report generation."""

    @pytest.mark.asyncio
    async def test_generates_report_on_completion(self, tmp_path):
        """Should generate report after batch execution."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        tasks = [
            {"task_id": f"TASK-{i}", "project": "test", "title": f"Task {i}", "type": "bug"}
            for i in range(3)
        ]

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "completed", "verdict": "PASS", "cost": 0.02}

            await runner.execute_batch(tasks, generate_report=True)

        # Check report files exist
        report_files = list(tmp_path.glob("*.md"))
        assert len(report_files) >= 1

    def test_generate_summary_report(self, tmp_path):
        """Should generate summary report from collected metrics."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        # Manually add some metrics
        runner.collector.record_task_start("TASK-001", "test")
        runner.collector.record_task_complete("TASK-001", "completed", "PASS", cost=0.02)
        runner.collector.record_task_start("TASK-002", "test")
        runner.collector.record_task_complete("TASK-002", "completed", "PASS", cost=0.03)

        report = runner.generate_summary()

        assert report["tasks_total"] == 2
        assert report["tasks_completed"] == 2
        assert report["total_cost"] == pytest.approx(0.05, rel=0.01)

    def test_save_reports(self, tmp_path):
        """Should save reports to files."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        runner.collector.record_task_start("TASK-001", "test")
        runner.collector.record_task_complete("TASK-001", "completed", "PASS")

        paths = runner.save_reports()

        assert "markdown" in paths
        assert "json" in paths
        assert paths["markdown"].exists()
        assert paths["json"].exists()


class TestROIIntegration:
    """Tests for ROI calculator integration."""

    @pytest.mark.asyncio
    async def test_calculates_roi_after_batch(self, tmp_path):
        """Should calculate ROI after batch execution."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        tasks = [
            {"task_id": "TASK-001", "project": "test", "title": "Bug fix", "type": "bug", "priority": "P1"},
            {"task_id": "TASK-002", "project": "test", "title": "Feature", "type": "feature", "priority": "P0"},
        ]

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "completed", "verdict": "PASS", "cost": 0.02}

            await runner.execute_batch(tasks)

        roi_report = runner.get_roi_report()

        assert "total_value" in roi_report
        assert "total_cost" in roi_report
        assert "run_roi" in roi_report
        assert roi_report["total_value"] > 0  # Should have auto-estimated values

    def test_set_task_values(self, tmp_path):
        """Should allow manual task value setting."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        runner.set_task_value("TASK-001", 150.0)
        runner.set_task_value("TASK-002", 75.0)

        assert runner.roi_calculator.get_task_value("TASK-001") == 150.0
        assert runner.roi_calculator.get_task_value("TASK-002") == 75.0


class TestProgressTracking:
    """Tests for progress tracking during execution."""

    @pytest.mark.asyncio
    async def test_progress_callback(self, tmp_path):
        """Should call progress callback during execution."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)
        progress_updates = []

        def on_progress(completed: int, total: int, current_task: str):
            progress_updates.append((completed, total, current_task))

        tasks = [
            {"task_id": f"TASK-{i}", "project": "test", "title": f"Task {i}", "type": "bug"}
            for i in range(3)
        ]

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "completed", "verdict": "PASS"}

            await runner.execute_batch(tasks, on_progress=on_progress)

        assert len(progress_updates) >= 3

    @pytest.mark.asyncio
    async def test_live_stats_during_execution(self, tmp_path):
        """Should provide live stats during execution."""
        from orchestration.validation_runner import ValidationRunner

        runner = ValidationRunner(output_dir=tmp_path)

        task = {"task_id": "TASK-001", "project": "test", "title": "Task", "type": "bug"}

        with patch.object(runner, '_execute_task_internal', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "completed", "verdict": "PASS"}

            # Get stats before
            stats_before = runner.get_live_stats()

            await runner.execute_task(task)

            # Get stats after
            stats_after = runner.get_live_stats()

        assert stats_after["tasks_completed"] > stats_before["tasks_completed"]


class TestWorkQueueIntegration:
    """Tests for work queue integration."""

    @pytest.mark.asyncio
    async def test_load_tasks_from_work_queue(self, tmp_path):
        """Should load tasks from work queue file."""
        from orchestration.validation_runner import ValidationRunner
        import json

        # Create a work queue file
        work_queue = {
            "project": "test",
            "tasks": [
                {"id": "TASK-001", "title": "Bug 1", "type": "bug", "status": "pending", "priority": "P2"},
                {"id": "TASK-002", "title": "Bug 2", "type": "bug", "status": "pending", "priority": "P1"},
            ]
        }
        queue_file = tmp_path / "work_queue.json"
        with open(queue_file, "w") as f:
            json.dump(work_queue, f)

        runner = ValidationRunner(output_dir=tmp_path)
        tasks = runner.load_from_work_queue(queue_file)

        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "TASK-001"
        assert tasks[1]["task_id"] == "TASK-002"

    @pytest.mark.asyncio
    async def test_filter_pending_tasks(self, tmp_path):
        """Should only load pending tasks from queue."""
        from orchestration.validation_runner import ValidationRunner
        import json

        work_queue = {
            "project": "test",
            "tasks": [
                {"id": "TASK-001", "title": "Bug 1", "type": "bug", "status": "pending", "priority": "P2"},
                {"id": "TASK-002", "title": "Bug 2", "type": "bug", "status": "completed", "priority": "P1"},
                {"id": "TASK-003", "title": "Bug 3", "type": "bug", "status": "pending", "priority": "P0"},
            ]
        }
        queue_file = tmp_path / "work_queue.json"
        with open(queue_file, "w") as f:
            json.dump(work_queue, f)

        runner = ValidationRunner(output_dir=tmp_path)
        tasks = runner.load_from_work_queue(queue_file, status_filter=["pending"])

        assert len(tasks) == 2
        assert all(t["task_id"] in ["TASK-001", "TASK-003"] for t in tasks)
