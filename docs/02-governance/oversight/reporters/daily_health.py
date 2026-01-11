"""
Daily Health Report Generator

Quick health check (30 seconds runtime, high-level metrics).

Usage:
    from governance.oversight.reporters.daily_health import generate_daily_report
    
    report = generate_daily_report(metrics, bottlenecks)
    print(report)
"""

from typing import List
from governance.oversight.coo_metrics import OperationalMetrics, Bottleneck
from datetime import datetime


def generate_daily_report(
    metrics: OperationalMetrics,
    bottlenecks: List[Bottleneck]
) -> str:
    """
    Generate daily health check report.
    
    Args:
        metrics: Operational metrics
        bottlenecks: Identified bottlenecks
        
    Returns:
        Formatted markdown report
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    report = f"""# AI Orchestrator Daily Health - {date_str}

## Key Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Autonomy** | {metrics.current_autonomy_pct:.0f}% | >90% | {_status_icon(metrics.current_autonomy_pct, 90)} |
| **Tasks/Session** | {metrics.tasks_per_session_avg:.1f} | 30-50 | {_status_icon_range(metrics.tasks_per_session_avg, 30, 50)} |
| **Total Tasks** | {metrics.total_tasks} | - | - |
| **Session Crashes** | {metrics.session_resume_frequency} | <5 | {_status_icon(5, metrics.session_resume_frequency, inverse=True)} |

## Alerts

"""

    # Add alerts for critical bottlenecks
    critical_bottlenecks = [b for b in bottlenecks if b.impact_score >= 7]
    
    if critical_bottlenecks:
        for bottleneck in critical_bottlenecks:
            report += f"⚠️  **{bottleneck.type.replace('_', ' ').title()}**: "
            report += f"{bottleneck.recommendation}\n\n"
    else:
        report += "✅ No critical issues detected\n\n"
    
    # Add quick recommendations
    report += "## Quick Recommendations\n\n"
    
    if metrics.iteration_budget_exhaustion_rate > 15:
        report += f"1. Increase iteration budgets - {metrics.iteration_budget_exhaustion_rate:.0f}% exhaustion rate\n"
    
    if metrics.current_autonomy_pct < 90:
        report += f"2. Investigate autonomy blockers - currently at {metrics.current_autonomy_pct:.0f}%\n"
    
    if not (30 <= metrics.tasks_per_session_avg <= 50):
        report += f"3. Review task throughput - {metrics.tasks_per_session_avg:.1f} tasks/session\n"
    
    if not critical_bottlenecks and metrics.current_autonomy_pct >= 90:
        report += "✅ System running optimally - no immediate action needed\n"
    
    report += "\n---\n\n"
    report += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    report += f"*Sessions analyzed: {metrics.total_sessions}*\n"
    
    return report


def _status_icon(value: float, target: float, inverse: bool = False) -> str:
    """Return status icon based on value vs target."""
    if inverse:
        return "✅" if value < target else "❌"
    return "✅" if value >= target else "❌"


def _status_icon_range(value: float, min_target: float, max_target: float) -> str:
    """Return status icon for range check."""
    return "✅" if min_target <= value <= max_target else "⚠️"
