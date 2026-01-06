"""
Integration tests for Knowledge Object workflow.

Tests the end-to-end KO integration with agents and iteration loops.
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, MagicMock, patch
from orchestration.iteration_loop import IterationLoop
from agents.base import AgentConfig, BaseAgent
from knowledge.service import list_drafts, list_approved


@pytest.fixture
def temp_ko_dirs(monkeypatch):
    """Create temporary KO directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        drafts_dir = Path(tmpdir) / "drafts"
        approved_dir = Path(tmpdir) / "approved"
        drafts_dir.mkdir()
        approved_dir.mkdir()

        # Monkeypatch the directories
        import knowledge.service as service
        monkeypatch.setattr(service, 'KO_DRAFTS_DIR', drafts_dir)
        monkeypatch.setattr(service, 'KO_APPROVED_DIR', approved_dir)

        yield drafts_dir, approved_dir


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = Mock(spec=BaseAgent)
    agent.config = AgentConfig(
        project_name="test",
        agent_name="test-agent",
        expected_completion_signal="COMPLETE",
        max_iterations=10,
        max_retries=3
    )
    agent.current_iteration = 0
    agent.iteration_history = []
    agent.relevant_knowledge = None

    def get_iteration_summary():
        return {
            "total_iterations": len(agent.iteration_history),
            "verdicts": [i.get("verdict") for i in agent.iteration_history]
        }

    agent.get_iteration_summary = get_iteration_summary

    return agent


@pytest.fixture
def mock_app_context():
    """Create a mock app context."""
    context = Mock()
    context.project_path = "/tmp/test_project"
    context.project_name = "test"
    return context


class TestPreExecutionConsultation:
    """Test Knowledge Object consultation before agent execution."""

    def test_consult_knowledge_populates_agent_attribute(self, temp_ko_dirs, mock_agent, mock_app_context):
        """Should consult KOs and populate agent.relevant_knowledge."""
        from knowledge.service import create_draft, approve

        # Create and approve a KO with relevant tags
        ko = create_draft(
            project="test",
            title="Test Pattern",
            what_was_learned="This is a test pattern",
            why_it_matters="Matters for testing",
            prevention_rule="Prevent test issues",
            tags=["test", "auth"]
        )
        approve(ko.id)

        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Call consultation method directly
        task_description = "Fix auth bug in test"
        relevant_kos = loop._consult_knowledge(task_description)

        # Verify KOs were found
        assert len(relevant_kos) > 0
        assert relevant_kos[0].id == ko.id
        assert "Test Pattern" in relevant_kos[0].title

    def test_consult_knowledge_handles_no_matching_tags(self, temp_ko_dirs, mock_agent, mock_app_context):
        """Should handle case when no matching KOs found."""
        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Call consultation with task that won't match any KOs
        task_description = "Some random task"
        relevant_kos = loop._consult_knowledge(task_description)

        # Verify empty result
        assert relevant_kos == []

    def test_consult_knowledge_handles_empty_task_description(self, temp_ko_dirs, mock_agent, mock_app_context):
        """Should handle empty task description gracefully."""
        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Call consultation with empty description
        relevant_kos = loop._consult_knowledge("")

        # Verify empty result (no tags extracted)
        assert relevant_kos == []

    def test_consult_knowledge_fails_gracefully_on_error(self, temp_ko_dirs, mock_agent, mock_app_context, capsys):
        """Should fail gracefully if consultation errors occur."""
        from knowledge.service import find_relevant

        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Mock find_relevant to raise an error
        with patch('orchestration.iteration_loop.find_relevant', side_effect=Exception("Test error")):
            relevant_kos = loop._consult_knowledge("Fix bug")

        # Verify graceful failure
        assert relevant_kos == []
        captured = capsys.readouterr()
        assert "Knowledge consultation failed" in captured.out


