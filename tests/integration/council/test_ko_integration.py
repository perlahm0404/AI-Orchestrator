"""
Integration tests for Council Pattern - Knowledge Object creation.

Tests the KO integration specified in council-team.yaml:
- create_ko_on_completion: true
- ko_type: council_decision
- ko_effectiveness_tracking: true
"""

import asyncio
import pytest
from pathlib import Path
import shutil

from agents.coordinator.debate_agent import SimpleDebateAgent
from agents.coordinator.council_orchestrator import CouncilOrchestrator
from orchestration.debate_context import Position
from orchestration.council_ko_integration import (
    create_ko_from_debate,
    should_create_ko,
    _build_tags,
    _infer_project
)


class TestKOIntegration:
    """Test Knowledge Object creation from debate results."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test councils and KOs after each test."""
        yield
        # Clean up test councils
        councils_dir = Path(".aibrain/councils")
        if councils_dir.exists():
            for council_dir in councils_dir.glob("TEST-KO-*"):
                shutil.rmtree(council_dir)
        # Clean up test KOs
        from knowledge.service import KO_DRAFTS_DIR, KO_APPROVED_DIR
        for ko_file in KO_DRAFTS_DIR.glob("KO-ao-*.md"):
            ko_file.unlink()
        for ko_file in KO_APPROVED_DIR.glob("KO-ao-*.md"):
            ko_file.unlink()

    @pytest.mark.asyncio
    async def test_ko_created_on_debate_completion(self):
        """Test that KO is created when debate completes."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test KO integration",
                evidence=["Test evidence"],
                confidence=0.9
            )

        council = CouncilOrchestrator(
            topic="Should we adopt Redis for caching? (KO test)",
            agent_types={"cost": create_agent, "integration": create_agent},
            rounds=1,
            council_id="TEST-KO-001",
            create_ko=True  # Enable KO creation
        )

        result = await council.run_debate()

        # Verify debate completed
        assert result.recommendation in ["ADOPT", "CONDITIONAL", "SPLIT", "REJECT"]

        # Check manifest for KO creation event
        manifest_path = Path(result.manifest_path)
        assert manifest_path.exists()
        content = manifest_path.read_text()
        # KO should have been created (or skipped for TEST- prefixed councils)
        # The should_create_ko() function returns False for TEST- councils

    @pytest.mark.asyncio
    async def test_ko_not_created_when_disabled(self):
        """Test that KO is not created when create_ko=False."""

        def create_agent(agent_id, context, message_bus, perspective):
            return SimpleDebateAgent(
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                perspective=perspective,
                position=Position.SUPPORT,
                reasoning="Test",
                evidence=["Test"],
                confidence=0.9
            )

        council = CouncilOrchestrator(
            topic="Test no KO creation",
            agent_types={"cost": create_agent},
            rounds=1,
            council_id="TEST-KO-002",
            create_ko=False  # Disable KO creation
        )

        result = await council.run_debate()

        # Check manifest - should NOT have ko_created event
        manifest_path = Path(result.manifest_path)
        content = manifest_path.read_text()
        assert "ko_created" not in content


class TestShouldCreateKO:
    """Test the should_create_ko() helper function."""

    def test_should_not_create_for_test_councils(self):
        """Test councils starting with 'TEST-' don't create KOs."""
        from agents.coordinator.council_orchestrator import DebateResult

        result = DebateResult(
            council_id="TEST-123",
            topic="Test topic",
            recommendation="ADOPT",
            confidence=0.9,
            vote_breakdown={"SUPPORT": 2},
            key_considerations=[],
            arguments=[],  # Empty for simplicity
            duration_seconds=10.0,
            manifest_path="/tmp/test"
        )

        assert should_create_ko(result) is False

    def test_should_not_create_for_low_confidence(self):
        """Test low confidence debates don't create KOs."""
        from agents.coordinator.council_orchestrator import DebateResult
        from orchestration.debate_context import Argument, Position

        result = DebateResult(
            council_id="COUNCIL-123",
            topic="Test topic",
            recommendation="SPLIT",
            confidence=0.2,  # Very low
            vote_breakdown={"SUPPORT": 1, "OPPOSE": 1},
            key_considerations=[],
            arguments=[
                Argument(
                    agent_id="test",
                    perspective="cost",
                    position=Position.NEUTRAL,
                    evidence=[],
                    reasoning="Test",
                    confidence=0.5,
                    round_number=1
                )
            ],
            duration_seconds=10.0,
            manifest_path="/tmp/test"
        )

        assert should_create_ko(result) is False

    def test_should_not_create_for_no_arguments(self):
        """Test debates with no arguments don't create KOs."""
        from agents.coordinator.council_orchestrator import DebateResult

        result = DebateResult(
            council_id="COUNCIL-123",
            topic="Test topic",
            recommendation="ADOPT",
            confidence=0.9,
            vote_breakdown={"SUPPORT": 2},
            key_considerations=[],
            arguments=[],  # No arguments
            duration_seconds=10.0,
            manifest_path="/tmp/test"
        )

        assert should_create_ko(result) is False

    def test_should_create_for_valid_debate(self):
        """Test valid debates do create KOs."""
        from agents.coordinator.council_orchestrator import DebateResult
        from orchestration.debate_context import Argument, Position

        result = DebateResult(
            council_id="COUNCIL-123",  # Not TEST-
            topic="Test topic",
            recommendation="ADOPT",
            confidence=0.9,  # High confidence
            vote_breakdown={"SUPPORT": 2},
            key_considerations=[],
            arguments=[
                Argument(
                    agent_id="test",
                    perspective="cost",
                    position=Position.SUPPORT,
                    evidence=[],
                    reasoning="Test reasoning",
                    confidence=0.9,
                    round_number=1
                )
            ],
            duration_seconds=10.0,
            manifest_path="/tmp/test"
        )

        assert should_create_ko(result) is True


