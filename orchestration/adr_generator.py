"""
ADR Generator

Generates ADR markdown from advisor consultation context.
Populates templates with smart defaults and extracts options from recommendations.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ADRContext:
    """Context for ADR generation from advisor consultation."""
    task_id: str
    description: str
    decision_type: str  # "strategic" | "tactical"
    advisor_type: str   # "data" | "app" | "uiux"
    confidence: float
    domain_tags: List[str]
    aligned_adrs: List[str]
    conflicting_adrs: List[str]
    recommendation: str
    iterations: int
    files_changed: List[str]
    escalated: bool
    escalation_reason: Optional[str]
    fingerprint: str


@dataclass
class OptionSpec:
    """Specification for an ADR option."""
    name: str
    approach: str
    pros: List[str]
    cons: List[str]
    best_for: str


class ADRGenerator:
    """Generates ADR markdown from context."""

    def __init__(self, template_path: Path):
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"ADR template not found: {template_path}")

    def generate_adr_draft(
        self,
        adr_number: int,
        context: ADRContext,
        project: str
    ) -> str:
        """
        Generate ADR markdown using template and context.

        Args:
            adr_number: ADR number (e.g., 6)
            context: ADRContext with all generation data
            project: Project name

        Returns:
            Complete ADR markdown string
        """
        # Read template
        template = self.template_path.read_text()

        # Extract title from description
        title = self._extract_title(context.description)

        # Extract or generate options
        options = self._extract_options_from_recommendation(context.recommendation)

        # Compute file patterns
        applies_to = self._compute_applies_to_patterns(context.files_changed)

        # Estimate complexity
        complexity = self._estimate_complexity(context.files_changed, context.iterations)

        # Build replacement mapping
        replacements = self._build_replacements(
            adr_number, title, context, project, options, applies_to, complexity
        )

        # Perform replacements
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result

    def _extract_title(self, description: str) -> str:
        """Extract concise title from task description."""
        # Remove common prefixes
        title = re.sub(r'^(fix|add|create|update|implement|refactor)\s+', '', description, flags=re.IGNORECASE)

        # Capitalize first letter
        title = title[0].upper() + title[1:] if title else "Decision Record"

        # Truncate if too long
        if len(title) > 80:
            title = title[:77] + "..."

        return title

    def _extract_options_from_recommendation(self, recommendation: str) -> List[OptionSpec]:
        """
        Parse advisor recommendation for Option A/B/C sections.

        Looks for patterns:
        - "Option [A-C]:"
        - "Approach [A-C]:"
        - "Alternative [A-C]:"

        Returns:
            List of OptionSpec objects (min 2, recommended from advisor or defaults)
        """
        options = []

        # Try to find explicit options in recommendation
        option_patterns = [
            r'Option ([A-C]):\s*([^\n]+(?:\n(?!Option|Approach|Alternative)[^\n]+)*)',
            r'Approach ([A-C]):\s*([^\n]+(?:\n(?!Option|Approach|Alternative)[^\n]+)*)',
            r'Alternative ([A-C]):\s*([^\n]+(?:\n(?!Option|Approach|Alternative)[^\n]+)*)',
        ]

        for pattern in option_patterns:
            for match in re.finditer(pattern, recommendation, re.MULTILINE):
                option_name = match.group(1)
                option_text = match.group(2).strip()

                # Parse option details
                option = self._parse_option_text(option_name, option_text)
                if option:
                    options.append(option)

        # If no options found, generate defaults
        if len(options) < 2:
            options = self._generate_default_options(recommendation)

        return options

    def _parse_option_text(self, name: str, text: str) -> Optional[OptionSpec]:
        """Parse option text to extract structure."""
        # Extract pros and cons
        pros = []
        cons = []

        pro_matches = re.findall(r'(?:Pro|Benefit|Advantage):\s*([^\n]+)', text, re.IGNORECASE)
        con_matches = re.findall(r'(?:Con|Drawback|Disadvantage):\s*([^\n]+)', text, re.IGNORECASE)

        pros.extend(pro_matches)
        cons.extend(con_matches)

        # Extract "best for" if present
        best_for_match = re.search(r'(?:Best for|Ideal for|Use when):\s*([^\n]+)', text, re.IGNORECASE)
        best_for = best_for_match.group(1) if best_for_match else "General use cases"

        # Remove pros/cons/best_for from approach text
        approach = re.sub(r'(?:Pro|Con|Benefit|Drawback|Advantage|Disadvantage|Best for|Ideal for|Use when):[^\n]+', '', text, flags=re.IGNORECASE)
        approach = approach.strip()

        # Default pros/cons if none found
        if not pros:
            pros = ["Aligns with advisor recommendation"]
        if not cons:
            cons = ["Requires careful implementation"]

        return OptionSpec(
            name=name,
            approach=approach or text[:100],
            pros=pros,
            cons=cons,
            best_for=best_for
        )

    def _generate_default_options(self, recommendation: str) -> List[OptionSpec]:
        """Generate default options when none are found in recommendation."""
        # Option A: Current approach (implied)
        option_a = OptionSpec(
            name="A",
            approach="Continue with current implementation patterns",
            pros=["Maintains consistency", "Familiar to team"],
            cons=["May not address underlying issues"],
            best_for="When current approach is sufficient"
        )

        # Option B: Recommended approach (from advisor)
        option_b = OptionSpec(
            name="B",
            approach=recommendation[:200] if len(recommendation) > 200 else recommendation,
            pros=["Advisor-recommended solution", "Addresses identified concerns"],
            cons=["Requires implementation effort"],
            best_for="When following best practices"
        )

        return [option_a, option_b]

    def _compute_applies_to_patterns(self, files_changed: List[str]) -> List[str]:
        """
        Convert file paths to glob patterns for applies_to field.

        Example:
            ["src/auth/session.py", "src/auth/token.py"]
            → ["src/auth/**"]
        """
        if not files_changed:
            return ["**/*"]

        # Group by directory
        directories = set()
        for file_path in files_changed:
            path = Path(file_path)
            if len(path.parts) > 1:
                # Use parent directory
                directories.add(str(path.parent) + "/**")
            else:
                # Top-level file
                directories.add(file_path)

        return sorted(list(directories))

    def _estimate_complexity(self, files_changed: List[str], iterations: int) -> str:
        """
        Estimate complexity for Implementation Notes.

        Rules:
        - iterations ≥5 OR files >10 → "High"
        - iterations ≥3 OR files >5 → "Medium"
        - otherwise → "Low"
        """
        file_count = len(files_changed)

        if iterations >= 5 or file_count > 10:
            return "High"
        elif iterations >= 3 or file_count > 5:
            return "Medium"
        else:
            return "Low"

    def _build_replacements(
        self,
        adr_number: int,
        title: str,
        context: ADRContext,
        project: str,
        options: List[OptionSpec],
        applies_to: List[str],
        complexity: str
    ) -> Dict[str, str]:
        """Build complete replacement mapping for template."""
        adr_id = f"ADR-{adr_number:03d}"
        date = datetime.now().strftime('%Y-%m-%d')

        # Base replacements
        replacements = {
            "{{NUMBER}}": f"{adr_number:03d}",
            "{{TITLE}}": title,
            "{{DATE}}": date,
            "{{HUMAN_NAME}}": "tmac",  # Default, will be updated on approval
            "{{TAGS}}": ", ".join(f'"{tag}"' for tag in context.domain_tags),
            "{{FILE_PATTERN_1}}": applies_to[0] if applies_to else "**/*",
            "{{FILE_PATTERN_2}}": applies_to[1] if len(applies_to) > 1 else "",
            "{{DOMAINS}}": ", ".join(f'"{domain}"' for domain in context.domain_tags),
            "{{CONTEXT}}": self._generate_context_section(context),
            "{{DECISION}}": context.recommendation[:500],  # First 500 chars
            "{{RATIONALE}}": self._generate_rationale_section(context),
            "{{SCHEMA_CHANGES}}": "None" if context.advisor_type != "data" else "To be determined during implementation",
            "{{API_CHANGES}}": "None" if context.advisor_type != "app" else "To be determined during implementation",
            "{{UI_CHANGES}}": "None" if context.advisor_type != "uiux" else "To be determined during implementation",
            "{{ESTIMATED_FILES}}": str(len(context.files_changed)),
            "{{DEPENDENCIES}}": ", ".join(context.aligned_adrs) if context.aligned_adrs else "None identified",
            "{{CONSEQUENCE_ENABLES_1}}": f"Implementation of {title.lower()}",
            "{{CONSEQUENCE_ENABLES_2}}": "Improved code quality and maintainability",
            "{{CONSEQUENCE_CONSTRAINS_1}}": "Future changes must align with this decision",
            "{{CONSEQUENCE_CONSTRAINS_2}}": "May require updates to related components",
            "{{RELATED_ADR_1}}": self._format_related_adrs(context.aligned_adrs, context.conflicting_adrs)[0] if context.aligned_adrs or context.conflicting_adrs else "None",
            "{{RELATED_ADR_2}}": self._format_related_adrs(context.aligned_adrs, context.conflicting_adrs)[1] if (context.aligned_adrs or context.conflicting_adrs) and len(context.aligned_adrs) + len(context.conflicting_adrs) > 1 else "",
            "{{ADVISOR_NAME}}": f"{context.advisor_type}-advisor",
            "{{CREATED_TIMESTAMP}}": datetime.now().isoformat(),
            "{{APPROVED_TIMESTAMP}}": "",
            "{{APPROVER}}": "",
            "{{CONFIDENCE}}": str(int(context.confidence * 100)),
            "{{AUTO_DECIDED}}": str(not context.escalated).lower(),
            "{{ESCALATION_REASON}}": context.escalation_reason or "N/A",
        }

        # Add option replacements
        for i, option in enumerate(options[:3]):  # Max 3 options
            if i == 0:
                prefix = "OPTION_A"
            elif i == 1:
                prefix = "OPTION_B"
            else:
                prefix = "OPTION_C"

            replacements[f"{{{{  {prefix}_NAME}}}}"] = option.name
            replacements[f"{{{{{prefix}_NAME}}}}"] = option.name
            replacements[f"{{{{{prefix}_DESCRIPTION}}}}"] = option.approach
            replacements[f"{{{{{prefix}_PRO}}}}"] = option.pros[0] if option.pros else "N/A"
            replacements[f"{{{{{prefix}_CON}}}}"] = option.cons[0] if option.cons else "N/A"
            replacements[f"{{{{{prefix}_USE_CASE}}}}"] = option.best_for

        # Additional options (if more than 2)
        if len(options) > 2:
            additional = self._format_additional_options(options[2:])
            replacements["{{ADDITIONAL_OPTIONS}}"] = additional
        else:
            replacements["{{ADDITIONAL_OPTIONS}}"] = ""

        return replacements

    def _generate_context_section(self, context: ADRContext) -> str:
        """Generate Context section from task details."""
        lines = [
            f"**Task**: {context.description}",
            f"**Iterations**: {context.iterations} iteration(s) to reach solution",
            f"**Type**: {context.decision_type.capitalize()} decision",
        ]

        if context.escalated:
            lines.append(f"**Escalation**: {context.escalation_reason}")

        return "\n\n".join(lines)

    def _generate_rationale_section(self, context: ADRContext) -> str:
        """Generate Rationale section from context."""
        lines = []

        if context.escalated and context.escalation_reason:
            lines.append(f"**Escalation Reason**: {context.escalation_reason}")

        if context.conflicting_adrs:
            lines.append(f"**Resolves Conflicts**: This decision addresses conflicts with {', '.join(context.conflicting_adrs)}")

        if context.aligned_adrs:
            lines.append(f"**Aligns With**: {', '.join(context.aligned_adrs)}")

        lines.append(f"\n**Confidence**: {int(context.confidence * 100)}% confidence based on advisor analysis")

        if not lines:
            lines.append("Advisor recommendation based on domain expertise and analysis.")

        return "\n\n".join(lines)

    def _format_related_adrs(self, aligned: List[str], conflicting: List[str]) -> List[str]:
        """Format related ADRs for display."""
        related = []

        for adr in aligned:
            related.append(f"{adr} (aligned)")

        for adr in conflicting:
            related.append(f"{adr} (conflicting - see Rationale)")

        # Pad to at least 2 entries
        while len(related) < 2:
            related.append("")

        return related

    def _format_additional_options(self, options: List[OptionSpec]) -> str:
        """Format additional options (beyond A and B) for template."""
        lines = []

        for option in options:
            lines.append(f"\n### Option {option.name}: {option.name}")
            lines.append(f"\n**Approach**: {option.approach}")
            lines.append("\n**Tradeoffs**:")
            for pro in option.pros:
                lines.append(f"- Pro: {pro}")
            for con in option.cons:
                lines.append(f"- Con: {con}")
            lines.append(f"\n**Best for**: {option.best_for}")

        return "\n".join(lines)


def generate_title_slug(title: str) -> str:
    """
    Generate URL-friendly slug from title.

    Example:
        "Provider Report Generation" → "provider-report-generation"
    """
    # Convert to lowercase
    slug = title.lower()

    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug
