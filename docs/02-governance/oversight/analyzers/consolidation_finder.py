"""
Consolidation Finder - Identify merge/sunset opportunities

Finds agents or skills that could be consolidated for efficiency.

Usage:
    from governance.oversight.analyzers.consolidation_finder import find_consolidation_opportunities
    
    opportunities = find_consolidation_opportunities(agent_performance)
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ConsolidationOpportunity:
    """Identified consolidation opportunity."""
    type: str  # "merge_agents" | "promote_skill" | "demote_agent"
    components: List[str]  # Components involved
    overlap_pct: float = 0.0  # % overlap if merging
    rationale: str = ""
    estimated_impact: str = ""  # Expected benefit
    complexity: str = "medium"  # "low" | "medium" | "high"


def find_consolidation_opportunities(
    agent_performance: Dict[str, Any],
    skill_usage: Dict[str, Any] = None
) -> List[ConsolidationOpportunity]:
    """
    Find opportunities to consolidate agents or promote skills.
    
    Args:
        agent_performance: Agent performance metrics by type
        skill_usage: Optional skill usage data
        
    Returns:
        List of consolidation opportunities
    """
    opportunities = []
    
    # Find agents with high task overlap
    opportunities.extend(_find_merge_candidates(agent_performance))
    
    # Find skills that should become agents
    if skill_usage:
        opportunities.extend(_find_promotion_candidates(skill_usage))
    
    # Find agents that should become skills
    opportunities.extend(_find_demotion_candidates(agent_performance))
    
    return opportunities


def _find_merge_candidates(agent_performance: Dict[str, Any]) -> List[ConsolidationOpportunity]:
    """Find agents that could be merged."""
    opportunities = []
    
    # Check BugFix + CodeQuality overlap (common pattern)
    bugfix = agent_performance.get("BugFix", {})
    codequality = agent_performance.get("CodeQuality", {})
    
    if bugfix and codequality:
        # Estimate overlap based on task similarity
        # (In reality, would need actual task data)
        estimated_overlap = 0.65  # Assume 65% overlap
        
        opportunities.append(ConsolidationOpportunity(
            type="merge_agents",
            components=["BugFix", "CodeQuality"],
            overlap_pct=estimated_overlap * 100,
            rationale=f"Estimated {estimated_overlap*100:.0f}% task overlap - could be single QualityAgent",
            estimated_impact="Reduce context switching, simplify contracts, -15% overhead",
            complexity="medium"
        ))
    
    return opportunities


def _find_promotion_candidates(skill_usage: Dict[str, Any]) -> List[ConsolidationOpportunity]:
    """Find skills that should become agents (high usage)."""
    opportunities = []
    
    for skill_name, usage in skill_usage.items():
        invocations_per_week = usage.get("invocations_per_week", 0)
        avg_time_min = usage.get("avg_time_min", 0)
        
        # Promotion criteria: high frequency OR time-consuming
        if invocations_per_week > 10:  # >10 uses/week
            opportunities.append(ConsolidationOpportunity(
                type="promote_skill",
                components=[skill_name],
                rationale=f"High usage: {invocations_per_week:.0f} invocations/week",
                estimated_impact=f"+2-4% autonomy, {invocations_per_week * avg_time_min:.0f}min/week time savings",
                complexity="low"
            ))
        elif avg_time_min > 15:  # Time-consuming
            opportunities.append(ConsolidationOpportunity(
                type="promote_skill",
                components=[skill_name],
                rationale=f"Time sink: {avg_time_min:.0f}min/invocation",
                estimated_impact=f"{avg_time_min * invocations_per_week:.0f}min/week time savings",
                complexity="medium"
            ))
    
    return opportunities


def _find_demotion_candidates(agent_performance: Dict[str, Any]) -> List[ConsolidationOpportunity]:
    """Find agents that should become skills (low usage, high quality)."""
    opportunities = []
    
    for agent_type, perf in agent_performance.items():
        total_tasks = perf.get("total_tasks", 0)
        completion_rate = perf.get("completion_rate", 0)
        
        # Demotion criteria: low usage but excellent performance
        if total_tasks < 10 and completion_rate > 95:
            opportunities.append(ConsolidationOpportunity(
                type="demote_agent",
                components=[agent_type],
                rationale=f"Low usage ({total_tasks} tasks) but excellent performance ({completion_rate:.0f}%)",
                estimated_impact="Convert to skill - reduce governance overhead while keeping capability",
                complexity="low"
            ))
    
    return opportunities
