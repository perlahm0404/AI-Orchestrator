"""
Integration tests for Council Pattern with real components.

These tests verify the full council workflow including:
- KO creation from debates
- Learning pattern extraction
- Effectiveness tracking
- CLI commands

Note: LLM tests require Claude Code CLI (claude.ai subscription).
Tests auto-detect if the 'claude' CLI is available.
"""

import pytest
import shutil
from unittest.mock import patch, MagicMock

# Check if Claude CLI is available
CLAUDE_CLI_AVAILABLE = shutil.which("claude") is not None

from agents.coordinator.council_orchestrator import (
    CouncilOrchestrator,
    DebateResult,
    CostTracker,
)
from agents.coordinator.debate_agent import SimpleDebateAgent
from orchestration.debate_context import Position
from orchestration.council_ko_integration import (
    create_ko_from_debate,
    should_create_ko,
)
from agents.coordinator.debate_learning import DebateLearner, LearnedPattern
from agents.coordinator.debate_metrics import MetricsCollector


class TestCouncilKOIntegration:
    """Test Knowledge Object creation from council debates."""

    @pytest.fixture
    def sample_debate_result(self) -> DebateResult:
        """Create a sample debate result for testing."""
        from orchestration.debate_context import Argument

        arguments = [
            Argument(
                agent_id="cost_analyst",
                perspective="cost",
                position=Position.SUPPORT,
                reasoning="Open source, no licensing fees",
                evidence=["GitHub - Apache 2.0 license"],
                confidence=0.8,
                round_number=1,
            ),
            Argument(
                agent_id="integration_analyst",
                perspective="integration",
                position=Position.SUPPORT,
                reasoning="Good documentation, moderate complexity",
                evidence=["Official docs"],
                confidence=0.75,
                round_number=1,
            ),
            Argument(
                agent_id="security_analyst",
                perspective="security",
                position=Position.NEUTRAL,
                reasoning="No critical CVEs, needs config review",
                evidence=["Security advisories"],
                confidence=0.7,
                round_number=1,
            ),
        ]

        return DebateResult(
            council_id="COUNCIL-TEST-001",
            topic="Should we adopt LlamaIndex for RAG?",
            recommendation="ADOPT",
            confidence=0.75,
            vote_breakdown={"SUPPORT": 2, "NEUTRAL": 1, "OPPOSE": 0},
            key_considerations=[
                "Open source with Apache license",
                "Good documentation",
                "Security review recommended",
            ],
            arguments=arguments,
            duration_seconds=45.5,
            manifest_path=".aibrain/councils/COUNCIL-TEST-001/manifest.jsonl",
            cost_summary={"total_cost": 0.50},
        )

    def test_should_create_ko_for_valid_debate(self, sample_debate_result):
        """Valid debates should create KOs."""
        assert should_create_ko(sample_debate_result) is True

    def test_should_not_create_ko_for_low_confidence(self, sample_debate_result):
        """Low confidence debates should not create KOs."""
        sample_debate_result.confidence = 0.2
        assert should_create_ko(sample_debate_result) is False

    def test_should_not_create_ko_for_test_councils(self, sample_debate_result):
        """Test councils should not create KOs."""
        sample_debate_result.council_id = "TEST-COUNCIL-001"
        assert should_create_ko(sample_debate_result) is False

    def test_create_ko_from_debate(self, sample_debate_result, tmp_path):
        """Create a Knowledge Object from a debate result."""
        # Patch the KO storage directory
        with patch("knowledge.service.KO_DRAFTS_DIR", tmp_path / "drafts"):
            with patch("knowledge.service.KO_APPROVED_DIR", tmp_path / "approved"):
                (tmp_path / "drafts").mkdir()
                (tmp_path / "approved").mkdir()

                ko_id = create_ko_from_debate(
                    sample_debate_result,
                    auto_approve_threshold=0.8  # Won't auto-approve at 0.75
                )

                assert ko_id is not None
                assert ko_id.startswith("KO-")

    def test_high_confidence_auto_approves(self, sample_debate_result, tmp_path):
        """High confidence debates auto-approve the KO."""
        sample_debate_result.confidence = 0.9

        with patch("knowledge.service.KO_DRAFTS_DIR", tmp_path / "drafts"):
            with patch("knowledge.service.KO_APPROVED_DIR", tmp_path / "approved"):
                (tmp_path / "drafts").mkdir()
                (tmp_path / "approved").mkdir()

                ko_id = create_ko_from_debate(
                    sample_debate_result,
                    auto_approve_threshold=0.8
                )

                # Should be in approved directory (auto-approved)
                approved_files = list((tmp_path / "approved").glob("*.md"))
                assert len(approved_files) == 1


