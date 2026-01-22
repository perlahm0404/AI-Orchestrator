"""
Unit tests for ContentPipeline - 7-stage editorial workflow orchestrator

Tests:
- Stage transitions (PREPARATION → RESEARCH → ... → COMPLETE)
- Decision tree logic (PROCEED, RETRY, ASK_HUMAN, ABORT)
- State persistence (write, read, cleanup)
- Resume from saved state
- Error handling (missing files, invalid state)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from orchestration.content_pipeline import (
    ContentPipeline,
    PipelineStage,
    StageDecision,
    StageResult,
    PipelineState,
    PipelineResult
)
from agents.editorial.editorial_agent import EditorialTask


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
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
    """Sample editorial task"""
    return EditorialTask(
        task_id="TEST-001",
        category="test",
        topic="Test Topic",
        keywords=["test", "keyword"],
        research_sources=["https://example.com"],
        target_audience="testers",
        target_word_count=1000,
        min_seo_score=50
    )


@pytest.fixture
def pipeline(mock_adapter, temp_dir, monkeypatch):
    """ContentPipeline instance with mocked paths"""
    # Patch Path.cwd() to return temp_dir
    monkeypatch.setattr(Path, "cwd", lambda: temp_dir)

    pipeline = ContentPipeline(adapter=mock_adapter)
    pipeline.state_dir = temp_dir / ".aibrain"
    pipeline.drafts_dir = temp_dir / "blog" / "credentialmate" / "drafts"
    pipeline.published_dir = temp_dir / "blog" / "credentialmate" / "published"
    pipeline.rejected_dir = temp_dir / ".aibrain" / "rejected"

    # Ensure directories exist
    pipeline.state_dir.mkdir(parents=True, exist_ok=True)
    pipeline.drafts_dir.mkdir(parents=True, exist_ok=True)
    pipeline.published_dir.mkdir(parents=True, exist_ok=True)
    pipeline.rejected_dir.mkdir(parents=True, exist_ok=True)

    return pipeline


class TestPipelineStageTransitions:
    """Test stage-by-stage transitions"""

    def test_preparation_stage_success(self, pipeline, sample_task):
        """PREPARATION stage with valid task"""
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.PREPARATION,
            iteration=0,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task
        )

        result = pipeline._stage_preparation()

        assert result.stage == PipelineStage.PREPARATION
        assert result.status == "success"
        assert len(result.errors) == 0

    def test_preparation_stage_missing_fields(self, pipeline):
        """PREPARATION stage with missing task fields"""
        invalid_task = EditorialTask(
            task_id="",  # Missing
            category="test",
            topic="",  # Missing
            keywords=[],  # Missing
            research_sources=[],
            target_audience="testers"
        )

        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.PREPARATION,
            iteration=0,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=invalid_task
        )

        result = pipeline._stage_preparation()

        assert result.stage == PipelineStage.PREPARATION
        assert result.status == "failed"
        assert len(result.errors) == 3  # task_id, topic, keywords


class TestPipelineDecisionLogic:
    """Test decision tree logic"""

    def test_decision_success_proceeds(self, pipeline):
        """SUCCESS status → PROCEED decision"""
        result = StageResult(
            stage=PipelineStage.PREPARATION,
            status="success",
            artifacts={},
            errors=[],
            warnings=[]
        )

        decision = pipeline._make_decision(result)
        assert decision == StageDecision.PROCEED

    def test_decision_blocked_asks_human(self, pipeline):
        """BLOCKED status → ASK_HUMAN decision"""
        result = StageResult(
            stage=PipelineStage.VALIDATION,
            status="blocked",
            artifacts={},
            errors=["Critical violation"],
            warnings=[]
        )

        decision = pipeline._make_decision(result)
        assert decision == StageDecision.ASK_HUMAN

    def test_decision_failed_with_budget_retries(self, pipeline, sample_task):
        """FAIL status + budget available → RETRY decision"""
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.RESEARCH,
            iteration=0,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            stage_history=[]  # No retries yet
        )

        result = StageResult(
            stage=PipelineStage.RESEARCH,
            status="failed",
            artifacts={},
            errors=["Network timeout"],
            warnings=[]
        )

        decision = pipeline._make_decision(result)
        assert decision == StageDecision.RETRY

    def test_decision_failed_budget_exhausted_asks_human(self, pipeline, sample_task):
        """FAIL status + budget exhausted → ASK_HUMAN decision"""
        # Simulate 5 failed research attempts (budget is 5)
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.RESEARCH,
            iteration=5,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            stage_history=[
                {"stage": "research", "status": "failed"},
                {"stage": "research", "status": "failed"},
                {"stage": "research", "status": "failed"},
                {"stage": "research", "status": "failed"},
                {"stage": "research", "status": "failed"}
            ]
        )

        result = StageResult(
            stage=PipelineStage.RESEARCH,
            status="failed",
            artifacts={},
            errors=["Network timeout"],
            warnings=[]
        )

        decision = pipeline._make_decision(result)
        assert decision == StageDecision.ASK_HUMAN


class TestPipelineStatePersistence:
    """Test state save/load/cleanup"""

    def test_save_state_creates_file(self, pipeline, sample_task, temp_dir):
        """State file is created with correct format"""
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.RESEARCH,
            iteration=2,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            draft_path=str(temp_dir / "draft.md"),
            seo_score=65
        )

        pipeline._save_state()

        state_file = pipeline.state_dir / "pipeline-TEST-001.md"
        assert state_file.exists()

        content = state_file.read_text()
        assert "content_id: TEST-001" in content
        assert "current_stage: research" in content
        assert "iteration: 2" in content
        assert "seo_score: 65" in content

    def test_load_state_restores_pipeline(self, pipeline, sample_task, temp_dir):
        """State can be loaded from file"""
        # First save state
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.VALIDATION,
            iteration=3,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            draft_path=str(temp_dir / "draft.md"),
            seo_score=72
        )
        pipeline._save_state()

        # Load state
        loaded_state = pipeline._load_state("TEST-001")

        assert loaded_state is not None
        assert loaded_state.content_id == "TEST-001"
        assert loaded_state.current_stage == PipelineStage.VALIDATION
        assert loaded_state.iteration == 3
        assert loaded_state.seo_score == 72

    def test_load_state_nonexistent_returns_none(self, pipeline):
        """Loading nonexistent state returns None"""
        loaded_state = pipeline._load_state("NONEXISTENT")
        assert loaded_state is None

    def test_cleanup_state_removes_file(self, pipeline, sample_task):
        """Cleanup removes state file"""
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.COMPLETE,
            iteration=5,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task
        )
        pipeline._save_state()

        state_file = pipeline.state_dir / "pipeline-TEST-001.md"
        assert state_file.exists()

        pipeline._cleanup_state()
        assert not state_file.exists()


class TestPipelineResume:
    """Test resume capability"""

    @patch('orchestration.content_pipeline.ContentPipeline._execute_stage')
    def test_resume_from_saved_state(self, mock_execute, pipeline, sample_task, temp_dir):
        """Pipeline resumes from saved state"""
        # Save a state at VALIDATION stage
        saved_state = PipelineState(
            content_id="TEST-RESUME",
            current_stage=PipelineStage.VALIDATION,
            iteration=3,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            draft_path=str(temp_dir / "draft.md")
        )
        pipeline.state = saved_state
        pipeline._save_state()

        # Mock execute_stage to return success for remaining stages
        mock_execute.side_effect = [
            StageResult(stage=PipelineStage.VALIDATION, status="success", artifacts={"verdict": Mock(type=Mock(value="PASS")), "seo_score": 75}),
            StageResult(stage=PipelineStage.REVIEW, status="success", artifacts={"approved": True}),
            StageResult(stage=PipelineStage.PUBLICATION, status="success", artifacts={"published_path": "/test/published.md"})
        ]

        # Resume pipeline
        result = pipeline.run(task=sample_task, resume=True, non_interactive=True)

        # Should have resumed from VALIDATION
        assert result.status == "completed"
        # execute_stage should be called for VALIDATION, REVIEW, PUBLICATION (3 times)
        assert mock_execute.call_count >= 3


class TestPipelineErrorHandling:
    """Test error handling scenarios"""

    def test_max_iterations_reached(self, pipeline, sample_task):
        """Pipeline stops when max iterations reached"""
        with patch.object(pipeline, '_execute_stage') as mock_execute:
            # Always return failed
            mock_execute.return_value = StageResult(
                stage=PipelineStage.RESEARCH,
                status="failed",
                errors=["Persistent error"]
            )

            result = pipeline.run(task=sample_task, max_iterations=3)

            assert result.status == "failed"
            assert "Max iterations" in result.reason

    def test_blocked_status_stops_pipeline(self, pipeline, sample_task):
        """BLOCKED status stops pipeline and returns blocked result"""
        with patch.object(pipeline, '_execute_stage') as mock_execute:
            mock_execute.side_effect = [
                StageResult(stage=PipelineStage.PREPARATION, status="success"),
                StageResult(stage=PipelineStage.RESEARCH, status="blocked", errors=["Guardrail violation"])
            ]

            result = pipeline.run(task=sample_task)

            assert result.status == "blocked"
            assert "RESEARCH" in result.reason


class TestPipelineHelperMethods:
    """Test helper methods"""

    def test_extract_state_from_url_ca_gov(self, pipeline):
        """Extract California from ca.gov URL"""
        url = "https://www.rn.ca.gov/regulations/"
        state = pipeline._extract_state_from_url(url)
        assert state == "California"

    def test_extract_state_from_url_ny_gov(self, pipeline):
        """Extract New York from ny.gov URL"""
        url = "https://www.op.nysed.gov/professions/nursing"
        state = pipeline._extract_state_from_url(url)
        assert state == "New York"

    def test_extract_state_from_url_unknown(self, pipeline):
        """Unknown URL returns 'Unknown'"""
        url = "https://example.com/nursing"
        state = pipeline._extract_state_from_url(url)
        assert state == "Unknown"

    def test_build_generation_prompt_includes_task_details(self, pipeline, sample_task):
        """Generation prompt includes all task details"""
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.GENERATION,
            iteration=0,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task
        )

        prompt = pipeline._build_generation_prompt()

        assert "Test Topic" in prompt
        assert "testers" in prompt
        assert "test, keyword" in prompt
        assert "1000" in prompt
        assert "50" in prompt

    def test_build_generation_prompt_includes_research_data(self, pipeline, sample_task):
        """Generation prompt includes research data if available"""
        pipeline.state = PipelineState(
            content_id="TEST-001",
            current_stage=PipelineStage.GENERATION,
            iteration=0,
            max_iterations=20,
            started_at="2026-01-22T10:00:00",
            task=sample_task,
            research_data={
                "regulatory_updates": [{"title": "Update 1"}],
                "competitor_analysis": [{"title": "Competitor Post", "seo_score": 85}]
            }
        )

        prompt = pipeline._build_generation_prompt()

        assert "Research Data" in prompt
        assert "Regulatory Updates" in prompt
        assert "Competitor Analysis" in prompt
