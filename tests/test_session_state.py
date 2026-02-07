"""
Tests for SessionState - session persistence and resumption

Tests cover:
- Basic save/load functionality
- Resume capability across context resets
- Edge cases (large files, special characters, malformed data)
- Integration with work queue
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from orchestration.session_state import SessionState, format_session_markdown


@pytest.fixture
def temp_session_dir(tmp_path):
    """Use temporary directory for session files."""
    session_dir = tmp_path / ".aibrain"
    session_dir.mkdir()
    original_dir = Path.cwd()

    # Create dummy .aibrain in temp location
    import os
    os.chdir(tmp_path)

    yield session_dir

    os.chdir(original_dir)


class TestSessionStateBasics:
    """Basic save/load functionality."""

    def test_save_creates_file(self):
        """Session.save() creates markdown file."""
        session = SessionState("TASK-1", "credentialmate")

        session.save({
            "iteration_count": 1,
            "phase": "feature_build",
            "status": "in_progress",
            "last_output": "Started implementation",
            "next_steps": ["Step 1", "Step 2"],
            "markdown_content": "## Test\nContent here",
        })

        files = list(Path(".aibrain").glob("session-credentialmate-TASK-1*.md"))
        assert len(files) > 0, "Session file not created"

    def test_save_includes_frontmatter(self):
        """Saved file includes JSON frontmatter."""
        session = SessionState("TASK-2", "credentialmate")
        session.save({
            "iteration_count": 5,
            "phase": "testing",
            "status": "in_progress",
            "last_output": "Testing...",
            "next_steps": [],
            "markdown_content": "",
        })

        file_path = Path(".aibrain") / "session-credentialmate-TASK-2-1.md"
        assert file_path.exists()

        content = file_path.read_text()
        assert "---" in content
        assert "iteration_count" in content
        assert "TASK-2" in content

    def test_save_includes_markdown_content(self):
        """Saved file includes markdown body."""
        session = SessionState("TASK-3", "credentialmate")
        markdown_content = "## Progress\n✅ Phase 1 complete\n🔄 Phase 2 in progress"

        session.save({
            "iteration_count": 3,
            "phase": "build",
            "status": "in_progress",
            "last_output": "Made progress",
            "next_steps": ["Continue"],
            "markdown_content": markdown_content,
        })

        file_path = list(Path(".aibrain").glob("session-credentialmate-TASK-3*.md"))[0]
        content = file_path.read_text()
        assert markdown_content in content

    def test_load_returns_all_data(self):
        """Session.load() returns all saved data."""
        session = SessionState("TASK-4", "credentialmate")
        original = {
            "iteration_count": 8,
            "phase": "complete",
            "status": "completed",
            "last_output": "Task finished",
            "next_steps": ["Archive"],
            "markdown_content": "Done!",
        }

        session.save(original)
        loaded = SessionState.load("TASK-4", "credentialmate")

        assert loaded["iteration_count"] == 8
        assert loaded["phase"] == "complete"
        assert loaded["status"] == "completed"
        assert loaded["markdown_content"] == "Done!"

    def test_load_parses_frontmatter_correctly(self):
        """Load correctly parses JSON frontmatter."""
        session = SessionState("TASK-5", "credentialmate")
        session.save({
            "iteration_count": 12,
            "phase": "testing",
            "status": "in_progress",
            "last_output": "Test output",
            "next_steps": ["Run tests", "Fix issues"],
            "context_window": 2,
            "tokens_used": 3847,
            "markdown_content": "",
        })

        loaded = SessionState.load("TASK-5", "credentialmate")
        assert loaded["iteration_count"] == 12
        assert loaded["context_window"] == 2
        assert loaded["tokens_used"] == 3847
        assert isinstance(loaded["next_steps"], list)
        assert "Run tests" in loaded["next_steps"]

    def test_load_nonexistent_raises_error(self):
        """Loading non-existent session raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            SessionState.load("NONEXISTENT-TASK")

    def test_malformed_frontmatter_raises_error(self):
        """Malformed JSON frontmatter raises error."""
        # Create file with bad JSON
        Path(".aibrain").mkdir(exist_ok=True)
        bad_file = Path(".aibrain") / "session-BAD-1.md"
        bad_file.write_text("---\nNOT VALID JSON\n---\nContent")

        with pytest.raises(json.JSONDecodeError):
            SessionState.load("BAD")