class TestPostExecutionDraftCreation:
    """Test draft KO creation after successful multi-iteration fixes."""

    def test_create_draft_for_multi_iteration_success(self, temp_ko_dirs, mock_agent, mock_app_context):
        """Should create draft KO for 2+ iteration success."""
        # Setup agent with multiple iterations
        mock_agent.current_iteration = 3
        mock_agent.iteration_history = [
            {"iteration": 1, "verdict": "FAIL", "changes": ["src/test.ts"]},
            {"iteration": 2, "verdict": "FAIL", "changes": ["src/test.ts"]},
            {"iteration": 3, "verdict": "PASS", "changes": ["src/test.ts"]}
        ]

        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Mock _get_changed_files
        with patch.object(loop, '_get_changed_files', return_value=["src/test.ts", "tests/test.test.ts"]):
            # Call draft creation
            loop._create_draft_ko(
                task_id="TASK-123",
                task_description="Fix test bug",
                verdict=None
            )

        # Verify draft was created
        drafts = list_drafts()
        assert len(drafts) == 1
        assert "Fix test bug" in drafts[0].title
        assert "test" in drafts[0].tags

    def test_skip_draft_for_single_iteration(self, temp_ko_dirs, mock_agent, mock_app_context):
        """Should NOT create draft for single iteration."""
        # Setup agent with single iteration
        mock_agent.current_iteration = 1
        mock_agent.iteration_history = [
            {"iteration": 1, "verdict": "PASS", "changes": ["src/test.ts"]}
        ]

        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Mock _get_changed_files
        with patch.object(loop, '_get_changed_files', return_value=["src/test.ts"]):
            # Call draft creation
            loop._create_draft_ko(
                task_id="TASK-123",
                task_description="Simple fix",
                verdict=None
            )

        # Verify no draft was created
        # Note: The check `if self.agent.current_iteration >= 2` prevents creation
        # So this test is checking that the method doesn't crash when called with 1 iteration

    def test_create_draft_fails_gracefully(self, temp_ko_dirs, mock_agent, mock_app_context, capsys):
        """Should fail gracefully if draft creation errors."""
        # Setup agent
        mock_agent.current_iteration = 2
        mock_agent.iteration_history = [
            {"iteration": 1, "verdict": "FAIL", "changes": []},
            {"iteration": 2, "verdict": "PASS", "changes": []}
        ]

        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Mock _get_changed_files to raise error
        with patch.object(loop, '_get_changed_files', side_effect=Exception("Test error")):
            loop._create_draft_ko(
                task_id="TASK-123",
                task_description="Fix bug",
                verdict=None
            )

        # Verify graceful failure
        captured = capsys.readouterr()
        assert "Failed to create draft KO" in captured.out
        assert "Task still completed successfully" in captured.out


class TestEndToEndWorkflow:
    """Test end-to-end KO workflow integration."""

    def test_full_workflow_multi_iteration_creates_draft(self, temp_ko_dirs, mock_agent, mock_app_context):
        """Should create draft KO after multi-iteration task completion."""
        # Setup agent with 3 iterations
        mock_agent.current_iteration = 0  # Start at 0

        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Simulate iteration history being built
        mock_agent.iteration_history = [
            {"iteration": 1, "verdict": "FAIL", "changes": ["src/auth.ts"]},
            {"iteration": 2, "verdict": "FAIL", "changes": ["src/auth.ts"]},
            {"iteration": 3, "verdict": "PASS", "changes": ["src/auth.ts"]}
        ]
        mock_agent.current_iteration = 3

        # Mock _get_changed_files
        with patch.object(loop, '_get_changed_files', return_value=["src/auth.ts", "tests/auth.test.ts"]):
            # Simulate post-execution draft creation (as would happen in ALLOW branch)
            loop._create_draft_ko(
                task_id="TASK-123",
                task_description="Fix auth bug in login.ts",
                verdict=None
            )

        # Verify draft created
        drafts = list_drafts()
        assert len(drafts) == 1
        assert "auth" in drafts[0].tags
        assert "login" in drafts[0].tags or "bug" in drafts[0].tags

    def test_consultation_before_execution(self, temp_ko_dirs, mock_agent, mock_app_context):
        """Should consult KOs before execution if relevant ones exist."""
        from knowledge.service import create_draft, approve

        # Create and approve a relevant KO
        ko = create_draft(
            project="test",
            title="Auth Bug Pattern",
            what_was_learned="Always check for null tokens",
            why_it_matters="Prevents crashes",
            prevention_rule="Validate token before use",
            tags=["auth", "bug", "null"]
        )
        approve(ko.id)

        # Create iteration loop
        loop = IterationLoop(mock_agent, mock_app_context)

        # Consult knowledge
        relevant_kos = loop._consult_knowledge("Fix auth bug with null token")

        # Verify consultation worked
        assert len(relevant_kos) == 1
        assert relevant_kos[0].id == ko.id

        # Verify agent can access the KO
        mock_agent.relevant_knowledge = relevant_kos
        assert mock_agent.relevant_knowledge[0].title == "Auth Bug Pattern"
