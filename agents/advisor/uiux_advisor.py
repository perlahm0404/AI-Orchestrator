"""
UI/UX Advisor for AI Team
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Specializes in:
- Component architecture
- Accessibility (a11y)
- User experience patterns
- Design system consistency
- Frontend performance

Invoked via: @uiux-advisor
"""

from pathlib import Path
from typing import Dict, List, Any

from .base_advisor import (
    BaseAdvisor,
    AdvisorConfig,
    AdvisorDecision,
    DecisionType,
    DomainType,
)


class UIUXAdvisor(BaseAdvisor):
    """
    Domain expert for UI/UX and frontend concerns.

    Handles questions about:
    - Component structure and organization
    - Accessibility compliance
    - User experience patterns
    - Design system consistency
    - Frontend performance
    """

    def __init__(self, project_root: Path):
        """Initialize UIUXAdvisor."""
        config = AdvisorConfig(
            name="uiux-advisor",
            domain=DomainType.UIUX,
            description="Expert in UI components, accessibility, and user experience",
            domain_patterns=[
                r"component|react|vue|angular|svelte",
                r"accessibility|a11y|aria|screen reader",
                r"responsive|mobile|tablet|breakpoint",
                r"animation|transition|motion",
                r"form|input|validation|error state",
                r"navigation|menu|sidebar|breadcrumb",
                r"modal|dialog|popup|toast",
                r"design system|theme|styling|css",
                r"user experience|ux|usability",
            ],
            handled_tags=[
                "components",
                "accessibility",
                "responsive",
                "forms",
                "navigation",
                "design_system",
            ],
        )
        super().__init__(project_root, config)

        # WCAG guidelines reference
        self.wcag_guidelines = {
            "perceivable": "Information must be presentable in ways users can perceive",
            "operable": "Interface must be operable by all users",
            "understandable": "Information and UI operation must be understandable",
            "robust": "Content must be robust enough for various assistive technologies",
        }

    def get_domain_patterns(self) -> List[str]:
        """Get patterns for UI/UX domain."""
        return self.config.domain_patterns

    def analyze(self, question: str, context: Dict[str, Any]) -> AdvisorDecision:
        """
        Analyze a UI/UX-related question.

        Args:
            question: The question to analyze
            context: Additional context (component info, design specs, etc.)

        Returns:
            AdvisorDecision with recommendation
        """
        # Classify the question
        domain_tags = self.classify_domain(question)

        # Add UI/UX-specific tags
        q_lower = question.lower()
        if "component" in q_lower or "react" in q_lower or "vue" in q_lower:
            domain_tags.append("component_structure")
        if "access" in q_lower or "a11y" in q_lower or "aria" in q_lower:
            domain_tags.append("accessibility")
        if "responsive" in q_lower or "mobile" in q_lower:
            domain_tags.append("responsive_design")
        if "form" in q_lower or "input" in q_lower:
            domain_tags.append("form_design")
        if "navigation" in q_lower or "menu" in q_lower:
            domain_tags.append("navigation")
        if "design" in q_lower or "theme" in q_lower or "style" in q_lower:
            domain_tags.append("design_system")

        # Generate recommendation
        recommendation = self._generate_recommendation(question, context, domain_tags)

        # Check for ADR conflicts
        conflicting_adrs = self.check_adr_conflicts(recommendation, domain_tags)
        aligned_adrs = self.find_aligned_adrs(domain_tags)

        # Calculate confidence
        confidence = self.calculate_confidence(question, recommendation, domain_tags)

        # UI/UX decisions are typically tactical unless they affect design system
        is_strategic = (
            "design_system" in domain_tags and
            any(kw in q_lower for kw in ["new", "change", "update", "replace"])
        )
        decision_type = DecisionType.STRATEGIC if is_strategic else DecisionType.TACTICAL

        return AdvisorDecision(
            advisor=self.config.name,
            question=question,
            recommendation=recommendation,
            confidence=confidence,
            decision_type=decision_type,
            aligned_adrs=aligned_adrs,
            conflicting_adrs=conflicting_adrs,
            domain_tags=domain_tags,
        )

    def _generate_recommendation(
        self,
        question: str,
        context: Dict[str, Any],
        domain_tags: List[str],
    ) -> str:
        """Generate UI/UX-specific recommendation."""
        q_lower = question.lower()
        recommendations = []

        # Component recommendations
        if "component" in q_lower:
            recommendations.extend([
                "Keep components focused on single responsibility",
                "Use composition over inheritance for flexibility",
                "Separate presentational and container components",
                "Document component props with TypeScript or PropTypes",
            ])
            if context.get("framework") == "react":
                recommendations.append(
                    "Consider using React.memo for expensive renders"
                )

        # Accessibility recommendations
        if "access" in q_lower or "a11y" in q_lower:
            recommendations.extend([
                "Use semantic HTML elements (button, nav, main, etc.)",
                "Ensure all interactive elements are keyboard accessible",
                "Add appropriate ARIA labels and roles",
                "Maintain color contrast ratio of at least 4.5:1",
                "Provide text alternatives for non-text content",
                "Test with screen readers (VoiceOver, NVDA)",
            ])

        # Responsive design recommendations
        if "responsive" in q_lower or "mobile" in q_lower:
            recommendations.extend([
                "Use mobile-first approach for CSS",
                "Define consistent breakpoints (sm, md, lg, xl)",
                "Ensure touch targets are at least 44x44 pixels",
                "Test on actual devices, not just browser devtools",
            ])

        # Form design recommendations
        if "form" in q_lower or "input" in q_lower:
            recommendations.extend([
                "Associate labels with inputs using for/id",
                "Show validation errors inline near the field",
                "Provide helpful error messages, not just 'Invalid'",
                "Support autofill for common fields",
                "Mark required fields clearly",
            ])
            if "valid" in q_lower:
                recommendations.append(
                    "Validate on blur for immediate feedback, on submit for final check"
                )

        # Navigation recommendations
        if "navigation" in q_lower or "menu" in q_lower:
            recommendations.extend([
                "Use consistent navigation patterns across the app",
                "Indicate current location clearly",
                "Ensure keyboard navigation works correctly",
                "Consider breadcrumbs for deep hierarchies",
            ])

        # Design system recommendations
        if "design" in q_lower or "theme" in q_lower:
            recommendations.extend([
                "Use design tokens for colors, spacing, typography",
                "Document component variants and states",
                "Maintain consistent spacing scale (4px, 8px, 16px, etc.)",
                "Create reusable style utilities",
            ])

        # Modal/Dialog recommendations
        if "modal" in q_lower or "dialog" in q_lower:
            recommendations.extend([
                "Trap focus within modal when open",
                "Allow closing with Escape key",
                "Return focus to trigger element on close",
                "Prevent background scroll when modal is open",
            ])

        # Animation recommendations
        if "animation" in q_lower or "motion" in q_lower:
            recommendations.extend([
                "Respect prefers-reduced-motion user preference",
                "Keep animations under 300ms for UI feedback",
                "Use easing functions for natural motion",
                "Avoid animations that could cause vestibular issues",
            ])

        # Default if no specific matches
        if not recommendations:
            recommendations.append(
                "Focus on user needs first, then consider implementation details. "
                "Prioritize accessibility and usability over visual polish."
            )

        return "\n".join(f"- {r}" for r in recommendations)

    def analyze_accessibility(
        self,
        component: str,
        current_implementation: str = None,
    ) -> AdvisorDecision:
        """
        Specialized accessibility analysis.

        Args:
            component: Component name or description
            current_implementation: Current HTML/JSX if available

        Returns:
            AdvisorDecision with a11y recommendations
        """
        question = f"Accessibility review for: {component}"
        context = {
            "component": component,
            "implementation": current_implementation,
        }
        return self.consult(question, context)

    def analyze_component_structure(
        self,
        component_name: str,
        responsibilities: List[str],
    ) -> AdvisorDecision:
        """
        Analyze component structure and organization.

        Args:
            component_name: Name of the component
            responsibilities: List of things the component handles

        Returns:
            AdvisorDecision with structure recommendations
        """
        question = f"Component structure review: {component_name}"
        context = {
            "component": component_name,
            "responsibilities": responsibilities,
        }
        return self.consult(question, context)

    def check_wcag_compliance(
        self,
        element_type: str,
        attributes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Quick WCAG compliance check.

        Args:
            element_type: HTML element type
            attributes: Element attributes

        Returns:
            Compliance check results
        """
        issues = []
        suggestions = []

        # Check for interactive elements
        interactive = {"button", "a", "input", "select", "textarea"}
        if element_type in interactive:
            # Check for accessible name
            has_name = any([
                attributes.get("aria-label"),
                attributes.get("aria-labelledby"),
                attributes.get("textContent"),
            ])
            if not has_name:
                issues.append("Missing accessible name")
                suggestions.append("Add aria-label or visible text content")

            # Check for keyboard accessibility
            if element_type == "div" and attributes.get("onClick"):
                issues.append("Non-semantic element with click handler")
                suggestions.append("Use <button> instead of <div> with onClick")

        # Check images
        if element_type == "img":
            if not attributes.get("alt"):
                issues.append("Image missing alt text")
                suggestions.append("Add alt attribute describing the image")

        # Check forms
        if element_type in {"input", "select", "textarea"}:
            if not attributes.get("id") or not attributes.get("label_for"):
                issues.append("Form field may not be properly labeled")
                suggestions.append("Ensure label is associated with for/id")

        return {
            "element": element_type,
            "wcag_compliant": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python uiux_advisor.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    advisor = UIUXAdvisor(project_root)

    # Test consultation
    decision = advisor.consult(
        "How should I structure the user profile component for accessibility?",
        context={"framework": "react"},
    )

    print(f"Advisor: {decision.advisor}")
    print(f"Decision Type: {decision.decision_type.value}")
    print(f"Confidence: {decision.confidence.total:.2%}")
    print(f"Auto-approved: {decision.auto_approved}")
    print(f"Recommendation:\n{decision.recommendation}")

    # Test WCAG check
    result = advisor.check_wcag_compliance("button", {"onClick": True})
    print(f"\nWCAG Check: {result}")
