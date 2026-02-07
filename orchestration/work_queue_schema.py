"""
Work Queue Schema - Updated for Multi-Agent Support (Phase 1, Step 1.5)

Extends existing work queue with fields for:
- Task complexity classification
- Estimated task value (for multi-agent routing)
- Preferred agent types
- Agent routing decisions

Maintains backward compatibility with existing work queue format.

Author: Claude Code (Autonomous Implementation)
Date: 2026-02-07
Version: 2.0 (Multi-Agent Ready)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal
from enum import Enum


class ComplexityCategory(str, Enum):
    """Task complexity categories for multi-agent routing."""

    LOW = "low"  # Simple bugs, documentation, minor fixes
    MEDIUM = "medium"  # Feature changes, refactoring, moderate complexity
    HIGH = "high"  # Cross-repo, HIPAA, deployment, major rewrites
    CRITICAL = "critical"  # Production incidents, security fixes


class EstimatedValueTier(str, Enum):
    """Task value tiers for multi-agent routing decision."""

    TRIVIAL = "trivial"  # < $10
    LOW = "low"  # $10-$50
    MEDIUM = "medium"  # $50-$200
    HIGH = "high"  # $200-$1000
    CRITICAL = "critical"  # > $1000


class AgentType(str, Enum):
    """Supported specialist agent types."""

    BUGFIX = "bugfix"
    FEATUREBUILDER = "featurebuilder"
    TESTWRITER = "testwriter"
    CODEQUALITY = "codequality"
    ADVISOR = "advisor"
    DEPLOYMENT = "deployment"
    MIGRATION = "migration"


@dataclass
class WorkQueueTaskMultiAgent:
    """
    Extended work queue task with multi-agent routing support.

    Maintains backward compatibility while adding new fields for
    intelligent agent routing decisions.
    """

    # ==================== Core Fields (Existing) ====================

    id: str  # Unique task ID
    description: str  # Task description
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"]
    priority: Literal["P0", "P1", "P2", "P3"]  # Impact priority
    type: Literal["bug", "feature", "refactor", "test", "deploy", "docs"]

    # ==================== Multi-Agent Fields (NEW) ====================

    # Complexity classification for routing
    complexity_category: ComplexityCategory = ComplexityCategory.MEDIUM

    # Estimated value in USD for cost-benefit analysis
    estimated_value_usd: float = 50.0

    # Preferred agent types for this task (if known)
    preferred_agents: List[AgentType] = field(default_factory=list)

    # Agent routing decision (set by router)
    agent_type_override: Optional[AgentType] = None

    # Whether to use multi-agent orchestrator
    use_multi_agent: Optional[bool] = None

    # Multi-agent decision rationale
    routing_reason: Optional[str] = None

    # ==================== Existing Optional Fields ====================

    file: Optional[str] = None
    tests: List[str] = field(default_factory=list)
    passes: bool = False
    error: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[str] = None
    completed_at: Optional[str] = None
    max_iterations: Optional[int] = None
    verification_verdict: Optional[Literal["PASS", "FAIL", "BLOCKED"]] = None
    files_actually_changed: Optional[List[str]] = None
    bug_count: Optional[int] = None
    branch: Optional[str] = None
    created_at: Optional[str] = None
    title: Optional[str] = None
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "type": self.type,
            "complexity_category": self.complexity_category.value,
            "estimated_value_usd": self.estimated_value_usd,
            "preferred_agents": [agent.value for agent in self.preferred_agents],
            "agent_type_override": self.agent_type_override.value
            if self.agent_type_override
            else None,
            "use_multi_agent": self.use_multi_agent,
            "routing_reason": self.routing_reason,
            "file": self.file,
            "tests": self.tests,
            "passes": self.passes,
            "error": self.error,
            "attempts": self.attempts,
            "last_attempt": self.last_attempt,
            "completed_at": self.completed_at,
            "max_iterations": self.max_iterations,
            "verification_verdict": self.verification_verdict,
            "files_actually_changed": self.files_actually_changed,
            "bug_count": self.bug_count,
            "branch": self.branch,
            "created_at": self.created_at,
            "title": self.title,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any]
    ) -> "WorkQueueTaskMultiAgent":
        """Create instance from dictionary (backward compatible)."""
        # Extract multi-agent fields with defaults
        complexity = ComplexityCategory(
            data.get("complexity_category", ComplexityCategory.MEDIUM.value)
        )
        value = float(data.get("estimated_value_usd", 50.0))
        preferred = [
            AgentType(agent) for agent in data.get("preferred_agents", [])
        ]
        override = (
            AgentType(data["agent_type_override"])
            if data.get("agent_type_override")
            else None
        )

        return cls(
            id=data["id"],
            description=data["description"],
            status=data["status"],
            priority=data["priority"],
            type=data["type"],
            complexity_category=complexity,
            estimated_value_usd=value,
            preferred_agents=preferred,
            agent_type_override=override,
            use_multi_agent=data.get("use_multi_agent"),
            routing_reason=data.get("routing_reason"),
            file=data.get("file"),
            tests=data.get("tests", []),
            passes=data.get("passes", False),
            error=data.get("error"),
            attempts=data.get("attempts", 0),
            last_attempt=data.get("last_attempt"),
            completed_at=data.get("completed_at"),
            max_iterations=data.get("max_iterations"),
            verification_verdict=data.get("verification_verdict"),
            files_actually_changed=data.get("files_actually_changed"),
            bug_count=data.get("bug_count"),
            branch=data.get("branch"),
            created_at=data.get("created_at"),
            title=data.get("title"),
            evidence=data.get("evidence", []),
        )


@dataclass
class WorkQueueValidator:
    """Validates work queue tasks for required fields and types."""

    @staticmethod
    def validate_task(task: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a work queue task dictionary.

        Returns:
            (is_valid, error_message)
        """
        # Required fields
        required = ["id", "description", "status", "priority", "type"]
        missing = [f for f in required if f not in task]
        if missing:
            return False, f"Missing required fields: {missing}"

        # Validate enums
        valid_statuses = {"pending", "in_progress", "completed", "blocked", "failed"}
        if task["status"] not in valid_statuses:
            return False, f"Invalid status: {task['status']}"

        valid_priorities = {"P0", "P1", "P2", "P3"}
        if task["priority"] not in valid_priorities:
            return False, f"Invalid priority: {task['priority']}"

        valid_types = {"bug", "feature", "refactor", "test", "deploy", "docs"}
        if task["type"] not in valid_types:
            return False, f"Invalid type: {task['type']}"

        # Validate multi-agent fields if present
        if "complexity_category" in task:
            valid_complexities = {cat.value for cat in ComplexityCategory}
            if task["complexity_category"] not in valid_complexities:
                return False, f"Invalid complexity_category: {task['complexity_category']}"

        if "estimated_value_usd" in task:
            try:
                float(task["estimated_value_usd"])
            except (ValueError, TypeError):
                return (
                    False,
                    f"Invalid estimated_value_usd: {task['estimated_value_usd']}",
                )

        if "preferred_agents" in task:
            if not isinstance(task["preferred_agents"], list):
                return False, "preferred_agents must be a list"
            valid_agents = {agent.value for agent in AgentType}
            for agent in task["preferred_agents"]:
                if agent not in valid_agents:
                    return False, f"Invalid agent type: {agent}"

        return True, None


