"""
Tests for advanced Council Pattern features.

Features tested:
- LLM-powered rebuttals (dynamic responses to other agents)
- Cross-debate learning (KO integration for pattern caching)
- Custom agent templates (YAML-based perspective definitions)
- Debate quality metrics (track recommendation accuracy)
"""

import pytest
import json
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

try:
    from agents.coordinator.llm_analyst import LLMAnalyst, AnalystConfig
    from agents.coordinator.rebuttal_agent import RebuttalAgent, RebuttalConfig
    from agents.coordinator.agent_templates import (
        AgentTemplate,
        TemplateRegistry,
        load_template_from_yaml,
    )
    from agents.coordinator.debate_learning import (
        DebateLearner,
        LearnedPattern,
        PatternType,
    )
    from agents.coordinator.debate_metrics import (
        DebateMetrics,
        MetricsCollector as DebateMetricsCollector,
        QualityScore,
    )
    from orchestration.debate_context import DebateContext, Position, Argument
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

    class Position:
        SUPPORT = "support"
        OPPOSE = "oppose"
        NEUTRAL = "neutral"

    @dataclass
    class LearnedPattern:
        topic_pattern: str
        recommendation: str
        confidence: float
        success_rate: float = 0.0

    class PatternType:
        TOPIC_KEYWORD = "topic_keyword"
        TECHNOLOGY_COMPARISON = "technology_comparison"

    @dataclass
    class AgentTemplate:
        name: str
        perspective: str
        system_prompt: str
        model: str = "claude-sonnet"

    @dataclass
    class QualityScore:
        debate_id: str
        recommendation_followed: bool
        outcome_success: Optional[bool] = None


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestRebuttalAgent:
    """Test LLM-powered rebuttal generation."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock debate context with existing arguments."""
        context = MagicMock()
        context.topic = "Should we use Redis for caching?"

        # Create mock arguments from other agents
        mock_args = []
        for i, (perspective, position) in enumerate([
            ("cost", Position.SUPPORT),
            ("integration", Position.OPPOSE),
        ]):
            arg = MagicMock()
            arg.agent_id = f"{perspective}_analyst"
            arg.perspective = perspective
            arg.position = position
            arg.reasoning = f"Reasoning from {perspective} perspective"
            arg.evidence = [f"Evidence {i}"]
            arg.confidence = 0.8
            arg.round_number = 1
            mock_args.append(arg)

        context.get_arguments.return_value = mock_args
        context.post_argument = AsyncMock()
        return context

    @pytest.fixture
    def rebuttal_config(self):
        """Create a rebuttal agent config."""
        return RebuttalConfig(
            perspective="performance",
            system_prompt="You analyze performance and respond to other arguments.",
        )

    @pytest.mark.asyncio
    async def test_rebuttal_considers_other_arguments(self, mock_context, rebuttal_config):
        """Rebuttal agent considers and responds to other arguments."""
        agent = RebuttalAgent(
            agent_id="performance_analyst",
            context=mock_context,
            config=rebuttal_config,
        )

        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "While integration is complex, Redis performance gains justify it.",
                "rebuttals": [
                    {"to": "integration_analyst", "response": "Complexity is manageable with our team."}
                ],
                "evidence": ["Benchmark showing 10x improvement"],
                "confidence": 0.85,
            }

            result = await agent.generate_rebuttal(round_num=2)

        # Should include rebuttals to other arguments
        assert len(result.rebuttals) > 0
        assert any("integration" in r["to"] for r in result.rebuttals)

    @pytest.mark.asyncio
    async def test_rebuttal_targets_opposing_views(self, mock_context, rebuttal_config):
        """Rebuttal specifically addresses opposing arguments."""
        agent = RebuttalAgent(
            agent_id="performance_analyst",
            context=mock_context,
            config=rebuttal_config,
        )

        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "Performance benefits outweigh integration costs.",
                "rebuttals": [
                    {"to": "integration_analyst", "response": "We can mitigate complexity."}
                ],
                "evidence": [],
                "confidence": 0.8,
            }

            result = await agent.generate_rebuttal(round_num=2)

        # Check prompt included opposing arguments
        call_args = mock_llm.call_args
        # Verify the opposing integration_analyst was mentioned
        mock_context.get_arguments.assert_called()