class TestSessionStateResume:
    """Resume capability across context resets."""

    def test_resume_continues_iteration_count(self):
        """Resuming task continues iteration count."""
        session = SessionState("TASK-6", "credentialmate")

        # First save
        session.save({
            "iteration_count": 5,
            "phase": "build",
            "status": "in_progress",
            "last_output": "Completed 5 iterations",
            "next_steps": ["Continue"],
            "markdown_content": "",
        })

        # Load and update
        session.update(iteration_count=6, last_output="Completed 6 iterations")

        # Verify
        loaded = SessionState.load("TASK-6", "credentialmate")
        assert loaded["iteration_count"] == 6

    def test_resume_preserves_progress(self):
        """Resuming preserves previous progress."""
        session = SessionState("TASK-7", "credentialmate")

        session.save({
            "iteration_count": 3,
            "phase": "build",
            "status": "in_progress",
            "last_output": "Phase 1 done",
            "next_steps": ["Phase 2"],
            "markdown_content": "## Progress\n✅ Phase 1\n✅ Phase 2\n🔄 Phase 3",
        })

        loaded = SessionState.load("TASK-7", "credentialmate")
        assert "✅ Phase 1" in loaded["markdown_content"]
        assert "🔄 Phase 3" in loaded["markdown_content"]

    def test_multiple_checkpoints_overwrite_previous(self):
        """Multiple saves create new checkpoints, don't append."""
        session = SessionState("TASK-8", "credentialmate")

        # Save iteration 1
        session.save({
            "iteration_count": 1,
            "phase": "build",
            "status": "in_progress",
            "last_output": "Iteration 1 done",
            "next_steps": [],
            "markdown_content": "## Iteration 1",
        })

        # Save iteration 2
        session.save({
            "iteration_count": 2,
            "phase": "test",
            "status": "in_progress",
            "last_output": "Iteration 2 done",
            "next_steps": [],
            "markdown_content": "## Iteration 2",
        })

        # Should load iteration 2 (latest)
        loaded = SessionState.load("TASK-8", "credentialmate")
        assert loaded["iteration_count"] == 2
        assert "Iteration 2" in loaded["markdown_content"]

    def test_context_reset_recovery(self):
        """Simulates context reset and recovery."""
        # Context 1: Create and save session
        session1 = SessionState("TASK-9", "credentialmate")
        session1.save({
            "iteration_count": 3,
            "phase": "build",
            "status": "in_progress",
            "last_output": "Context 1 work done",
            "next_steps": ["Continue in context 2"],
            "context_window": 1,
            "markdown_content": "## Context 1\n✅ 3 iterations done",
        })

        # Simulate context reset - new session object
        session2 = SessionState("TASK-9", "credentialmate")

        # Resume from saved state
        loaded = session2.get_latest()
        assert loaded["iteration_count"] == 3
        assert loaded["context_window"] == 1

        # Continue work
        session2.update(
            iteration_count=4,
            context_window=2,
            last_output="Context 2 work done",
            markdown_content="## Context 1\n✅ 3 iterations done\n## Context 2\n✅ 1 iteration done",
        )

        # Verify
        final = SessionState.load("TASK-9", "credentialmate")
        assert final["iteration_count"] == 4
        assert final["context_window"] == 2


