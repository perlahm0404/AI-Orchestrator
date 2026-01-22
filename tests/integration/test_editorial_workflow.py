"""
Integration tests for end-to-end editorial workflow

Tests:
- End-to-end: Task → Research → Generate → Validate → Approve → Publish
- Interruption & resume (kill mid-pipeline, resume from state)
- Approval gate decisions (APPROVE, REJECT, MODIFY)
- State file cleanup on completion
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import time

from orchestration.content_pipeline import ContentPipeline, PipelineStage
from agents.editorial.editorial_agent import EditorialTask
from orchestration.content_approval import ApprovalDecision


@pytest.fixture
def temp_dir():
    """Create temporary directory for integration tests"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_adapter():
    """Mock application adapter"""
    adapter = Mock()
    adapter.get_context.return_value = Mock(
        project_name="credentialmate",
        project_path="/test/project"
    )
    return adapter


@pytest.fixture
def sample_task():
    """Sample editorial task for integration tests"""
    return EditorialTask(
        task_id="INTEGRATION-001",
        category="integration-test",
        topic="Integration Test Article",
        keywords=["integration", "test"],
        research_sources=["https://example.gov", "https://competitor.com"],
        target_audience="testers",
        target_word_count=1000,
        min_seo_score=50
    )


@pytest.fixture
def pipeline(mock_adapter, temp_dir, monkeypatch):
    """ContentPipeline with temp directories"""
    monkeypatch.setattr(Path, "cwd", lambda: temp_dir)

    pipeline = ContentPipeline(adapter=mock_adapter)
    pipeline.state_dir = temp_dir / ".aibrain"
    pipeline.drafts_dir = temp_dir / "blog" / "credentialmate" / "drafts"
    pipeline.published_dir = temp_dir / "blog" / "credentialmate" / "published"
    pipeline.rejected_dir = temp_dir / ".aibrain" / "rejected"

    pipeline.state_dir.mkdir(parents=True, exist_ok=True)
    pipeline.drafts_dir.mkdir(parents=True, exist_ok=True)
    pipeline.published_dir.mkdir(parents=True, exist_ok=True)
    pipeline.rejected_dir.mkdir(parents=True, exist_ok=True)

    return pipeline


class TestEndToEndWorkflow:
    """Test complete editorial workflow"""

    @patch('orchestration.content_pipeline.BrowserAutomationClient')
    @patch('orchestration.content_pipeline.create_agent')
    @patch('orchestration.content_pipeline.IterationLoop')
    @patch('orchestration.content_pipeline.ContentValidator')
    @patch('builtins.input', return_value='A')  # Auto-approve
    def test_happy_path_workflow(
        self, mock_input, mock_validator_class, mock_loop_class,
        mock_create_agent, mock_browser_client, pipeline, sample_task, temp_dir
    ):
        """
        Full workflow: PREPARATION → RESEARCH → GENERATION → VALIDATION → REVIEW → PUBLICATION → COMPLETE
        """
        # Mock browser automation
        mock_browser = MagicMock()
        mock_browser_client.return_value = mock_browser
        mock_browser.scrape_regulatory_updates.return_value = [{"title": "Update 1"}]
        mock_browser.analyze_competitor_blog.return_value = {"title": "Blog 1"}

        # Mock agent generation
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        mock_loop = MagicMock()
        mock_loop_class.return_value = mock_loop
        mock_loop.run.return_value = Mock(status="completed", iterations=2)

        # Create draft file that IterationLoop would have created
        draft_path = pipeline.drafts_dir / "2026-01-22-integration-test-article.md"
        draft_path.write_text("""---
title: "Integration Test Article"
keywords: ["integration", "test"]
---

# Integration Test Article

Content here.
""")

        # Mock validation
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_verdict = Mock()
        mock_verdict.type = Mock(value="PASS")
        mock_verdict.steps = [
            Mock(step="seo", passed=True, output="SEO score: 75")
        ]
        mock_validator.validate.return_value = mock_verdict

        # Run pipeline
        result = pipeline.run(task=sample_task, non_interactive=False)

        # Assertions
        assert result.status == "completed"
        assert result.seo_score is not None

        # Verify draft was published
        published_files = list(pipeline.published_dir.glob("*.md"))
        assert len(published_files) == 1

        # Verify state file was cleaned up
        state_file = pipeline.state_dir / f"pipeline-{sample_task.task_id}.md"
        assert not state_file.exists()

    @patch('orchestration.content_pipeline.BrowserAutomationClient')
    def test_research_stage_integration(self, mock_browser_client, pipeline, sample_task):
        """Research stage integrates with browser automation"""
        # Mock browser automation
        mock_browser = MagicMock()
        mock_browser_client.return_value = mock_browser
        mock_browser.scrape_regulatory_updates.return_value = [
            {"title": "Regulation Update", "date": "2026-01-15"}
        ]
        mock_browser.analyze_competitor_blog.return_value = {
            "title": "Competitor Article",
            "seo_score": 80
        }

        pipeline.state = Mock(
            task=sample_task,
            research_data=None,
            content_id="TEST-001"
        )

        result = pipeline._stage_research()

        assert result.status == "success"
        assert "research_data" in result.artifacts
        assert len(result.artifacts["research_data"]["regulatory_updates"]) == 1
        assert len(result.artifacts["research_data"]["competitor_analysis"]) == 1

        # Verify session cleanup called
        mock_browser.cleanup_session.assert_called_once()


