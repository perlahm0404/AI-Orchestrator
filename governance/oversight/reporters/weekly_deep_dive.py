"""
Weekly Deep Dive Report Generator

Comprehensive analysis (5 minutes runtime, full metrics).

Usage:
    from governance.oversight.reporters.weekly_deep_dive import generate_weekly_report
    
    report = generate_weekly_report(coo_metrics, agent_scores, bottlenecks, bloat, consolidation)
    print(report)
"""

from typing import List, Dict, Any
from governance.oversight.coo_metrics import OperationalMetrics, Bottleneck
from governance.oversight.analyzers.agent_scorer import AgentScore
from governance.oversight.analyzers.bloat_detector import BloatIndicator
from governance.oversight.analyzers.consolidation_finder import ConsolidationOpportunity
from datetime import datetime, timedelta


def generate_weekly_report(
    coo_metrics: OperationalMetrics,
    agent_scores: List[AgentScore],
    bottlenecks: List[Bottleneck],
    bloat: List[BloatIndicator],
    consolidation: List[ConsolidationOpportunity]
) -> str:
    """
    Generate weekly deep dive report.
    
    Args:
        coo_metrics: Operational metrics
        agent_scores: Agent performance scorecards
        bottlenecks: Identified bottlenecks
        bloat: Identified bloat
        consolidation: Consolidation opportunities
        
    Returns:
        Formatted markdown report
    """
    week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = datetime.now().strftime("%Y-%m-%d")
    
    report = f"""# Weekly Operational Review - Week of {week_start}

## Executive Summary

- **Total Tasks**: {coo_metrics.total_tasks} (across {coo_metrics.total_sessions} sessions)
- **Autonomy**: {coo_metrics.current_autonomy_pct:.0f}% ({_trend_icon(coo_metrics.autonomy_trend)} {coo_metrics.autonomy_trend})
- **Tasks/Session**: {coo_metrics.tasks_per_session_avg:.1f}
- **Critical Bottlenecks**: {len([b for b in bottlenecks if b.impact_score >= 7])}

---

## Agent Performance Scorecard

| Agent | Tasks | Completion | Ralph PASS | Avg Iterations | Grade | Recommendation |
|-------|-------|-----------|------------|----------------|-------|----------------|
"""
    
    # Add agent scores
    for score in agent_scores:
        report += f"| **{score.agent_type}** | {score.total_tasks} | "
        report += f"{score.completion_rate:.0f}% | {score.ralph_pass_rate:.0f}% | "
        report += f"{score.avg_iterations:.1f} | {score.grade} | "
        report += f"{score.recommendation_icon} {score.recommendation} |\n"
    
    report += "\n---\n\n## Process Bottlenecks\n\n"
    
    if bottlenecks:
        for i, bottleneck in enumerate(bottlenecks[:5], 1):  # Top 5
            report += f"### {i}. {bottleneck.type.replace('_', ' ').title()} "
            report += f"(Impact: {bottleneck.impact_score}/10)\n\n"
            report += f"**Recommendation**: {bottleneck.recommendation}\n\n"
            if bottleneck.affected_sessions > 0:
                report += f"*Affected sessions: {bottleneck.affected_sessions}*\n\n"
    else:
        report += "✅ No significant bottlenecks detected\n\n"
    
    report += "---\n\n## Governance Health\n\n"
    
    if bloat:
        report += "**Bloat Detected**:\n\n"
        for indicator in bloat:
            report += f"- **{indicator.component}** ({indicator.type.replace('_', ' ')})\n"
            report += f"  - {indicator.recommendation}\n"
            if indicator.false_positive_rate > 0:
                report += f"  - False positive rate: {indicator.false_positive_rate*100:.0f}%\n"
            report += "\n"
    else:
        report += "✅ No significant bloat detected\n\n"
    
    report += f"**Governance Overhead**: {coo_metrics.governance_gate_time_avg_sec:.1f}s avg\n"
    report += f"**False Positive Blocks**: {coo_metrics.false_positive_blocks_count}\n\n"
    
    report += "---\n\n## Consolidation Opportunities\n\n"
    
    if consolidation:
        for i, opp in enumerate(consolidation, 1):
            report += f"### {i}. {opp.type.replace('_', ' ').title()}\n\n"
            report += f"**Components**: {', '.join(opp.components)}\n\n"
            report += f"**Rationale**: {opp.rationale}\n\n"
            report += f"**Expected Impact**: {opp.estimated_impact}\n\n"
    else:
        report += "No consolidation opportunities identified\n\n"
    
    report += "---\n\n## Cost Trends\n\n"
    report += f"- **Total Cost**: ${coo_metrics.total_cost_usd:.2f}\n"
    report += f"- **Cost/Task**: ${coo_metrics.cost_per_completed_task_usd:.2f}\n"
    report += f"- **Wasted Iterations**: {coo_metrics.wasted_iterations_pct:.0f}%\n\n"
    
    report += "---\n\n## Next Week Focus\n\n"
    
    # Generate action items from analysis
    action_items = _generate_action_items(coo_metrics, bottlenecks, bloat)
    for item in action_items:
        report += f"- [ ] {item}\n"
    
    report += "\n---\n\n"
    report += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    return report


def _trend_icon(trend: str) -> str:
    """Return icon for trend."""
    if trend == "improving":
        return "📈"
    elif trend == "declining":
        return "📉"
    return "➡️"


def _generate_action_items(
    metrics: OperationalMetrics,
    bottlenecks: List[Bottleneck],
    bloat: List[BloatIndicator]
) -> List[str]:
    """Generate action items from analysis."""
    items = []
    
    # Address top bottlenecks
    for bottleneck in bottlenecks[:3]:
        items.append(bottleneck.recommendation)
    
    # Address bloat
    if bloat:
        items.append(f"Review and remove {len(bloat)} bloated components")
    
    # General improvements
    if metrics.current_autonomy_pct < 90:
        items.append(f"Increase autonomy from {metrics.current_autonomy_pct:.0f}% to >90%")
    
    return items
