"""
Quarterly Review Report Generator

Strategic review with ROI analysis and ADR generation.

Usage:
    from governance.oversight.reporters.quarterly_review import generate_quarterly_report
    
    report = generate_quarterly_report(metrics, agents, consolidation)
    print(report)
"""

from typing import List, Dict, Any
from governance.oversight.coo_metrics import OperationalMetrics
from governance.oversight.analyzers.agent_scorer import AgentScore
from governance.oversight.analyzers.consolidation_finder import ConsolidationOpportunity
from datetime import datetime, timedelta


def generate_quarterly_report(
    current_metrics: OperationalMetrics,
    previous_quarter_metrics: OperationalMetrics,
    agent_scores: List[AgentScore],
    consolidation: List[ConsolidationOpportunity]
) -> str:
    """
    Generate quarterly strategic review.
    
    Args:
        current_metrics: Current quarter metrics
        previous_quarter_metrics: Previous quarter for comparison
        agent_scores: Agent performance scorecards
        consolidation: Consolidation opportunities
        
    Returns:
        Formatted markdown report
    """
    quarter_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    quarter_end = datetime.now().strftime("%Y-%m-%d")
    
    # Calculate improvements
    autonomy_delta = current_metrics.current_autonomy_pct - previous_quarter_metrics.current_autonomy_pct
    tasks_delta = current_metrics.total_tasks - previous_quarter_metrics.total_tasks
    
    report = f"""# Q{_get_quarter()} {datetime.now().year} System Health Report

**Period**: {quarter_start} to {quarter_end}

---

## Executive Summary

### Key Metrics

| Metric | Current | Previous | Change |
|--------|---------|----------|--------|
| **Autonomy** | {current_metrics.current_autonomy_pct:.0f}% | {previous_quarter_metrics.current_autonomy_pct:.0f}% | {_format_delta(autonomy_delta)}% |
| **Tasks Completed** | {current_metrics.total_tasks} | {previous_quarter_metrics.total_tasks} | {_format_delta(tasks_delta)} |
| **Tasks/Session** | {current_metrics.tasks_per_session_avg:.1f} | {previous_quarter_metrics.tasks_per_session_avg:.1f} | {_format_delta(current_metrics.tasks_per_session_avg - previous_quarter_metrics.tasks_per_session_avg, decimals=1)} |
| **Cost/Task** | ${current_metrics.cost_per_completed_task_usd:.2f} | ${previous_quarter_metrics.cost_per_completed_task_usd:.2f} | {_format_delta(previous_quarter_metrics.cost_per_completed_task_usd - current_metrics.cost_per_completed_task_usd, prefix='$')} |

### Key Achievements

"""
    
    # List achievements
    if autonomy_delta > 10:
        report += f"- ✅ Autonomy increased by {autonomy_delta:.0f}% (significant improvement)\n"
    
    if tasks_delta > 0:
        increase_pct = (tasks_delta / previous_quarter_metrics.total_tasks * 100) if previous_quarter_metrics.total_tasks > 0 else 0
        report += f"- ✅ Task throughput increased {increase_pct:.0f}%\n"
    
    # Agent performance highlights
    top_performers = [s for s in agent_scores if s.grade in ["A", "B"]]
    if top_performers:
        report += f"- ✅ {len(top_performers)} agents performing excellently\n"
    
    report += "\n---\n\n## Strategic Recommendations for Next Quarter\n\n"
    
    # Generate strategic recommendations
    recommendations = _generate_strategic_recommendations(
        current_metrics, agent_scores, consolidation
    )
    
    for i, rec in enumerate(recommendations, 1):
        report += f"### {i}. {rec['title']}\n\n"
        report += f"**Impact**: {rec['impact']}\n\n"
        report += f"**Risk**: {rec['risk']}\n\n"
        report += f"**Timeline**: {rec['timeline']}\n\n"
    
    report += "---\n\n## Agent Fleet Status\n\n"
    
    # Categorize agents
    active = [s for s in agent_scores if s.total_tasks >= 10]
    underutilized = [s for s in agent_scores if s.total_tasks < 10]
    high_performers = [s for s in agent_scores if s.grade in ["A", "B"]]
    needs_work = [s for s in agent_scores if s.grade in ["D", "F"]]
    
    report += f"- **Active Agents**: {len(active)}\n"
    report += f"- **Underutilized**: {len(underutilized)}\n"
    report += f"- **High Performers**: {len(high_performers)}\n"
    report += f"- **Needs Improvement**: {len(needs_work)}\n\n"
    
    report += "### Sunset Recommendations\n\n"
    for agent in underutilized:
        report += f"- **{agent.agent_type}**: {agent.recommendation}\n"
    
    report += "\n---\n\n## ROI Analysis\n\n"
    
    # Calculate ROI
    time_saved_hours = current_metrics.total_tasks * 0.5  # Assume 30min saved per task
    cost_per_hour = 100  # Estimate $100/hour
    value_generated = time_saved_hours * cost_per_hour
    
    roi_pct = (value_generated / (current_metrics.total_cost_usd or 1) - 1) * 100
    
    report += f"- **Investment**: ${current_metrics.total_cost_usd:.2f} (API costs)\n"
    report += f"- **Time Saved**: {time_saved_hours:.0f} hours (estimated)\n"
    report += f"- **Value Generated**: ${value_generated:.2f}\n"
    report += f"- **ROI**: {roi_pct:.0f}%\n\n"
    
    report += "---\n\n## System Health Score\n\n"
    
    # Calculate overall health score
    health_score = _calculate_health_score(current_metrics, agent_scores)
    
    report += f"**Overall Health**: {health_score}/100 ({_health_rating(health_score)})\n\n"
    
    report += "### Score Breakdown\n\n"
    report += f"- Autonomy: {min(current_metrics.current_autonomy_pct, 100):.0f}/100\n"
    report += f"- Agent Performance: {_agent_performance_score(agent_scores)}/100\n"
    report += f"- Cost Efficiency: {_cost_efficiency_score(current_metrics)}/100\n"
    report += f"- Throughput: {_throughput_score(current_metrics)}/100\n\n"
    
    report += "---\n\n"
    report += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    report += f"*Next Review: {(datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')}*\n"
    
    return report


