"""
HR Metrics - Agent Performance Tracking & Lifecycle Management

Monitors agent effectiveness, utilization, and quality.
Chief of HR role: track performance, recommend hire/fire/promote decisions.

Usage:
    from governance.oversight.hr_metrics import AgentPerformance
    perf = AgentPerformance.from_sessions("BugFix", sessions)
    print(f"Completion rate: {perf.completion_rate}%")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgentPerformance:
    """Agent performance metrics."""
    
    agent_type: str  # "BugFix", "CodeQuality", etc.
    
    # Effectiveness
    total_tasks: int = 0
    completion_rate: float = 0.0  # % that reached COMPLETE signal
    ralph_pass_rate: float = 0.0  # % that got PASS verdict
    avg_iterations: float = 0.0
    avg_completion_time_min: float = 0.0
    
    # Quality
    regression_rate: float = 0.0  # % that broke existing tests
    rework_rate: float = 0.0  # % that required human intervention
    knowledge_object_creation_rate: float = 0.0  # Learning capture
    
    # Utilization
    tasks_per_week: float = 0.0
    idle_sessions: int = 0  # Sessions where agent wasn't used
    
    # Trend
    completion_rate_trend: str = "stable"  # "improving" | "stable" | "declining"
    
    # Recommendation
    lifecycle_recommendation: str = "maintain"  # "promote" | "maintain" | "sunset" | "needs_improvement"
    recommendation_reason: str = ""
    
    # Raw data
    task_data: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_sessions(cls, agent_type: str, sessions: List[Dict[str, Any]]) -> "AgentPerformance":
        """
        Calculate agent performance from session data.
        
        Args:
            agent_type: Agent type to analyze (e.g., "BugFix")
            sessions: List of session handoff dicts
            
        Returns:
            AgentPerformance with calculated values
        """
        # Filter sessions for this agent
        agent_tasks = []
        for session in sessions:
            tasks = session.get("tasks", [])
            for task in tasks:
                if task.get("agent_type") == agent_type:
                    agent_tasks.append(task)
        
        if not agent_tasks:
            return cls(agent_type=agent_type, lifecycle_recommendation="no_data")
        
        total_tasks = len(agent_tasks)
        
        # Calculate completion rate
        completed = sum(1 for t in agent_tasks if t.get("completed", False))
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Calculate Ralph PASS rate
        ralph_passes = sum(1 for t in agent_tasks if t.get("ralph_verdict") == "PASS")
        ralph_pass_rate = (ralph_passes / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Calculate average iterations
        iterations = [t.get("iterations", 0) for t in agent_tasks if t.get("iterations")]
        avg_iterations = sum(iterations) / len(iterations) if iterations else 0.0
        
        # Calculate regression rate
        regressions = sum(1 for t in agent_tasks if t.get("caused_regression", False))
        regression_rate = (regressions / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Calculate rework rate
        rework = sum(1 for t in agent_tasks if t.get("required_human_fix", False))
        rework_rate = (rework / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Calculate KO creation rate
        ko_created = sum(1 for t in agent_tasks if t.get("knowledge_object_created", False))
        ko_rate = (ko_created / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Determine lifecycle recommendation
        recommendation, reason = cls._determine_lifecycle(
            completion_rate, ralph_pass_rate, total_tasks, rework_rate
        )
        
        # Determine trend
        if len(agent_tasks) >= 20:
            recent = agent_tasks[-10:]
            previous = agent_tasks[-20:-10]
            
            recent_completion = sum(1 for t in recent if t.get("completed", False)) / len(recent) * 100
            previous_completion = sum(1 for t in previous if t.get("completed", False)) / len(previous) * 100
            
            if recent_completion > previous_completion + 10:
                trend = "improving"
            elif recent_completion < previous_completion - 10:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return cls(
            agent_type=agent_type,
            total_tasks=total_tasks,
            completion_rate=completion_rate,
            ralph_pass_rate=ralph_pass_rate,
            avg_iterations=avg_iterations,
            regression_rate=regression_rate,
            rework_rate=rework_rate,
            knowledge_object_creation_rate=ko_rate,
            completion_rate_trend=trend,
            lifecycle_recommendation=recommendation,
            recommendation_reason=reason,
            task_data=agent_tasks
        )
    
    @staticmethod
    def _determine_lifecycle(
        completion_rate: float,
        ralph_pass_rate: float,
        total_tasks: int,
        rework_rate: float
    ) -> tuple[str, str]:
        """Determine lifecycle recommendation."""
        
        # Sunset criteria
        if total_tasks < 10:
            return ("low_usage", "Low utilization: <10 tasks total")
        
        if completion_rate < 50:
            return ("sunset", f"Low completion rate: {completion_rate:.0f}% (target: >80%)")
        
        if rework_rate > 40:
            return ("sunset", f"High rework rate: {rework_rate:.0f}% (target: <20%)")
        
        # Needs improvement
        if completion_rate < 80 or ralph_pass_rate < 70:
            return ("needs_improvement", f"Completion: {completion_rate:.0f}%, Ralph PASS: {ralph_pass_rate:.0f}%")
        
        # Maintain (good performance)
        if completion_rate >= 80 and ralph_pass_rate >= 85:
            return ("maintain", "Performing well - maintain current approach")
        
        # Default
        return ("maintain", "Standard performance")


@dataclass
class SkillUsage:
    """Skill usage tracking (for promotion candidate analysis)."""
    skill_name: str
    invocations_per_week: float = 0.0
    avg_time_min: float = 0.0
    promotion_candidate: bool = False
    promotion_reason: str = ""
