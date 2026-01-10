"""
Tests for Coordinator ADR Close-Out Functionality

Tests cover:
1. on_adr_closed() basic functionality
2. Verification of task completion
3. ADR file updates (status, acceptance criteria, completion summary)
4. ADR-INDEX.md updates
5. Error handling for incomplete tasks
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from agents.coordinator.coordinator import (
    Coordinator,
    CoordinatorConfig,
    CoordinatorEvent,
    ADR,
)
from agents.coordinator.task_manager import Task, TaskStatus, TaskType


class TestCoordinatorEventTypes:
    """Tests for CoordinatorEvent enum."""

    def test_adr_closed_event_exists(self):
        """ADR_CLOSED event type should exist."""
        assert hasattr(CoordinatorEvent, 'ADR_CLOSED')
        assert CoordinatorEvent.ADR_CLOSED.value == "adr_closed"


class TestADRParsing:
    """Tests for ADR parsing functionality."""

    def test_parse_adr_from_file(self, tmp_path):
        """ADR.from_file() should correctly parse ADR metadata."""
        adr_content = """# ADR-003: Lambda Cost Controls

**Status**: Approved
**Date**: 2026-01-10
**Advisor**: app-advisor
**Domain**: infrastructure

---

## Context

Some context here.

## Acceptance Criteria

- [ ] Budget alert fires
- [ ] Concurrency limit works
"""
        adr_file = tmp_path / "ADR-003-lambda-cost-controls.md"
        adr_file.write_text(adr_content)

        adr = ADR.from_file(adr_file)

        assert adr.id == "ADR-003-lambda-cost-controls"
        assert adr.number == 3
        assert adr.title == "Lambda Cost Controls"
        assert adr.status == "approved"
        assert adr.advisor == "app-advisor"


class TestOnAdrClosed:
    """Tests for on_adr_closed() method."""

    @pytest.fixture
    def coordinator_setup(self, tmp_path):
        """Set up coordinator with temp directory structure."""
        # Create directory structure
        ai_team_dir = tmp_path / "AI-Team-Plans"
        ai_team_dir.mkdir()
        (ai_team_dir / "tasks").mkdir()
        (ai_team_dir / "decisions").mkdir()
        (ai_team_dir / "sessions").mkdir()

        # Create work queue with completed tasks
        work_queue = {
            "version": "3.0",
            "project": "test_project",
            "tasks": [
                {
                    "id": "TASK-003-001",
                    "title": "Create AWS Budget",
                    "adr": "ADR-003-lambda-cost-controls",
                    "status": "completed",
                    "type": "infrastructure",
                    "agent": "manual",
                    "priority": "P1",
                    "phase": 1,
                },
                {
                    "id": "TASK-003-002",
                    "title": "Implement CircuitBreaker",
                    "adr": "ADR-003-lambda-cost-controls",
                    "status": "completed",
                    "type": "feature",
                    "agent": "FeatureBuilder",
                    "priority": "P1",
                    "phase": 2,
                },
            ]
        }
        import json
        (ai_team_dir / "tasks" / "work_queue.json").write_text(json.dumps(work_queue))

        # Create ADR file
        adr_content = """# ADR-003: Lambda Cost Controls

**Status**: Approved
**Date**: 2026-01-10
**Advisor**: app-advisor
**Domain**: infrastructure

---

## Context

Lambda usage grew to 2.6M invocations/month.

## Acceptance Criteria

- [ ] Budget alert fires at $5 threshold
- [ ] Circuit breaker stops agent after 100 calls

## References

- AWS Lambda Pricing
"""
        adr_file = ai_team_dir / "decisions" / "ADR-003-lambda-cost-controls.md"
        adr_file.write_text(adr_content)

        # Create ADR-INDEX.md
        index_content = """# ADR Index

**Last Updated**: 2026-01-10T14:00:00Z

## ADR Registry

| ADR | Title | Project | Status | Date |
|-----|-------|---------|--------|------|
| ADR-003 | Lambda Cost Controls | test_project | approved | 2026-01-10 |

## By Project

