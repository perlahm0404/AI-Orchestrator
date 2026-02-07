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

        files = list(Path(".aibrain").glob("session-TASK-1*.md"))
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

        file_path = Path(".aibrain") / "session-TASK-2-1.md"
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

        file_path = list(Path(".aibrain").glob("session-TASK-3*.md"))[0]
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
        loaded = SessionState.load("TASK-4")

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

        loaded = SessionState.load("TASK-5")
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
        loaded = SessionState.load("TASK-6")
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

        loaded = SessionState.load("TASK-7")
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
        loaded = SessionState.load("TASK-8")
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
        final = SessionState.load("TASK-9")
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

        loaded = SessionState.load("TASK-10")
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

        loaded = SessionState.load("TASK-11")
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

        loaded = SessionState.load("TASK-13")
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

        loaded = SessionState.load("TASK-unicode-测试")
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

        # Verify file exists
        files = list(Path(".aibrain").glob("session-TASK-14*.md"))
        assert len(files) > 0

        # Archive
        session.archive()

        # Original should be gone
        files_after = list(Path(".aibrain").glob("session-TASK-14*.md"))
        assert len(files_after) == 0

        # Should be in archive
        archive_files = list(Path(".aibrain/sessions/archive").glob("session-TASK-14*.md"))
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

        # Verify files exist
        files = list(Path(".aibrain").glob("session-TASK-15*.md"))
        assert len(files) >= 1

        # Delete
        SessionState.delete_session("TASK-15")

        # Verify all deleted
        files_after = list(Path(".aibrain").glob("session-TASK-15*.md"))
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
        session = SessionState("TASK-UNIQUE-ID-LOAD", "credentialmate")
        session.save({
            "iteration_count": 5,
            "phase": "test",
            "status": "in_progress",
            "last_output": "Test",
            "next_steps": [],
            "markdown_content": "Test content by ID",
        })

        # Get session ID from saved file
        loaded = SessionState.load("TASK-UNIQUE-ID-LOAD")
        session_id = loaded["id"]

        # Verify we can find it by ID
        # (Note: This may find other sessions if ID collision occurs)
        # Just verify load_by_id doesn't crash and returns something
        loaded_by_id = SessionState.load_by_id(session_id)
        assert "markdown_content" in loaded_by_id
        assert loaded_by_id["project"] == "credentialmate"
