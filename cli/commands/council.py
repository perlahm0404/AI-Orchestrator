"""
CLI commands for Council Pattern debate management.

Usage:
    aibrain council debate --topic "Should we adopt LlamaIndex?"
    aibrain council list
    aibrain council show COUNCIL-ID
    aibrain council replay COUNCIL-ID

Council Pattern provides multi-perspective debates for architectural decisions.
Each debate runs 5 analyst agents through 3 rounds to reach a recommendation.
"""

from typing import Any
import argparse
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Directories for council artifacts
COUNCILS_DIR = Path(".aibrain/councils")


def council_debate_command(args: Any) -> int:
    """Start a new council debate on a topic."""
    from agents.coordinator.council_orchestrator import CouncilOrchestrator, DebateResult

    topic = args.topic
    rounds = getattr(args, 'rounds', 3)
    timeout = getattr(args, 'timeout', 30)

    print(f"\n{'='*60}")
    print(f"  COUNCIL DEBATE")
    print(f"{'='*60}\n")
    print(f"Topic: {topic}")
    print(f"Rounds: {rounds}")
    print(f"Timeout: {timeout} minutes")
    print()

    # For now, use SimpleDebateAgents with pattern-based analysis
    # In production, these would be the real analyst agents with LLM integration

    # Analyze topic to determine positions (pattern-based for MVP)
    agent_types = _create_agents_for_topic(topic)

    print(f"Perspectives: {', '.join(agent_types.keys())}")
    print("\nStarting debate...")
    print("="*60)

    # Run debate
    async def run() -> DebateResult:
        council = CouncilOrchestrator(
            topic=topic,
            agent_types=agent_types,
            rounds=rounds,
            max_duration_minutes=timeout,
            enforce_budget=True
        )
        return await council.run_debate()

    result: DebateResult = asyncio.run(run())

    # Display results
    print(f"\n{'='*60}")
    print(f"  DEBATE RESULT")
    print(f"{'='*60}\n")

    print(f"Council ID: {result.council_id}")
    print(f"Topic: {result.topic}")
    print()
    print(f"Recommendation: {result.recommendation}")
    print(f"Confidence: {result.confidence:.1%}")
    print()
    print(f"Vote Breakdown:")
    for position, count in result.vote_breakdown.items():
        print(f"  {position}: {count}")
    print()

    if result.key_considerations:
        print("Key Considerations:")
        for consideration in result.key_considerations:
            print(f"  - {consideration}")
        print()

    if result.cost_summary:
        print(f"Cost: ${result.cost_summary.get('total_cost', 0):.2f}")
        print(f"Budget: ${2.00 - result.cost_summary.get('remaining_budget', 2.00):.2f} / $2.00")

    print()
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Manifest: {result.manifest_path}")
    print()
    print(f"View details with: aibrain council show {result.council_id}")
    print(f"Replay with: aibrain council replay {result.council_id}")
    print(f"{'='*60}\n")

    return 0