### test_project
| ADR | Title | Status |
|-----|-------|--------|
| ADR-003 | Lambda Cost Controls | approved |
"""
        (ai_team_dir / "ADR-INDEX.md").write_text(index_content)

        # Create coordinator
        config = CoordinatorConfig(
            project_root=tmp_path,
            auto_update_hq=False,  # Disable for testing
        )
        coordinator = Coordinator(config)

        return {
            "coordinator": coordinator,
            "tmp_path": tmp_path,
            "ai_team_dir": ai_team_dir,
            "adr_file": adr_file,
        }

    def test_close_adr_success(self, coordinator_setup):
        """on_adr_closed() should close ADR when all tasks complete."""
        setup = coordinator_setup
        coordinator = setup["coordinator"]
        adr_file = setup["adr_file"]

        # Mock task manager to return completed tasks
        mock_tasks = [
            MagicMock(
                id="TASK-003-001",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Create AWS Budget",
                agent="manual",
                phase=1,
                iterations=1,
            ),
            MagicMock(
                id="TASK-003-002",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Implement CircuitBreaker",
                agent="FeatureBuilder",
                phase=2,
                iterations=5,
            ),
        ]
        coordinator.task_manager.get_all_tasks = MagicMock(return_value=mock_tasks)

        # Call on_adr_closed
        result = coordinator.on_adr_closed(adr_file)

        # Verify result
        assert result["status"] == "closed"
        assert result["adr_id"] == "ADR-003-lambda-cost-controls"
        assert result["adr_number"] == 3
        assert result["tasks_completed"] == 2
        assert "TASK-003-001" in result["task_ids"]
        assert "TASK-003-002" in result["task_ids"]

    def test_close_adr_updates_status(self, coordinator_setup):
        """on_adr_closed() should update ADR status to Complete."""
        setup = coordinator_setup
        coordinator = setup["coordinator"]
        adr_file = setup["adr_file"]

        # Mock task manager
        mock_tasks = [
            MagicMock(
                id="TASK-003-001",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Test Task",
                agent="manual",
                phase=1,
            ),
        ]
        coordinator.task_manager.get_all_tasks = MagicMock(return_value=mock_tasks)

        # Close ADR
        coordinator.on_adr_closed(adr_file)

        # Read updated ADR
        content = adr_file.read_text()

        assert "**Status**: Complete" in content
        assert "**Completed**:" in content

    def test_close_adr_checks_acceptance_criteria(self, coordinator_setup):
        """on_adr_closed() should check acceptance criteria boxes."""
        setup = coordinator_setup
        coordinator = setup["coordinator"]
        adr_file = setup["adr_file"]

        # Mock task manager
        mock_tasks = [
            MagicMock(
                id="TASK-003-001",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Test Task",
                agent="manual",
                phase=1,
            ),
        ]
        coordinator.task_manager.get_all_tasks = MagicMock(return_value=mock_tasks)

        # Close ADR
        coordinator.on_adr_closed(adr_file)

        # Read updated ADR
        content = adr_file.read_text()

        # All checkboxes should be checked
        assert "- [ ]" not in content
        assert "- [x]" in content

    def test_close_adr_adds_completion_summary(self, coordinator_setup):
        """on_adr_closed() should add completion summary section."""
        setup = coordinator_setup
        coordinator = setup["coordinator"]
        adr_file = setup["adr_file"]

        # Mock task manager
        mock_tasks = [
            MagicMock(
                id="TASK-003-001",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Create AWS Budget",
                agent="manual",
                phase=1,
                iterations=1,
            ),
        ]
        coordinator.task_manager.get_all_tasks = MagicMock(return_value=mock_tasks)

        # Close ADR
        coordinator.on_adr_closed(adr_file)

        # Read updated ADR
        content = adr_file.read_text()

        assert "## Completion Summary" in content
        assert "TASK-003-001" in content

    def test_close_adr_updates_index(self, coordinator_setup):
        """on_adr_closed() should update ADR-INDEX.md."""
        setup = coordinator_setup
        coordinator = setup["coordinator"]
        adr_file = setup["adr_file"]
        ai_team_dir = setup["ai_team_dir"]

        # Mock task manager
        mock_tasks = [
            MagicMock(
                id="TASK-003-001",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Test Task",
                agent="manual",
                phase=1,
            ),
        ]
        coordinator.task_manager.get_all_tasks = MagicMock(return_value=mock_tasks)

        # Close ADR
        coordinator.on_adr_closed(adr_file)

        # Read updated index
        index_content = (ai_team_dir / "ADR-INDEX.md").read_text()

        assert "complete" in index_content.lower()

    def test_close_adr_fails_with_incomplete_tasks(self, coordinator_setup):
        """on_adr_closed() should raise error if tasks incomplete."""
        setup = coordinator_setup
        coordinator = setup["coordinator"]
        adr_file = setup["adr_file"]

        # Mock task manager with incomplete task
        mock_tasks = [
            MagicMock(
                id="TASK-003-001",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Complete Task",
                agent="manual",
                phase=1,
            ),
            MagicMock(
                id="TASK-003-002",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.PENDING,  # Incomplete!
                title="Incomplete Task",
                agent="FeatureBuilder",
                phase=2,
            ),
        ]
        coordinator.task_manager.get_all_tasks = MagicMock(return_value=mock_tasks)

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            coordinator.on_adr_closed(adr_file)

        assert "incomplete" in str(exc_info.value).lower()
        assert "TASK-003-002" in str(exc_info.value)

    def test_close_adr_idempotent(self, coordinator_setup):
        """on_adr_closed() should be safe to call multiple times."""
        setup = coordinator_setup
        coordinator = setup["coordinator"]
        adr_file = setup["adr_file"]

        # Mock task manager
        mock_tasks = [
            MagicMock(
                id="TASK-003-001",
                adr="ADR-003-lambda-cost-controls",
                status=TaskStatus.COMPLETED,
                title="Test Task",
                agent="manual",
                phase=1,
            ),
        ]
        coordinator.task_manager.get_all_tasks = MagicMock(return_value=mock_tasks)

        # Close ADR twice
        result1 = coordinator.on_adr_closed(adr_file)
        result2 = coordinator.on_adr_closed(adr_file)

        # Both should succeed
        assert result1["status"] == "closed"
        assert result2["status"] == "closed"

        # Content should only have one completion summary
        content = adr_file.read_text()
        assert content.count("## Completion Summary") == 1


class TestCompletionSummaryGeneration:
    """Tests for completion summary generation."""

    def test_groups_tasks_by_phase(self, tmp_path):
        """Completion summary should group tasks by phase."""
        # Setup
        ai_team_dir = tmp_path / "AI-Team-Plans"
        ai_team_dir.mkdir()
        (ai_team_dir / "tasks").mkdir()
        (ai_team_dir / "sessions").mkdir()

        import json
        (ai_team_dir / "tasks" / "work_queue.json").write_text(json.dumps({"tasks": []}))

        config = CoordinatorConfig(project_root=tmp_path, auto_update_hq=False)
        coordinator = Coordinator(config)

        # Create mock ADR
        adr = MagicMock()
        adr.id = "ADR-001"

        # Create tasks in different phases
        tasks = [
            MagicMock(id="TASK-001-001", title="Phase 1 Task", agent="manual", phase=1, iterations=1),
            MagicMock(id="TASK-001-002", title="Phase 2 Task", agent="FeatureBuilder", phase=2, iterations=5),
            MagicMock(id="TASK-001-003", title="Phase 3 Task", agent="TestWriter", phase=3, iterations=3),
        ]

        # Generate summary
        summary = coordinator._generate_completion_summary(adr, tasks)

        # Verify phase sections
        assert "### Phase 1" in summary
        assert "### Phase 2" in summary
        assert "### Phase 3" in summary
        assert "TASK-001-001" in summary
        assert "TASK-001-002" in summary
        assert "TASK-001-003" in summary


class TestADRIndexUpdate:
    """Tests for ADR-INDEX.md update functionality."""

    def test_updates_timestamp(self, tmp_path):
        """_update_adr_index() should update Last Updated timestamp."""
        # Setup
        ai_team_dir = tmp_path / "AI-Team-Plans"
        ai_team_dir.mkdir()
        (ai_team_dir / "tasks").mkdir()
        (ai_team_dir / "sessions").mkdir()

        import json
        (ai_team_dir / "tasks" / "work_queue.json").write_text(json.dumps({"tasks": []}))

        # Create index file
        index_content = """# ADR Index

**Last Updated**: 2026-01-01T00:00:00Z

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Test | approved |
"""
        (ai_team_dir / "ADR-INDEX.md").write_text(index_content)

        config = CoordinatorConfig(project_root=tmp_path, auto_update_hq=False)
        coordinator = Coordinator(config)

        # Create mock ADR
        adr = MagicMock()
        adr.number = 1

        # Update index
        coordinator._update_adr_index(adr)

        # Verify timestamp changed
        updated_content = (ai_team_dir / "ADR-INDEX.md").read_text()
        assert "2026-01-01T00:00:00Z" not in updated_content
