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
    use_llm = getattr(args, 'llm', False)

    print(f"\n{'='*60}")
    print(f"  COUNCIL DEBATE")
    print(f"{'='*60}\n")
    print(f"Topic: {topic}")
    print(f"Rounds: {rounds}")
    print(f"Timeout: {timeout} minutes")
    print(f"Mode: {'LLM-powered' if use_llm else 'Pattern-based'}")
    print()

    # Create agent types - use LLM-powered if --llm flag is set
    if use_llm:
        agent_types = _create_llm_agents()
    else:
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


def _create_llm_agents() -> dict[str, Any]:
    """
    Create LLM-powered agent factories.

    Uses Claude for dynamic analysis and rebuttals.
    """
    from agents.coordinator.llm_debate_agent import create_llm_agent

    def make_llm_factory(perspective: str) -> Any:
        def factory(agent_id: str, context: Any, message_bus: Any, persp: str) -> Any:
            return create_llm_agent(
                perspective=persp,
                agent_id=agent_id,
                context=context,
                message_bus=message_bus,
                use_llm=True
            )
        return factory

    return {
        "cost": make_llm_factory("cost"),
        "integration": make_llm_factory("integration"),
        "performance": make_llm_factory("performance"),
        "alternatives": make_llm_factory("alternatives"),
        "security": make_llm_factory("security"),
    }


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


def council_outcome_command(args: Any) -> int:
    """Record the outcome of a council decision."""
    from orchestration.council_effectiveness import record_outcome, Outcome

    council_id = args.council_id
    outcome = args.outcome.upper()
    notes = getattr(args, 'notes', '') or ''

    # Validate outcome
    valid_outcomes = [o.value for o in Outcome if o != Outcome.PENDING]
    if outcome not in valid_outcomes:
        print(f"\n  Invalid outcome: {outcome}")
        print(f"  Valid options: {', '.join(valid_outcomes)}\n")
        return 1

    record = record_outcome(
        council_id=council_id,
        outcome=outcome,
        notes=notes,
        recorded_by="cli"
    )

    print(f"\n{'='*60}")
    print(f"  OUTCOME RECORDED")
    print(f"{'='*60}\n")
    print(f"Council: {record.council_id}")
    print(f"Recommendation: {record.recommendation}")
    print(f"Confidence: {record.confidence:.1%}")
    print(f"Outcome: {record.outcome.value}")
    if notes:
        print(f"Notes: {notes}")
    print()
    print(f"{'='*60}\n")

    return 0


def council_perspectives_command(args: Any) -> int:
    """List available perspectives for council debates."""
    from agents.coordinator.agent_templates import list_perspectives, BUILTIN_PERSPECTIVES

    perspectives = list_perspectives()

    print(f"\n{'='*60}")
    print(f"  AVAILABLE PERSPECTIVES ({len(perspectives)})")
    print(f"{'='*60}\n")

    print("Built-in Perspectives:")
    for name, template in perspectives.items():
        if name in BUILTIN_PERSPECTIVES:
            print(f"  {name}: {template.focus}")
    print()

    custom = {k: v for k, v in perspectives.items() if k not in BUILTIN_PERSPECTIVES}
    if custom:
        print("Custom Perspectives:")
        for name, template in custom.items():
            print(f"  {name}: {template.focus}")
        print()

    print("Add custom perspective with:")
    print("  aibrain council add-perspective --name NAME --focus \"DESCRIPTION\"")
    print(f"\n{'='*60}\n")

    return 0


def council_add_perspective_command(args: Any) -> int:
    """Add a custom perspective for council debates."""
    from agents.coordinator.agent_templates import register_perspective

    name = args.name.lower().replace(" ", "_")
    focus = args.focus
    prompt = getattr(args, 'prompt', None)
    tags = getattr(args, 'tags', None)
    if tags:
        tags = [t.strip() for t in tags.split(",")]

    try:
        template = register_perspective(
            name=name,
            focus=focus,
            analysis_prompt=prompt,
            tags=tags
        )

        print(f"\n{'='*60}")
        print(f"  PERSPECTIVE CREATED")
        print(f"{'='*60}\n")
        print(f"Name: {template.name}")
        print(f"Display: {template.display_name}")
        print(f"Focus: {template.focus}")
        print(f"Tags: {', '.join(template.tags)}")
        print()
        print("Use in debates with:")
        print(f"  Custom perspectives are automatically available")
        print(f"\n{'='*60}\n")

        return 0

    except ValueError as e:
        print(f"\n  Error: {e}\n")
        return 1