def _create_agents_for_topic(topic: str) -> dict[str, Any]:
    """
    Create agent factories based on topic analysis.

    Uses pattern matching to determine likely positions.
    In production, this would use LLM-powered analysis.
    """
    from orchestration.debate_context import Position

    topic_lower = topic.lower()

    # Default neutral analysis for each perspective
    agents = {}

    # Cost perspective
    if "free" in topic_lower or "open source" in topic_lower:
        position = Position.SUPPORT
        reasoning = "Open source solutions reduce licensing costs."
        confidence = 0.75
    elif "enterprise" in topic_lower or "paid" in topic_lower:
        position = Position.OPPOSE
        reasoning = "Enterprise solutions have significant licensing costs."
        confidence = 0.65
    else:
        position = Position.NEUTRAL
        reasoning = "Cost analysis requires more specific details."
        confidence = 0.5

    agents["cost"] = _make_agent_factory("cost", position, reasoning, confidence)

    # Integration perspective
    if "simple" in topic_lower or "easy" in topic_lower:
        position = Position.SUPPORT
        reasoning = "Integration appears straightforward."
        confidence = 0.7
    elif "complex" in topic_lower or "migration" in topic_lower:
        position = Position.OPPOSE
        reasoning = "Integration complexity may be challenging."
        confidence = 0.6
    else:
        position = Position.NEUTRAL
        reasoning = "Integration effort needs assessment."
        confidence = 0.5

    agents["integration"] = _make_agent_factory("integration", position, reasoning, confidence)

    # Performance perspective
    if "fast" in topic_lower or "performance" in topic_lower or "scalable" in topic_lower:
        position = Position.SUPPORT
        reasoning = "Performance characteristics look favorable."
        confidence = 0.7
    elif "slow" in topic_lower or "legacy" in topic_lower:
        position = Position.OPPOSE
        reasoning = "Performance may be a concern."
        confidence = 0.6
    else:
        position = Position.NEUTRAL
        reasoning = "Performance needs benchmarking."
        confidence = 0.5

    agents["performance"] = _make_agent_factory("performance", position, reasoning, confidence)

    # Alternatives perspective
    position = Position.NEUTRAL
    reasoning = "Multiple alternatives exist and should be evaluated."
    confidence = 0.5
    agents["alternatives"] = _make_agent_factory("alternatives", position, reasoning, confidence)

    # Security perspective
    if "security" in topic_lower or "hipaa" in topic_lower or "compliance" in topic_lower:
        position = Position.OPPOSE
        reasoning = "Security implications require careful review."
        confidence = 0.7
    else:
        position = Position.NEUTRAL
        reasoning = "Security assessment needed."
        confidence = 0.5

    agents["security"] = _make_agent_factory("security", position, reasoning, confidence)

    return agents


def _make_agent_factory(perspective_name: str, position: Any, reasoning: str, confidence: float) -> Any:
    """Create an agent factory function."""
    from agents.coordinator.debate_agent import SimpleDebateAgent

    def factory(agent_id: str, context: Any, message_bus: Any, perspective: str) -> SimpleDebateAgent:
        # Note: perspective is passed by the orchestrator and should match perspective_name
        return SimpleDebateAgent(
            agent_id=agent_id,
            context=context,
            message_bus=message_bus,
            perspective=perspective,
            position=position,
            reasoning=reasoning,
            evidence=[f"{perspective_name.title()} analysis (pattern-based)"],
            confidence=confidence
        )
    return factory


def council_list_command(args: Any) -> int:
    """List recent council debates."""
    COUNCILS_DIR.mkdir(parents=True, exist_ok=True)

    councils = []
    for council_dir in sorted(COUNCILS_DIR.iterdir(), reverse=True):
        if not council_dir.is_dir():
            continue

        manifest_path = council_dir / "manifest.jsonl"
        if not manifest_path.exists():
            continue

        # Read first line to get init info
        try:
            with open(manifest_path) as f:
                first_line = f.readline().strip()
                if first_line:
                    init_event = json.loads(first_line)
                    # Topic/perspectives may be at root level or in data dict
                    topic = init_event.get("topic") or init_event.get("data", {}).get("topic", "Unknown")
                    perspectives = init_event.get("perspectives") or init_event.get("data", {}).get("perspectives", [])
                    councils.append({
                        "id": council_dir.name,
                        "timestamp": init_event.get("timestamp", ""),
                        "topic": topic,
                        "perspectives": perspectives
                    })
        except (json.JSONDecodeError, IOError):
            continue

    if not councils:
        print("\n  No council debates found.")
        print(f"\n  Start one with: aibrain council debate --topic \"Your question\"\n")
        return 0

    # Limit to most recent
    limit = getattr(args, 'limit', 10)
    councils = councils[:limit]

    print(f"\n{'='*60}")
    print(f"  RECENT COUNCIL DEBATES ({len(councils)})")
    print(f"{'='*60}\n")

    for c in councils:
        print(f"{c['id']}")
        print(f"  Topic: {c['topic'][:50]}{'...' if len(c['topic']) > 50 else ''}")
        print(f"  Perspectives: {', '.join(c['perspectives'])}")
        timestamp = c['timestamp'][:19] if c['timestamp'] else 'Unknown'
        print(f"  Started: {timestamp}")
        print()

    print(f"View details with: aibrain council show <COUNCIL-ID>")
    print(f"{'='*60}\n")

    return 0


