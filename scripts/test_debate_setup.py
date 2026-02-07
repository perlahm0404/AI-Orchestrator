#!/usr/bin/env python3
"""
Quick test of council debate setup (no LLM calls, uses pattern-based fallback).

This validates the infrastructure is working before running the full LLM-powered debate.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coordinator.council_orchestrator import CouncilOrchestrator
from agents.coordinator.llm_debate_agent import create_llm_agent


async def test_debate() -> bool:
    """Run a quick test debate with fallback analysis (no LLM)."""

    print("\n" + "="*80)
    print("TESTING COUNCIL DEBATE INFRASTRUCTURE")
    print("="*80)
    print("\nMode: Pattern-based fallback (no LLM calls)")
    print("This is a quick test to validate the infrastructure works.")
    print("="*80 + "\n")

    # Define agent factories using pattern-based analysis
    agent_types = {}

    perspectives = ["integration", "cost", "alternatives", "performance", "security"]

    for key in perspectives:
        # Create factory function for this perspective
        def make_factory(perspective_key: str):  # type: ignore
            def factory(agent_id: str, context, message_bus, perspective: str):  # type: ignore
                return create_llm_agent(
                    perspective=perspective_key,
                    agent_id=agent_id,
                    context=context,
                    message_bus=message_bus,
                    use_llm=False  # Use pattern-based fallback for testing
                )
            return factory

        agent_types[key] = make_factory(key)

    # Create orchestrator
    council = CouncilOrchestrator(
        topic=(
            "Should we adopt approach A (2026 Best Practices) or "
            "approach B (AI-Agency-Agents Orchestration Repo)?"
        ),
        agent_types=agent_types,
        rounds=3,
        max_duration_minutes=5,
        enforce_budget=False,  # Disable budget for test
        create_ko=False,  # Don't create KO for test
        enable_learning=False  # Don't learn from test
    )

    print("🚀 Starting test debate...\n")

    try:
        # Run debate
        result = await council.run_debate()

        # Display results
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"\n✅ Council ID: {result.council_id}")
        print(f"✅ Recommendation: {result.recommendation}")
        print(f"✅ Confidence: {result.confidence:.1%}")
        print(f"✅ Vote Breakdown: {result.vote_breakdown}")
        print(f"✅ Duration: {result.duration_seconds:.1f} seconds")
        print(f"✅ Arguments collected: {len(result.arguments)}")
        print(f"✅ Manifest: {result.manifest_path}")
        print("="*80 + "\n")

        print("✅ Infrastructure test PASSED!")
        print("\nYou can now run the full LLM-powered debate:")
        print("  python scripts/debate_2026_vs_v2.py")

        return True

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    """Main entry point."""
    success = asyncio.run(test_debate())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