class TestCouncilLearning:
    """Test debate learning integration."""

    @pytest.fixture
    def learner(self, tmp_path):
        """Create a debate learner with test storage."""
        return DebateLearner(storage_dir=tmp_path / "patterns")

    @pytest.fixture
    def sample_debate_result(self):
        """Create a mock debate result."""
        result = MagicMock()
        result.topic = "Should we adopt Redis for caching?"
        result.recommendation = "ADOPT"
        result.confidence = 0.85
        result.key_factors = ["performance", "cost_effective"]
        return result

    def test_learn_pattern_from_debate(self, learner, sample_debate_result):
        """Learner extracts patterns from debates."""
        pattern = learner.learn_from_debate(sample_debate_result)

        assert pattern is not None
        # Pattern is extracted from topic keywords (caching or redis)
        assert pattern.topic_pattern.startswith("*")
        assert pattern.recommendation == "ADOPT"
        assert pattern.confidence == 0.85

    def test_find_similar_patterns(self, learner, sample_debate_result):
        """Learner finds similar patterns for new topics."""
        # Learn from one debate - pattern will be *caching*
        learner.learn_from_debate(sample_debate_result)

        # Search for similar - should match on caching keyword
        matches = learner.find_similar("Should we implement caching for session storage?")

        assert len(matches) >= 1

    def test_pattern_persistence(self, tmp_path):
        """Patterns persist across learner instances."""
        storage_dir = tmp_path / "patterns"

        # Create and learn
        learner1 = DebateLearner(storage_dir=storage_dir)
        learner1.add_pattern(LearnedPattern(
            topic_pattern="*postgres*",
            recommendation="ADOPT",
            confidence=0.8,
            success_rate=0.9,
        ))

        # New instance should have pattern
        learner2 = DebateLearner(storage_dir=storage_dir)
        assert learner2.get_pattern("*postgres*") is not None

    def test_outcome_tracking_updates_success_rate(self, learner):
        """Recording outcomes updates pattern success rate."""
        learner.add_pattern(LearnedPattern(
            topic_pattern="*mongodb*",
            recommendation="CONDITIONAL",
            confidence=0.7,
            success_rate=0.0,
        ))

        learner.record_outcome("*mongodb*", success=True)
        learner.record_outcome("*mongodb*", success=True)
        learner.record_outcome("*mongodb*", success=False)

        pattern = learner.get_pattern("*mongodb*")
        assert pattern.outcome_count == 3
        assert 0.6 <= pattern.success_rate <= 0.7


class TestCouncilMetrics:
    """Test debate metrics tracking."""

    @pytest.fixture
    def collector(self, tmp_path):
        """Create a metrics collector with test storage."""
        return MetricsCollector(storage_dir=tmp_path / "metrics")

    def test_record_and_retrieve_debate(self, collector):
        """Record and retrieve debate metrics."""
        collector.record_debate(
            debate_id="COUNCIL-001",
            topic="Test topic",
            recommendation="ADOPT",
            confidence=0.85,
        )

        stats = collector.get_stats()
        assert stats["total_debates"] == 1

    def test_calculate_accuracy_with_outcomes(self, collector):
        """Calculate accuracy from recorded outcomes."""
        # Record debates
        for i in range(5):
            collector.record_debate(
                debate_id=f"COUNCIL-{i:03d}",
                topic=f"Topic {i}",
                recommendation="ADOPT",
                confidence=0.8,
            )
            collector.record_outcome(
                debate_id=f"COUNCIL-{i:03d}",
                recommendation_followed=True,
                outcome_success=(i < 4),  # 4 success, 1 failure
            )

        accuracy = collector.calculate_accuracy()
        assert accuracy == 0.8  # 4/5

    def test_confidence_calibration(self, collector):
        """Test confidence calibration tracking."""
        # High confidence debates
        for i in range(3):
            collector.record_debate(
                debate_id=f"HIGH-{i}",
                topic=f"Topic {i}",
                recommendation="ADOPT",
                confidence=0.9,
            )
            collector.record_outcome(f"HIGH-{i}", True, outcome_success=True)

        # Low confidence debates
        for i in range(3):
            collector.record_debate(
                debate_id=f"LOW-{i}",
                topic=f"Topic {i}",
                recommendation="CONDITIONAL",
                confidence=0.6,
            )
            collector.record_outcome(f"LOW-{i}", True, outcome_success=(i < 1))

        calibration = collector.get_calibration()
        assert calibration["high_confidence_accuracy"] == 1.0
        assert calibration["low_confidence_accuracy"] < 0.5


