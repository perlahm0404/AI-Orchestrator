"""
Agent Scorer - Generate agent performance scorecards

Creates comprehensive agent scorecards with lifecycle recommendations.

Usage:
    from governance.oversight.analyzers.agent_scorer import generate_scorecard
    
    scorecard = generate_scorecard(agent_performance)
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from governance.oversight.hr_metrics import AgentPerformance


@dataclass
class AgentScore:
    """Agent scorecard entry."""
    agent_type: str
    total_tasks: int
    completion_rate: float
    ralph_pass_rate: float
    avg_iterations: float
    grade: str  # "A" | "B" | "C" | "D" | "F"
    recommendation: str
    recommendation_icon: str  # "✅" | "⚠️" | "🗑️" | "❓"
    details: str = ""


def generate_scorecard(agent_performance: Dict[str, AgentPerformance]) -> List[AgentScore]:
    """
    Generate agent performance scorecard.

    Args:
        agent_performance: Dict mapping agent type to AgentPerformance

    Returns:
        List of agent scores, sorted by grade
    """
    scores = []

    for agent_type, perf in agent_performance.items():
        score = _calculate_score(agent_type, perf)
        scores.append(score)

    # Sort by grade (A first, F last)
    grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4}
    return sorted(scores, key=lambda s: grade_order.get(s.grade, 5))


def _calculate_score(agent_type: str, perf: AgentPerformance) -> AgentScore:
    """Calculate score for a single agent."""
    total_tasks = perf.total_tasks
    completion_rate = perf.completion_rate
    ralph_pass_rate = perf.ralph_pass_rate
    avg_iterations = perf.avg_iterations
    
    # Calculate grade based on performance
    grade, details = _assign_grade(completion_rate, ralph_pass_rate, total_tasks)
    
    # Determine recommendation
    recommendation, icon = _determine_recommendation(
        total_tasks, completion_rate, ralph_pass_rate, grade
    )
    
    return AgentScore(
        agent_type=agent_type,
        total_tasks=total_tasks,
        completion_rate=completion_rate,
        ralph_pass_rate=ralph_pass_rate,
        avg_iterations=avg_iterations,
        grade=grade,
        recommendation=recommendation,
        recommendation_icon=icon,
        details=details
    )


def _assign_grade(
    completion_rate: float,
    ralph_pass_rate: float,
    total_tasks: int
) -> tuple[str, str]:
    """Assign letter grade based on performance."""
    
    if total_tasks < 5:
        return "F", "Insufficient data (< 5 tasks)"
    
    # Calculate composite score
    score = (completion_rate * 0.6) + (ralph_pass_rate * 0.4)
    
    if score >= 90:
        return "A", "Excellent performance"
    elif score >= 80:
        return "B", "Good performance"
    elif score >= 70:
        return "C", "Acceptable performance"
    elif score >= 60:
        return "D", "Needs improvement"
    else:
        return "F", "Poor performance"


def _determine_recommendation(
    total_tasks: int,
    completion_rate: float,
    ralph_pass_rate: float,
    grade: str
) -> tuple[str, str]:
    """Determine lifecycle recommendation."""
    
    # Low usage
    if total_tasks < 10:
        return "Sunset or Convert to Skill", "🗑️"
    
    # Poor performance
    if grade in ["D", "F"]:
        return "Needs Improvement or Sunset", "⚠️"
    
    # Good performance
    if grade in ["A", "B"]:
        return "Maintain - Excellent", "✅"
    
    # Acceptable
    return "Maintain with Monitoring", "❓"