def _get_quarter() -> int:
    """Get current quarter (1-4)."""
    return (datetime.now().month - 1) // 3 + 1


def _format_delta(delta: float, prefix: str = "", decimals: int = 0) -> str:
    """Format delta with color indicator."""
    if decimals == 0:
        formatted = f"{abs(delta):.0f}"
    else:
        formatted = f"{abs(delta):.1f}"
    
    if delta > 0:
        return f"🟢 +{prefix}{formatted}"
    elif delta < 0:
        return f"🔴 -{prefix}{formatted}"
    return "➡️ 0"


def _generate_strategic_recommendations(
    metrics: OperationalMetrics,
    agents: List[AgentScore],
    consolidation: List[ConsolidationOpportunity]
) -> List[Dict[str, str]]:
    """Generate strategic recommendations."""
    recs = []
    
    # Consolidation opportunities
    if consolidation:
        for opp in consolidation[:2]:  # Top 2
            recs.append({
                "title": f"{opp.type.replace('_', ' ').title()}: {', '.join(opp.components)}",
                "impact": opp.estimated_impact,
                "risk": "Low" if opp.complexity == "low" else "Medium",
                "timeline": "2-4 weeks" if opp.complexity == "low" else "4-6 weeks"
            })
    
    # Autonomy improvement
    if metrics.current_autonomy_pct < 90:
        recs.append({
            "title": "Increase Autonomy to 90%+",
            "impact": f"Current: {metrics.current_autonomy_pct:.0f}%, Target: 90%+",
            "risk": "Low",
            "timeline": "6-8 weeks"
        })
    
    return recs


def _calculate_health_score(metrics: OperationalMetrics, agents: List[AgentScore]) -> int:
    """Calculate overall system health score (0-100)."""
    autonomy_score = min(metrics.current_autonomy_pct, 100)
    agent_score = _agent_performance_score(agents)
    cost_score = _cost_efficiency_score(metrics)
    throughput_score = _throughput_score(metrics)
    
    # Weighted average
    return int((autonomy_score * 0.4) + (agent_score * 0.3) + (cost_score * 0.2) + (throughput_score * 0.1))


def _agent_performance_score(agents: List[AgentScore]) -> int:
    """Calculate agent performance score (0-100)."""
    if not agents:
        return 0
    
    grade_values = {"A": 95, "B": 85, "C": 75, "D": 65, "F": 50}
    scores = [grade_values.get(a.grade, 0) for a in agents]
    return int(sum(scores) / len(scores))


def _cost_efficiency_score(metrics: OperationalMetrics) -> int:
    """Calculate cost efficiency score (0-100)."""
    # Lower cost/task is better
    if metrics.cost_per_completed_task_usd <= 0.10:
        return 100
    elif metrics.cost_per_completed_task_usd <= 0.20:
        return 80
    elif metrics.cost_per_completed_task_usd <= 0.30:
        return 60
    return 40


def _throughput_score(metrics: OperationalMetrics) -> int:
    """Calculate throughput score (0-100)."""
    if metrics.tasks_per_session_avg >= 40:
        return 100
    elif metrics.tasks_per_session_avg >= 30:
        return 80
    elif metrics.tasks_per_session_avg >= 20:
        return 60
    return 40


def _health_rating(score: int) -> str:
    """Convert health score to rating."""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Fair"
    return "Needs Improvement"
