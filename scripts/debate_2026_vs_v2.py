#!/usr/bin/env python3
"""
Council Debate: 2026 Best Practices vs AI-Agency-Agents Orchestration Repo

Debate Topic: Which approach should we adopt for setting up an AI agent team
for web application development?

Approach A: 2026 Best Practices (claude-mem + Agent Teams + Claude Code 2026 features)
Approach B: AI-Agency-Agents Orchestration Repo (custom orchestration layer + Ralph + work queue)

This script uses the Council debate pattern with 5 specialized analyst agents:
- Integration Analyst: Implementation complexity, team capacity, learning curve
- Cost Analyst: Total cost of ownership, ongoing maintenance, resource efficiency
- Alternatives Analyst: Hybrid approaches, middle ground, other options
- Performance Analyst: Developer productivity, agent effectiveness, autonomy levels
- Security Analyst: Compliance, governance, audit trails, risk management (used for governance analysis)

Expected outcome: CONDITIONAL recommendation (use A for new projects, B for enterprise)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coordinator.council_orchestrator import CouncilOrchestrator
from agents.coordinator.llm_debate_agent import create_llm_agent


# Background context for all agents
BACKGROUND_CONTEXT = """
You are analyzing two approaches for AI agent team setup:

APPROACH A: 2026 Best Practices
- claude-mem plugin for memory (auto-capture, session-level, zero-config)
- Claude Code 2.1 native Tasks system (built-in)
- Opus 4.6 TeammateTool for agent coordination (native API)
- Lean CLAUDE.md (150-200 instructions, not 2000+ lines)
- File-scoped rules (.claude/rules/) for modular governance
- On-demand skills (.claude/skills/) for reusable playbooks
- PostToolUse hooks for fast feedback (3-tier CI)
- Target: Small teams, new apps, interactive development
- Setup: 1-3 days
- Learning curve: Low (uses Claude Code features)
- Architecture: Lightweight, plugin-based

APPROACH B: AI-Agency-Agents Orchestration Repo
- Custom orchestration repo (new repo to manage other repos)
- Role-based contracts (Lead, Architect, Builder, Refactorer, Reviewer, QA, Security, Release)
- work_queue.json system-of-record (JSON-based task management)
- Ralph verifier with risk levels (L0-L4 governance gates)
- Telemetry + evals/golden fixtures (quality assurance)
- Formal DoD enforcement (Definition of Done)
- Target: Enterprise teams, multi-repo, autonomous execution
- Setup: 1-2 weeks
- Learning curve: High (custom orchestration layer)
- Architecture: Heavy governance, custom orchestration

Reference documents:
- Approach A: sessions/ai-orchestrator/active/20260205-autoforge-implementation-roadmap.md
- Approach B: sessions/ai-orchestrator/active/20260205-state-of-the-art claude-v2.md

Key Trade-offs:
A Strengths: Fast setup, leverages 2026 features, low learning curve, lightweight
A Weaknesses: Less formal governance, not designed for multi-repo, weaker audit trails

B Strengths: Strong governance, system-of-record, formal contracts, evals/golden fixtures
B Weaknesses: High setup complexity, custom layer maintenance, steeper learning curve