def council_show_command(args: Any) -> int:
    """Show details of a specific council debate."""
    council_id = args.council_id

    council_dir = COUNCILS_DIR / council_id
    manifest_path = council_dir / "manifest.jsonl"

    if not manifest_path.exists():
        print(f"\n  Council not found: {council_id}")
        print(f"  List councils with: aibrain council list\n")
        return 1

    # Parse manifest
    events = []
    with open(manifest_path) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not events:
        print(f"\n  No events found in manifest for: {council_id}\n")
        return 1

    # Extract key information (event field may be "event" or "event_type")
    init_event = next((e for e in events if e.get("event_type") == "council_init" or e.get("event") == "council_init"), None)
    synthesis_event = next((e for e in events if e.get("event_type") == "synthesis" or e.get("event") == "synthesis"), None)
    cost_event = next((e for e in events if e.get("event_type") == "cost_summary" or e.get("event") == "cost_summary"), None)
    arguments = [e for e in events if e.get("event_type") == "argument_posted" or e.get("event") == "argument_posted"]
    spawns = [e for e in events if e.get("event_type") == "agent_spawn" or e.get("event") == "agent_spawn"]

    print(f"\n{'='*60}")
    print(f"  COUNCIL DEBATE: {council_id}")
    print(f"{'='*60}\n")

    if init_event:
        # Data may be at root level or in 'data' dict
        data = init_event.get("data", {}) if "data" in init_event else init_event
        topic = init_event.get("topic") or data.get("topic", "Unknown")
        perspectives = init_event.get("perspectives") or data.get("perspectives", [])
        metadata = init_event.get("metadata") or data.get("metadata", {})
        print(f"Topic: {topic}")
        print(f"Perspectives: {', '.join(perspectives)}")
        print(f"Rounds: {metadata.get('rounds', 3)}")
        print(f"Max Duration: {metadata.get('max_duration_minutes', 30)} minutes")
        print()

    if synthesis_event:
        data = synthesis_event.get("data", {})
        print(f"Recommendation: {data.get('recommendation', 'Unknown')}")
        print(f"Confidence: {data.get('confidence', 0):.1%}")
        print()
        breakdown = data.get("vote_breakdown", {})
        if breakdown:
            print("Vote Breakdown:")
            for position, count in breakdown.items():
                print(f"  {position}: {count}")
            print()

    if cost_event:
        data = cost_event.get("data", {})
        print(f"Cost: ${data.get('total_cost', 0):.4f}")
        print(f"Budget Exceeded: {data.get('budget_exceeded', False)}")
        if data.get("halted"):
            print(f"Halted: Yes - {data.get('halt_reason', 'Unknown')}")
        print()

    print(f"Agents Spawned: {len(spawns)}")
    print(f"Arguments Posted: {len(arguments)}")
    print()

    print(f"Manifest: {manifest_path}")
    print()
    print(f"Replay timeline with: aibrain council replay {council_id}")
    print(f"{'='*60}\n")

    return 0


