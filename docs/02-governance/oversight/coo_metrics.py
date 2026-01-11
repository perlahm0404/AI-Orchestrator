"""
COO Metrics - Operational Efficiency Tracking

Monitors system health, bottlenecks, and governance overhead.
Chief Operating Officer role: optimize processes, eliminate friction.

Usage:
    from governance.oversight.coo_metrics import OperationalMetrics
    metrics = OperationalMetrics.from_sessions(sessions)
    print(f"Autonomy: {metrics.current_autonomy_pct}%")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class OperationalMetrics:
    """Operational efficiency metrics."""
    
    # System health
    current_autonomy_pct: float = 0.0  # % tasks completed without human intervention
    tasks_per_session_avg: float = 0.0
    session_resume_frequency: int = 0  # How often loops crash/interrupt
    total_sessions: int = 0
    total_tasks: int = 0
    
    # Process bottlenecks
    ralph_verification_time_avg_sec: float = 0.0
    iteration_budget_exhaustion_rate: float = 0.0  # % tasks hitting max iterations
    human_approval_wait_time_avg_min: float = 0.0
    
    # Governance overhead
    governance_gate_time_avg_sec: float = 0.0  # Meta-agent gate time
    false_positive_blocks_count: int = 0  # Tasks blocked then approved
    
    # Cost efficiency
    cost_per_completed_task_usd: float = 0.0
    total_cost_usd: float = 0.0
    lambda_invocations_per_task: int = 0
    wasted_iterations_pct: float = 0.0  # Iterations that didn't progress task
    
    # Trends
    autonomy_trend: str = "stable"  # "improving" | "stable" | "declining"
    task_throughput_trend: str = "stable"
    
    # Raw data for deeper analysis
    session_data: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_sessions(cls, sessions: List[Dict[str, Any]]) -> "OperationalMetrics":
        """
        Calculate operational metrics from session data.
        
        Args:
            sessions: List of session handoff dicts
            
        Returns:
            OperationalMetrics with calculated values
        """
        if not sessions:
            return cls()
        
        total_sessions = len(sessions)
        total_tasks = sum(s.get("tasks_completed", 0) for s in sessions)
        
        # Calculate autonomy (tasks without human intervention)
        autonomous_tasks = sum(
            s.get("tasks_completed", 0) 
            for s in sessions 
            if not s.get("human_intervention_required", False)
        )
        autonomy_pct = (autonomous_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Calculate iteration budget exhaustion
        budget_exhausted = sum(
            1 for s in sessions 
            if s.get("iteration_budget_exhausted", False)
        )
        exhaustion_rate = (budget_exhausted / total_sessions * 100) if total_sessions > 0 else 0.0
        
        # Calculate average Ralph time (if recorded)
        ralph_times = [s.get("ralph_verification_time_sec", 0) for s in sessions]
        ralph_avg = sum(ralph_times) / len(ralph_times) if ralph_times else 0.0
        
        # Calculate session resume frequency (interrupted sessions)
        resume_count = sum(1 for s in sessions if s.get("resumed_from_checkpoint", False))
        
        # Calculate false positive blocks
        false_positives = sum(
            1 for s in sessions 
            if s.get("blocked_by_governance", False) and s.get("later_approved", False)
        )
        
        # Determine trends (simple: compare last 10 sessions to previous)
        if len(sessions) >= 20:
            recent = sessions[-10:]
            previous = sessions[-20:-10]
            
            recent_autonomy = sum(
                s.get("tasks_completed", 0) for s in recent 
                if not s.get("human_intervention_required", False)
            ) / sum(s.get("tasks_completed", 1) for s in recent) * 100
            
            previous_autonomy = sum(
                s.get("tasks_completed", 0) for s in previous 
                if not s.get("human_intervention_required", False)
            ) / sum(s.get("tasks_completed", 1) for s in previous) * 100
            
            if recent_autonomy > previous_autonomy + 5:
                autonomy_trend = "improving"
            elif recent_autonomy < previous_autonomy - 5:
                autonomy_trend = "declining"
            else:
                autonomy_trend = "stable"
        else:
            autonomy_trend = "stable"
        
        return cls(
            current_autonomy_pct=autonomy_pct,
            tasks_per_session_avg=total_tasks / total_sessions if total_sessions > 0 else 0.0,
            session_resume_frequency=resume_count,
            total_sessions=total_sessions,
            total_tasks=total_tasks,
            ralph_verification_time_avg_sec=ralph_avg,
            iteration_budget_exhaustion_rate=exhaustion_rate,
            false_positive_blocks_count=false_positives,
            autonomy_trend=autonomy_trend,
            session_data=sessions
        )


@dataclass
class Bottleneck:
    """Identified process bottleneck."""
    type: str  # "verification_slow" | "iteration_budget_too_low" | "approval_delays"
    impact_score: int  # 0-10, higher = more critical
    recommendation: str
    affected_sessions: int = 0
    avg_delay_sec: float = 0.0