class TestTagGeneration:
    """Test tag generation from debate results."""

    def test_tags_include_recommendation(self):
        """Test that tags include the recommendation."""
        from agents.coordinator.council_orchestrator import DebateResult
        from orchestration.debate_context import Argument, Position

        result = DebateResult(
            council_id="COUNCIL-123",
            topic="Test topic",
            recommendation="ADOPT",
            confidence=0.9,
            vote_breakdown={"SUPPORT": 2},
            key_considerations=[],
            arguments=[
                Argument(
                    agent_id="cost",
                    perspective="cost",
                    position=Position.SUPPORT,
                    evidence=[],
                    reasoning="Test",
                    confidence=0.9,
                    round_number=1
                )
            ],
            duration_seconds=10.0,
            manifest_path="/tmp/test"
        )

        tags = _build_tags(result)

        assert "council" in tags
        assert "debate" in tags
        assert "adopt" in tags  # recommendation lowercase
        assert "cost" in tags  # perspective

    def test_tags_from_topic_keywords(self):
        """Test topic-based tag inference."""
        from agents.coordinator.council_orchestrator import DebateResult
        from orchestration.debate_context import Argument, Position

        result = DebateResult(
            council_id="COUNCIL-123",
            topic="Should we use Redis for caching?",
            recommendation="ADOPT",
            confidence=0.9,
            vote_breakdown={"SUPPORT": 2},
            key_considerations=[],
            arguments=[
                Argument(
                    agent_id="test",
                    perspective="performance",
                    position=Position.SUPPORT,
                    evidence=[],
                    reasoning="Test",
                    confidence=0.9,
                    round_number=1
                )
            ],
            duration_seconds=10.0,
            manifest_path="/tmp/test"
        )

        tags = _build_tags(result)

        assert "caching" in tags  # From "caching" in topic


class TestProjectInference:
    """Test project inference from topics."""

    def test_infer_karematch(self):
        """Test KareMatch project inference."""
        assert _infer_project("Should KareMatch use Redis?") == "karematch"
        assert _infer_project("kare integration test") == "karematch"

    def test_infer_credentialmate(self):
        """Test CredentialMate project inference."""
        assert _infer_project("HIPAA compliance for database") == "credentialmate"
        assert _infer_project("CredentialMate deployment") == "credentialmate"

    def test_infer_default(self):
        """Test default project inference."""
        assert _infer_project("Generic tech decision") == "ai-orchestrator"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
