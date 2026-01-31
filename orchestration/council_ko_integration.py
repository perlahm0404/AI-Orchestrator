"""
Council Pattern - Knowledge Object Integration

Creates Knowledge Objects from council debate results.
Implements the integration specified in council-team.yaml:
- create_ko_on_completion: true
- ko_type: council_decision
- ko_effectiveness_tracking: true

Usage:
    from orchestration.council_ko_integration import create_ko_from_debate

    # After debate completes
    result = await council.run_debate()
    ko = create_ko_from_debate(result)
"""

from typing import Optional
from pathlib import Path

from agents.coordinator.council_orchestrator import DebateResult


def create_ko_from_debate(
    result: DebateResult,
    auto_approve_threshold: float = 0.8
) -> Optional[str]:
    """
    Create a Knowledge Object from a debate result.

    Args:
        result: The DebateResult from a completed council debate
        auto_approve_threshold: Auto-approve KOs with confidence above this threshold

    Returns:
        KO ID if created, None if creation failed

    Per council-team.yaml integration:
    - create_ko_on_completion: true
    - ko_type: council_decision
    - ko_effectiveness_tracking: true
    """
    from knowledge.service import create_draft, approve

    # Build KO content from debate result
    what_was_learned = _build_what_was_learned(result)
    why_it_matters = _build_why_it_matters(result)
    prevention_rule = _build_prevention_rule(result)
    tags = _build_tags(result)

    # Determine project from topic or default
    project = _infer_project(result.topic)

    # Create draft KO
    try:
        ko = create_draft(
            project=project,
            title=f"Council Decision: {_shorten_topic(result.topic)}",
            what_was_learned=what_was_learned,
            why_it_matters=why_it_matters,
            prevention_rule=prevention_rule,
            tags=tags,
            detection_pattern="",  # No detection pattern for council decisions
            file_patterns=[]
        )

        # Auto-approve high-confidence decisions
        # Per council-team.yaml: auto_approve_if confidence_high (>0.85)
        # Using 0.8 as threshold for slightly more conservative approach
        if result.confidence >= auto_approve_threshold:
            approve(ko.id)

        return ko.id

    except Exception as e:
        # Log error but don't fail - KO creation is optional
        print(f"Warning: Failed to create KO from debate: {e}")
        return None


def _build_what_was_learned(result: DebateResult) -> str:
    """Build the 'what was learned' section from debate result."""
    lines = []

    # Main decision
    lines.append(f"Council debate on '{result.topic}' reached a {result.recommendation} recommendation ")
    lines.append(f"with {result.confidence:.0%} confidence.")
    lines.append("")

    # Vote breakdown
    lines.append("Vote breakdown:")
    for position, count in result.vote_breakdown.items():
        if count > 0:
            lines.append(f"  - {position}: {count} agent(s)")

    # Key considerations
    if result.key_considerations:
        lines.append("")
        lines.append("Key considerations from analysts:")
        for consideration in result.key_considerations[:3]:  # Top 3
            lines.append(f"  - {consideration}")

    return "\n".join(lines)


def _build_why_it_matters(result: DebateResult) -> str:
    """Build the 'why it matters' section."""
    lines = []

    if result.recommendation == "ADOPT":
        lines.append("This technology/approach was recommended by the council. ")
        lines.append("Proceeding with adoption is supported by multi-perspective analysis.")
    elif result.recommendation == "REJECT":
        lines.append("This technology/approach was NOT recommended by the council. ")
        lines.append("Alternatives should be considered before proceeding.")
    elif result.recommendation == "CONDITIONAL":
        lines.append("This technology/approach has conditional support from the council. ")
        lines.append("Proceed only if the identified conditions and caveats are addressed.")
    else:  # SPLIT
        lines.append("The council was divided on this decision. ")
        lines.append("Additional analysis, prototyping, or stakeholder input is recommended before committing.")

    # Add cost info if available
    if result.cost_summary:
        cost = result.cost_summary.get("total_cost", 0)
        lines.append(f"\nDebate cost: ${cost:.2f}")

    return "\n".join(lines)


def _build_prevention_rule(result: DebateResult) -> str:
    """Build the 'prevention rule' from key arguments."""
    lines = []

    lines.append(f"Before making similar decisions about '{_category_from_topic(result.topic)}', consult this council decision.")
    lines.append("")
    lines.append("Key perspectives to consider:")

    # Extract unique perspectives from arguments
    perspectives_seen = set()
    for arg in result.arguments:
        if arg.perspective not in perspectives_seen:
            perspectives_seen.add(arg.perspective)
            # First 100 chars of reasoning
            reasoning_summary = arg.reasoning[:100] + "..." if len(arg.reasoning) > 100 else arg.reasoning
            lines.append(f"  - {arg.perspective.title()}: {reasoning_summary}")

    return "\n".join(lines)


def _build_tags(result: DebateResult) -> list[str]:
    """Build tags from debate result."""
    tags = [
        "council",
        "debate",
        result.recommendation.lower(),
    ]

    # Add perspective tags
    for arg in result.arguments:
        if arg.perspective not in tags:
            tags.append(arg.perspective)

    # Add topic-based tags
    topic_lower = result.topic.lower()
    if "llama" in topic_lower or "rag" in topic_lower:
        tags.append("rag")
    if "database" in topic_lower or "postgres" in topic_lower or "jsonb" in topic_lower:
        tags.append("database")
    if "deploy" in topic_lower or "sst" in topic_lower or "vercel" in topic_lower:
        tags.append("deployment")
    if "cache" in topic_lower or "redis" in topic_lower:
        tags.append("caching")
    if "auth" in topic_lower or "security" in topic_lower:
        tags.append("security")

    return list(set(tags))  # Remove duplicates


def _infer_project(topic: str) -> str:
    """Infer project from topic or default to ai-orchestrator."""
    topic_lower = topic.lower()

    if "karematch" in topic_lower or "kare" in topic_lower:
        return "karematch"
    elif "credential" in topic_lower or "hipaa" in topic_lower:
        return "credentialmate"
    else:
        return "ai-orchestrator"


def _shorten_topic(topic: str, max_len: int = 50) -> str:
    """Shorten topic for title."""
    if len(topic) <= max_len:
        return topic
    return topic[:max_len-3] + "..."


def _category_from_topic(topic: str) -> str:
    """Extract category from topic."""
    topic_lower = topic.lower()

    if "adopt" in topic_lower:
        # "Should we adopt X?" -> "X adoption"
        parts = topic_lower.split("adopt")
        if len(parts) > 1:
            return parts[1].strip().rstrip("?").strip() + " adoption"

    if "use" in topic_lower:
        parts = topic_lower.split("use")
        if len(parts) > 1:
            return parts[1].strip().rstrip("?").strip()

    return "technology decisions"


def should_create_ko(result: DebateResult) -> bool:
    """
    Determine if a KO should be created for this debate.

    Returns True for meaningful debates that provide actionable learning.
    """
    # Don't create KO for very low confidence decisions
    if result.confidence < 0.3:
        return False

    # Don't create KO if there were no arguments
    if not result.arguments:
        return False

    # Don't create KO for test councils
    if result.council_id.startswith("TEST-"):
        return False

    return True