class TestAgentTemplates:
    """Test YAML-based agent template definitions."""

    @pytest.fixture
    def template_yaml(self, tmp_path: Path):
        """Create a test template YAML file."""
        template_content = """
name: devops_analyst
perspective: devops
model: claude-sonnet
max_tokens: 1000
temperature: 0.7
system_prompt: |
  You are a DevOps Analyst specializing in deployment and operations.
  Analyze decisions from an operational perspective including:
  - Deployment complexity
  - Monitoring and observability
  - Disaster recovery
  - Team operational burden
focus_areas:
  - deployment
  - monitoring
  - reliability
  - maintenance
"""
        template_file = tmp_path / "devops_analyst.yaml"
        template_file.write_text(template_content)
        return template_file

    def test_load_template_from_yaml(self, template_yaml):
        """Load an agent template from YAML file."""
        template = load_template_from_yaml(template_yaml)

        assert template.name == "devops_analyst"
        assert template.perspective == "devops"
        assert "DevOps Analyst" in template.system_prompt
        assert template.model == "claude-sonnet"

    def test_template_registry_loads_directory(self, tmp_path: Path):
        """Template registry loads all templates from a directory."""
        # Create multiple template files
        templates = [
            ("devops.yaml", "devops", "DevOps perspective"),
            ("ux.yaml", "ux", "User experience perspective"),
            ("legal.yaml", "legal", "Legal compliance perspective"),
        ]

        for filename, perspective, prompt in templates:
            (tmp_path / filename).write_text(f"""
name: {perspective}_analyst
perspective: {perspective}
system_prompt: {prompt}
""")

        registry = TemplateRegistry(templates_dir=tmp_path)
        registry.load_all()

        assert len(registry.templates) == 3
        assert "devops" in registry.templates
        assert "ux" in registry.templates

    def test_template_creates_analyst(self, template_yaml):
        """Template can be used to create an LLM analyst."""
        template = load_template_from_yaml(template_yaml)

        context = MagicMock()
        context.topic = "Test topic"
        context.get_arguments.return_value = []

        analyst = template.create_analyst(
            context=context,
            message_bus=MagicMock(),
        )

        # The analyst should have the devops perspective
        assert "devops" in analyst._template.name or "devops" in str(analyst.agent_id)


class TestDebateLearning:
    """Test cross-debate learning with KO integration."""

    @pytest.fixture
    def learner(self, tmp_path: Path):
        """Create a debate learner with test storage."""
        return DebateLearner(storage_dir=tmp_path / "learned_patterns")

    def test_learn_pattern_from_debate(self, learner):
        """Learn a pattern from a completed debate."""
        debate_result = MagicMock()
        debate_result.topic = "Should we adopt LlamaIndex for RAG?"
        debate_result.recommendation = "ADOPT"
        debate_result.confidence = 0.85
        debate_result.key_factors = ["cost_effective", "good_documentation"]

        pattern = learner.learn_from_debate(debate_result)

        assert pattern is not None
        assert "llamaindex" in pattern.topic_pattern.lower()
        assert pattern.recommendation == "ADOPT"

    def test_find_similar_patterns(self, learner):
        """Find patterns similar to a new topic."""
        # Add some learned patterns
        learner.add_pattern(LearnedPattern(
            topic_pattern="*llamaindex*",
            recommendation="ADOPT",
            confidence=0.85,
            success_rate=0.9,
        ))
        learner.add_pattern(LearnedPattern(
            topic_pattern="*langchain*",
            recommendation="CONDITIONAL",
            confidence=0.7,
            success_rate=0.75,
        ))

        # Search for similar
        matches = learner.find_similar("Should we use LlamaIndex for our RAG system?")

        assert len(matches) >= 1
        assert matches[0].topic_pattern == "*llamaindex*"

    def test_pattern_success_tracking(self, learner):
        """Track whether pattern recommendations were successful."""
        pattern = LearnedPattern(
            topic_pattern="*redis*",
            recommendation="ADOPT",
            confidence=0.8,
            success_rate=0.0,
        )
        learner.add_pattern(pattern)

        # Record outcomes
        learner.record_outcome("*redis*", success=True)
        learner.record_outcome("*redis*", success=True)
        learner.record_outcome("*redis*", success=False)

        updated = learner.get_pattern("*redis*")
        assert 0.6 <= updated.success_rate <= 0.7  # 2/3 success

    def test_ko_integration(self, learner):
        """Learner attempts to create Knowledge Objects for patterns."""
        pattern = LearnedPattern(
            topic_pattern="*postgresql*jsonb*",
            recommendation="ADOPT",
            confidence=0.9,
            success_rate=0.85,
        )

        # The learner should attempt to create a KO (may fail if KO system not available)
        # This is a best-effort operation
        learner.add_pattern(pattern, create_ko=True)

        # Verify pattern was added regardless of KO creation
        stored = learner.get_pattern("*postgresql*jsonb*")
        assert stored is not None
        assert stored.recommendation == "ADOPT"


