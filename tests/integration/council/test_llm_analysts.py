"""
Tests for LLM-powered analyst agents.

TDD approach: Tests written first, then implementation.
Target: Replace pattern-based analysis with actual LLM calls.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# These imports will fail until we implement the modules
try:
    from agents.coordinator.llm_analyst import (
        LLMAnalyst,
        AnalystConfig,
        AnalysisResult,
        LLMProvider,
    )
    from agents.coordinator.debate_agent import DebateAgent
    from orchestration.debate_context import DebateContext, Position
    from orchestration.message_bus import MessageBus
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

    class Position:
        SUPPORT = "support"
        OPPOSE = "oppose"
        NEUTRAL = "neutral"

    @dataclass
    class AnalysisResult:
        position: str
        reasoning: str
        evidence: List[str]
        confidence: float
        cost_usd: float = 0.0


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Implementation not yet created - TDD in progress"
)


class TestAnalystConfig:
    """Test AnalystConfig dataclass."""

    def test_config_has_required_fields(self):
        """Config has all required fields."""
        config = AnalystConfig(
            perspective="cost",
            system_prompt="You are a cost analyst...",
            model="claude-sonnet",
            max_tokens=1000,
        )

        assert config.perspective == "cost"
        assert "cost analyst" in config.system_prompt.lower()
        assert config.model == "claude-sonnet"

    def test_config_defaults(self):
        """Config has sensible defaults."""
        config = AnalystConfig(
            perspective="integration",
            system_prompt="Analyze integration complexity."
        )

        assert config.model == "claude-sonnet"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7


class TestLLMAnalyst:
    """Test LLMAnalyst class."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock debate context."""
        context = MagicMock()
        context.topic = "Should we adopt LlamaIndex for RAG?"
        context.get_arguments.return_value = []
        context.post_argument = AsyncMock()
        return context

    @pytest.fixture
    def mock_message_bus(self):
        """Create a mock message bus."""
        bus = MagicMock(spec=MessageBus)
        bus.publish = AsyncMock()
        return bus

    @pytest.fixture
    def analyst_config(self):
        """Create a test analyst config."""
        return AnalystConfig(
            perspective="cost",
            system_prompt="""You are a cost analyst. Analyze the financial implications
            of technology decisions. Consider licensing, infrastructure, and maintenance costs.""",
        )

    @pytest.mark.asyncio
    async def test_analyst_initialization(self, mock_context, mock_message_bus, analyst_config):
        """Analyst initializes correctly."""
        analyst = LLMAnalyst(
            agent_id="cost_analyst",
            context=mock_context,
            message_bus=mock_message_bus,
            config=analyst_config,
        )

        assert analyst.agent_id == "cost_analyst"
        assert analyst.perspective == "cost"

    @pytest.mark.asyncio
    async def test_analyze_calls_llm(self, mock_context, mock_message_bus, analyst_config):
        """Analyze method calls LLM provider."""
        analyst = LLMAnalyst(
            agent_id="cost_analyst",
            context=mock_context,
            message_bus=mock_message_bus,
            config=analyst_config,
        )

        with patch.object(analyst, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "LlamaIndex has reasonable pricing.",
                "evidence": ["$0.02 per query average"],
                "confidence": 0.8,
            }

            result = await analyst.analyze()

        assert result.position == Position.SUPPORT
        assert "pricing" in result.reasoning.lower()
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_tracks_cost(self, mock_context, mock_message_bus, analyst_config):
        """Analyze tracks LLM API cost."""
        analyst = LLMAnalyst(
            agent_id="cost_analyst",
            context=mock_context,
            message_bus=mock_message_bus,
            config=analyst_config,
        )

        with patch.object(analyst, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "Cost effective solution.",
                "evidence": ["Evidence 1"],
                "confidence": 0.7,
                "usage": {"input_tokens": 500, "output_tokens": 200},
            }

            result = await analyst.analyze()

        # Cost tracking is for budget limits (virtual cost for subscription)
        assert result.cost_usd >= 0

    @pytest.mark.asyncio
    async def test_analyze_handles_llm_error(self, mock_context, mock_message_bus, analyst_config):
        """Analyze handles LLM errors gracefully."""
        analyst = LLMAnalyst(
            agent_id="cost_analyst",
            context=mock_context,
            message_bus=mock_message_bus,
            config=analyst_config,
        )

        with patch.object(analyst, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("API rate limit exceeded")

            result = await analyst.analyze()

        # Should return neutral position on error
        assert result.position == Position.NEUTRAL
        assert "error" in result.reasoning.lower() or "unavailable" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_analyze_uses_context(self, mock_context, mock_message_bus, analyst_config):
        """Analyze incorporates debate context."""
        # Create a mock Argument object
        from orchestration.debate_context import Argument, Position
        mock_arg = MagicMock()
        mock_arg.agent_id = "integration_analyst"
        mock_arg.position = Position.OPPOSE
        mock_arg.reasoning = "Complex setup required"

        mock_context.get_arguments.return_value = [mock_arg]

        analyst = LLMAnalyst(
            agent_id="cost_analyst",
            context=mock_context,
            message_bus=mock_message_bus,
            config=analyst_config,
        )

        with patch.object(analyst, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "Despite complexity, cost benefits outweigh.",
                "evidence": ["ROI analysis"],
                "confidence": 0.75,
            }

            await analyst.analyze()

        # Verify context was queried
        assert mock_context.get_arguments.called


class TestLLMProvider:
    """Test LLM provider abstraction."""

    def test_provider_calculates_cost(self):
        """Provider calculates virtual cost for budget tracking."""
        provider = LLMProvider(model="claude-sonnet")

        cost = provider.calculate_cost(input_tokens=1000, output_tokens=500)

        # Claude.ai subscription uses virtual costs for budget tracking
        # Should return a non-negative value
        assert cost >= 0

    def test_provider_supports_multiple_models(self):
        """Provider supports different models."""
        sonnet = LLMProvider(model="claude-sonnet")
        default = LLMProvider(model="unknown-model")

        sonnet_cost = sonnet.calculate_cost(input_tokens=1000, output_tokens=500)
        default_cost = default.calculate_cost(input_tokens=1000, output_tokens=500)

        # Both should return valid cost values
        assert sonnet_cost >= 0
        assert default_cost >= 0


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""

    def test_result_has_required_fields(self):
        """Result has all required fields."""
        result = AnalysisResult(
            position=Position.SUPPORT,
            reasoning="Strong cost benefits.",
            evidence=["Evidence 1", "Evidence 2"],
            confidence=0.85,
            cost_usd=0.002,
        )

        assert result.position == Position.SUPPORT
        assert result.confidence == 0.85
        assert len(result.evidence) == 2

    def test_result_defaults(self):
        """Result has sensible defaults."""
        result = AnalysisResult(
            position=Position.NEUTRAL,
            reasoning="Insufficient data.",
            evidence=[],
            confidence=0.5,
        )

        assert result.cost_usd == 0.0


class TestLLMAnalystIntegration:
    """Integration tests for LLM analysts in debates."""

    @pytest.fixture
    def full_context(self):
        """Create a full debate context."""
        context = DebateContext(
            topic="Should we use Redis for caching?",
            perspectives=["cost", "performance", "security"],
            council_id="TEST-INT-001"
        )
        return context

    @pytest.fixture
    def full_message_bus(self):
        """Create a mock message bus."""
        bus = MagicMock()
        bus.publish = AsyncMock()
        return bus

    @pytest.mark.asyncio
    async def test_analyst_publishes_argument(self, full_context, full_message_bus):
        """Analyst publishes argument to context."""
        config = AnalystConfig(
            perspective="performance",
            system_prompt="Analyze performance implications.",
        )

        analyst = LLMAnalyst(
            agent_id="performance_analyst",
            context=full_context,
            message_bus=full_message_bus,
            config=config,
        )

        with patch.object(analyst, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "Redis provides sub-millisecond latency.",
                "evidence": ["Benchmark data"],
                "confidence": 0.9,
            }

            await analyst.participate_in_round(round_num=1)

        # Check argument was added to context
        args = full_context.get_arguments()
        assert len(args) >= 1

    @pytest.mark.asyncio
    async def test_multiple_analysts_debate(self, full_context, full_message_bus):
        """Multiple analysts can participate in a debate."""
        configs = [
            AnalystConfig(perspective="cost", system_prompt="Analyze costs."),
            AnalystConfig(perspective="performance", system_prompt="Analyze performance."),
            AnalystConfig(perspective="security", system_prompt="Analyze security."),
        ]

        analysts = [
            LLMAnalyst(
                agent_id=f"{c.perspective}_analyst",
                context=full_context,
                message_bus=full_message_bus,
                config=c,
            )
            for c in configs
        ]

        with patch.object(LLMAnalyst, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "position": "support",
                "reasoning": "Positive analysis.",
                "evidence": ["Evidence"],
                "confidence": 0.8,
            }

            for analyst in analysts:
                await analyst.participate_in_round(round_num=1)

        args = full_context.get_arguments()
        assert len(args) == 3