class TestSessionStateEdgeCases:
    """Edge cases and error handling."""

    def test_large_session_file(self):
        """Large session files (100KB+) handled correctly."""
        session = SessionState("TASK-10", "credentialmate")

        # Create large content
        large_content = "x" * (100 * 1024)  # 100KB

        session.save({
            "iteration_count": 100,
            "phase": "test",
            "status": "in_progress",
            "last_output": "Large file",
            "next_steps": [],
            "markdown_content": large_content,
        })

        loaded = SessionState.load("TASK-10", "credentialmate")
        assert len(loaded["markdown_content"]) == 100 * 1024

    def test_special_characters_in_content(self):
        """Special characters, JSON escaping handled."""
        session = SessionState("TASK-11", "credentialmate")

        special_content = '''Error: "quotes" and 'apostrophes' and
newlines and\\backslashes and $variables and unicode: 你好'''

        session.save({
            "iteration_count": 1,
            "phase": "debug",
            "status": "blocked",
            "last_output": special_content,
            "next_steps": ["Fix"],
            "markdown_content": "# Code\n```json\n{\"key\": \"value\"}\n```",
        })

        loaded = SessionState.load("TASK-11", "credentialmate")
        assert "quotes" in loaded["last_output"]
        assert "newlines" in loaded["last_output"]
        assert "你好" in loaded["last_output"]

    def test_missing_required_fields_raises_error(self):
        """Saving without required fields raises error."""
        session = SessionState("TASK-12", "credentialmate")

        with pytest.raises(ValueError):
            session.save({
                "iteration_count": 1,
                # Missing 'phase' and 'status'
                "last_output": "Test",
                "next_steps": [],
                "markdown_content": "",
            })

    def test_empty_session_data(self):
        """Saving minimal data works."""
        session = SessionState("TASK-13", "credentialmate")

        session.save({
            "iteration_count": 0,
            "phase": "initial",
            "status": "pending",
            "markdown_content": "",
        })

        loaded = SessionState.load("TASK-13", "credentialmate")
        assert loaded["iteration_count"] == 0
        assert loaded["phase"] == "initial"

    def test_unicode_filenames(self):
        """Unicode in task_id handled (though not recommended)."""
        session = SessionState("TASK-unicode-测试", "credentialmate")

        session.save({
            "iteration_count": 1,
            "phase": "test",
            "status": "in_progress",
            "last_output": "Test",
            "next_steps": [],
            "markdown_content": "Unicode test",
        })

        loaded = SessionState.load("TASK-unicode-测试", "credentialmate")
        assert loaded["markdown_content"] == "Unicode test"


class TestSessionStateArchival:
    """Session archival and cleanup."""

    def test_archive_moves_to_archive_dir(self):
        """Archive moves completed session to archive."""
        session = SessionState("TASK-14", "credentialmate")

        session.save({
            "iteration_count": 50,
            "phase": "complete",
            "status": "completed",
            "last_output": "Complete",
            "next_steps": [],
            "markdown_content": "Done",
        })

        # Verify file exists (now uses project-scoped naming)
        files = list(Path(".aibrain").glob("session-credentialmate-TASK-14*.md"))
        assert len(files) > 0

        # Archive
        session.archive()

        # Original should be gone
        files_after = list(Path(".aibrain").glob("session-credentialmate-TASK-14*.md"))
        assert len(files_after) == 0

        # Should be in archive
        archive_files = list(Path(".aibrain/sessions/archive").glob("session-credentialmate-TASK-14*.md"))
        assert len(archive_files) > 0

    def test_delete_session(self):
        """Delete removes all session files for task."""
        session = SessionState("TASK-15", "credentialmate")

        # Create multiple checkpoints
        for i in range(3):
            session.save({
                "iteration_count": i + 1,
                "phase": "test",
                "status": "in_progress",
                "last_output": f"Iteration {i+1}",
                "next_steps": [],
                "markdown_content": "",
                "checkpoint_number": i + 1,
            })

        # Verify files exist (now uses project-scoped naming)
        files = list(Path(".aibrain").glob("session-credentialmate-TASK-15*.md"))
        assert len(files) >= 1

        # Delete with project scope
        SessionState.delete_session("TASK-15", "credentialmate")

        # Verify all deleted
        files_after = list(Path(".aibrain").glob("session-credentialmate-TASK-15*.md"))
        assert len(files_after) == 0


