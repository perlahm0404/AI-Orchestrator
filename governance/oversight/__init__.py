"""
Oversight System - Strategic monitoring without runtime overhead

Usage:
    from governance.oversight import generate_report
    
    report = generate_report(period="daily")
    print(report)
"""

from .data_collector import DataCollector
from .coo_metrics import OperationalMetrics
from .hr_metrics import AgentPerformance

__all__ = [
    "DataCollector",
    "OperationalMetrics",
    "AgentPerformance",
    "generate_report",
]


def generate_report(period: str = "daily", days_back: int = 30) -> str:
    """
    Generate oversight report.
    
    Args:
        period: Report period ("daily" | "weekly" | "quarterly")
        days_back: How many days of history to analyze
        
    Returns:
        Formatted markdown report
    """
    # Collect data
    collector = DataCollector()
    data = collector.collect_all(days_back=days_back)
    
    # Calculate metrics
    coo_metrics = OperationalMetrics.from_sessions(data["sessions"])
    
    # Generate agent performance metrics
    agent_performance = {}
    for agent_type in ["BugFix", "CodeQuality", "FeatureBuilder", "TestWriter"]:
        agent_performance[agent_type] = AgentPerformance.from_sessions(
            agent_type, data["sessions"]
        )
    
    # Run analysis
    from .analyzers.bottleneck_detector import identify_bottlenecks
    from .analyzers.bloat_detector import detect_bloat
    from .analyzers.consolidation_finder import find_consolidation_opportunities
    from .analyzers.agent_scorer import generate_scorecard
    
    bottlenecks = identify_bottlenecks(coo_metrics)
    bloat = detect_bloat(data["sessions"], agent_performance)
    consolidation = find_consolidation_opportunities(agent_performance)
    agent_scores = generate_scorecard(agent_performance)
    
    # Generate report based on period
    if period == "daily":
        from .reporters.daily_health import generate_daily_report
        return generate_daily_report(coo_metrics, bottlenecks)
    
    elif period == "weekly":
        from .reporters.weekly_deep_dive import generate_weekly_report
        return generate_weekly_report(
            coo_metrics, agent_scores, bottlenecks, bloat, consolidation
        )
    
    elif period == "quarterly":
        from .reporters.quarterly_review import generate_quarterly_report
        # For quarterly, need previous quarter metrics (placeholder)
        previous_metrics = OperationalMetrics()  # Would load from historical data
        return generate_quarterly_report(
            coo_metrics, previous_metrics, agent_scores, consolidation
        )
    
    else:
        raise ValueError(f"Unknown period: {period}. Use 'daily', 'weekly', or 'quarterly'")