CRITICAL CONTEXT: The user is building a new AI agent team for web application development.
Consider: project size, team size, compliance needs, single vs multi-repo, interactive vs autonomous.
"""


async def run_debate():  # type: ignore
    """Run the council debate and return results."""

    print("\n" + "="*80)
    print("COUNCIL DEBATE: 2026 Best Practices vs AI-Agency-Agents Orchestration Repo")
    print("="*80)
    print("\nTopic: Which approach for AI agent team setup?")
    print("  A) 2026 Best Practices (claude-mem + TeammateTool)")
    print("  B) AI-Agency-Agents Orchestration Repo (custom orchestration + Ralph)")
    print("\nPerspectives: Integration, Cost, Alternatives, Performance, Security (Governance)")
    print("Rounds: 3 (Analysis → Rebuttals → Synthesis)")
    print("Budget: $2.00 max, 30 minutes max")
    print("="*80 + "\n")

    # Define agent factories using LLM-powered agents
    agent_types = {}

    # Create factory for each perspective
    # Note: "security" is used for governance analysis (compliance, audit trails, risk management)
    perspectives = ["integration", "cost", "alternatives", "performance", "security"]

    for key in perspectives:
        # Create factory function for this perspective
        def make_factory(perspective_key: str):  # type: ignore
            def factory(agent_id: str, context, message_bus, perspective: str):  # type: ignore
                # Use the perspective key we captured, not the one passed
                return create_llm_agent(
                    perspective=perspective_key,
                    agent_id=agent_id,
                    context=context,
                    message_bus=message_bus,
                    use_llm=True  # Enable LLM-powered analysis
                )
            return factory

        agent_types[key] = make_factory(key)

    # Create orchestrator
    council = CouncilOrchestrator(
        topic=(
            "Which approach should we adopt for AI agent team setup: "
            "2026 Best Practices (claude-mem + TeammateTool) or "
            "AI-Agency-Agents Orchestration Repo (custom orchestration + Ralph)?"
        ),
        agent_types=agent_types,
        rounds=3,
        max_duration_minutes=30,
        enforce_budget=True,
        create_ko=True,  # Create Knowledge Object after debate
        enable_learning=True  # Learn patterns from this debate
    )

    print("🚀 Starting debate...\n")

    try:
        # Run debate
        result = await council.run_debate()

        # Display results
        print("\n" + "="*80)
        print("COUNCIL DEBATE RESULTS")
        print("="*80)
        print(f"\nCouncil ID: {result.council_id}")
        print(f"Topic: {result.topic}")
        print(f"\n🎯 RECOMMENDATION: {result.recommendation}")
        print(f"📊 CONFIDENCE: {result.confidence:.1%}")
        print(f"\n📋 Vote Breakdown: {result.vote_breakdown}")
        print(f"⏱️  Duration: {result.duration_seconds:.1f} seconds")

        if result.cost_summary:
            print(f"💰 Cost: ${result.cost_summary.get('total_cost', 0):.2f}")
            if result.cost_summary.get('halted'):
                print(f"⚠️  Halted: {result.cost_summary.get('halt_reason', 'Unknown')}")

        print(f"\n🔑 Key Considerations:")
        for consideration in result.key_considerations:
            print(f"  • {consideration}")

        print(f"\n📄 Manifest: {result.manifest_path}")
        print("="*80 + "\n")

        # Show timeline
        print("="*80)
        print("DEBATE TIMELINE")
        print("="*80)
        print(council.get_debate_timeline())
        print("="*80 + "\n")

        # Show arguments summary
        print("="*80)
        print("ARGUMENTS SUMMARY")
        print("="*80)
        for arg in result.arguments:
            print(f"\n[{arg.perspective.upper()}] {arg.position.value} (confidence: {arg.confidence:.0%})")
            print(f"  {arg.reasoning[:200]}..." if len(arg.reasoning) > 200 else f"  {arg.reasoning}")
        print("="*80 + "\n")

        return result

    except Exception as e:
        print(f"\n❌ Error during debate: {e}")
        import traceback
        traceback.print_exc()
        return None


def main() -> None:
    """Main entry point."""
    # Run the debate
    result = asyncio.run(run_debate())  # type: ignore

    if result:
        print("\n✅ Debate completed successfully!")
        print(f"\nNext steps:")
        print(f"  1. Review the debate manifest: {result.manifest_path}")
        print(f"  2. Check for generated ADR in: AI-Team-Plans/decisions/")
        print(f"  3. View Knowledge Object: aibrain ko list | grep agent-team")
        print(f"  4. Record outcome when decision is implemented:")
        print(f"     aibrain council outcome {result.council_id} SUCCESS|PARTIAL|FAILURE")

        sys.exit(0)
    else:
        print("\n❌ Debate failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