class TestSessionStateFormatMarkdown:
    """Markdown formatting for human readability."""

    def test_format_session_markdown_basic(self):
        """format_session_markdown creates readable output."""
        session_data = {
            "task_id": "TASK-1",
            "project": "credentialmate",
            "status": "in_progress",
            "iteration_count": 5,
            "max_iterations": 50,
            "phase": "build",
            "last_output": "Implementation complete",
            "context_window": 1,
            "tokens_used": 3847,
            "next_steps": ["Run tests", "Update docs"],
        }

        markdown = format_session_markdown(session_data)

        assert "## Task Summary" in markdown
        assert "TASK-1" in markdown
        assert "credentialmate" in markdown
        assert "## Next Steps" in markdown
        assert "1. Run tests" in markdown

    def test_format_with_progress_sections(self):
        """format_session_markdown includes progress sections."""
        session_data = {
            "task_id": "TASK-2",
            "project": "karematch",
            "status": "in_progress",
            "iteration_count": 3,
            "max_iterations": 50,
            "phase": "test",
            "next_steps": [],
        }

        progress = [
            "1. ✅ Phase 1: Design",
            "2. ✅ Phase 2: Build",
            "3. 🔄 Phase 3: Test",
        ]

        markdown = format_session_markdown(session_data, progress_sections=progress)

        assert "## Progress" in markdown
        assert "✅ Phase 1: Design" in markdown
        assert "🔄 Phase 3: Test" in markdown

    def test_format_with_iteration_log(self):
        """format_session_markdown includes iteration log."""
        session_data = {
            "task_id": "TASK-3",
            "project": "credentialmate",
            "status": "in_progress",
            "iteration_count": 2,
            "max_iterations": 50,
            "phase": "build",
            "next_steps": [],
        }

        iterations = [
            {"num": 1, "task": "Implement auth", "result": "PASS", "notes": "Clean implementation"},
            {"num": 2, "task": "Add tests", "result": "FAIL", "notes": "Need 100% coverage"},
        ]

        markdown = format_session_markdown(session_data, iteration_log=iterations)

        assert "## Iteration Log" in markdown
        assert "### Iteration 1" in markdown
        assert "Implement auth" in markdown
        assert "Clean implementation" in markdown


class TestSessionStateMultiproject:
    """Cross-project session management."""

    def test_get_all_sessions_by_project(self):
        """get_all_sessions can filter by project."""
        # Create sessions for different projects
        s1 = SessionState("TASK-A", "credentialmate")
        s1.save({
            "iteration_count": 1,
            "phase": "test",
            "status": "in_progress",
            "last_output": "Test",
            "next_steps": [],
            "markdown_content": "",
        })

        s2 = SessionState("TASK-B", "karematch")
        s2.save({
            "iteration_count": 1,
            "phase": "test",
            "status": "in_progress",
            "last_output": "Test",
            "next_steps": [],
            "markdown_content": "",
        })

        # Get all credentialmate sessions
        credentialmate_sessions = SessionState.get_all_sessions(project="credentialmate")

        # Should only include credentialmate
        projects = [s["project"] for s in credentialmate_sessions]
        assert "credentialmate" in projects
        assert len([p for p in projects if p == "credentialmate"]) >= 1

    def test_load_by_session_id(self):
        """load_by_id can load session by ID from frontmatter."""
        import time
        # Use unique task ID with timestamp to avoid collisions
        unique_task_id = f"TASK-UNIQUE-ID-LOAD-{int(time.time() * 1000)}"

        session = SessionState(unique_task_id, "credentialmate")
        session.save({
            "iteration_count": 5,
            "phase": "test",
            "status": "in_progress",
            "last_output": "Test",
            "next_steps": [],
            "markdown_content": "Test content by ID",
        })

        # Get session ID from saved file
        loaded = SessionState.load(unique_task_id, "credentialmate")
        session_id = loaded["id"]

        # Verify we can find it by ID
        # load_by_id returns the first matching session found
        loaded_by_id = SessionState.load_by_id(session_id)
        assert "markdown_content" in loaded_by_id
        # Verify we got a session with the same ID
        assert loaded_by_id["id"] == session_id