def council_replay_command(args: Any) -> int:
    """Replay the timeline of a council debate."""
    council_id = args.council_id

    council_dir = COUNCILS_DIR / council_id
    manifest_path = council_dir / "manifest.jsonl"

    if not manifest_path.exists():
        print(f"\n  Council not found: {council_id}")
        print(f"  List councils with: aibrain council list\n")
        return 1

    # Parse manifest
    events = []
    with open(manifest_path) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not events:
        print(f"\n  No events found in manifest for: {council_id}\n")
        return 1

    print(f"\n{'='*60}")
    print(f"  DEBATE TIMELINE: {council_id}")
    print(f"{'='*60}\n")

    for event in events:
        event_type = event.get("event_type") or event.get("event", "unknown")
        timestamp = event.get("timestamp", "")[:19]
        data = event.get("data", {}) if "data" in event else event

        if event_type == "council_init":
            print(f"[{timestamp}] INIT: {data.get('topic', '')}")
            print(f"              Perspectives: {', '.join(data.get('perspectives', []))}")

        elif event_type == "agent_spawn":
            print(f"[{timestamp}] SPAWN: {data.get('agent_id', '')} ({data.get('perspective', '')})")

        elif event_type == "round_start":
            print(f"[{timestamp}] ROUND {data.get('round_number', '?')} START")

        elif event_type == "argument_posted":
            agent = data.get("agent_id", "unknown")
            position = data.get("position", "NEUTRAL")
            confidence = data.get("confidence", 0)
            reasoning = data.get("reasoning", "")[:60]
            print(f"[{timestamp}] ARGUMENT: {agent}")
            print(f"              Position: {position} (confidence: {confidence:.1%})")
            print(f"              \"{reasoning}...\"")

        elif event_type == "round_cost":
            round_num = data.get("round", "?")
            cost = data.get("cumulative_cost", 0)
            print(f"[{timestamp}] ROUND {round_num} COST: ${cost:.4f} cumulative")

        elif event_type == "synthesis":
            rec = data.get("recommendation", "Unknown")
            conf = data.get("confidence", 0)
            print(f"[{timestamp}] SYNTHESIS: {rec} (confidence: {conf:.1%})")

        elif event_type == "cost_summary":
            total = data.get("total_cost", 0)
            print(f"[{timestamp}] FINAL COST: ${total:.4f}")

        elif event_type == "circuit_breaker":
            print(f"[{timestamp}] CIRCUIT BREAKER: {data.get('type', 'Unknown')}")
            print(f"              {data.get('message', '')}")

        elif event_type == "error":
            print(f"[{timestamp}] ERROR: {data.get('error', 'Unknown')}")

        else:
            print(f"[{timestamp}] {event_type.upper()}")

        print()

    print(f"{'='*60}\n")

    return 0


def setup_parser(subparsers: Any) -> None:
    """Setup argparse for council commands."""

    # Main 'council' command
    council_parser = subparsers.add_parser(
        "council",
        help="Multi-perspective debate for architectural decisions",
        description="Run council debates with 5 analyst perspectives"
    )

    council_subparsers = council_parser.add_subparsers(
        dest='council_command',
        help='Council subcommand'
    )

    # council debate
    debate_parser = council_subparsers.add_parser(
        "debate",
        help="Start a new council debate"
    )
    debate_parser.add_argument(
        "--topic", "-t",
        required=True,
        help="The topic/question to debate (e.g., 'Should we adopt LlamaIndex?')"
    )
    debate_parser.add_argument(
        "--rounds", "-r",
        type=int,
        default=3,
        help="Number of debate rounds (default: 3)"
    )
    debate_parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Maximum duration in minutes (default: 30)"
    )
    debate_parser.set_defaults(func=council_debate_command)

    # council list
    list_parser = council_subparsers.add_parser(
        "list",
        help="List recent council debates"
    )
    list_parser.add_argument(
        "--limit", "-n",
        type=int,
        default=10,
        help="Maximum number of debates to show (default: 10)"
    )
    list_parser.set_defaults(func=council_list_command)

    # council show
    show_parser = council_subparsers.add_parser(
        "show",
        help="Show details of a council debate"
    )
    show_parser.add_argument(
        "council_id",
        help="Council ID (e.g., COUNCIL-20260130-123456)"
    )
    show_parser.set_defaults(func=council_show_command)

    # council replay
    replay_parser = council_subparsers.add_parser(
        "replay",
        help="Replay the timeline of a council debate"
    )
    replay_parser.add_argument(
        "council_id",
        help="Council ID to replay"
    )
    replay_parser.set_defaults(func=council_replay_command)
