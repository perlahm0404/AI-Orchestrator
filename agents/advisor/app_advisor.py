"""
App Advisor for AI Team
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Specializes in:
- Application architecture
- API design
- Design patterns
- Code organization
- Performance optimization

Invoked via: @app-advisor
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


class AppAdvisor(BaseAdvisor):
    """
    Domain expert for application architecture and design.

    Handles questions about:
    - System architecture
    - API design and versioning
    - Design patterns
    - Code organization
    - Performance and scalability
    """

    def __init__(self, project_root: Path):
        """Initialize AppAdvisor."""
        config = AdvisorConfig(
            name="app-advisor",
            domain=DomainType.APP,
            description="Expert in application architecture, APIs, and design patterns",
            domain_patterns=[
                r"architecture|design pattern|pattern",
                r"api|endpoint|rest|graphql",
                r"service|controller|model|repository",
                r"dependency injection|di|ioc",
                r"microservice|monolith|modular",
                r"cache|caching|redis|memcached",
                r"queue|async|background job",
                r"error handling|exception|retry",
                r"logging|monitoring|observability",
            ],
            handled_tags=[
                "architecture",
                "api_design",
                "patterns",
                "performance",
                "services",
                "error_handling",
            ],
        )
        super().__init__(project_root, config)

        # Architecture patterns for recommendations
        self.patterns = {
            "layered": "Separate concerns into presentation, business, and data layers",
            "hexagonal": "Use ports and adapters for loose coupling",
            "cqrs": "Separate read and write operations for complex domains",
            "event_driven": "Use events for decoupled communication",
            "repository": "Abstract data access behind repository interfaces",
        }

    def get_domain_patterns(self) -> List[str]:
        """Get patterns for app domain."""
        return self.config.domain_patterns

    def analyze(self, question: str, context: Dict[str, Any]) -> AdvisorDecision:
        """
        Analyze an architecture-related question.

        Args:
            question: The question to analyze
            context: Additional context (codebase info, requirements, etc.)

        Returns:
            AdvisorDecision with recommendation
        """
        # Classify the question
        domain_tags = self.classify_domain(question)

        # Add app-specific tags
        q_lower = question.lower()
        if "api" in q_lower or "endpoint" in q_lower:
            domain_tags.append("api_design")
        if "architect" in q_lower or "structure" in q_lower:
            domain_tags.append("architecture")
        if "pattern" in q_lower:
            domain_tags.append("design_patterns")
        if "performance" in q_lower or "scale" in q_lower:
            domain_tags.append("performance")
        if "error" in q_lower or "exception" in q_lower:
            domain_tags.append("error_handling")

        # Generate recommendation
        recommendation = self._generate_recommendation(question, context, domain_tags)

        # Check for ADR conflicts
        conflicting_adrs = self.check_adr_conflicts(recommendation, domain_tags)
        aligned_adrs = self.find_aligned_adrs(domain_tags)

        # Calculate confidence
        confidence = self.calculate_confidence(question, recommendation, domain_tags)

        # Determine decision type
        is_strategic = (
            "api_versioning" in domain_tags or
            "breaking_changes" in domain_tags or
            "external_integrations" in domain_tags or
            any(kw in q_lower for kw in ["breaking", "deprecate", "version"])
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
        """Generate architecture-specific recommendation."""
        q_lower = question.lower()
        recommendations = []

        # API design recommendations
        if "api" in q_lower or "endpoint" in q_lower:
            recommendations.extend([
                "Use RESTful conventions for resource endpoints",
                "Version your API (e.g., /api/v1/) for future compatibility",
                "Implement consistent error response format",
                "Document endpoints with OpenAPI/Swagger",
            ])
            if "auth" in q_lower:
                recommendations.append(
                    "Use JWT or OAuth2 for API authentication"
                )

        # Architecture recommendations
        if "architect" in q_lower or "structure" in q_lower:
            recommendations.extend([
                "Separate concerns into distinct layers/modules",
                "Use dependency injection for loose coupling",
                "Define clear interfaces between components",
            ])
            # Suggest specific patterns based on context
            if context.get("complexity") == "high":
                recommendations.append(
                    "Consider CQRS for complex domain logic"
                )
            if context.get("scale_requirement"):
                recommendations.append(
                    "Design for horizontal scalability from the start"
                )

        # Design pattern recommendations
        if "pattern" in q_lower:
            recommendations.extend([
                "Repository pattern for data access abstraction",
                "Factory pattern for complex object creation",
                "Strategy pattern for interchangeable algorithms",
            ])

        # Performance recommendations
        if "performance" in q_lower or "slow" in q_lower:
            recommendations.extend([
                "Implement caching at appropriate layers",
                "Use async processing for non-blocking operations",
                "Profile before optimizing - measure first",
                "Consider connection pooling for database access",
            ])

        # Error handling recommendations
        if "error" in q_lower or "exception" in q_lower:
            recommendations.extend([
                "Use structured error types with error codes",
                "Implement global exception handling",
                "Log errors with context for debugging",
                "Distinguish between recoverable and fatal errors",
            ])

        # Service organization
        if "service" in q_lower or "module" in q_lower:
            recommendations.extend([
                "Keep services focused on single responsibility",
                "Define clear contracts between services",
                "Use events for cross-service communication when appropriate",
            ])

        # Default if no specific matches
        if not recommendations:
            recommendations.append(
                "Analyze requirements and propose an architecture that "
                "balances simplicity with future extensibility"
            )

        return "\n".join(f"- {r}" for r in recommendations)

    def analyze_api_change(
        self,
        endpoint: str,
        change_type: str,
        breaking: bool = False,
    ) -> AdvisorDecision:
        """
        Specialized analysis for API changes.

        Args:
            endpoint: API endpoint being modified
            change_type: Type of change
            breaking: Whether this is a breaking change

        Returns:
            AdvisorDecision
        """
        question = f"API change: {change_type} for {endpoint}" + (
            " (BREAKING)" if breaking else ""
        )
        context = {
            "endpoint": endpoint,
            "change_type": change_type,
            "breaking": breaking,
        }
        return self.consult(question, context)

    def recommend_pattern(
        self,
        problem: str,
        constraints: List[str] = None,
    ) -> AdvisorDecision:
        """
        Recommend a design pattern for a problem.

        Args:
            problem: Description of the problem
            constraints: Any constraints to consider

        Returns:
            AdvisorDecision with pattern recommendation
        """
        question = f"Design pattern recommendation for: {problem}"
        context = {
            "problem": problem,
            "constraints": constraints or [],
        }
        return self.consult(question, context)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python app_advisor.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    advisor = AppAdvisor(project_root)

    # Test consultation
    decision = advisor.consult(
        "How should I structure the API endpoints for user management?",
        context={"existing_endpoints": ["/users", "/auth"]},
    )

    print(f"Advisor: {decision.advisor}")
    print(f"Decision Type: {decision.decision_type.value}")
    print(f"Confidence: {decision.confidence.total:.2%}")
    print(f"Auto-approved: {decision.auto_approved}")
    print(f"Recommendation:\n{decision.recommendation}")