class TestSessionStateMultiAgent:
    """Test multi-agent session state tracking methods."""

    def test_record_team_lead_analysis(self):
        """Test recording team lead task analysis."""
        session = SessionState("TASK-MULTI-001", "ai-orchestrator")

        analysis = {
            "key_challenges": ["cross-repo", "testing"],
            "recommended_specialists": ["bugfix", "testwriter"],
            "subtask_breakdown": ["fix bug", "write tests"],
            "risk_factors": ["integration"],
            "estimated_complexity": "high",
        }

        session.record_team_lead_analysis(analysis)

        # Verify it was saved to multi-agent file
        retrieved = session.get_team_lead_analysis()
        assert retrieved is not None
        assert retrieved["estimated_complexity"] == "high"
        assert "bugfix" in retrieved["recommended_specialists"]

    def test_record_specialist_launch(self):
        """Test recording specialist launch."""
        session = SessionState("TASK-MULTI-002", "ai-orchestrator")

        session.record_specialist_launch("bugfix", "SUBTASK-001")

        # Verify it was recorded
        status = session.get_specialist_status("bugfix")
        assert status["status"] == "in_progress"
        assert "SUBTASK-001" in status["subtask_ids"]

    def test_record_specialist_iteration(self):
        """Test recording specialist iteration progress."""
        # Use unique task ID to avoid interference from previous test runs
        task_id = "TASK-MULTI-003-ITER"
        project = "ai-orchestrator"
        session = SessionState(task_id, project)

        # Clean up any existing multi-agent file for this task
        # File naming is: .multi-agent-{project}-{task_id}.json
        ma_file = Path(".aibrain") / f".multi-agent-{project}-{task_id}.json"
        if ma_file.exists():
            ma_file.unlink()

        session.record_specialist_launch("featurebuilder", "SUBTASK-001")
        session.record_specialist_iteration("featurebuilder", 1, "Implementing feature...")
        session.record_specialist_iteration("featurebuilder", 2, "Feature complete", "PASS")

        # Verify iterations recorded
        status = session.get_specialist_status("featurebuilder")
        assert status["iterations"] == 2
        assert "iteration_history" in status
        assert len(status["iteration_history"]) == 2

    def test_record_specialist_completion(self):
        """Test recording specialist completion."""
        session = SessionState("TASK-MULTI-004", "ai-orchestrator")

        session.record_specialist_launch("bugfix", "SUBTASK-001")
        session.record_specialist_completion(
            "bugfix",
            "completed",
            {"type": "PASS"},
            "Bug fixed and verified",
            tokens_used=45000,
            cost=0.067,
        )

        # Verify completion recorded
        status = session.get_specialist_status("bugfix")
        assert status["status"] == "completed"
        assert status["verdict"] == "PASS"
        assert status["tokens_used"] == 45000
        assert status["cost"] == 0.067
        assert "end_time" in status

    def test_get_specialist_status(self):
        """Test querying specialist status."""
        session = SessionState("TASK-MULTI-005", "ai-orchestrator")

        session.record_specialist_launch("testwriter", "SUBTASK-001")
        session.record_specialist_iteration("testwriter", 1, "Writing tests...")

        status = session.get_specialist_status("testwriter")

        assert status["status"] == "in_progress"
        assert status["iterations"] == 1

    def test_get_all_specialists_status(self):
        """Test querying all specialists status."""
        session = SessionState("TASK-MULTI-006", "ai-orchestrator")

        session.record_specialist_launch("bugfix", "SUBTASK-001")
        session.record_specialist_launch("featurebuilder", "SUBTASK-002")
        session.record_specialist_iteration("bugfix", 1, "Analyzing bug...")
        session.record_specialist_iteration("featurebuilder", 1, "Building feature...")

        all_status = session.get_all_specialists_status()

        assert "bugfix" in all_status
        assert "featurebuilder" in all_status
        assert len(all_status) == 2

    def test_all_specialists_complete_false(self):
        """Test checking if all specialists are complete (negative case)."""
        session = SessionState("TASK-MULTI-007", "ai-orchestrator")

        session.record_specialist_launch("bugfix", "SUBTASK-001")
        session.record_specialist_launch("testwriter", "SUBTASK-002")

        # Record only first specialist as complete
        session.record_specialist_completion("bugfix", "completed", {"type": "PASS"}, "Done")

        # Should be False because testwriter not complete
        assert session.all_specialists_complete() is False

    def test_all_specialists_complete_true(self):
        """Test checking if all specialists are complete (positive case)."""
        session = SessionState("TASK-MULTI-008", "ai-orchestrator")

        session.record_specialist_launch("bugfix", "SUBTASK-001")
        session.record_specialist_launch("testwriter", "SUBTASK-002")

        # Complete both
        session.record_specialist_completion("bugfix", "completed", {"type": "PASS"}, "Done")
        session.record_specialist_completion("testwriter", "completed", {"type": "PASS"}, "Done")

        # Should be True
        assert session.all_specialists_complete() is True

    def test_all_specialists_complete_no_specialists(self):
        """Test checking completion with no specialists launched."""
        session = SessionState("TASK-MULTI-009", "ai-orchestrator")

        # No specialists launched
        assert session.all_specialists_complete() is True

    def test_get_team_lead_analysis(self):
        """Test retrieving team lead analysis."""
        session = SessionState("TASK-MULTI-010", "ai-orchestrator")

        analysis = {
            "key_challenges": ["refactoring"],
            "recommended_specialists": ["codequality"],
            "subtask_breakdown": [],
            "risk_factors": [],
            "estimated_complexity": "medium",
        }

        session.record_team_lead_analysis(analysis)

        retrieved = session.get_team_lead_analysis()

        assert retrieved is not None
        assert retrieved["estimated_complexity"] == "medium"
        assert "codequality" in retrieved["recommended_specialists"]

    def test_multiple_specialists_isolated_tracking(self):
        """Test that multiple specialists are tracked independently."""
        session = SessionState("TASK-MULTI-011", "ai-orchestrator")

        # Launch 3 specialists
        session.record_specialist_launch("bugfix", "SUBTASK-001")
        session.record_specialist_launch("featurebuilder", "SUBTASK-002")
        session.record_specialist_launch("testwriter", "SUBTASK-003")

        # Different iteration counts
        session.record_specialist_iteration("bugfix", 2, "Analyzing")
        session.record_specialist_iteration("featurebuilder", 5, "Building")
        session.record_specialist_iteration("testwriter", 1, "Testing")

        # Different completions
        session.record_specialist_completion("bugfix", "completed", {"type": "PASS"}, "Done")
        # featurebuilder still running
        session.record_specialist_completion("testwriter", "blocked", {"type": "BLOCKED"}, "Blocked")

        # Verify isolation
        bugfix_status = session.get_specialist_status("bugfix")
        featurebuilder_status = session.get_specialist_status("featurebuilder")
        testwriter_status = session.get_specialist_status("testwriter")

        assert bugfix_status["status"] == "completed"
        assert bugfix_status["iterations"] == 2
        assert featurebuilder_status["status"] == "in_progress"
        assert featurebuilder_status["iterations"] == 5
        assert testwriter_status["status"] == "blocked"
        assert testwriter_status["iterations"] == 1

    def test_iteration_history_truncated_to_last_three(self):
        """Test that iteration history keeps only last 3 iterations."""
        session = SessionState("TASK-MULTI-012", "ai-orchestrator")

        session.record_specialist_launch("bugfix", "SUBTASK-001")

        # Record 5 iterations
        for i in range(1, 6):
            session.record_specialist_iteration("bugfix", i, f"Iteration {i}")

        # Check history is truncated to 3
        status = session.get_specialist_status("bugfix")
        history = status["iteration_history"]

        assert len(history) == 3
        # Should be iterations 3, 4, 5
        assert history[0]["iteration"] == 3
        assert history[1]["iteration"] == 4
        assert history[2]["iteration"] == 5
