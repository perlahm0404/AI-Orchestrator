"""
Unit tests for verification bug fixes.

Tests the critical fixes that eliminated false positive completions:
1. Stop hook blocks exit when no files changed
2. WorkQueue stores verification verdicts correctly
3. Task validation catches missing files
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import dataclass

from tasks.work_queue import WorkQueue, Task
from governance.hooks.stop_hook import agent_stop_hook, StopDecision, StopHookResult


# Test fixtures
@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    return Task(
        id="TEST-001",
        description="Test task",
        file="src/test.ts",
        status="pending",
        tests=["tests/test.test.ts"],
        passes=False
    )


@pytest.fixture
def work_queue(sample_task):
    """Create a work queue with sample tasks"""
    return WorkQueue(
        project="test-project",
        features=[sample_task]
    )


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing"""
    agent = Mock()
    agent.config.expected_completion_signal = "COMPLETE"
    agent.config.max_iterations = 15
    agent.current_iteration = 1
    agent.check_completion_signal = Mock(return_value=None)
    return agent


@pytest.fixture
def mock_app_context():
    """Create a mock app context"""
    context = Mock()
    context.project_name = "test-project"
    context.project_path = "/tmp/test-project"
    return context


class TestStopHookNoChanges:
    """Test Bug #1 fix: Stop hook blocks exit when no files changed"""

    def test_no_changes_blocks_exit(self, mock_agent, mock_app_context):
        """Agent should be blocked from exiting when no files changed"""
        result = agent_stop_hook(
            agent=mock_agent,
            session_id="test-session",
            changes=[],  # No files changed
            output="Some output",
            app_context=mock_app_context
        )

        assert result.decision == StopDecision.BLOCK
        assert "No changes detected" in result.reason
        assert result.system_message is not None

    def test_with_changes_runs_verification(self, mock_agent, mock_app_context):
        """Agent with changes should proceed to Ralph verification"""
        with patch('ralph.engine.verify') as mock_verify:
            # Mock Ralph to return PASS
            from ralph.verdict import VerdictType
            mock_verdict = Mock()
            mock_verdict.type = VerdictType.PASS
            mock_verify.return_value = mock_verdict

            result = agent_stop_hook(
                agent=mock_agent,
                session_id="test-session",
                changes=["src/test.ts"],  # Files changed
                output="Some output",
                app_context=mock_app_context
            )

            # Should call Ralph verification
            mock_verify.assert_called_once()
            assert result.decision == StopDecision.ALLOW

    def test_completion_signal_allows_exit(self, mock_agent, mock_app_context):
        """Agent with completion signal should be allowed to exit"""
        mock_agent.check_completion_signal.return_value = "COMPLETE"

        result = agent_stop_hook(
            agent=mock_agent,
            session_id="test-session",
            changes=[],
            output="Task complete. <promise>COMPLETE</promise>",
            app_context=mock_app_context
        )

        assert result.decision == StopDecision.ALLOW
        assert "Completion signal detected" in result.reason


class TestWorkQueueVerdict:
    """Test Bug #4 fix: WorkQueue stores verification verdicts correctly"""

    def test_mark_complete_with_pass_verdict(self, work_queue):
        """Task marked complete with PASS verdict should set passes=True"""
        work_queue.mark_complete(
            task_id="TEST-001",
            verdict="PASS",
            files_changed=["src/test.ts"]
        )

        task = work_queue.features[0]
        assert task.status == "complete"
        assert task.passes is True
        assert task.verification_verdict == "PASS"
        assert task.files_actually_changed == ["src/test.ts"]

    def test_mark_complete_with_fail_verdict(self, work_queue):
        """Task marked complete with FAIL verdict should set passes=False"""
        work_queue.mark_complete(
            task_id="TEST-001",
            verdict="FAIL",
            files_changed=["src/test.ts"]
        )

        task = work_queue.features[0]
        assert task.status == "complete"
        assert task.passes is False
        assert task.verification_verdict == "FAIL"

    def test_mark_complete_without_verdict(self, work_queue):
        """Task marked complete without verdict should default to passes=True"""
        work_queue.mark_complete(task_id="TEST-001")

        task = work_queue.features[0]
        assert task.status == "complete"
        assert task.passes is True
        assert task.verification_verdict is None

    def test_mark_complete_stores_changed_files(self, work_queue):
        """Changed files should be stored in task"""
        changed_files = ["src/test.ts", "src/helper.ts", "tests/test.test.ts"]
        work_queue.mark_complete(
            task_id="TEST-001",
            verdict="PASS",
            files_changed=changed_files
        )

        task = work_queue.features[0]
        assert task.files_actually_changed == changed_files