class TestInterruptionAndResume:
    """Test interruption and resume capability"""

    @patch('orchestration.content_pipeline.BrowserAutomationClient')
    @patch('orchestration.content_pipeline.create_agent')
    @patch('orchestration.content_pipeline.IterationLoop')
    @patch('orchestration.content_pipeline.ContentValidator')
    @patch('builtins.input', return_value='A')
    def test_resume_from_interruption(
        self, mock_input, mock_validator_class, mock_loop_class,
        mock_create_agent, mock_browser_client, pipeline, sample_task, temp_dir
    ):
        """Pipeline resumes from saved state after interruption"""
        # Simulate partial execution - save state at VALIDATION stage
        pipeline.state = Mock(
            content_id=sample_task.task_id,
            current_stage=PipelineStage.VALIDATION,
            iteration=3,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            draft_path=str(temp_dir / "blog/credentialmate/drafts/test.md"),
            seo_score=None,
            validation_issues=[],
            validation_warnings=[],
            stage_history=[
                {"stage": "preparation", "status": "success", "iteration": 1, "duration": 1.0, "errors": [], "warnings": []},
                {"stage": "research", "status": "success", "iteration": 2, "duration": 5.0, "errors": [], "warnings": []},
                {"stage": "generation", "status": "success", "iteration": 3, "duration": 10.0, "errors": [], "warnings": []}
            ],
            research_data={"regulatory_updates": [], "competitor_analysis": []}
        )
        pipeline._save_state()

        # Create draft file
        draft_path = Path(pipeline.state.draft_path)
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text("# Test Article\n\nContent")

        # Mock remaining stages
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_verdict = Mock()
        mock_verdict.type = Mock(value="PASS")
        mock_verdict.steps = [Mock(step="seo", passed=True, output="SEO score: 70")]
        mock_validator.validate.return_value = mock_verdict

        # Resume pipeline
        result = pipeline.run(task=sample_task, resume=True, non_interactive=False)

        # Should resume from VALIDATION stage
        assert result.status == "completed"

        # State file should be cleaned up
        state_file = pipeline.state_dir / f"pipeline-{sample_task.task_id}.md"
        assert not state_file.exists()

    def test_state_file_format(self, pipeline, sample_task, temp_dir):
        """State file has correct Markdown + YAML format"""
        pipeline.state = Mock(
            content_id=sample_task.task_id,
            current_stage=PipelineStage.RESEARCH,
            iteration=2,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            draft_path=None,
            seo_score=None,
            stage_history=[
                {"stage": "preparation", "status": "success", "iteration": 1, "duration": 1.0, "errors": [], "warnings": []}
            ]
        )

        pipeline._save_state()

        state_file = pipeline.state_dir / f"pipeline-{sample_task.task_id}.md"
        content = state_file.read_text()

        # Check YAML frontmatter
        assert "---" in content
        assert "content_id:" in content
        assert "current_stage:" in content

        # Check Markdown body
        assert "# Pipeline State:" in content
        assert "## Stage History" in content