def council_metrics_command(args: Any) -> int:
    """Show council debate metrics and effectiveness."""
    from orchestration.council_effectiveness import get_effectiveness_report, get_council_stats

    stats = get_council_stats()
    effectiveness = get_effectiveness_report()

    print(f"\n{'='*60}")
    print(f"  COUNCIL DEBATE METRICS")
    print(f"{'='*60}\n")

    # Overall stats
    print("Overall Statistics:")
    print(f"  Total debates: {stats['total_debates']}")
    print(f"  Total cost: ${stats['total_cost']:.2f}")
    print(f"  Avg cost/debate: ${stats['avg_cost_per_debate']:.2f}")
    print()

    # Recommendation distribution
    if stats['recommendation_distribution']:
        print("Recommendation Distribution:")
        for rec, count in stats['recommendation_distribution'].items():
            pct = count / max(stats['total_debates'], 1) * 100
            print(f"  {rec}: {count} ({pct:.0f}%)")
        print()

    # Effectiveness
    print("Effectiveness:")
    print(f"  Outcomes recorded: {effectiveness['total_decisions']}")
    print(f"  Success rate: {effectiveness['success_rate']:.1f}%")
    print()

    if effectiveness['outcomes']:
        print("Outcome Breakdown:")
        for outcome, count in effectiveness['outcomes'].items():
            print(f"  {outcome}: {count}")
        print()

    # By confidence band
    if effectiveness['by_confidence_band']:
        print("Success Rate by Confidence:")
        for band, data in effectiveness['by_confidence_band'].items():
            if data['total'] > 0:
                rate = data['success'] / data['total'] * 100
                print(f"  {band}: {rate:.0f}% ({data['success']}/{data['total']})")
        print()

    # Recent outcomes
    if effectiveness['recent_outcomes']:
        print("Recent Outcomes:")
        for outcome in effectiveness['recent_outcomes'][:5]:
            print(f"  {outcome['council_id']}: {outcome['outcome']} ({outcome['recommendation']})")
        print()

    print(f"For detailed dashboard: aibrain council dashboard")
    print(f"{'='*60}\n")

    return 0


def council_dashboard_command(args: Any) -> int:
    """Show comprehensive council dashboard with trends and quality metrics."""
    from orchestration.council_dashboard import get_dashboard_data

    days = getattr(args, 'days', 30)
    data = get_dashboard_data(days=days)

    print(f"\n{'='*70}")
    print(f"  COUNCIL PATTERN DASHBOARD ({days} day analysis)")
    print(f"{'='*70}\n")

    # Summary Section
    summary = data["summary"]
    print("SUMMARY")
    print("-" * 40)
    print(f"  Total debates:       {summary['total_debates']}")
    print(f"  Total cost:          ${summary['total_cost']:.2f}")
    print(f"  Avg cost/debate:     ${summary['avg_cost_per_debate']:.4f}")
    print(f"  Avg confidence:      {summary['avg_confidence']:.0%}")
    print(f"  Most common rec:     {summary['most_common_recommendation']}")
    print(f"  Success rate:        {summary['success_rate']:.1f}%")
    print(f"  Outcomes recorded:   {summary['outcomes_recorded']}")
    print()

    # Cost Analysis
    cost = data["cost_analysis"]
    print("COST ANALYSIS")
    print("-" * 40)
    print(f"  Total spent:         ${cost['total']:.2f}")
    print(f"  Average/debate:      ${cost['average']:.4f}")
    print(f"  Min/Max:             ${cost['min']:.4f} / ${cost['max']:.4f}")
    print(f"  Budget utilization:  {cost['budget_utilization']:.1f}% of $2.00 limit")
    print()

    # Recommendation Distribution
    recs = data["recommendations"]
    if recs:
        print("RECOMMENDATION DISTRIBUTION")
        print("-" * 40)
        for rec, stats in recs.items():
            bar = "█" * int(stats['percentage'] / 5)  # 20 char max
            print(f"  {rec:12} {bar:20} {stats['count']:3} ({stats['percentage']:.0f}%)")
            print(f"               avg conf: {stats['avg_confidence']:.0%}  avg cost: ${stats['avg_cost']:.4f}")
        print()

    # Trends
    trends = data["trends"]
    if trends:
        print("WEEKLY TRENDS")
        print("-" * 40)
        for t in trends[-8:]:  # Last 8 periods
            print(f"  {t['period']:12} | {t['debates']:3} debates | "
                  f"conf: {t['avg_confidence']:.0%} | ${t['avg_cost']:.4f} | {t['dominant_recommendation']}")
        print()

    # Quality Metrics (recent debates)
    quality = data["quality"]
    if quality:
        print("DEBATE QUALITY (recent)")
        print("-" * 40)
        for q in quality[:5]:
            consensus_bar = "●" * int(q['consensus_strength'] * 5)
            print(f"  {q['council_id']}")
            print(f"    Args: {q['total_arguments']}  Consensus: {consensus_bar:5}  "
                  f"Efficiency: {q['cost_efficiency']:.0f}")
        print()

    print(f"{'='*70}")
    print(f"Record outcomes: aibrain council outcome <ID> SUCCESS|FAILURE")
    print(f"{'='*70}\n")

    return 0


