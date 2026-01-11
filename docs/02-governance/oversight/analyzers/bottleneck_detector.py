"""
Bottleneck Detector - Identify where agents get stuck

Analyzes operational metrics to find process bottlenecks.

Usage:
    from governance.oversight.analyzers.bottleneck_detector import identify_bottlenecks
    from governance.oversight.coo_metrics import OperationalMetrics
    
    metrics = OperationalMetrics.from_sessions(sessions)
    bottlenecks = identify_bottlenecks(metrics)
"""

from typing import List
from governance.oversight.coo_metrics import OperationalMetrics, Bottleneck


def identify_bottlenecks(metrics: OperationalMetrics) -> List[Bottleneck]:
    """
    Identify process bottlenecks from operational metrics.
    
    Args:
        metrics: Operational metrics to analyze
        
    Returns:
        List of identified bottlenecks, sorted by impact score (highest first)
    """
    bottlenecks = []
    
    # Check Ralph verification time
    if metrics.ralph_verification_time_avg_sec > 60:
        bottlenecks.append(Bottleneck(
            type="verification_slow",
            impact_score=8,  # High impact (blocks every iteration)
            recommendation="Consider Ralph caching or parallel verification",
            avg_delay_sec=metrics.ralph_verification_time_avg_sec
        ))
    
    # Check iteration budget exhaustion
    if metrics.iteration_budget_exhaustion_rate > 15:  # >15% hit budget
        bottlenecks.append(Bottleneck(
            type="iteration_budget_too_low",
            impact_score=7,
            recommendation=f"Increase iteration budgets by 10-20% ({metrics.iteration_budget_exhaustion_rate:.0f}% exhaustion rate)",
            affected_sessions=int(metrics.total_sessions * metrics.iteration_budget_exhaustion_rate / 100)
        ))
    
    # Check human approval delays
    if metrics.human_approval_wait_time_avg_min > 120:  # >2h wait
        bottlenecks.append(Bottleneck(
            type="approval_delays",
            impact_score=6,
            recommendation="Reduce approval requirements or batch approvals",
            avg_delay_sec=metrics.human_approval_wait_time_avg_min * 60
        ))
    
    # Check governance gate overhead
    if metrics.governance_gate_time_avg_sec > 30:
        bottlenecks.append(Bottleneck(
            type="governance_overhead",
            impact_score=5,
            recommendation="Review governance gates - may be slowing development",
            avg_delay_sec=metrics.governance_gate_time_avg_sec
        ))
    
    # Check false positive rate
    if metrics.false_positive_blocks_count > 5:
        bottlenecks.append(Bottleneck(
            type="false_positive_blocks",
            impact_score=6,
            recommendation=f"Review governance rules - {metrics.false_positive_blocks_count} false positives detected",
            affected_sessions=metrics.false_positive_blocks_count
        ))
    
    # Check session resume frequency (crashes/interrupts)
    if metrics.session_resume_frequency > metrics.total_sessions * 0.2:  # >20% resume rate
        bottlenecks.append(Bottleneck(
            type="session_instability",
            impact_score=7,
            recommendation="Investigate session crashes/interrupts - high resume rate",
            affected_sessions=metrics.session_resume_frequency
        ))
    
    # Check autonomy level
    if metrics.current_autonomy_pct < 85:
        bottlenecks.append(Bottleneck(
            type="low_autonomy",
            impact_score=9,  # Critical
            recommendation=f"Autonomy at {metrics.current_autonomy_pct:.0f}% (target: >90%) - review blocking factors",
            affected_sessions=metrics.total_sessions
        ))
    
    # Sort by impact score (highest first)
    return sorted(bottlenecks, key=lambda b: b.impact_score, reverse=True)
