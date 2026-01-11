"""
Bloat Detector - Identify governance theater and unused components

Finds rules/agents that add overhead without safety value.

Usage:
    from governance.oversight.analyzers.bloat_detector import detect_bloat
    
    report = detect_bloat(sessions, agents_performance)
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class BloatIndicator:
    """Identified bloat in the system."""
    type: str  # "false_positive_rule" | "unused_agent" | "redundant_check"
    component: str  # Name of bloated component
    false_positive_rate: float = 0.0  # 0-1
    usage_count: int = 0
    recommendation: str = ""
    estimated_overhead_pct: float = 0.0  # % of total time/cost


def detect_bloat(
    sessions: List[Dict[str, Any]],
    agent_performance: Dict[str, Any]
) -> List[BloatIndicator]:
    """
    Detect bloat in governance and agent systems.
    
    Args:
        sessions: Session data from data collector
        agent_performance: Agent performance metrics by type
        
    Returns:
        List of bloat indicators
    """
    bloat = []
    
    # Detect false positive governance rules
    # (Rules that block tasks but are frequently overridden)
    bloat.extend(_detect_false_positive_rules(sessions))
    
    # Detect low-utilization agents
    bloat.extend(_detect_unused_agents(agent_performance))
    
    # Detect redundant checks
    bloat.extend(_detect_redundant_checks(sessions))
    
    return bloat


def _detect_false_positive_rules(sessions: List[Dict[str, Any]]) -> List[BloatIndicator]:
    """Find governance rules with high false positive rates."""
    # Track blocks vs overrides per rule type
    rule_stats = {}
    
    for session in sessions:
        # Look for governance blocks in session data
        if session.get("blocked_by_governance"):
            rule = session.get("blocking_rule", "unknown")
            if rule not in rule_stats:
                rule_stats[rule] = {"blocks": 0, "overrides": 0}
            
            rule_stats[rule]["blocks"] += 1
            
            if session.get("later_approved"):
                rule_stats[rule]["overrides"] += 1
    
    # Identify rules with >80% override rate
    bloat = []
    for rule, stats in rule_stats.items():
        if stats["blocks"] < 5:  # Need minimum sample size
            continue
        
        override_rate = stats["overrides"] / stats["blocks"]
        
        if override_rate > 0.8:  # >80% false positives
            bloat.append(BloatIndicator(
                type="false_positive_rule",
                component=rule,
                false_positive_rate=override_rate,
                usage_count=stats["blocks"],
                recommendation=f"Remove or relax '{rule}' - {override_rate*100:.0f}% override rate indicates governance theater",
                estimated_overhead_pct=5.0  # Estimate 5% overhead per false positive rule
            ))
    
    return bloat


def _detect_unused_agents(agent_performance: Dict[str, Any]) -> List[BloatIndicator]:
    """Find agents with low utilization."""
    bloat = []
    
    for agent_type, perf in agent_performance.items():
        total_tasks = perf.get("total_tasks", 0)
        
        # Low utilization threshold
        if total_tasks < 5 and perf.get("total_sessions", 50) > 50:  # <5 tasks in 50+ sessions
            bloat.append(BloatIndicator(
                type="unused_agent",
                component=agent_type,
                usage_count=total_tasks,
                recommendation=f"Sunset '{agent_type}' agent - low utilization ({total_tasks} tasks total)",
                estimated_overhead_pct=2.0  # Each unused agent adds ~2% complexity
            ))
    
    return bloat


def _detect_redundant_checks(sessions: List[Dict[str, Any]]) -> List[BloatIndicator]:
    """Find redundant verification checks."""
    # This is a placeholder - would need more detailed session data
    # to detect actual redundant checks
    return []
