"""
End-to-end test: Council debate → ADR generation.

Tests complete workflow from debate to ADR document creation.
"""

import pytest
from pathlib import Path
import shutil

from agents.analyst.cost_analyst import CostAnalystAgent
from agents.analyst.integration_analyst import IntegrationAnalystAgent
from agents.analyst.performance_analyst import PerformanceAnalystAgent
from agents.analyst.alternatives_analyst import AlternativesAnalystAgent
from agents.analyst.security_analyst import SecurityAnalystAgent
from agents.coordinator.council_orchestrator import CouncilOrchestrator
from orchestration.create_adr_from_debate import create_adr_from_debate


class TestCouncilToADR:
    """Test end-to-end council debate to ADR workflow."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test artifacts after each test."""
        yield
        # Clean up councils
        councils_dir = Path(".aibrain/councils")
        if councils_dir.exists():
            for council_dir in councils_dir.glob("TEST-*"):
                shutil.rmtree(council_dir)

        # Clean up test ADRs
        decisions_dir = Path("AI-Team-Plans/decisions")
        if decisions_dir.exists():
            for adr_file in decisions_dir.glob("ADR-*test*.md"):
                adr_file.unlink()

    @pytest.mark.asyncio
    async def test_debate_to_adr_workflow(self):
        """
        Test complete workflow: debate → ADR.

        Steps:
        1. Run council debate on a topic
        2. Generate ADR from debate result
        3. Verify ADR content includes debate summary
        4. Verify ADR file is created
        """
        # Step 1: Run council debate
        council = CouncilOrchestrator(
            topic="Should we adopt LlamaIndex for RAG in CredentialMate?",
            agent_types={
                "cost": CostAnalystAgent,
                "integration": IntegrationAnalystAgent,
                "performance": PerformanceAnalystAgent,
                "alternatives": AlternativesAnalystAgent,
                "security": SecurityAnalystAgent
            },
            rounds=3,
            council_id="TEST-ADR-LLAMAINDEX-001"
        )

        debate_result = await council.run_debate()

        # Verify debate completed
        assert debate_result.recommendation in ["ADOPT", "REJECT", "CONDITIONAL", "SPLIT"]
        assert len(debate_result.arguments) >= 5

        # Step 2: Generate ADR from debate result
        adr_result = create_adr_from_debate(
            debate_result=debate_result,
            context="CredentialMate requires RAG capabilities for physician license verification to reduce manual document review time.",
            project="credentialmate"
        )

        # Verify ADR creation succeeded
        assert adr_result["status"] == "completed"
        assert "adr_number" in adr_result
        assert "adr_path" in adr_result
        assert adr_result["council_id"] == "TEST-ADR-LLAMAINDEX-001"

        adr_number = adr_result["adr_number"]
        adr_path = Path(adr_result["adr_path"])

        # Step 3: Verify ADR file exists
        assert adr_path.exists()

        # Step 4: Verify ADR content
        adr_content = adr_path.read_text()

        # Should contain ADR number (either "ADR-001" or "ADR 001")
        assert adr_number in adr_content or adr_number.replace("-", " ") in adr_content

        # Should contain debate topic
        assert "LlamaIndex" in adr_content

        # Should contain council ID
        assert "TEST-ADR-LLAMAINDEX-001" in adr_content

        # Should contain vote breakdown
        assert "Vote Breakdown" in adr_content
        assert "SUPPORT" in adr_content or "OPPOSE" in adr_content or "NEUTRAL" in adr_content

        # Should contain agent positions
        assert "Cost Analysis" in adr_content or "cost" in adr_content.lower()
        assert "Integration Analysis" in adr_content or "integration" in adr_content.lower()
        assert "Performance Analysis" in adr_content or "performance" in adr_content.lower()

        # Should contain recommendation
        assert debate_result.recommendation in adr_content

        # Should contain confidence score
        assert f"{debate_result.confidence:.2f}" in adr_content

        # Should contain manifest path
        assert debate_result.manifest_path in adr_content

        # Print ADR summary for manual inspection
        print("\n" + "="*60)
        print(f"ADR Created: {adr_number}")
        print(f"File: {adr_path}")
        print(f"Council: {debate_result.council_id}")
        print(f"Recommendation: {debate_result.recommendation} (confidence: {debate_result.confidence:.2f})")
        print("="*60)
        print("\nADR Content Preview (first 1000 chars):")
        print(adr_content[:1000])
        print("="*60)

    @pytest.mark.asyncio
    async def test_adr_contains_all_perspectives(self):
        """Verify ADR includes analysis from all 5 perspectives."""

        council = CouncilOrchestrator(
            topic="Choose between SST and Vercel for deployment?",
            agent_types={
                "cost": CostAnalystAgent,
                "integration": IntegrationAnalystAgent,
                "performance": PerformanceAnalystAgent,
                "alternatives": AlternativesAnalystAgent,
                "security": SecurityAnalystAgent
            },
            rounds=3,
            council_id="TEST-ADR-SST-001"
        )

        debate_result = await council.run_debate()

        # Generate ADR
        adr_result = create_adr_from_debate(
            debate_result=debate_result,
            context="CredentialMate needs to choose deployment platform.",
            project="credentialmate"
        )

        # Read ADR
        adr_path = Path(adr_result["adr_path"])
        adr_content = adr_path.read_text()

        # Verify all 5 perspectives are represented
        perspectives = ["cost", "integration", "performance", "alternatives", "security"]
        for perspective in perspectives:
            assert perspective in adr_content.lower(), f"Perspective '{perspective}' not found in ADR"

    @pytest.mark.asyncio
    async def test_adr_approval_workflow(self):
        """Test ADR is created in 'Proposed' status awaiting approval."""

        council = CouncilOrchestrator(
            topic="Test ADR approval workflow",
            agent_types={
                "cost": CostAnalystAgent,
                "performance": PerformanceAnalystAgent
            },
            rounds=2,
            council_id="TEST-ADR-APPROVAL-001"
        )

        debate_result = await council.run_debate()

        # Generate ADR
        adr_result = create_adr_from_debate(
            debate_result=debate_result,
            context="Test context",
            project="test"
        )

        # Read ADR
        adr_path = Path(adr_result["adr_path"])
        adr_content = adr_path.read_text()

        # Verify status is "Proposed" (awaiting approval)
        assert "**Status**: Proposed" in adr_content

        # Verify approved_by is "Pending"
        assert "**Approved By**: Pending" in adr_content or "Pending" in adr_content


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