class TestCouncilOrchestratorIntegration:
    """Test full council orchestrator workflow."""

    def _make_agent_factory(self, position, reasoning, confidence):
        """Create a simple agent factory."""
        def factory(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=position,
                reasoning=reasoning,
                evidence=["Test evidence"],
                confidence=confidence,
            )
        return factory

    @pytest.mark.asyncio
    async def test_full_debate_with_learning(self, tmp_path):
        """Run a full debate with learning enabled."""
        agent_types = {
            "cost": self._make_agent_factory(
                Position.SUPPORT, "Cost effective", 0.8
            ),
            "integration": self._make_agent_factory(
                Position.SUPPORT, "Easy to integrate", 0.75
            ),
        }

        # Patch storage directories
        with patch("agents.coordinator.debate_learning.DebateLearner") as MockLearner:
            mock_learner = MagicMock()
            mock_learner.learn_from_debate.return_value = LearnedPattern(
                topic_pattern="*test*",
                recommendation="ADOPT",
                confidence=0.8,
            )
            MockLearner.return_value = mock_learner

            council = CouncilOrchestrator(
                topic="Should we adopt TestLib?",
                agent_types=agent_types,
                rounds=2,
                create_ko=False,  # Disable KO for this test
                enable_learning=True,
            )

            result = await council.run_debate()

            assert result.recommendation in ["ADOPT", "CONDITIONAL", "SPLIT"]
            assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_debate_cost_tracking(self):
        """Debate tracks costs per round."""
        agent_types = {
            "cost": self._make_agent_factory(
                Position.SUPPORT, "Cost effective", 0.8
            ),
        }

        council = CouncilOrchestrator(
            topic="Test cost tracking",
            agent_types=agent_types,
            rounds=2,
            create_ko=False,
            enable_learning=False,
        )

        result = await council.run_debate()

        assert result.cost_summary is not None
        assert "total_cost" in result.cost_summary
        assert result.cost_summary["total_cost"] >= 0


class TestCouncilCLI:
    """Test council CLI commands."""

    def test_debate_command_exists(self):
        """Debate command should be available."""
        from cli.commands.council import council_debate_command
        assert callable(council_debate_command)

    def test_learn_command_exists(self):
        """Learn command should be available."""
        from cli.commands.council import council_learn_command
        assert callable(council_learn_command)

    def test_metrics_command_exists(self):
        """Metrics command should be available."""
        from cli.commands.council import council_metrics_command
        assert callable(council_metrics_command)

    def test_perspectives_command_lists_builtin(self):
        """Perspectives command lists built-in perspectives."""
        from agents.coordinator.agent_templates import list_perspectives, BUILTIN_PERSPECTIVES

        perspectives = list_perspectives()

        for name in BUILTIN_PERSPECTIVES:
            assert name in perspectives


@pytest.mark.skipif(
    not CLAUDE_CLI_AVAILABLE,
    reason="Claude CLI not available - install with: npm install -g @anthropic-ai/claude-code"
)
class TestCouncilWithLLM:
    """Tests that require Claude Code CLI (claude.ai subscription)."""

    @pytest.mark.asyncio
    async def test_llm_debate_produces_arguments(self):
        """LLM-powered debate produces real arguments."""
        from cli.commands.council import _create_llm_agents

        agent_types = _create_llm_agents()

        council = CouncilOrchestrator(
            topic="Should we use SQLite for development?",
            agent_types={"cost": agent_types["cost"]},  # Just one agent for speed
            rounds=1,
            max_duration_minutes=5,
            create_ko=False,
            enable_learning=False,
        )

        result = await council.run_debate()

        assert len(result.arguments) > 0
        assert result.cost_summary["total_cost"] > 0