# Default task templates for common scenarios

SIMPLE_BUG_TASK_TEMPLATE = {
    "complexity_category": ComplexityCategory.LOW.value,
    "estimated_value_usd": 25.0,
    "preferred_agents": [AgentType.BUGFIX.value],
    "use_multi_agent": False,
}

FEATURE_TASK_TEMPLATE = {
    "complexity_category": ComplexityCategory.MEDIUM.value,
    "estimated_value_usd": 100.0,
    "preferred_agents": [
        AgentType.FEATUREBUILDER.value,
        AgentType.TESTWRITER.value,
    ],
    "use_multi_agent": True,
}

COMPLEX_TASK_TEMPLATE = {
    "complexity_category": ComplexityCategory.HIGH.value,
    "estimated_value_usd": 200.0,
    "preferred_agents": [
        AgentType.BUGFIX.value,
        AgentType.FEATUREBUILDER.value,
        AgentType.TESTWRITER.value,
        AgentType.CODEQUALITY.value,
    ],
    "use_multi_agent": True,
}

DEPLOYMENT_TASK_TEMPLATE = {
    "complexity_category": ComplexityCategory.CRITICAL.value,
    "estimated_value_usd": 500.0,
    "preferred_agents": [AgentType.DEPLOYMENT.value, AgentType.ADVISOR.value],
    "use_multi_agent": True,
}