class TestApprovalGateDecisions:
    """Test approval gate decision handling"""

    @patch('orchestration.content_pipeline.BrowserAutomationClient')
    @patch('orchestration.content_pipeline.create_agent')
    @patch('orchestration.content_pipeline.IterationLoop')
    @patch('orchestration.content_pipeline.ContentValidator')
    @patch('builtins.input', return_value='R')  # Reject
    def test_reject_decision_moves_to_rejected(
        self, mock_input, mock_validator_class, mock_loop_class,
        mock_create_agent, mock_browser_client, pipeline, sample_task, temp_dir
    ):
        """REJECT decision moves draft to rejected directory"""
        # Setup mocks for stages before REVIEW
        mock_browser = MagicMock()
        mock_browser_client.return_value = mock_browser
        mock_browser.scrape_regulatory_updates.return_value = []
        mock_browser.analyze_competitor_blog.return_value = {}

        mock_loop = MagicMock()
        mock_loop_class.return_value = mock_loop
        mock_loop.run.return_value = Mock(status="completed")

        draft_path = pipeline.drafts_dir / "test-reject.md"
        draft_path.write_text("# Test")

        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_verdict = Mock(type=Mock(value="PASS"), steps=[Mock(step="seo", passed=True, output="SEO score: 60")])
        mock_validator.validate.return_value = mock_verdict

        pipeline.state = Mock(
            content_id=sample_task.task_id,
            current_stage=PipelineStage.REVIEW,
            iteration=5,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            draft_path=str(draft_path),
            seo_score=60,
            validation_issues=[],
            validation_warnings=[],
            stage_history=[]
        )

        result = pipeline._stage_review(non_interactive=False)

        # Should be blocked (rejected)
        assert result.status == "blocked"

        # Draft should be moved to rejected/
        rejected_files = list(pipeline.rejected_dir.glob("*.md"))
        assert len(rejected_files) == 1

    @patch('orchestration.content_pipeline.BrowserAutomationClient')
    @patch('orchestration.content_pipeline.create_agent')
    @patch('orchestration.content_pipeline.IterationLoop')
    @patch('orchestration.content_pipeline.ContentValidator')
    @patch('builtins.input', side_effect=['M', 'Needs more examples'])  # Modify
    def test_modify_decision_retries_generation(
        self, mock_input, mock_validator_class, mock_loop_class,
        mock_create_agent, mock_browser_client, pipeline, sample_task, temp_dir
    ):
        """MODIFY decision triggers retry to GENERATION stage"""
        draft_path = pipeline.drafts_dir / "test-modify.md"
        draft_path.write_text("# Test")

        pipeline.state = Mock(
            content_id=sample_task.task_id,
            current_stage=PipelineStage.REVIEW,
            iteration=3,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            draft_path=str(draft_path),
            seo_score=55,
            validation_issues=["Low keyword density"],
            validation_warnings=[],
            stage_history=[]
        )

        result = pipeline._stage_review(non_interactive=False)

        # Should be failed (triggers retry)
        assert result.status == "failed"
        assert "Modifications requested" in result.errors

        # Notes should be captured
        assert result.warnings[0] == "Needs more examples"


class TestValidationIntegration:
    """Test ContentValidator integration"""

    @patch('orchestration.content_pipeline.ContentValidator')
    def test_validation_pass_proceeds(self, mock_validator_class, pipeline, sample_task, temp_dir):
        """PASS verdict proceeds to REVIEW"""
        draft_path = temp_dir / "blog/credentialmate/drafts/test-pass.md"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text("# Test Article\n\nContent")

        pipeline.state = Mock(
            draft_path=str(draft_path),
            seo_score=None,
            validation_issues=[],
            validation_warnings=[],
            task=sample_task
        )

        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_verdict = Mock()
        mock_verdict.type = Mock(value="PASS")
        mock_verdict.steps = [Mock(step="seo", passed=True, output="SEO score: 85")]
        mock_validator.validate.return_value = mock_verdict

        result = pipeline._stage_validation()

        assert result.status == "success"
        assert pipeline.state.seo_score == 85

    @patch('orchestration.content_pipeline.ContentValidator')
    def test_validation_blocked_escalates(self, mock_validator_class, pipeline, sample_task, temp_dir):
        """BLOCKED verdict escalates to human"""
        draft_path = temp_dir / "blog/credentialmate/drafts/test-blocked.md"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text("# Test")

        pipeline.state = Mock(
            draft_path=str(draft_path),
            seo_score=None,
            validation_issues=[],
            validation_warnings=[],
            task=sample_task
        )

        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_verdict = Mock()
        mock_verdict.type = Mock(value="BLOCKED")
        mock_verdict.reason = "Missing frontmatter"
        mock_verdict.steps = []
        mock_validator.validate.return_value = mock_verdict

        result = pipeline._stage_validation()

        assert result.status == "blocked"
        assert "Missing frontmatter" in result.errors

    @patch('orchestration.content_pipeline.ContentValidator')
    def test_validation_fail_retries(self, mock_validator_class, pipeline, sample_task, temp_dir):
        """FAIL verdict triggers retry"""
        draft_path = temp_dir / "blog/credentialmate/drafts/test-fail.md"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text("# Test")

        pipeline.state = Mock(
            draft_path=str(draft_path),
            seo_score=None,
            validation_issues=[],
            validation_warnings=[],
            task=sample_task
        )

        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_verdict = Mock()
        mock_verdict.type = Mock(value="FAIL")
        mock_verdict.steps = [
            Mock(step="seo", passed=False, output="SEO score: 35")
        ]
        mock_validator.validate.return_value = mock_verdict

        result = pipeline._stage_validation()

        assert result.status == "failed"
        assert len(result.errors) > 0
        assert pipeline.state.seo_score == 35
