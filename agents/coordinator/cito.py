"""
CITO - Chief Information & Technology Officer Module

Provides strategic oversight for the AI Agentic Technology Team:
1. Strategic technology planning & architecture decisions
2. Agent performance management (AI HR Officer)
3. Task routing & resource allocation
4. Escalation handling
5. Quality assurance oversight
6. Continuous improvement recommendations

This is the primary interface for Claude Code acting as CITO + AI HR Officer.

Usage:
    from agents.coordinator.cito import CITOInterface

    cito = CITOInterface()

    # Strategic overview
    overview = cito.get_strategic_overview()

    # Route a task to the best agent
    routing = cito.route_task(task_description, task_type)

    # Get performance report
    report = cito.get_performance_report()
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.coordinator.metrics import (
    AIHRDashboard,
    GovernanceDashboard,
    MetricsCollector,
    AGENT_ROSTER,
    SKILLS_CATALOG,
    PERFORMANCE_TARGETS,
)
from agents.coordinator.traceability import TraceabilityEngine


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class EscalationDecision:
    """Decision from escalation handling."""
    action: str  # approve, modify, block, escalate_further
    reasoning: str
    modifications: Optional[Dict[str, Any]] = None
    requires_human: bool = False


@dataclass
class TaskRouting:
    """Result of task routing decision."""
    recommended_agent: str
    agent_name: str
    team: str
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]]
    requires_approval: bool


class CITOInterface:
    """
    Chief Information & Technology Officer Interface.

    Provides unified access to:
    - AI HR Dashboard (agent management)
    - Governance Dashboard (policy compliance)
    - Traceability Engine (audit trail)
    - Meta-agent coordination

    Role: Strategic oversight and coordination layer
    """

    def __init__(self):
        self.hr_dashboard = AIHRDashboard()
        self.governance_dashboard = GovernanceDashboard()
        self.traceability = TraceabilityEngine()
        self.metrics = MetricsCollector()

    # ═══════════════════════════════════════════════════════════════════════════
    # STRATEGIC OVERVIEW
    # ═══════════════════════════════════════════════════════════════════════════

    def get_strategic_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive strategic overview of the AI team.

        Returns:
            Strategic overview with all key metrics and status
        """
        # Get performance data
        performance = self.hr_dashboard.get_performance_dashboard()

        # Get skill gaps
        skill_gaps = self.hr_dashboard.analyze_skill_gaps()

        # Get governance status
        governance = self.governance_dashboard.get_autonomy_summary()

        # Get traceability summary
        trace_report = self.traceability.get_full_traceability_report()

        return {
            "generated_at": utc_now().isoformat(),
            "role": "Chief Information & Technology Officer + AI HR",
            "strategic_summary": {
                "overall_health": performance.get("overall_health", "Unknown"),
                "total_agents": len(AGENT_ROSTER),
                "total_skills": len(SKILLS_CATALOG),
                "autonomy_targets": {
                    repo.get("repo"): {
                        "current": repo.get("current_autonomy_pct"),
                        "target": repo.get("target_autonomy_pct"),
                        "on_target": repo.get("on_target"),
                    }
                    for repo in governance.get("repos", [])
                },
            },
            "key_metrics": {
                "performance_targets": performance.get("targets", []),
                "skill_gaps_count": len(skill_gaps.get("gaps", [])),
                "high_priority_gaps": [
                    g for g in skill_gaps.get("gaps", [])
                    if g.get("priority") == "high"
                ],
            },
            "traceability": {
                "total_objectives": trace_report.get("total_objectives", 0),
                "total_links": trace_report.get("total_links", 0),
            },
            "recommendations": self._generate_strategic_recommendations(
                performance, skill_gaps, governance
            ),
        }

    def _generate_strategic_recommendations(
        self,
        performance: Dict[str, Any],
        skill_gaps: Dict[str, Any],
        governance: Dict[str, Any],
    ) -> List[str]:
        """Generate strategic recommendations based on current state."""
        recommendations = []

        # Check performance targets
        for target in performance.get("targets", []):
            if target.get("status") == "🔴":
                recommendations.append(
                    f"ACTION: {target['metric_name']} is below target "
                    f"({target['current']} vs {target['target']}). "
                    f"Gap: {abs(target['gap']):.1f}{target['unit']}"
                )

        # Check skill gaps
        high_priority_gaps = [
            g for g in skill_gaps.get("gaps", [])
            if g.get("priority") == "high"
        ]
        for gap in high_priority_gaps:
            recommendations.append(
                f"SKILL GAP: {gap['skill_name']} coverage at {gap['current_coverage']}% "
                f"(target: {gap['target_coverage']}%). {gap['remediation']}"
            )

        # Check autonomy
        for repo in governance.get("repos", []):
            if not repo.get("on_target"):
                recommendations.append(
                    f"AUTONOMY: {repo['repo']} at {repo['current_autonomy_pct']}% "
                    f"(target: {repo['target_autonomy_pct']}%)"
                )

        if not recommendations:
            recommendations.append("✅ All systems operating within targets")

        return recommendations

    # ═══════════════════════════════════════════════════════════════════════════
    # TASK ROUTING
    # ═══════════════════════════════════════════════════════════════════════════

    def route_task(
        self,
        task_description: str,
        task_type: str,
        repo: Optional[str] = None,
    ) -> TaskRouting:
        """
        Route a task to the most appropriate agent.

        Args:
            task_description: Description of the task
            task_type: Type of task (bugfix, feature, test, etc.)
            repo: Optional repository context

        Returns:
            TaskRouting with recommendation and alternatives
        """
        # Get recommendation from HR dashboard
        recommendation = self.hr_dashboard.recommend_agent_for_task(
            task_description, task_type
        )

        # Determine if approval is required based on task type and authority
        requires_approval = self._check_requires_approval(task_type, repo)

        # Build reasoning
        reasoning = self._build_routing_reasoning(
            task_type, recommendation, requires_approval
        )

        return TaskRouting(
            recommended_agent=recommendation["recommended"]["agent_id"],
            agent_name=recommendation["recommended"]["name"],
            team=recommendation["recommended"]["team"],
            confidence=recommendation["recommended"]["overall_score"],
            reasoning=reasoning,
            alternatives=recommendation.get("alternatives", []),
            requires_approval=requires_approval,
        )

    def _check_requires_approval(
        self,
        task_type: str,
        repo: Optional[str],
    ) -> bool:
        """Check if task requires human approval."""
        # High-risk task types always require approval
        high_risk_types = ["deployment", "migration", "security"]
        if task_type in high_risk_types:
            return True

        # HIPAA repo requires approval for certain operations
        if repo == "credentialmate" and task_type in ["feature", "migration"]:
            return True

        return False

    def _build_routing_reasoning(
        self,
        task_type: str,
        recommendation: Dict[str, Any],
        requires_approval: bool,
    ) -> str:
        """Build reasoning for routing decision."""
        agent = recommendation["recommended"]
        skills = recommendation.get("required_skills", [])

        reasoning_parts = [
            f"Selected {agent['name']} for {task_type} task.",
            f"Skill match: {agent['skill_match_pct']}%",
            f"Required skills: {', '.join(skills)}",
        ]

        if requires_approval:
            reasoning_parts.append("⚠️ Requires human approval before execution.")

        return " ".join(reasoning_parts)

    # ═══════════════════════════════════════════════════════════════════════════
    # ESCALATION HANDLING
    # ═══════════════════════════════════════════════════════════════════════════

    def handle_escalation(
        self,
        task_id: str,
        escalation_reason: str,
        current_agent: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EscalationDecision:
        """
        Handle an escalated task from an agent.

        Args:
            task_id: ID of the escalated task
            escalation_reason: Why the task was escalated
            current_agent: Agent that escalated
            context: Additional context

        Returns:
            EscalationDecision with action and reasoning
        """
        # Analyze escalation reason
        escalation_categories = self._categorize_escalation(escalation_reason)

        # Check if this can be handled automatically
        if "iteration_limit" in escalation_categories:
            return self._handle_iteration_limit_escalation(
                task_id, current_agent, context
            )

        if "permission" in escalation_categories:
            return self._handle_permission_escalation(
                task_id, current_agent, context
            )

        if "unclear_requirements" in escalation_categories:
            return EscalationDecision(
                action="escalate_further",
                reasoning="Requirements need clarification from human",
                requires_human=True,
            )

        # Default: requires human decision
        return EscalationDecision(
            action="escalate_further",
            reasoning=f"Escalation reason '{escalation_reason}' requires human review",
            requires_human=True,
        )

    def _categorize_escalation(self, reason: str) -> List[str]:
        """Categorize the escalation reason."""
        categories = []
        reason_lower = reason.lower()

        if "iteration" in reason_lower or "limit" in reason_lower or "budget" in reason_lower:
            categories.append("iteration_limit")

        if "permission" in reason_lower or "approval" in reason_lower or "authority" in reason_lower:
            categories.append("permission")

        if "unclear" in reason_lower or "ambiguous" in reason_lower or "requirement" in reason_lower:
            categories.append("unclear_requirements")

        if "blocked" in reason_lower or "guardrail" in reason_lower:
            categories.append("guardrail_violation")

        return categories if categories else ["unknown"]

    def _handle_iteration_limit_escalation(
        self,
        task_id: str,
        current_agent: str,
        context: Optional[Dict[str, Any]],
    ) -> EscalationDecision:
        """Handle escalation due to iteration limit."""
        agent_profile = AGENT_ROSTER.get(current_agent)

        if agent_profile:
            # Check if we can extend iterations (up to 2x max)
            max_allowed = agent_profile.max_iterations * 2
            current_iterations = context.get("iterations", 0) if context else 0

            if current_iterations < max_allowed:
                return EscalationDecision(
                    action="modify",
                    reasoning=f"Extending iteration budget to {max_allowed}",
                    modifications={"max_iterations": max_allowed},
                    requires_human=False,
                )

        return EscalationDecision(
            action="escalate_further",
            reasoning="Maximum iteration limit reached, requires human decision",
            requires_human=True,
        )

    def _handle_permission_escalation(
        self,
        task_id: str,
        current_agent: str,
        context: Optional[Dict[str, Any]],
    ) -> EscalationDecision:
        """Handle escalation due to permission requirements."""
        # Permission escalations always require human approval
        return EscalationDecision(
            action="escalate_further",
            reasoning="Permission/approval required - escalating to human",
            requires_human=True,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # PERFORMANCE REPORTING
    # ═══════════════════════════════════════════════════════════════════════════

    def get_performance_report(
        self,
        include_agents: bool = True,
        include_skills: bool = True,
        include_gaps: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance report.

        Args:
            include_agents: Include agent roster
            include_skills: Include skills matrix
            include_gaps: Include skill gap analysis

        Returns:
            Performance report
        """
        report = {
            "generated_at": utc_now().isoformat(),
            "title": "CITO Performance Report",
            "performance_dashboard": self.hr_dashboard.get_performance_dashboard(),
            "governance_status": self.governance_dashboard.get_autonomy_summary(),
        }

        if include_agents:
            report["agent_roster"] = self.hr_dashboard.get_agent_roster()

        if include_skills:
            report["skills_matrix"] = self.hr_dashboard.get_skills_matrix()

        if include_gaps:
            report["skill_gaps"] = self.hr_dashboard.analyze_skill_gaps()

        return report

    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent."""
        if agent_id not in AGENT_ROSTER:
            return None

        agent = AGENT_ROSTER[agent_id]
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "team": agent.team,
            "authority_level": agent.authority_level,
            "skills": agent.skills,
            "performance": {
                "total_tasks": agent.total_tasks,
                "completed_tasks": agent.completed_tasks,
                "fix_rate": agent.fix_rate,
                "escalation_rate": agent.escalation_rate,
            },
            "capacity": {
                "max_iterations": agent.max_iterations,
                "completion_signal": agent.completion_signal,
            },
        }

    def get_team_status(self, team: str) -> Dict[str, Any]:
        """Get status of all agents in a team."""
        team_agents = [
            self.get_agent_status(agent_id)
            for agent_id, agent in AGENT_ROSTER.items()
            if agent.team == team
        ]

        return {
            "team": team,
            "agent_count": len(team_agents),
            "agents": team_agents,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTINUOUS IMPROVEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def suggest_improvements(self) -> List[Dict[str, Any]]:
        """
        Analyze current state and suggest improvements.

        Returns:
            List of improvement suggestions with priority
        """
        suggestions = []

        # Analyze skill gaps
        gaps = self.hr_dashboard.analyze_skill_gaps()
        for gap in gaps.get("gaps", []):
            if gap["priority"] == "high":
                suggestions.append({
                    "type": "skill_gap",
                    "priority": "high",
                    "description": f"Address {gap['skill_name']} skill gap",
                    "action": gap["remediation"],
                    "impact": f"Improve {gap['skill_name']} coverage from {gap['current_coverage']}% to {gap['target_coverage']}%",
                })

        # Analyze performance targets
        performance = self.hr_dashboard.get_performance_dashboard()
        for target in performance.get("targets", []):
            if target["status"] == "🔴":
                suggestions.append({
                    "type": "performance",
                    "priority": "high",
                    "description": f"Improve {target['metric_name']}",
                    "action": self._suggest_performance_improvement(target),
                    "impact": f"Close gap of {abs(target['gap']):.1f}{target['unit']}",
                })

        # Analyze autonomy
        governance = self.governance_dashboard.get_autonomy_summary()
        for repo in governance.get("repos", []):
            if not repo.get("on_target"):
                suggestions.append({
                    "type": "autonomy",
                    "priority": "medium",
                    "description": f"Improve {repo['repo']} autonomy",
                    "action": "Review blocked tasks and enhance agent capabilities",
                    "impact": f"Reach {repo['target_autonomy_pct']}% autonomy target",
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 2))

        return suggestions

    def _suggest_performance_improvement(self, target: Dict[str, Any]) -> str:
        """Suggest action for performance improvement."""
        metric = target["metric_name"]

        improvement_actions = {
            "autonomy_pct": "Reduce human interventions by improving agent self-correction",
            "task_completion_rate": "Review and address blocked/failed tasks",
            "avg_iterations": "Optimize agent prompts and context loading",
            "escalation_rate": "Expand agent capabilities for common escalation reasons",
            "code_quality_score": "Enhance CodeQualityAgent with additional linting rules",
            "test_coverage": "Expand TestWriter coverage targets",
            "regression_rate": "Strengthen regression detection in Ralph verification",
        }

        return improvement_actions.get(metric, f"Review and optimize {metric}")

    # ═══════════════════════════════════════════════════════════════════════════
    # EXPORT & REPORTING
    # ═══════════════════════════════════════════════════════════════════════════

    def export_executive_summary(self, output_path: Optional[Path] = None) -> str:
        """
        Export executive summary for stakeholder review.

        Args:
            output_path: Optional path to write file

        Returns:
            JSON string of executive summary
        """
        summary = {
            "title": "AI Agentic Technology Team - Executive Summary",
            "generated_at": utc_now().isoformat(),
            "cito_role": "Chief Information & Technology Officer + AI HR",
            "strategic_overview": self.get_strategic_overview(),
            "improvement_suggestions": self.suggest_improvements()[:5],  # Top 5
        }

        json_str = json.dumps(summary, indent=2)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_str)

        return json_str


# CLI interface
def main():
    """CLI entry point for CITO interface."""
    import argparse

    parser = argparse.ArgumentParser(description="CITO Interface")
    parser.add_argument('command', choices=[
        'overview',
        'route',
        'report',
        'agent',
        'team',
        'improvements',
        'export',
    ])
    parser.add_argument('--task-type', '-t', help='Task type for routing')
    parser.add_argument('--agent', '-a', help='Agent ID')
    parser.add_argument('--team', help='Team name')
    parser.add_argument('--export', '-e', action='store_true', help='Export to file')
    args = parser.parse_args()

    cito = CITOInterface()

    if args.command == 'overview':
        result = cito.get_strategic_overview()
        print("\n🎯 CITO Strategic Overview")
        print("=" * 60)
        print(f"\n📈 Overall Health: {result['strategic_summary']['overall_health']}")
        print(f"   Total Agents: {result['strategic_summary']['total_agents']}")
        print(f"   Total Skills: {result['strategic_summary']['total_skills']}")
        print("\n📋 Recommendations:")
        for rec in result['recommendations']:
            print(f"   • {rec}")

    elif args.command == 'route':
        task_type = args.task_type or 'bugfix'
        routing = cito.route_task("", task_type)
        print(f"\n🔀 Task Routing for '{task_type}'")
        print("=" * 60)
        print(f"\n✅ Recommended: {routing.agent_name}")
        print(f"   Team: {routing.team}")
        print(f"   Confidence: {routing.confidence:.1f}%")
        print(f"   Reasoning: {routing.reasoning}")
        if routing.requires_approval:
            print("   ⚠️  Requires human approval")

    elif args.command == 'report':
        result = cito.get_performance_report(
            include_agents=False,
            include_skills=False,
            include_gaps=True,
        )
        print(json.dumps(result, indent=2))

    elif args.command == 'agent':
        if args.agent:
            result = cito.get_agent_status(args.agent)
            if result:
                print(json.dumps(result, indent=2))
            else:
                print(f"Agent '{args.agent}' not found")
        else:
            print("--agent required")

    elif args.command == 'team':
        team_name = args.team or 'QA'
        result = cito.get_team_status(team_name)
        print(json.dumps(result, indent=2))

    elif args.command == 'improvements':
        suggestions = cito.suggest_improvements()
        print("\n💡 Improvement Suggestions")
        print("=" * 60)
        for i, suggestion in enumerate(suggestions, 1):
            priority_icon = "🔴" if suggestion['priority'] == 'high' else "🟡" if suggestion['priority'] == 'medium' else "🟢"
            print(f"\n{i}. {priority_icon} [{suggestion['type'].upper()}] {suggestion['description']}")
            print(f"   Action: {suggestion['action']}")
            print(f"   Impact: {suggestion['impact']}")

    elif args.command == 'export':
        output_path = Path("vibe-kanban/reports/executive-summary.json")
        cito.export_executive_summary(output_path)
        print(f"Executive summary exported to {output_path}")


if __name__ == "__main__":
    main()