class TestWorkQueueValidation:
    """Test Phase 3: Work queue validation"""

    def test_validate_tasks_with_existing_files(self, work_queue, tmp_path):
        """Validation should pass when all files exist"""
        # Create the files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "test.ts").write_text("// test file")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test.test.ts").write_text("// test file")

        errors = work_queue.validate_tasks(tmp_path)
        assert len(errors) == 0

    def test_validate_tasks_with_missing_target_file(self, work_queue, tmp_path):
        """Validation should fail when target file is missing"""
        errors = work_queue.validate_tasks(tmp_path)

        assert len(errors) > 0
        assert any("Target file not found" in e for e in errors)
        assert any("src/test.ts" in e for e in errors)

    def test_validate_tasks_with_missing_test_file(self, work_queue, tmp_path):
        """Validation should fail when test file is missing"""
        # Create target file but not test file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "test.ts").write_text("// test file")

        errors = work_queue.validate_tasks(tmp_path)

        assert len(errors) > 0
        assert any("Test file not found" in e for e in errors)
        assert any("tests/test.test.ts" in e for e in errors)

    def test_validate_multiple_tasks(self, tmp_path):
        """Validation should check all tasks"""
        queue = WorkQueue(
            project="test",
            features=[
                Task(
                    id="TASK-1",
                    description="Task 1",
                    file="src/exists.ts",
                    status="pending",
                    tests=[],
                    passes=False
                ),
                Task(
                    id="TASK-2",
                    description="Task 2",
                    file="src/missing.ts",
                    status="pending",
                    tests=[],
                    passes=False
                )
            ]
        )

        # Create only one file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "exists.ts").write_text("// exists")

        errors = queue.validate_tasks(tmp_path)

        # Should have error for TASK-2 only
        assert len(errors) == 1
        assert "TASK-2" in errors[0]
        assert "missing.ts" in errors[0]

    def test_validate_feature_task_allows_missing_file(self, tmp_path):
        """Feature tasks should NOT fail validation when target file is missing (they CREATE files)"""
        queue = WorkQueue(
            project="test",
            features=[
                Task(
                    id="FEAT-001",
                    description="Create new feature",
                    file="src/new_feature.ts",
                    status="pending",
                    tests=[],
                    passes=False,
                    type="feature",
                    agent="FeatureBuilder"
                ),
                Task(
                    id="BUGFIX-001",
                    description="Fix existing bug",
                    file="src/existing.ts",
                    status="pending",
                    tests=[],
                    passes=False,
                    type="bugfix",
                    agent="BugFix"
                )
            ]
        )

        # Create neither file - feature task should pass, bugfix should fail
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        errors = queue.validate_tasks(tmp_path)

        # Should only have error for BUGFIX-001, not FEAT-001
        assert len(errors) == 1
        assert "BUGFIX-001" in errors[0]
        assert "existing.ts" in errors[0]
        # Feature task should NOT be in errors
        assert not any("FEAT-001" in e for e in errors)

    def test_validate_feature_builder_agent_allows_missing_file(self, tmp_path):
        """Tasks with FeatureBuilder agent should allow missing files"""
        queue = WorkQueue(
            project="test",
            features=[
                Task(
                    id="BACKUP-001",
                    description="Create backup script",
                    file="infra/scripts/backup.sh",
                    status="pending",
                    tests=[],
                    passes=False,
                    type="feature",
                    agent="FeatureBuilder"
                )
            ]
        )

        # File doesn't exist - should be allowed for FeatureBuilder
        errors = queue.validate_tasks(tmp_path)
        assert len(errors) == 0


class TestVerificationIntegration:
    """Integration tests for verification workflow"""

    def test_task_lifecycle_with_no_changes(self, work_queue):
        """Task with no changes should be blocked, not completed"""
        # Simulate agent making no changes
        task = work_queue.features[0]
        task.status = "in_progress"

        # Agent would be blocked by stop hook (tested above)
        # Instead of mark_complete, should call mark_blocked
        work_queue.mark_blocked(task.id, "No changes detected")

        assert task.status == "blocked"
        assert task.passes is False
        assert task.error == "No changes detected"

    def test_task_lifecycle_with_pass(self, work_queue):
        """Task with PASS verdict should be completed successfully"""
        work_queue.mark_complete(
            task_id="TEST-001",
            verdict="PASS",
            files_changed=["src/test.ts"]
        )

        task = work_queue.features[0]
        assert task.status == "complete"
        assert task.passes is True
        assert task.verification_verdict == "PASS"
        assert task.completed_at is not None

    def test_task_lifecycle_with_fail(self, work_queue):
        """Task with FAIL verdict can still be marked complete (for pre-existing issues)"""
        work_queue.mark_complete(
            task_id="TEST-001",
            verdict="FAIL",
            files_changed=["src/test.ts"]
        )

        task = work_queue.features[0]
        assert task.status == "complete"
        assert task.passes is False
        assert task.verification_verdict == "FAIL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