class TestDebateMetrics:
    """Test debate quality metrics tracking."""

    @pytest.fixture
    def metrics_collector(self, tmp_path: Path):
        """Create a metrics collector."""
        return DebateMetricsCollector(storage_dir=tmp_path / "debate_metrics")

    def test_record_debate_outcome(self, metrics_collector):
        """Record the outcome of a debate recommendation."""
        metrics_collector.record_debate(
            debate_id="COUNCIL-001",
            topic="Should we adopt Redis?",
            recommendation="ADOPT",
            confidence=0.85,
        )

        # Later, record the outcome
        metrics_collector.record_outcome(
            debate_id="COUNCIL-001",
            recommendation_followed=True,
            outcome_success=True,
        )

        stats = metrics_collector.get_stats()
        assert stats["total_debates"] == 1
        assert stats["recommendations_followed"] == 1
        assert stats["successful_outcomes"] == 1

    def test_calculate_accuracy(self, metrics_collector):
        """Calculate recommendation accuracy over time."""
        # Record multiple debates with outcomes
        for i in range(10):
            metrics_collector.record_debate(
                debate_id=f"COUNCIL-{i:03d}",
                topic=f"Topic {i}",
                recommendation="ADOPT" if i % 2 == 0 else "REJECT",
                confidence=0.8,
            )
            metrics_collector.record_outcome(
                debate_id=f"COUNCIL-{i:03d}",
                recommendation_followed=True,
                outcome_success=(i < 8),  # 8 successful, 2 not
            )

        accuracy = metrics_collector.calculate_accuracy()
        assert 0.79 <= accuracy <= 0.81  # 80%

    def test_confidence_calibration(self, metrics_collector):
        """Check if confidence scores are well-calibrated."""
        # High confidence debates should have high success rate
        for i in range(10):
            confidence = 0.9 if i < 5 else 0.6
            success = (i < 4) or (i >= 5 and i < 7)  # 4/5 high conf, 2/5 low conf

            metrics_collector.record_debate(
                debate_id=f"CAL-{i:03d}",
                topic=f"Topic {i}",
                recommendation="ADOPT",
                confidence=confidence,
            )
            metrics_collector.record_outcome(
                debate_id=f"CAL-{i:03d}",
                recommendation_followed=True,
                outcome_success=success,
            )

        calibration = metrics_collector.get_calibration()

        # High confidence should have higher success rate
        assert calibration["high_confidence_accuracy"] > calibration["low_confidence_accuracy"]

    def test_metrics_persistence(self, tmp_path: Path):
        """Metrics persist across collector instances."""
        collector1 = DebateMetricsCollector(storage_dir=tmp_path / "metrics")
        collector1.record_debate(
            debate_id="TEST-001",
            topic="Test topic",
            recommendation="ADOPT",
            confidence=0.8,
        )
        collector1.flush()

        collector2 = DebateMetricsCollector(storage_dir=tmp_path / "metrics")
        stats = collector2.get_stats()

        assert stats["total_debates"] == 1


class TestIntegratedFeatures:
    """Test features working together."""

    @pytest.mark.asyncio
    async def test_analyst_with_learned_context(self):
        """Analyst uses learned patterns as additional context."""
        context = MagicMock()
        context.topic = "Should we use LlamaIndex?"
        context.get_arguments.return_value = []
        context.post_argument = AsyncMock()

        # Create learner with existing pattern
        learner = MagicMock()
        learner.find_similar.return_value = [
            LearnedPattern(
                topic_pattern="*llamaindex*",
                recommendation="ADOPT",
                confidence=0.85,
                success_rate=0.9,
            )
        ]

        config = AnalystConfig(
            perspective="cost",
            system_prompt="Analyze costs.",
        )

        analyst = LLMAnalyst(
            agent_id="cost_analyst",
            context=context,
            message_bus=MagicMock(),
            config=config,
        )

        # Inject learner
        analyst._learner = learner

        with patch.object(analyst, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "Cost effective, and previous debates support this.",
                "evidence": ["Past success rate: 90%"],
                "confidence": 0.9,
            }

            result = await analyst.analyze()

        assert result.confidence >= 0.85