def council_learn_command(args: Any) -> int:
    """Show and manage learned debate patterns."""
    from agents.coordinator.debate_learning import DebateLearner

    learner = DebateLearner()

    # Search for patterns by topic
    if args.topic:
        matches = learner.find_similar(args.topic)

        print(f"\n{'='*60}")
        print(f"  PATTERNS MATCHING: {args.topic[:40]}")
        print(f"{'='*60}\n")

        if not matches:
            print("  No matching patterns found.\n")
            return 0

        for pattern in matches:
            print(f"Pattern: {pattern.topic_pattern}")
            print(f"  Recommendation: {pattern.recommendation}")
            print(f"  Confidence: {pattern.confidence:.1%}")
            print(f"  Success Rate: {pattern.success_rate:.1%} ({pattern.outcome_count} outcomes)")
            if pattern.key_factors:
                print(f"  Key Factors: {', '.join(pattern.key_factors[:3])}")
            print()

        print(f"{'='*60}\n")
        return 0

    # List all patterns
    if args.list or not args.topic:
        patterns = list(learner._patterns.values())

        print(f"\n{'='*60}")
        print(f"  LEARNED PATTERNS ({len(patterns)})")
        print(f"{'='*60}\n")

        if not patterns:
            print("  No learned patterns yet.")
            print("  Patterns are learned automatically from completed debates.\n")
            return 0

        # Sort by success rate
        patterns.sort(key=lambda p: p.success_rate, reverse=True)

        for pattern in patterns:
            print(f"{pattern.topic_pattern}")
            print(f"  → {pattern.recommendation} (conf: {pattern.confidence:.0%}, success: {pattern.success_rate:.0%})")
            print()

        print(f"Search patterns: aibrain council learn --topic \"your topic\"")
        print(f"{'='*60}\n")
        return 0

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
    debate_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM-powered agents for dynamic analysis (requires ANTHROPIC_API_KEY)"
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

    # council outcome
    outcome_parser = council_subparsers.add_parser(
        "outcome",
        help="Record the outcome of a council decision"
    )
    outcome_parser.add_argument(
        "council_id",
        help="Council ID to record outcome for"
    )
    outcome_parser.add_argument(
        "outcome",
        choices=["SUCCESS", "PARTIAL", "FAILURE", "CANCELLED"],
        help="Outcome of the decision"
    )
    outcome_parser.add_argument(
        "--notes", "-n",
        default="",
        help="Additional notes about the outcome"
    )
    outcome_parser.set_defaults(func=council_outcome_command)

    # council metrics
    metrics_parser = council_subparsers.add_parser(
        "metrics",
        help="Show council debate metrics and effectiveness"
    )
    metrics_parser.set_defaults(func=council_metrics_command)

    # council perspectives
    perspectives_parser = council_subparsers.add_parser(
        "perspectives",
        help="List available perspectives for debates"
    )
    perspectives_parser.set_defaults(func=council_perspectives_command)

    # council add-perspective
    add_perspective_parser = council_subparsers.add_parser(
        "add-perspective",
        help="Add a custom perspective for debates"
    )
    add_perspective_parser.add_argument(
        "--name", "-n",
        required=True,
        help="Name for the perspective (e.g., 'compliance')"
    )
    add_perspective_parser.add_argument(
        "--focus", "-f",
        required=True,
        help="What this perspective focuses on"
    )
    add_perspective_parser.add_argument(
        "--prompt", "-p",
        help="Custom analysis prompt (auto-generated if not provided)"
    )
    add_perspective_parser.add_argument(
        "--tags", "-t",
        help="Comma-separated tags for KO lookup"
    )
    add_perspective_parser.set_defaults(func=council_add_perspective_command)

    # council dashboard
    dashboard_parser = council_subparsers.add_parser(
        "dashboard",
        help="Show comprehensive council dashboard with trends and quality"
    )
    dashboard_parser.add_argument(
        "--days", "-d",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)"
    )
    dashboard_parser.set_defaults(func=council_dashboard_command)

    # council learn
    learn_parser = council_subparsers.add_parser(
        "learn",
        help="Show and manage learned debate patterns"
    )
    learn_parser.add_argument(
        "--topic", "-t",
        help="Search for patterns matching a topic"
    )
    learn_parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all learned patterns"
    )
    learn_parser.set_defaults(func=council_learn_command)
