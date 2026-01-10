"""
Data Advisor for AI Team
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Specializes in:
- Database schema design
- Data modeling
- Migrations
- Query optimization
- Data validation

Invoked via: @data-advisor
"""

from dataclasses import field
from pathlib import Path
from typing import Dict, List, Any

from .base_advisor import (
    BaseAdvisor,
    AdvisorConfig,
    AdvisorDecision,
    ConfidenceScore,
    DecisionType,
    DomainType,
)


class DataAdvisor(BaseAdvisor):
    """
    Domain expert for data and database concerns.

    Handles questions about:
    - Schema design and normalization
    - Migration strategies
    - Query performance
    - Data validation rules
    - Relationship modeling
    """

    def __init__(self, project_root: Path):
        """Initialize DataAdvisor."""
        config = AdvisorConfig(
            name="data-advisor",
            domain=DomainType.DATA,
            description="Expert in database design, schemas, and data modeling",
            domain_patterns=[
                r"database|schema|table|column",
                r"migration|migrate",
                r"query|sql|select|join",
                r"index|performance|optimize",
                r"foreign key|relationship|one-to-many|many-to-many",
                r"validation|constraint|unique|not null",
                r"normalization|denormalization",
                r"postgresql|mysql|sqlite|mongodb",
            ],
            handled_tags=[
                "database",
                "schema",
                "migration",
                "data_model",
                "query",
                "validation",
            ],
        )
        super().__init__(project_root, config)

        # Data-specific patterns for recommendations
        self.recommendation_patterns = {
            "schema_change": [
                "Consider creating a migration file",
                "Add appropriate indexes for query performance",
                "Ensure foreign key constraints are in place",
            ],
            "query_optimization": [
                "Add index on frequently queried columns",
                "Consider query caching for expensive operations",
                "Review N+1 query patterns",
            ],
            "validation": [
                "Add database-level constraints",
                "Implement application-level validation",
                "Consider using CHECK constraints",
            ],
        }

    def get_domain_patterns(self) -> List[str]:
        """Get patterns for data domain."""
        return self.config.domain_patterns

    def analyze(self, question: str, context: Dict[str, Any]) -> AdvisorDecision:
        """
        Analyze a data-related question.

        Args:
            question: The question to analyze
            context: Additional context (schema files, query examples, etc.)

        Returns:
            AdvisorDecision with recommendation
        """
        # Classify the question
        domain_tags = self.classify_domain(question)

        # Add data-specific tags
        q_lower = question.lower()
        if "schema" in q_lower or "table" in q_lower:
            domain_tags.append("schema_design")
        if "migration" in q_lower:
            domain_tags.append("database_migrations")
        if "query" in q_lower or "performance" in q_lower:
            domain_tags.append("query_optimization")
        if "valid" in q_lower or "constraint" in q_lower:
            domain_tags.append("data_validation")

        # Generate recommendation
        recommendation = self._generate_recommendation(question, context, domain_tags)

        # Check for ADR conflicts
        conflicting_adrs = self.check_adr_conflicts(recommendation, domain_tags)
        aligned_adrs = self.find_aligned_adrs(domain_tags)

        # Calculate confidence
        confidence = self.calculate_confidence(question, recommendation, domain_tags)

        # Determine decision type
        decision_type = (
            DecisionType.STRATEGIC
            if "database_migrations" in domain_tags or "schema_design" in domain_tags
            else DecisionType.TACTICAL
        )

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
        """Generate data-specific recommendation."""
        q_lower = question.lower()
        recommendations = []

        # Schema design recommendations
        if "schema" in q_lower or "table" in q_lower:
            recommendations.extend([
                "Define clear primary keys for all tables",
                "Use appropriate data types for columns",
                "Consider normalization level (3NF recommended for most cases)",
            ])
            if "relationship" in q_lower:
                recommendations.append(
                    "Use foreign key constraints to enforce referential integrity"
                )

        # Migration recommendations
        if "migration" in q_lower:
            recommendations.extend([
                "Create reversible migrations where possible",
                "Test migrations on a copy of production data",
                "Consider data backfill requirements",
            ])
            if context.get("has_production_data"):
                recommendations.append(
                    "Schedule migration during low-traffic period"
                )

        # Query optimization
        if "query" in q_lower or "slow" in q_lower or "performance" in q_lower:
            recommendations.extend([
                "Analyze query execution plan (EXPLAIN ANALYZE)",
                "Add indexes on columns used in WHERE clauses",
                "Consider query result caching for repeated queries",
            ])

        # Validation
        if "valid" in q_lower:
            recommendations.extend([
                "Implement validation at both database and application layers",
                "Use NOT NULL constraints for required fields",
                "Add CHECK constraints for value ranges",
            ])

        # Default if no specific matches
        if not recommendations:
            recommendations.append(
                "Analyze the data requirements and propose a schema that "
                "balances normalization with query performance"
            )

        return "\n".join(f"- {r}" for r in recommendations)

    def analyze_schema_change(
        self,
        table_name: str,
        change_type: str,
        details: Dict[str, Any],
    ) -> AdvisorDecision:
        """
        Specialized analysis for schema changes.

        Args:
            table_name: Table being modified
            change_type: Type of change (add_column, remove_column, etc.)
            details: Change details

        Returns:
            AdvisorDecision
        """
        question = f"Schema change: {change_type} on table {table_name}"
        context = {
            "table_name": table_name,
            "change_type": change_type,
            "details": details,
        }
        return self.consult(question, context)

    def analyze_query_performance(
        self,
        query: str,
        execution_time_ms: float,
    ) -> AdvisorDecision:
        """
        Analyze query performance issues.

        Args:
            query: The SQL query
            execution_time_ms: Current execution time

        Returns:
            AdvisorDecision with optimization recommendations
        """
        question = f"Query performance issue: {execution_time_ms}ms execution time"
        context = {
            "query": query,
            "execution_time_ms": execution_time_ms,
        }
        return self.consult(question, context)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python data_advisor.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1])
    advisor = DataAdvisor(project_root)

    # Test consultation
    decision = advisor.consult(
        "How should I structure the user_preferences table schema?",
        context={"tables": ["users", "preferences"]},
    )

    print(f"Advisor: {decision.advisor}")
    print(f"Decision Type: {decision.decision_type.value}")
    print(f"Confidence: {decision.confidence.total:.2%}")
    print(f"Auto-approved: {decision.auto_approved}")
    print(f"Recommendation:\n{decision.recommendation}")
