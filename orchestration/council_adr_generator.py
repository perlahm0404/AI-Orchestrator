"""
CouncilADRGenerator - Generates ADRs from council debate results.

Converts DebateResult into formatted ADR markdown using council template.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from agents.coordinator.council_orchestrator import DebateResult


class CouncilADRGenerator:
    """
    Generates ADR markdown from council debate results.

    Usage:
        generator = CouncilADRGenerator()
        adr_markdown = generator.generate_from_debate(
            adr_number=42,
            result=debate_result,
            context="CredentialMate needs RAG for physician license verification"
        )
    """

    def __init__(self, template_path: Path = None):
        """
        Initialize generator.

        Args:
            template_path: Path to council ADR template (defaults to templates/adr/council-debate-template.md)
        """
        if template_path is None:
            # Default to council template in this repo
            orchestrator_root = Path(__file__).parent.parent
            template_path = orchestrator_root / "templates" / "adr" / "council-debate-template.md"

        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Council ADR template not found: {template_path}")

    def generate_from_debate(
        self,
        adr_number: int,
        result: DebateResult,
        context: str,
        status: str = "Proposed",
        approved_by: str = "Pending"
    ) -> str:
        """
        Generate ADR markdown from debate result.

        Args:
            adr_number: ADR number (e.g., 42 for ADR-042)
            result: DebateResult from council debate
            context: Background context for the decision
            status: ADR status (default: "Proposed")
            approved_by: Who approved it (default: "Pending")

        Returns:
            Complete ADR markdown string
        """
        # Read template
        template = self.template_path.read_text()

        # Build replacements
        replacements = {
            "{ADR_NUMBER}": f"{adr_number:03d}",
            "{TITLE}": self._extract_title(result.topic),
            "{STATUS}": status,
            "{DATE}": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "{DECISION_TYPE}": self._determine_decision_type(result),
            "{COUNCIL_ID}": result.council_id,
            "{CONTEXT}": context,
            "{TOPIC}": result.topic,
            "{PERSPECTIVES_COUNT}": str(len(result.vote_breakdown)),
            "{PERSPECTIVES_LIST}": self._format_perspectives_list(result),
            "{DURATION}": f"{result.duration_seconds:.1f} seconds",
            "{ROUNDS}": "3",  # Standard council pattern
            "{VOTE_BREAKDOWN}": self._format_vote_breakdown(result),
            "{AGENT_POSITIONS}": self._format_agent_positions(result),
            "{RECOMMENDATION}": result.recommendation,
            "{CONFIDENCE}": f"{result.confidence:.2f}",
            "{KEY_CONSIDERATIONS}": self._format_key_considerations(result),
            "{POSITIVE_CONSEQUENCES}": self._extract_positive_consequences(result),
            "{NEGATIVE_CONSEQUENCES}": self._extract_negative_consequences(result),
            "{RISKS}": self._extract_risks(result),
            "{IMPLEMENTATION_NOTES}": self._extract_implementation_notes(result),
            "{ALTERNATIVES}": self._extract_alternatives(result),
            "{MANIFEST_PATH}": result.manifest_path,
            "{TIMELINE_SUMMARY}": self._generate_timeline_summary(result),
            "{COUNCIL_PARTICIPANTS}": self._format_participants(result),
            "{GENERATED_TIMESTAMP}": datetime.now(timezone.utc).isoformat(),
            "{APPROVED_BY}": approved_by
        }

        # Perform replacements
        adr_markdown = template
        for placeholder, value in replacements.items():
            adr_markdown = adr_markdown.replace(placeholder, value)

        return adr_markdown

    def _extract_title(self, topic: str) -> str:
        """Extract concise title from debate topic."""
        # Remove question marks, truncate to 80 chars
        title = topic.replace("?", "").strip()
        if len(title) > 80:
            title = title[:77] + "..."
        return title

    def _determine_decision_type(self, result: DebateResult) -> str:
        """Determine if decision is strategic or tactical."""
        # Strategic if security/compliance mentioned or high impact
        strategic_keywords = ["hipaa", "security", "compliance", "database", "migration", "architecture"]

        for arg in result.arguments:
            if any(keyword in arg.reasoning.lower() for keyword in strategic_keywords):
                return "Strategic"

        return "Tactical"

    def _format_perspectives_list(self, result: DebateResult) -> str:
        """Format list of perspectives analyzed."""
        perspectives = {arg.perspective for arg in result.arguments}
        return ", ".join(sorted(perspectives))

    def _format_vote_breakdown(self, result: DebateResult) -> str:
        """Format vote breakdown table."""
        lines = ["| Position | Count | Percentage |", "|----------|-------|------------|"]

        total = sum(result.vote_breakdown.values())
        for position, count in sorted(result.vote_breakdown.items()):
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"| {position} | {count} | {pct:.1f}% |")

        return "\n".join(lines)

    def _format_agent_positions(self, result: DebateResult) -> str:
        """Format agent positions with reasoning."""
        lines = []

        # Group arguments by agent (take latest from each)
        latest_by_agent = {}
        for arg in result.arguments:
            if arg.agent_id not in latest_by_agent or arg.round_number > latest_by_agent[arg.agent_id].round_number:
                latest_by_agent[arg.agent_id] = arg

        for agent_id, arg in sorted(latest_by_agent.items()):
            lines.append(f"### {arg.perspective.title()} Analysis ({arg.position.value})")
            lines.append(f"**Confidence**: {arg.confidence:.2f}")
            lines.append(f"\n{arg.reasoning}\n")

            if arg.evidence:
                lines.append("**Evidence**:")
                for evidence in arg.evidence[:3]:  # Top 3 evidence items
                    lines.append(f"- {evidence}")
                lines.append("")

        return "\n".join(lines)

    def _format_key_considerations(self, result: DebateResult) -> str:
        """Format key considerations as bullet list."""
        if not result.key_considerations:
            return "- No specific considerations identified"

        return "\n".join(f"- {consideration}" for consideration in result.key_considerations)

    def _extract_positive_consequences(self, result: DebateResult) -> str:
        """Extract positive consequences from SUPPORT arguments."""
        positives = []

        for arg in result.arguments:
            if arg.position.value == "SUPPORT":
                # Extract first sentence or first 150 chars
                reasoning = arg.reasoning.split('.')[0] if '.' in arg.reasoning else arg.reasoning[:150]
                positives.append(f"- **{arg.perspective.title()}**: {reasoning}")

        return "\n".join(positives) if positives else "- None identified"

    def _extract_negative_consequences(self, result: DebateResult) -> str:
        """Extract negative consequences from OPPOSE arguments."""
        negatives = []

        for arg in result.arguments:
            if arg.position.value == "OPPOSE":
                reasoning = arg.reasoning.split('.')[0] if '.' in arg.reasoning else arg.reasoning[:150]
                negatives.append(f"- **{arg.perspective.title()}**: {reasoning}")

        return "\n".join(negatives) if negatives else "- None identified"

    def _extract_risks(self, result: DebateResult) -> str:
        """Extract risks from arguments."""
        risks = []

        for arg in result.arguments:
            # Look for risk-related keywords
            if any(keyword in arg.reasoning.lower() for keyword in ["risk", "concern", "issue", "problem", "challenge"]):
                # Extract sentence containing risk keyword
                sentences = arg.reasoning.split('.')
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in ["risk", "concern", "issue", "problem"]):
                        risks.append(f"- **{arg.perspective.title()}**: {sentence.strip()}")
                        break

        return "\n".join(risks[:5]) if risks else "- No significant risks identified"

    def _extract_implementation_notes(self, result: DebateResult) -> str:
        """Extract implementation guidance from arguments."""
        notes = []

        # Extract from integration and alternatives perspectives
        for arg in result.arguments:
            if arg.perspective in ["integration", "alternatives"]:
                # Look for actionable recommendations
                if any(keyword in arg.reasoning.lower() for keyword in ["recommend", "should", "need to", "requires"]):
                    sentences = arg.reasoning.split('.')
                    for sentence in sentences:
                        if any(keyword in sentence.lower() for keyword in ["recommend", "should", "need"]):
                            notes.append(f"- {sentence.strip()}")
                            break

        if not notes:
            if result.recommendation == "ADOPT":
                notes.append("- Proceed with adoption following team's standard implementation process")
            elif result.recommendation == "REJECT":
                notes.append("- Do not proceed with this approach")
            elif result.recommendation == "CONDITIONAL":
                notes.append("- Proceed with caution, address concerns identified in debate")
            else:
                notes.append("- Further analysis required before proceeding")

        return "\n".join(notes[:5])

    def _extract_alternatives(self, result: DebateResult) -> str:
        """Extract alternatives from alternatives perspective."""
        for arg in result.arguments:
            if arg.perspective == "alternatives":
                # Return full reasoning from alternatives agent
                return arg.reasoning

        return "No alternatives analysis performed."

    def _generate_timeline_summary(self, result: DebateResult) -> str:
        """Generate brief timeline summary."""
        round_counts = {}
        for arg in result.arguments:
            round_counts[arg.round_number] = round_counts.get(arg.round_number, 0) + 1

        rounds_summary = ", ".join(f"R{r}: {c} args" for r, c in sorted(round_counts.items()))
        return f"{len(result.arguments)} total arguments ({rounds_summary})"

    def _format_participants(self, result: DebateResult) -> str:
        """Format council participants list."""
        participants = {}
        for arg in result.arguments:
            participants[arg.agent_id] = arg.perspective

        lines = []
        for agent_id, perspective in sorted(participants.items()):
            lines.append(f"- `{agent_id}` ({perspective.title()} Analyst)")

        return "\n".join(lines)
