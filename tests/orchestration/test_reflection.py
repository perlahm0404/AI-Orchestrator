"""
Tests for Session Reflection System

Tests:
1. SessionResult creation
2. SessionReflection handoff generation
3. Symlink updates
4. Content validation
5. Integration with Ralph verification

Implementation: v5.0 - Session Reflection
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from orchestration.reflection import (
    SessionReflection,
    SessionResult,
    SessionStatus,
    FileChange,
    SessionTestSummary,
    create_session_handoff
)
from ralph.engine import Verdict, VerdictType, StepResult


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())
    (temp_dir / "sessions").mkdir()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_verdict():
    """Create sample Ralph verdict."""
    return Verdict(
        type=VerdictType.PASS,
        steps=[
            StepResult(step="lint", passed=True, output="", duration_ms=100),
            StepResult(step="typecheck", passed=True, output="", duration_ms=200),
            StepResult(step="tests", passed=True, output="", duration_ms=500),
        ],
        reason=None,
        safe_to_merge=True,
        regression_detected=False,
        pre_existing_failures=[]
    )


@pytest.fixture
def sample_result(sample_verdict):
    """Create sample SessionResult."""
    return SessionResult(
        task_id="BUG-001",
        status=SessionStatus.COMPLETED,
        accomplished=[
            "Fixed authentication bug in src/auth.ts",
            "Added test coverage for token refresh"
        ],
        incomplete=[],
        blockers=[],
        file_changes=[
            FileChange(file="src/auth.ts", action="Modified", lines_added=15, lines_removed=8),
            FileChange(file="tests/auth.test.ts", action="Modified", lines_added=42, lines_removed=0)
        ],
        tests=SessionTestSummary(
            total=50,
            passed=50,
            failed=0,
            added=3,
            modified=1
        ),
        verdict=sample_verdict,
        handoff_notes="Fixed token refresh flow. All tests passing. Ready for merge.",
        regression_risk="LOW",
        merge_confidence="HIGH",
        requires_review=True
    )


class TestSessionResult:
    """Tests for SessionResult dataclass."""

    def test_create_completed_result(self, sample_result):
        """Test creating a completed session result."""
        assert sample_result.task_id == "BUG-001"
        assert sample_result.status == SessionStatus.COMPLETED
        assert len(sample_result.accomplished) == 2
        assert len(sample_result.file_changes) == 2

    def test_create_blocked_result(self):
        """Test creating a blocked session result."""
        result = SessionResult(
            task_id="BUG-002",
            status=SessionStatus.BLOCKED,
            accomplished=[],
            incomplete=["Fix applied but not verified"],
            blockers=["Guardrail violation: test.skip() detected"],
            file_changes=[]
        )

        assert result.status == SessionStatus.BLOCKED
        assert len(result.blockers) == 1
        assert "guardrail" in result.blockers[0].lower()

    def test_create_partial_result(self):
        """Test creating a partial session result."""
        result = SessionResult(
            task_id="BUG-003",
            status=SessionStatus.PARTIAL,
            accomplished=["Fixed part 1 of bug"],
            incomplete=["Part 2 still needs work"],
            next_steps=["Complete part 2", "Add tests"]
        )

        assert result.status == SessionStatus.PARTIAL
        assert len(result.next_steps) == 2


class TestSessionReflection:
    """Tests for SessionReflection class."""

    def test_create_reflection(self, temp_project_dir, sample_result):
        """Test creating a session reflection."""
        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        assert reflection.session_id == "session-123"
        assert reflection.agent_name == "bugfix"
        assert reflection.result == sample_result

    def test_generate_handoff_document(self, temp_project_dir, sample_result):
        """Test generating handoff document."""
        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        handoff_path = reflection.generate()

        # Check file exists
        assert handoff_path.exists()
        assert handoff_path.parent.name == "sessions"

        # Check content
        content = handoff_path.read_text()
        assert "Session:" in content
        assert "BUG-001" in content
        assert "session-123" in content
        assert "bugfix" in content
        assert "COMPLETED" in content

    def test_handoff_contains_required_sections(self, temp_project_dir, sample_result):
        """Test that handoff contains all required sections."""
        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        handoff_path = reflection.generate()
        content = handoff_path.read_text()

        required_sections = [
            "What Was Accomplished",
            "What Was NOT Done",
            "Blockers / Open Questions",
            "Ralph Verdict",
            "Files Modified",
            "Handoff Notes",
            "Risk Assessment"
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_handoff_contains_ralph_verdict_details(self, temp_project_dir, sample_result):
        """Test that Ralph verdict is properly formatted."""
        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        handoff_path = reflection.generate()
        content = handoff_path.read_text()

        # Check verdict details
        assert "**Status**: PASS" in content
        assert "**Safe to Merge**: ✅ YES" in content
        assert "**Tests**: 50/50 passing" in content

        # Check step details
        assert "lint" in content.lower()
        assert "typecheck" in content.lower()
        assert "tests" in content.lower()

    def test_handoff_contains_file_changes(self, temp_project_dir, sample_result):
        """Test that file changes are properly formatted."""
        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        handoff_path = reflection.generate()
        content = handoff_path.read_text()

        # Check file changes table
        assert "src/auth.ts" in content
        assert "tests/auth.test.ts" in content
        assert "Modified" in content
        assert "+15/-8" in content
        assert "+42/-0" in content

    def test_latest_symlink_created(self, temp_project_dir, sample_result):
        """Test that latest.md symlink is created."""
        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        handoff_path = reflection.generate()
        latest_link = temp_project_dir / "sessions" / "latest.md"

        assert latest_link.is_symlink()
        assert latest_link.resolve() == handoff_path.resolve()

    def test_latest_symlink_updated_on_new_session(self, temp_project_dir, sample_result):
        """Test that latest.md symlink is updated for new sessions."""
        # First session
        reflection1 = SessionReflection(
            session_id="session-1",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )
        handoff1 = reflection1.generate()

        latest_link = temp_project_dir / "sessions" / "latest.md"
        assert latest_link.resolve() == handoff1.resolve()

        # Second session
        result2 = SessionResult(
            task_id="BUG-002",
            status=SessionStatus.COMPLETED,
            accomplished=["Fixed bug 2"]
        )
        reflection2 = SessionReflection(
            session_id="session-2",
            agent_name="bugfix",
            result=result2,
            project_root=temp_project_dir
        )
        handoff2 = reflection2.generate()

        # Check symlink points to new handoff
        assert latest_link.resolve() == handoff2.resolve()
        assert latest_link.resolve() != handoff1.resolve()

    def test_handoff_with_blockers(self, temp_project_dir, sample_verdict):
        """Test handoff generation with blockers."""
        result = SessionResult(
            task_id="BUG-002",
            status=SessionStatus.BLOCKED,
            accomplished=[],
            incomplete=["Fix not verified"],
            blockers=[
                "Guardrail violation: test.skip() detected",
                "Cannot proceed without removing skip"
            ],
            verdict=Verdict(
                type=VerdictType.BLOCKED,
                steps=[],
                reason="Guardrail violation",
                safe_to_merge=False
            )
        )

        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=result,
            project_root=temp_project_dir
        )

        handoff_path = reflection.generate()
        content = handoff_path.read_text()

        assert "BLOCKED" in content
        assert "Guardrail violation" in content
        assert "test.skip()" in content

    def test_handoff_with_next_steps(self, temp_project_dir):
        """Test handoff generation with next steps."""
        result = SessionResult(
            task_id="BUG-003",
            status=SessionStatus.PARTIAL,
            accomplished=["Fixed part 1"],
            incomplete=["Part 2 incomplete"],
            next_steps=[
                "Complete part 2 implementation",
                "Add integration tests",
                "Update documentation"
            ]
        )

        reflection = SessionReflection(
            session_id="session-123",
            agent_name="bugfix",
            result=result,
            project_root=temp_project_dir
        )

        handoff_path = reflection.generate()
        content = handoff_path.read_text()

        assert "Next Steps" in content
        assert "Complete part 2 implementation" in content
        assert "Add integration tests" in content
        assert "Update documentation" in content


class TestCreateSessionHandoff:
    """Tests for create_session_handoff convenience function."""

    def test_create_handoff_convenience_function(self, temp_project_dir, sample_result):
        """Test convenience function for creating handoff."""
        handoff_path = create_session_handoff(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        assert handoff_path.exists()
        assert "BUG-001" in handoff_path.name

        content = handoff_path.read_text()
        assert "session-123" in content
        assert "bugfix" in content


class TestHandoffFilenameFormat:
    """Tests for handoff filename format."""

    def test_filename_includes_date_and_task(self, temp_project_dir, sample_result):
        """Test that filename includes date and task ID."""
        handoff_path = create_session_handoff(
            session_id="session-123",
            agent_name="bugfix",
            result=sample_result,
            project_root=temp_project_dir
        )

        filename = handoff_path.name
        date_str = datetime.now().strftime("%Y-%m-%d")

        assert date_str in filename
        assert "BUG-001" in filename
        assert filename.endswith(".md")
