"""
Task Router for Multi-Agent Routing Decisions (Phase 1, Step 1.6)

Determines whether a task should use multi-agent orchestration or single-agent execution
based on task complexity, value, and other factors.

This router integrates with autonomous_loop.py to make intelligent routing decisions
that balance quality, cost, and execution speed.

Author: Claude Code (Autonomous Implementation)
Date: 2026-02-07
Version: 1.0
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

from orchestration.work_queue_schema import (
    WorkQueueTaskMultiAgent,
    ComplexityCategory,
    EstimatedValueTier,
    AgentType,
)


class RoutingDecision(str, Enum):
    """Routing decision outcomes."""

    USE_MULTI_AGENT = "use_multi_agent"
    USE_SINGLE_AGENT = "use_single_agent"
    FALLBACK_SINGLE_AGENT = "fallback_single_agent"  # Multi-agent not available
    BLOCKED = "blocked"  # Cannot route (insufficient resources)


@dataclass
class RoutingAnalysis:
    """Result of routing analysis for a task."""

    task_id: str
    decision: RoutingDecision
    reason: str
    estimated_cost_multi: float  # Estimated cost if using multi-agent
    estimated_cost_single: float  # Estimated cost if using single-agent
    quality_improvement_pct: float  # Estimated quality improvement with multi-agent
    recommended_specialists: List[AgentType]
    confidence: float  # 0.0-1.0 confidence in this decision


class TaskRouter:
    """
    Intelligent task router for multi-agent vs single-agent decisions.

    Routing Rules:
    1. Value-based: Tasks worth >= $50 → multi-agent
    2. Complexity-based: HIGH/CRITICAL → multi-agent
    3. Type-based: HIPAA, deployment, cross-repo → multi-agent
    4. Fallback: If multi-agent unavailable → single-agent
    5. Explicit override: agent_type_override → single-agent (ignore multi-agent)

    Cost Thresholds:
    - Trivial (<$10): Always single-agent
    - Low ($10-$50): Single-agent (unless high complexity)
    - Medium ($50-$200): Multi-agent if complex, single otherwise
    - High ($200-$1000): Multi-agent
    - Critical (>$1000): Always multi-agent
    """

    # Cost thresholds for value-based routing
    VALUE_THRESHOLD_USD = 50.0  # Tasks worth >= $50 use multi-agent

    # Agent type costs (estimated token usage in $)
    AGENT_COSTS = {
        AgentType.BUGFIX: 0.067,  # ~15 iterations × 3000 tokens × $0.0015/K
        AgentType.FEATUREBUILDER: 0.220,  # ~50 iterations × 3000 tokens
        AgentType.TESTWRITER: 0.067,  # ~15 iterations × 3000 tokens
        AgentType.CODEQUALITY: 0.087,  # ~20 iterations × 3000 tokens
        AgentType.ADVISOR: 0.030,  # ~10 iterations × 2000 tokens
        AgentType.DEPLOYMENT: 0.087,  # ~20 iterations × 3000 tokens
        AgentType.MIGRATION: 0.220,  # ~50 iterations × 3000 tokens
    }

    # Quality improvement estimates (multi-agent vs single-agent)
    QUALITY_IMPROVEMENTS = {
        ComplexityCategory.LOW: 0.05,  # 5% improvement
        ComplexityCategory.MEDIUM: 0.15,  # 15% improvement
        ComplexityCategory.HIGH: 0.30,  # 30% improvement
        ComplexityCategory.CRITICAL: 0.40,  # 40% improvement
    }

    @staticmethod
    def should_use_multi_agent(
        task: WorkQueueTaskMultiAgent,
    ) -> RoutingAnalysis:
        """
        Determine if a task should use multi-agent orchestration.

        Args:
            task: Work queue task to analyze

        Returns:
            RoutingAnalysis with decision and reasoning
        """
        task_id = task.id

        # Rule 1: Explicit override takes precedence
        if task.agent_type_override is not None:
            return RoutingAnalysis(
                task_id=task_id,
                decision=RoutingDecision.USE_SINGLE_AGENT,
                reason=f"Explicit override to {task.agent_type_override.value}",
                estimated_cost_multi=0.0,
                estimated_cost_single=TaskRouter.AGENT_COSTS.get(
                    task.agent_type_override, 0.1
                ),
                quality_improvement_pct=0.0,
                recommended_specialists=[task.agent_type_override],
                confidence=1.0,
            )

        # Rule 2: Explicit use_multi_agent flag
        if task.use_multi_agent is True:
            return TaskRouter._build_multi_agent_analysis(task)

        # Rule 3: Explicit use_multi_agent=False flag
        if task.use_multi_agent is False:
            return RoutingAnalysis(
                task_id=task_id,
                decision=RoutingDecision.USE_SINGLE_AGENT,
                reason="Explicitly disabled multi-agent (use_multi_agent=False)",
                estimated_cost_multi=0.0,
                estimated_cost_single=TaskRouter._estimate_single_agent_cost(task),
                quality_improvement_pct=0.0,
                recommended_specialists=task.preferred_agents or [],
                confidence=1.0,
            )

        # Rule 4: Type-based routing (HIPAA, deployment, cross-repo)
        if TaskRouter._is_special_task_type(task):
            return TaskRouter._build_multi_agent_analysis(
                task, reason_override="Special task type (HIPAA/deployment/cross-repo)"
            )

        # Rule 5: Complexity-based routing
        if task.complexity_category in (
            ComplexityCategory.HIGH,
            ComplexityCategory.CRITICAL,
        ):
            return TaskRouter._build_multi_agent_analysis(
                task, reason_override=f"Task complexity: {task.complexity_category.value}"
            )

        # Rule 6: Value-based routing (>= $50)
        if task.estimated_value_usd >= TaskRouter.VALUE_THRESHOLD_USD:
            return TaskRouter._build_multi_agent_analysis(
                task,
                reason_override=f"Task value ${task.estimated_value_usd:.2f} >= ${TaskRouter.VALUE_THRESHOLD_USD}",
            )

        # Default: Single-agent
        return RoutingAnalysis(
            task_id=task_id,
            decision=RoutingDecision.USE_SINGLE_AGENT,
            reason=f"Low value (${task.estimated_value_usd:.2f}) and {task.complexity_category.value} complexity",
            estimated_cost_multi=0.0,
            estimated_cost_single=TaskRouter._estimate_single_agent_cost(task),
            quality_improvement_pct=0.0,
            recommended_specialists=task.preferred_agents or [],
            confidence=0.9,
        )

    @staticmethod
    def _is_special_task_type(task: WorkQueueTaskMultiAgent) -> bool:
        """Check if task is a special type that triggers multi-agent."""
        # HIPAA-related keywords
        hipaa_keywords = [
            "hipaa",
            "pii",
            "phi",
            "protected health",
            "credential",
            "license",
            "compliance",
            "audit",
        ]
        description_lower = task.description.lower()
        if any(kw in description_lower for kw in hipaa_keywords):
            return True

        # Deployment-related types
        if task.type in ("deploy", "migration", "rollback"):
            return True

        # Cross-repo keywords
        if any(
            kw in description_lower
            for kw in ["cross-repo", "cross repo", "shared"]
        ):
            return True

        return False

    @staticmethod
    def _build_multi_agent_analysis(
        task: WorkQueueTaskMultiAgent, reason_override: Optional[str] = None
    ) -> RoutingAnalysis:
        """Build routing analysis recommending multi-agent."""
        specialists = TaskRouter._select_specialists(task)
        multi_cost = sum(TaskRouter.AGENT_COSTS.get(s, 0.1) for s in specialists)
        single_cost = TaskRouter._estimate_single_agent_cost(task)
        quality_improvement = TaskRouter.QUALITY_IMPROVEMENTS.get(
            task.complexity_category, 0.15
        )

        reason = reason_override or "Multi-agent routing determined"

        return RoutingAnalysis(
            task_id=task.id,
            decision=RoutingDecision.USE_MULTI_AGENT,
            reason=reason,
            estimated_cost_multi=multi_cost,
            estimated_cost_single=single_cost,
            quality_improvement_pct=quality_improvement,
            recommended_specialists=specialists,
            confidence=0.95,
        )

    @staticmethod
    def _select_specialists(task: WorkQueueTaskMultiAgent) -> List[AgentType]:
        """
        Select appropriate specialists for a task.

        Uses preferred_agents if provided, otherwise infers based on task type.
        """
        if task.preferred_agents:
            return task.preferred_agents

        # Infer specialists based on task type
        if task.type == "bug":
            return [AgentType.BUGFIX, AgentType.TESTWRITER]
        elif task.type == "feature":
            return [
                AgentType.FEATUREBUILDER,
                AgentType.TESTWRITER,
                AgentType.CODEQUALITY,
            ]
        elif task.type == "refactor":
            return [AgentType.CODEQUALITY, AgentType.TESTWRITER]
        elif task.type == "test":
            return [AgentType.TESTWRITER]
        elif task.type in ("deploy", "migration"):
            return [AgentType.DEPLOYMENT, AgentType.ADVISOR]
        else:
            # Default: Use CodeQuality for unknown types
            return [AgentType.CODEQUALITY]

    @staticmethod
    def _estimate_single_agent_cost(task: WorkQueueTaskMultiAgent) -> float:
        """Estimate cost for single-agent execution."""
        # Base estimate: 30 iterations × 3000 tokens × $0.0015/K tokens
        return 0.135

    @staticmethod
    def is_multi_agent_available() -> bool:
        """
        Check if multi-agent orchestration is available.

        In production, this would check:
        - TeamLead agent availability
        - Specialist agent pool availability
        - Resource constraints

        For now, always returns True (unlimited resources).
        """
        return True

    @staticmethod
    def fallback_to_single_agent(
        task: WorkQueueTaskMultiAgent,
    ) -> RoutingAnalysis:
        """
        Generate fallback routing analysis (multi-agent → single-agent).

        Used when multi-agent becomes unavailable during execution.
        """
        return RoutingAnalysis(
            task_id=task.id,
            decision=RoutingDecision.FALLBACK_SINGLE_AGENT,
            reason="Multi-agent unavailable, falling back to single-agent",
            estimated_cost_multi=0.0,
            estimated_cost_single=TaskRouter._estimate_single_agent_cost(task),
            quality_improvement_pct=0.0,
            recommended_specialists=task.preferred_agents or [],
            confidence=0.5,
        )

    @staticmethod
    def estimate_roi(analysis: RoutingAnalysis) -> Dict[str, Any]:
        """
        Estimate return-on-investment for multi-agent execution.

        Returns:
            dict with:
            - cost_delta: Additional cost for multi-agent
            - quality_improvement_value: Estimated value of quality improvement
            - roi_pct: Return on investment percentage
            - payoff: "Worth it" if quality improvement > cost increase
        """
        cost_delta = analysis.estimated_cost_multi - analysis.estimated_cost_single
        quality_improvement_value = (
            analysis.estimated_cost_single * analysis.quality_improvement_pct
        )
        roi_pct = (quality_improvement_value / cost_delta * 100) if cost_delta > 0 else 0

        return {
            "cost_delta": cost_delta,
            "cost_delta_pct": (
                (cost_delta / analysis.estimated_cost_single * 100)
                if analysis.estimated_cost_single > 0
                else 0
            ),
            "quality_improvement_value": quality_improvement_value,
            "roi_pct": roi_pct,
            "payoff": "Worth it" if quality_improvement_value > cost_delta else "Not worth it",
        }
