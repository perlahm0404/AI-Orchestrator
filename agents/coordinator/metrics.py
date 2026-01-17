"""
Metrics Module for Governance Harmonization & AI HR Performance

Provides:
1. Autonomy tracking - % tasks completed without human intervention
2. Token usage profiling - Governance context tokens per task
3. Governance dashboard - Cross-repo status and agent utilization
4. AI HR Framework - Agent roster, skills matrix, performance tracking
5. Skill gap analysis - Identify training needs

Integration: Phase 5 of Governance Harmonization + Strategic AI Team Vision
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


# ═══════════════════════════════════════════════════════════════════════════════
# AI HR FRAMEWORK - Agent Roster & Skills
# ═══════════════════════════════════════════════════════════════════════════════


class PerformanceStatus(Enum):
    """Performance status indicators."""
    EXCELLENT = "🟢"  # >= 100% of target
    ON_TRACK = "🟡"   # 80-99% of target
    NEEDS_IMPROVEMENT = "🔴"  # < 80% of target


class AuthorityLevel(Enum):
    """Agent authority levels (from CLAUDE.md governance)."""
    L0 = "L0 - Observer"       # Read only
    L05 = "L0.5 - Operator"    # Ops with strict gates
    L1 = "L1 - Contributor"    # Limited writes
    L2 = "L2 - Developer"      # Full dev with tests
    L3 = "L3 - Architect"      # Config changes
    L4 = "L4 - Admin"          # All permissions


@dataclass
class Skill:
    """A skill that an agent can possess."""
    id: str
    name: str
    category: str  # debugging, testing, deployment, security, etc.
    description: str
    proficiency_levels: List[str] = field(default_factory=lambda: ["basic", "intermediate", "advanced", "expert"])


@dataclass
class AgentProfile:
    """Complete profile of an AI agent including skills and performance."""
    agent_id: str
    name: str
    team: str  # QA, Dev, Ops
    authority_level: str
    description: str
    skills: List[str]  # Skill IDs
    max_iterations: int
    completion_signal: str

    # Performance metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_iterations: float = 0.0
    escalation_count: int = 0
    regression_count: int = 0

    # Computed metrics
    @property
    def fix_rate(self) -> float:
        """Percentage of tasks completed successfully."""
        if self.total_tasks == 0:
            return 0.0
        return round(self.completed_tasks / self.total_tasks * 100, 1)

    @property
    def escalation_rate(self) -> float:
        """Percentage of tasks that required escalation."""
        if self.total_tasks == 0:
            return 0.0
        return round(self.escalation_count / self.total_tasks * 100, 1)

    @property
    def regression_rate(self) -> float:
        """Percentage of tasks that introduced regressions."""
        if self.completed_tasks == 0:
            return 0.0
        return round(self.regression_count / self.completed_tasks * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "team": self.team,
            "authority_level": self.authority_level,
            "description": self.description,
            "skills": self.skills,
            "max_iterations": self.max_iterations,
            "completion_signal": self.completion_signal,
            "performance": {
                "total_tasks": self.total_tasks,
                "completed_tasks": self.completed_tasks,
                "failed_tasks": self.failed_tasks,
                "avg_iterations": self.avg_iterations,
                "escalation_count": self.escalation_count,
                "regression_count": self.regression_count,
                "fix_rate": self.fix_rate,
                "escalation_rate": self.escalation_rate,
                "regression_rate": self.regression_rate,
            }
        }


@dataclass
class SkillGap:
    """Represents a gap between current and required skill coverage."""
    skill_id: str
    skill_name: str
    current_coverage: float  # 0-100%
    target_coverage: float   # 0-100%
    gap: float              # target - current
    remediation: str        # Suggested remediation
    priority: str           # high, medium, low


@dataclass
class PerformanceTarget:
    """A performance target with actual value and status."""
    metric_name: str
    target_value: float
    current_value: float
    unit: str  # %, count, etc.

    @property
    def status(self) -> PerformanceStatus:
        if self.target_value == 0:
            return PerformanceStatus.ON_TRACK
        ratio = self.current_value / self.target_value
        if ratio >= 1.0:
            return PerformanceStatus.EXCELLENT
        elif ratio >= 0.8:
            return PerformanceStatus.ON_TRACK
        else:
            return PerformanceStatus.NEEDS_IMPROVEMENT

    @property
    def gap(self) -> float:
        return round(self.target_value - self.current_value, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target": self.target_value,
            "current": self.current_value,
            "unit": self.unit,
            "status": self.status.value,
            "gap": self.gap,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT ROSTER - Single Source of Truth
# ═══════════════════════════════════════════════════════════════════════════════


# Skills Catalog - Core competencies
SKILLS_CATALOG: Dict[str, Skill] = {
    # Debugging & Fixing
    "debugging": Skill("debugging", "Debugging", "fixing", "Identify root cause of issues"),
    "root_cause_analysis": Skill("root_cause_analysis", "Root Cause Analysis", "fixing", "Deep analysis to find underlying issues"),
    "error_handling": Skill("error_handling", "Error Handling", "fixing", "Implement proper error handling patterns"),

    # Testing
    "unit_testing": Skill("unit_testing", "Unit Testing", "testing", "Write and maintain unit tests"),
    "integration_testing": Skill("integration_testing", "Integration Testing", "testing", "Test component interactions"),
    "e2e_testing": Skill("e2e_testing", "E2E Testing", "testing", "End-to-end test automation"),
    "test_design": Skill("test_design", "Test Design", "testing", "Design effective test strategies"),
    "tdd": Skill("tdd", "Test-Driven Development", "testing", "Write tests before implementation"),
    "coverage_analysis": Skill("coverage_analysis", "Coverage Analysis", "testing", "Analyze and improve test coverage"),

    # Code Quality
    "linting": Skill("linting", "Linting", "quality", "Static code analysis and fixes"),
    "refactoring": Skill("refactoring", "Refactoring", "quality", "Improve code structure without changing behavior"),
    "code_standards": Skill("code_standards", "Code Standards", "quality", "Enforce coding conventions"),
    "type_checking": Skill("type_checking", "Type Checking", "quality", "TypeScript/mypy type safety"),
    "documentation": Skill("documentation", "Documentation", "quality", "Write clear technical documentation"),

    # Development
    "implementation": Skill("implementation", "Implementation", "development", "Build new features from specs"),
    "api_design": Skill("api_design", "API Design", "development", "Design RESTful APIs"),
    "integration": Skill("integration", "Integration", "development", "Integrate with external systems"),
    "database_design": Skill("database_design", "Database Design", "development", "Schema design and migrations"),

    # Architecture
    "system_design": Skill("system_design", "System Design", "architecture", "High-level architecture planning"),
    "pattern_recognition": Skill("pattern_recognition", "Pattern Recognition", "architecture", "Identify and apply design patterns"),
    "adr_creation": Skill("adr_creation", "ADR Creation", "architecture", "Create Architecture Decision Records"),

    # Deployment & Ops
    "ci_cd": Skill("ci_cd", "CI/CD", "deployment", "Continuous integration and deployment"),
    "deployment": Skill("deployment", "Deployment", "deployment", "Application deployment"),
    "migration": Skill("migration", "Migration", "deployment", "Database and data migrations"),
    "rollback": Skill("rollback", "Rollback", "deployment", "Safe rollback procedures"),
    "monitoring": Skill("monitoring", "Monitoring", "deployment", "Health checks and observability"),

    # Security & Compliance
    "security_scanning": Skill("security_scanning", "Security Scanning", "security", "Detect security vulnerabilities"),
    "hipaa_compliance": Skill("hipaa_compliance", "HIPAA Compliance", "security", "PHI handling and compliance"),
    "secret_management": Skill("secret_management", "Secret Management", "security", "Secure credential handling"),
    "access_control": Skill("access_control", "Access Control", "security", "Permission and authorization"),

    # Strategy & Planning
    "prioritization": Skill("prioritization", "Prioritization", "strategy", "Evidence-based task prioritization"),
    "roadmap_planning": Skill("roadmap_planning", "Roadmap Planning", "strategy", "Product roadmap development"),
    "market_analysis": Skill("market_analysis", "Market Analysis", "strategy", "GTM and competitive analysis"),
    "resource_allocation": Skill("resource_allocation", "Resource Allocation", "strategy", "Efficient resource distribution"),
}


# Agent Roster - Complete list of agents with skills
AGENT_ROSTER: Dict[str, AgentProfile] = {
    # QA Team (L2 Autonomy)
    "bugfix": AgentProfile(
        agent_id="bugfix",
        name="BugFixAgent",
        team="QA",
        authority_level="L2",
        description="Fixes bugs autonomously with root cause analysis",
        skills=["debugging", "root_cause_analysis", "unit_testing", "error_handling"],
        max_iterations=15,
        completion_signal="BUGFIX_COMPLETE",
    ),
    "codequality": AgentProfile(
        agent_id="codequality",
        name="CodeQualityAgent",
        team="QA",
        authority_level="L2",
        description="Improves code quality through linting and refactoring",
        skills=["linting", "refactoring", "code_standards", "type_checking"],
        max_iterations=20,
        completion_signal="CODEQUALITY_COMPLETE",
    ),
    "testfixer": AgentProfile(
        agent_id="testfixer",
        name="TestFixerAgent",
        team="QA",
        authority_level="L2",
        description="Repairs broken tests and improves coverage",
        skills=["unit_testing", "test_design", "coverage_analysis", "debugging"],
        max_iterations=15,
        completion_signal="TESTS_COMPLETE",
    ),

    # Dev Team (L1 Autonomy)
    "featurebuilder": AgentProfile(
        agent_id="featurebuilder",
        name="FeatureBuilderAgent",
        team="Dev",
        authority_level="L2",
        description="Builds new features from specifications",
        skills=["implementation", "api_design", "integration", "unit_testing"],
        max_iterations=50,
        completion_signal="FEATURE_COMPLETE",
    ),
    "testwriter": AgentProfile(
        agent_id="testwriter",
        name="TestWriterAgent",
        team="Dev",
        authority_level="L2",
        description="Writes comprehensive tests using TDD",
        skills=["tdd", "test_design", "unit_testing", "integration_testing", "coverage_analysis"],
        max_iterations=15,
        completion_signal="TESTS_COMPLETE",
    ),

    # Ops Team (L0.5 Autonomy)
    "deployment": AgentProfile(
        agent_id="deployment",
        name="DeploymentAgent",
        team="Ops",
        authority_level="L0.5",
        description="Deploys applications with environment gates",
        skills=["deployment", "ci_cd", "monitoring", "rollback"],
        max_iterations=10,
        completion_signal="DEPLOY_COMPLETE",
    ),
    "migration": AgentProfile(
        agent_id="migration",
        name="MigrationAgent",
        team="Ops",
        authority_level="L0.5",
        description="Executes database migrations safely",
        skills=["migration", "database_design", "rollback", "hipaa_compliance"],
        max_iterations=10,
        completion_signal="MIGRATION_COMPLETE",
    ),

    # Meta-Agents (C-Suite Functions)
    "pm_agent": AgentProfile(
        agent_id="pm_agent",
        name="ProductManagerAgent",
        team="Strategy",
        authority_level="L3",
        description="Evidence-driven prioritization and validation",
        skills=["prioritization", "roadmap_planning", "adr_creation"],
        max_iterations=5,
        completion_signal="PM_REVIEW_COMPLETE",
    ),
    "cmo_agent": AgentProfile(
        agent_id="cmo_agent",
        name="CMOAgent",
        team="Strategy",
        authority_level="L3",
        description="GTM strategy and market positioning",
        skills=["market_analysis", "prioritization", "documentation"],
        max_iterations=5,
        completion_signal="CMO_REVIEW_COMPLETE",
    ),
    "governance_agent": AgentProfile(
        agent_id="governance_agent",
        name="GovernanceAgent",
        team="Compliance",
        authority_level="L3",
        description="Compliance validation and policy enforcement",
        skills=["hipaa_compliance", "security_scanning", "access_control", "secret_management"],
        max_iterations=5,
        completion_signal="GOVERNANCE_COMPLETE",
    ),

    # Advisor Agents
    "data_advisor": AgentProfile(
        agent_id="data_advisor",
        name="DataAdvisor",
        team="Advisory",
        authority_level="L2",
        description="Schema, migrations, and query optimization",
        skills=["database_design", "migration", "api_design"],
        max_iterations=10,
        completion_signal="ADVISOR_COMPLETE",
    ),
    "app_advisor": AgentProfile(
        agent_id="app_advisor",
        name="AppAdvisor",
        team="Advisory",
        authority_level="L2",
        description="Architecture patterns and API design",
        skills=["system_design", "api_design", "pattern_recognition"],
        max_iterations=10,
        completion_signal="ADVISOR_COMPLETE",
    ),
    "uiux_advisor": AgentProfile(
        agent_id="uiux_advisor",
        name="UIUXAdvisor",
        team="Advisory",
        authority_level="L2",
        description="Component design and accessibility",
        skills=["implementation", "documentation", "code_standards"],
        max_iterations=10,
        completion_signal="ADVISOR_COMPLETE",
    ),
}


# Performance Targets - Strategic Goals
PERFORMANCE_TARGETS: Dict[str, Dict[str, Union[float, str]]] = {
    "autonomy_pct": {"target": 95.0, "unit": "%"},
    "task_completion_rate": {"target": 98.0, "unit": "%"},
    "avg_iterations": {"target": 5.0, "unit": "iterations", "direction": "lower_is_better"},
    "escalation_rate": {"target": 5.0, "unit": "%", "direction": "lower_is_better"},
    "code_quality_score": {"target": 90.0, "unit": "score"},  # A = 90+
    "test_coverage": {"target": 85.0, "unit": "%"},
    "regression_rate": {"target": 2.0, "unit": "%", "direction": "lower_is_better"},
}


# Skill Coverage Targets by Category
SKILL_COVERAGE_TARGETS: Dict[str, float] = {
    "fixing": 100.0,      # Must have full debugging capability
    "testing": 90.0,      # High priority for quality
    "quality": 90.0,      # High priority for standards
    "development": 80.0,  # Core development skills
    "architecture": 60.0, # Strategic planning
    "deployment": 70.0,   # Ops capability
    "security": 80.0,     # Critical for HIPAA
    "strategy": 50.0,     # Meta-agent capability
}


# Paths
VIBE_KANBAN_ROOT = Path("/Users/tmac/1_REPOS/AI_Orchestrator/vibe-kanban")
METRICS_PATH = VIBE_KANBAN_ROOT / "metrics"
METRICS_LOG = METRICS_PATH / "metrics-log.json"
ADAPTERS_PATH = Path("/Users/tmac/1_REPOS/AI_Orchestrator/adapters")
WORK_QUEUE_PATH = Path("/Users/tmac/1_REPOS/AI_Orchestrator/tasks")


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class TaskMetrics:
    """Metrics for a single task execution."""
    task_id: str
    repo: str
    started_at: str
    completed_at: Optional[str] = None
    iterations: int = 0
    human_interventions: int = 0
    escalations: int = 0
    status: str = "pending"  # pending, completed, blocked, escalated
    governance_tokens: int = 0
    total_tokens: int = 0
    ralph_verdict: Optional[str] = None  # PASS, FAIL, BLOCKED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo": self.repo,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "iterations": self.iterations,
            "human_interventions": self.human_interventions,
            "escalations": self.escalations,
            "status": self.status,
            "governance_tokens": self.governance_tokens,
            "total_tokens": self.total_tokens,
            "ralph_verdict": self.ralph_verdict,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskMetrics":
        return cls(
            task_id=data.get("task_id", ""),
            repo=data.get("repo", ""),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at"),
            iterations=data.get("iterations", 0),
            human_interventions=data.get("human_interventions", 0),
            escalations=data.get("escalations", 0),
            status=data.get("status", "pending"),
            governance_tokens=data.get("governance_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            ralph_verdict=data.get("ralph_verdict"),
        )


@dataclass
class RepoMetrics:
    """Aggregated metrics for a repository."""
    repo: str
    total_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    escalated_tasks: int = 0
    total_iterations: int = 0
    total_human_interventions: int = 0
    total_escalations: int = 0
    total_governance_tokens: int = 0
    total_tokens: int = 0
    autonomy_pct: float = 0.0
    avg_iterations: float = 0.0
    escalation_rate: float = 0.0
    governance_token_avg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo": self.repo,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "blocked_tasks": self.blocked_tasks,
            "escalated_tasks": self.escalated_tasks,
            "total_iterations": self.total_iterations,
            "total_human_interventions": self.total_human_interventions,
            "total_escalations": self.total_escalations,
            "total_governance_tokens": self.total_governance_tokens,
            "total_tokens": self.total_tokens,
            "autonomy_pct": self.autonomy_pct,
            "avg_iterations": self.avg_iterations,
            "escalation_rate": self.escalation_rate,
            "governance_token_avg": self.governance_token_avg,
        }


class MetricsCollector:
    """
    Collects and aggregates metrics for governance tracking.

    Features:
    1. Task-level metrics collection
    2. Repo-level aggregation
    3. Autonomy percentage calculation
    4. Token usage profiling
    """

    def __init__(self):
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self._ensure_directories()
        self._load_state()

    def _ensure_directories(self) -> None:
        """Ensure metrics directories exist."""
        METRICS_PATH.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> None:
        """Load metrics state from file."""
        if METRICS_LOG.exists():
            try:
                with open(METRICS_LOG, 'r') as f:
                    data = json.load(f)
                for task_data in data.get("tasks", []):
                    task = TaskMetrics.from_dict(task_data)
                    self.task_metrics[task.task_id] = task
            except Exception as e:
                print(f"Error loading metrics state: {e}")

    def _save_state(self) -> None:
        """Save metrics state to file."""
        try:
            data = {
                "version": "1.0",
                "last_updated": utc_now().isoformat(),
                "tasks": [t.to_dict() for t in self.task_metrics.values()],
            }
            with open(METRICS_LOG, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving metrics state: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # TASK METRICS
    # ═══════════════════════════════════════════════════════════════════════════

    def start_task(self, task_id: str, repo: str) -> TaskMetrics:
        """
        Record task start.

        Args:
            task_id: Task identifier
            repo: Repository name

        Returns:
            TaskMetrics object
        """
        metrics = TaskMetrics(
            task_id=task_id,
            repo=repo,
            started_at=utc_now().isoformat(),
            status="in_progress",
        )
        self.task_metrics[task_id] = metrics
        self._save_state()
        return metrics

    def record_iteration(self, task_id: str) -> None:
        """Record an iteration for a task."""
        if task_id in self.task_metrics:
            self.task_metrics[task_id].iterations += 1
            self._save_state()

    def record_human_intervention(self, task_id: str) -> None:
        """Record a human intervention for a task."""
        if task_id in self.task_metrics:
            self.task_metrics[task_id].human_interventions += 1
            self._save_state()

    def record_escalation(self, task_id: str) -> None:
        """Record an escalation for a task."""
        if task_id in self.task_metrics:
            self.task_metrics[task_id].escalations += 1
            self.task_metrics[task_id].status = "escalated"
            self._save_state()

    def record_tokens(
        self,
        task_id: str,
        governance_tokens: int,
        total_tokens: int,
    ) -> None:
        """
        Record token usage for a task.

        Args:
            task_id: Task identifier
            governance_tokens: Tokens used for governance context
            total_tokens: Total tokens used
        """
        if task_id in self.task_metrics:
            self.task_metrics[task_id].governance_tokens += governance_tokens
            self.task_metrics[task_id].total_tokens += total_tokens
            self._save_state()

    def complete_task(
        self,
        task_id: str,
        ralph_verdict: Optional[str] = None,
    ) -> None:
        """
        Record task completion.

        Args:
            task_id: Task identifier
            ralph_verdict: Ralph verification result (PASS/FAIL/BLOCKED)
        """
        if task_id in self.task_metrics:
            self.task_metrics[task_id].completed_at = utc_now().isoformat()
            self.task_metrics[task_id].status = "completed"
            self.task_metrics[task_id].ralph_verdict = ralph_verdict
            self._save_state()

    def block_task(self, task_id: str, _reason: str = "") -> None:
        """Record task blocked."""
        if task_id in self.task_metrics:
            self.task_metrics[task_id].status = "blocked"
            self._save_state()

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Get metrics for a specific task."""
        return self.task_metrics.get(task_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # REPO AGGREGATION
    # ═══════════════════════════════════════════════════════════════════════════

    def get_repo_metrics(self, repo: str) -> RepoMetrics:
        """
        Get aggregated metrics for a repository.

        Args:
            repo: Repository name

        Returns:
            RepoMetrics with aggregated statistics
        """
        repo_tasks = [
            t for t in self.task_metrics.values()
            if t.repo == repo
        ]

        if not repo_tasks:
            return RepoMetrics(repo=repo)

        total = len(repo_tasks)
        completed = len([t for t in repo_tasks if t.status == "completed"])
        blocked = len([t for t in repo_tasks if t.status == "blocked"])
        escalated = len([t for t in repo_tasks if t.status == "escalated"])

        total_iterations = sum(t.iterations for t in repo_tasks)
        total_interventions = sum(t.human_interventions for t in repo_tasks)
        total_escalations = sum(t.escalations for t in repo_tasks)
        total_gov_tokens = sum(t.governance_tokens for t in repo_tasks)
        total_all_tokens = sum(t.total_tokens for t in repo_tasks)

        # Calculate autonomy percentage
        # Autonomy = (completed without intervention) / total completed
        autonomous_completed = len([
            t for t in repo_tasks
            if t.status == "completed" and t.human_interventions == 0
        ])
        autonomy_pct = (autonomous_completed / completed * 100) if completed > 0 else 0

        # Average iterations per completed task
        avg_iterations = (
            total_iterations / completed
            if completed > 0 else 0
        )

        # Escalation rate
        escalation_rate = (escalated / total * 100) if total > 0 else 0

        # Average governance tokens per task
        gov_token_avg = (
            total_gov_tokens / total
            if total > 0 else 0
        )

        return RepoMetrics(
            repo=repo,
            total_tasks=total,
            completed_tasks=completed,
            blocked_tasks=blocked,
            escalated_tasks=escalated,
            total_iterations=total_iterations,
            total_human_interventions=total_interventions,
            total_escalations=total_escalations,
            total_governance_tokens=total_gov_tokens,
            total_tokens=total_all_tokens,
            autonomy_pct=round(autonomy_pct, 1),
            avg_iterations=round(avg_iterations, 2),
            escalation_rate=round(escalation_rate, 1),
            governance_token_avg=round(gov_token_avg, 0),
        )

    def get_all_repo_metrics(self) -> List[RepoMetrics]:
        """Get metrics for all repositories."""
        repos = set(t.repo for t in self.task_metrics.values())
        return [self.get_repo_metrics(repo) for repo in repos]


class GovernanceDashboard:
    """
    Governance dashboard for cross-repo monitoring.

    Provides:
    1. Cross-repo task status
    2. Agent utilization
    3. Policy violations
    4. Autonomy trends
    """

    def __init__(self):
        self.metrics = MetricsCollector()
        self._load_adapters()

    def _load_adapters(self) -> None:
        """Load adapter configurations."""
        self.adapters: Dict[str, Dict[str, Any]] = {}

        if not ADAPTERS_PATH.exists():
            return

        for adapter_dir in ADAPTERS_PATH.iterdir():
            if not adapter_dir.is_dir():
                continue

            config_file = adapter_dir / "config.yaml"
            if not config_file.exists():
                continue

            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                self.adapters[adapter_dir.name] = config
            except Exception:
                continue

    def get_cross_repo_status(self) -> Dict[str, Any]:
        """
        Get cross-repo task status.

        Returns:
            Status summary for all repos
        """
        all_metrics = self.metrics.get_all_repo_metrics()

        total_tasks = sum(m.total_tasks for m in all_metrics)
        total_completed = sum(m.completed_tasks for m in all_metrics)
        total_blocked = sum(m.blocked_tasks for m in all_metrics)
        total_escalated = sum(m.escalated_tasks for m in all_metrics)

        return {
            "generated_at": utc_now().isoformat(),
            "summary": {
                "total_repos": len(all_metrics),
                "total_tasks": total_tasks,
                "total_completed": total_completed,
                "total_blocked": total_blocked,
                "total_escalated": total_escalated,
                "overall_completion_pct": (
                    round(total_completed / total_tasks * 100, 1)
                    if total_tasks > 0 else 0
                ),
            },
            "repos": [m.to_dict() for m in all_metrics],
        }

    def get_agent_utilization(self) -> Dict[str, Any]:
        """
        Get agent utilization metrics.

        Returns:
            Utilization data per agent type
        """
        # Load work queues to get task assignments
        utilization: Dict[str, Dict[str, int]] = {}

        if WORK_QUEUE_PATH.exists():
            for queue_file in WORK_QUEUE_PATH.glob("work_queue_*.json"):
                try:
                    with open(queue_file, 'r') as f:
                        data = json.load(f)

                    for feature in data.get('features', []):
                        agent = feature.get('agent', 'unknown')
                        status = feature.get('status', 'pending')

                        if agent not in utilization:
                            utilization[agent] = {
                                "total": 0,
                                "pending": 0,
                                "completed": 0,
                                "in_progress": 0,
                            }

                        utilization[agent]["total"] += 1
                        if status in utilization[agent]:
                            utilization[agent][status] += 1

                except Exception:
                    continue

        return {
            "generated_at": utc_now().isoformat(),
            "agents": utilization,
        }

    def get_policy_violations(self) -> Dict[str, Any]:
        """
        Get policy violation summary.

        Returns:
            Violations grouped by type and repo
        """
        violations: Dict[str, List[Dict[str, Any]]] = {}

        # Check task metrics for Ralph BLOCKED verdicts
        for task in self.metrics.task_metrics.values():
            if task.ralph_verdict == "BLOCKED":
                repo = task.repo
                if repo not in violations:
                    violations[repo] = []

                violations[repo].append({
                    "task_id": task.task_id,
                    "escalations": task.escalations,
                    "status": task.status,
                })

        return {
            "generated_at": utc_now().isoformat(),
            "total_violations": sum(len(v) for v in violations.values()),
            "by_repo": violations,
        }

    def get_autonomy_summary(self) -> Dict[str, Any]:
        """
        Get autonomy metrics summary.

        Returns:
            Autonomy percentages and targets
        """
        all_metrics = self.metrics.get_all_repo_metrics()

        targets = {
            "credentialmate": 85.0,  # HIPAA repo - 85% target
            "karematch": 90.0,       # Standard repo - 90% target
            "research": 95.0,        # Research repo - 95% target
        }

        summary = {
            "generated_at": utc_now().isoformat(),
            "repos": [],
        }

        for m in all_metrics:
            target = targets.get(m.repo, 85.0)
            gap = target - m.autonomy_pct

            summary["repos"].append({
                "repo": m.repo,
                "current_autonomy_pct": m.autonomy_pct,
                "target_autonomy_pct": target,
                "gap_pct": round(gap, 1),
                "on_target": m.autonomy_pct >= target,
                "avg_iterations": m.avg_iterations,
                "escalation_rate": m.escalation_rate,
            })

        return summary

    def get_token_profile(self) -> Dict[str, Any]:
        """
        Get token usage profile.

        Returns:
            Token usage by repo and task
        """
        all_metrics = self.metrics.get_all_repo_metrics()

        # Target: 2K governance tokens per task
        target_gov_tokens = 2000

        profile = {
            "generated_at": utc_now().isoformat(),
            "target_governance_tokens": target_gov_tokens,
            "repos": [],
        }

        for m in all_metrics:
            profile["repos"].append({
                "repo": m.repo,
                "avg_governance_tokens": m.governance_token_avg,
                "total_governance_tokens": m.total_governance_tokens,
                "total_tokens": m.total_tokens,
                "governance_pct": (
                    round(m.total_governance_tokens / m.total_tokens * 100, 1)
                    if m.total_tokens > 0 else 0
                ),
                "on_target": m.governance_token_avg <= target_gov_tokens,
            })

        return profile

    def generate_full_dashboard(self) -> Dict[str, Any]:
        """
        Generate the full governance dashboard.

        Returns:
            Complete dashboard with all metrics
        """
        return {
            "generated_at": utc_now().isoformat(),
            "version": "1.0",
            "cross_repo_status": self.get_cross_repo_status(),
            "agent_utilization": self.get_agent_utilization(),
            "policy_violations": self.get_policy_violations(),
            "autonomy_summary": self.get_autonomy_summary(),
            "token_profile": self.get_token_profile(),
        }

    def export_dashboard(self, output_path: Optional[Path] = None) -> str:
        """
        Export dashboard to JSON file.

        Args:
            output_path: Path to write JSON (default: metrics/dashboard.json)

        Returns:
            JSON string
        """
        dashboard = self.generate_full_dashboard()
        json_str = json.dumps(dashboard, indent=2)

        if output_path is None:
            output_path = METRICS_PATH / "dashboard.json"

        output_path.write_text(json_str)
        return json_str


# ═══════════════════════════════════════════════════════════════════════════════
# AI HR DASHBOARD - Agent Performance & Skills Management
# ═══════════════════════════════════════════════════════════════════════════════


class AIHRDashboard:
    """
    AI HR Dashboard for agent performance management.

    Provides:
    1. Agent roster & skills matrix
    2. Performance metrics vs targets
    3. Skill gap analysis
    4. Team composition analysis
    5. Agent recommendations

    Role: Chief HR of AI Agents Officer
    """

    def __init__(self):
        self.metrics = MetricsCollector()
        self._agent_performance_cache: Dict[str, Dict[str, Any]] = {}

    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT ROSTER & SKILLS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_agent_roster(self) -> Dict[str, Any]:
        """
        Get the complete agent roster with skills and performance.

        Returns:
            Roster organized by team
        """
        roster_by_team: Dict[str, List[Dict[str, Any]]] = {}

        for agent_id, agent in AGENT_ROSTER.items():
            team = agent.team
            if team not in roster_by_team:
                roster_by_team[team] = []

            agent_dict = agent.to_dict()
            # Enrich with skill details
            agent_dict["skill_details"] = [
                {
                    "id": skill_id,
                    "name": SKILLS_CATALOG[skill_id].name,
                    "category": SKILLS_CATALOG[skill_id].category,
                }
                for skill_id in agent.skills
                if skill_id in SKILLS_CATALOG
            ]
            roster_by_team[team].append(agent_dict)

        return {
            "generated_at": utc_now().isoformat(),
            "total_agents": len(AGENT_ROSTER),
            "total_skills": len(SKILLS_CATALOG),
            "teams": roster_by_team,
        }

    def get_skills_matrix(self) -> Dict[str, Any]:
        """
        Generate skills matrix showing agent coverage per skill.

        Returns:
            Skills matrix with coverage percentages
        """
        skill_coverage: Dict[str, List[str]] = {}

        # Map skills to agents that have them
        for agent_id, agent in AGENT_ROSTER.items():
            for skill_id in agent.skills:
                if skill_id not in skill_coverage:
                    skill_coverage[skill_id] = []
                skill_coverage[skill_id].append(agent_id)

        # Build matrix by category
        matrix_by_category: Dict[str, List[Dict[str, Any]]] = {}

        for skill_id, skill in SKILLS_CATALOG.items():
            category = skill.category
            if category not in matrix_by_category:
                matrix_by_category[category] = []

            agents_with_skill = skill_coverage.get(skill_id, [])
            matrix_by_category[category].append({
                "skill_id": skill_id,
                "skill_name": skill.name,
                "description": skill.description,
                "agents": agents_with_skill,
                "agent_count": len(agents_with_skill),
                "coverage_pct": round(len(agents_with_skill) / len(AGENT_ROSTER) * 100, 1),
            })

        return {
            "generated_at": utc_now().isoformat(),
            "categories": matrix_by_category,
            "skill_count": len(SKILLS_CATALOG),
            "agent_count": len(AGENT_ROSTER),
        }

    def get_agent_by_skill(self, skill_id: str) -> List[Dict[str, Any]]:
        """
        Find all agents with a specific skill.

        Args:
            skill_id: Skill ID to search for

        Returns:
            List of agents with that skill
        """
        agents = []
        for agent_id, agent in AGENT_ROSTER.items():
            if skill_id in agent.skills:
                agents.append({
                    "agent_id": agent_id,
                    "name": agent.name,
                    "team": agent.team,
                    "authority_level": agent.authority_level,
                })
        return agents

    # ═══════════════════════════════════════════════════════════════════════════
    # PERFORMANCE METRICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive performance dashboard with targets.

        Returns:
            Performance metrics vs targets with status indicators
        """
        # Get aggregated metrics from all repos
        all_repo_metrics = self.metrics.get_all_repo_metrics()

        # Calculate overall metrics
        total_tasks = sum(m.total_tasks for m in all_repo_metrics)
        completed_tasks = sum(m.completed_tasks for m in all_repo_metrics)
        escalated_tasks = sum(m.escalated_tasks for m in all_repo_metrics)
        total_iterations = sum(m.total_iterations for m in all_repo_metrics)

        # Calculate current values
        autonomous_completed = sum(
            len([t for t in self.metrics.task_metrics.values()
                 if t.repo == m.repo and t.status == "completed" and t.human_interventions == 0])
            for m in all_repo_metrics
        )

        current_autonomy = (autonomous_completed / completed_tasks * 100) if completed_tasks > 0 else 0
        current_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        current_avg_iterations = (total_iterations / completed_tasks) if completed_tasks > 0 else 0
        current_escalation_rate = (escalated_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Build performance targets with status
        targets = []
        metric_values = {
            "autonomy_pct": current_autonomy,
            "task_completion_rate": current_completion_rate,
            "avg_iterations": current_avg_iterations,
            "escalation_rate": current_escalation_rate,
            "code_quality_score": 85.0,  # Placeholder - integrate with actual quality analysis
            "test_coverage": 82.0,        # Placeholder - integrate with coverage tools
            "regression_rate": 1.5,       # Placeholder - integrate with regression tracking
        }

        for metric_name, config in PERFORMANCE_TARGETS.items():
            target_value = float(config["target"])
            current_value = metric_values.get(metric_name, 0.0)
            unit = str(config.get("unit", ""))
            direction = config.get("direction", "higher_is_better")

            # Adjust status calculation for "lower is better" metrics
            if direction == "lower_is_better":
                # For lower_is_better, we want current <= target
                if current_value <= target_value:
                    status = PerformanceStatus.EXCELLENT
                elif current_value <= target_value * 1.2:
                    status = PerformanceStatus.ON_TRACK
                else:
                    status = PerformanceStatus.NEEDS_IMPROVEMENT
                gap = current_value - target_value  # Positive gap means over target (bad)
            else:
                # For higher_is_better
                if target_value == 0:
                    status = PerformanceStatus.ON_TRACK
                elif current_value >= target_value:
                    status = PerformanceStatus.EXCELLENT
                elif current_value >= target_value * 0.8:
                    status = PerformanceStatus.ON_TRACK
                else:
                    status = PerformanceStatus.NEEDS_IMPROVEMENT
                gap = target_value - current_value  # Positive gap means under target (bad)

            targets.append({
                "metric_name": metric_name,
                "target": target_value,
                "current": round(current_value, 2),
                "unit": unit,
                "status": status.value,
                "gap": round(gap, 2),
                "direction": direction,
            })

        return {
            "generated_at": utc_now().isoformat(),
            "summary": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "escalated_tasks": escalated_tasks,
            },
            "targets": targets,
            "overall_health": self._calculate_overall_health(targets),
        }

    def _calculate_overall_health(self, targets: List[Dict[str, Any]]) -> str:
        """Calculate overall system health from targets."""
        excellent = sum(1 for t in targets if t["status"] == PerformanceStatus.EXCELLENT.value)
        on_track = sum(1 for t in targets if t["status"] == PerformanceStatus.ON_TRACK.value)
        needs_improvement = sum(1 for t in targets if t["status"] == PerformanceStatus.NEEDS_IMPROVEMENT.value)

        total = len(targets)
        if excellent == total:
            return "🟢 EXCELLENT - All targets exceeded"
        elif needs_improvement == 0:
            return "🟡 ON TRACK - Meeting most targets"
        elif needs_improvement <= total / 3:
            return "🟡 ATTENTION - Some targets need improvement"
        else:
            return "🔴 ACTION REQUIRED - Multiple targets below threshold"

    # ═══════════════════════════════════════════════════════════════════════════
    # SKILL GAP ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def analyze_skill_gaps(self) -> Dict[str, Any]:
        """
        Analyze skill gaps across the agent team.

        Returns:
            Gap analysis with remediation recommendations
        """
        gaps: List[SkillGap] = []

        # Calculate current coverage by category
        category_coverage: Dict[str, Dict[str, int]] = {}

        for skill_id, skill in SKILLS_CATALOG.items():
            category = skill.category
            if category not in category_coverage:
                category_coverage[category] = {"total": 0, "covered": 0}

            category_coverage[category]["total"] += 1

            # Check if any agent has this skill
            has_coverage = any(
                skill_id in agent.skills
                for agent in AGENT_ROSTER.values()
            )
            if has_coverage:
                category_coverage[category]["covered"] += 1

        # Calculate gaps
        for category, counts in category_coverage.items():
            target = SKILL_COVERAGE_TARGETS.get(category, 80.0)
            current = (counts["covered"] / counts["total"] * 100) if counts["total"] > 0 else 0
            gap_pct = target - current

            if gap_pct > 0:
                # Determine priority based on gap size and category importance
                if gap_pct > 30 or category in ["security", "fixing"]:
                    priority = "high"
                elif gap_pct > 15:
                    priority = "medium"
                else:
                    priority = "low"

                # Generate remediation recommendation
                remediation = self._generate_remediation(category, gap_pct)

                gaps.append(SkillGap(
                    skill_id=category,
                    skill_name=category.title(),
                    current_coverage=round(current, 1),
                    target_coverage=target,
                    gap=round(gap_pct, 1),
                    remediation=remediation,
                    priority=priority,
                ))

        # Sort by priority and gap size
        priority_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda g: (priority_order[g.priority], -g.gap))

        return {
            "generated_at": utc_now().isoformat(),
            "gaps": [
                {
                    "skill_category": g.skill_id,
                    "skill_name": g.skill_name,
                    "current_coverage": g.current_coverage,
                    "target_coverage": g.target_coverage,
                    "gap": g.gap,
                    "priority": g.priority,
                    "remediation": g.remediation,
                }
                for g in gaps
            ],
            "coverage_summary": {
                category: {
                    "current": round(counts["covered"] / counts["total"] * 100, 1) if counts["total"] > 0 else 0,
                    "target": SKILL_COVERAGE_TARGETS.get(category, 80.0),
                }
                for category, counts in category_coverage.items()
            },
        }

    def _generate_remediation(self, category: str, gap_pct: float) -> str:
        """Generate remediation recommendation for a skill gap."""
        remediations = {
            "security": "Add SecurityAgent or train GovernanceAgent with security scanning skills",
            "testing": "Enhance TestWriter with e2e_testing or add E2ETestAgent",
            "deployment": "Expand DeploymentAgent capabilities or add RollbackAgent",
            "architecture": "Train existing advisors on system_design patterns",
            "fixing": "Critical: Ensure BugFixAgent has full debugging capability",
            "quality": "Add code review agent or enhance CodeQualityAgent",
            "development": "Expand FeatureBuilder with additional integration skills",
            "strategy": "Add strategic planning skills to PM/CMO agents",
        }
        return remediations.get(category, f"Increase {category} skill coverage by {gap_pct:.0f}%")

    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def recommend_agent_for_task(self, task_description: str, task_type: str) -> Dict[str, Any]:
        """
        Recommend the best agent for a task based on skills and performance.

        Args:
            task_description: Description of the task
            task_type: Type of task (bugfix, feature, test, etc.)

        Returns:
            Recommended agent with reasoning
        """
        # Map task types to required skills
        task_skill_requirements = {
            "bugfix": ["debugging", "root_cause_analysis", "unit_testing"],
            "feature": ["implementation", "api_design", "integration", "unit_testing"],
            "test": ["tdd", "test_design", "unit_testing", "integration_testing"],
            "refactor": ["refactoring", "code_standards", "type_checking"],
            "deployment": ["deployment", "ci_cd", "monitoring"],
            "migration": ["migration", "database_design", "rollback"],
            "security": ["security_scanning", "hipaa_compliance", "secret_management"],
        }

        required_skills = task_skill_requirements.get(task_type, ["implementation"])

        # Score agents based on skill match
        agent_scores: List[tuple] = []
        for agent_id, agent in AGENT_ROSTER.items():
            skill_match = len(set(agent.skills) & set(required_skills))
            total_required = len(required_skills)
            match_pct = (skill_match / total_required * 100) if total_required > 0 else 0

            # Factor in performance (fix_rate)
            performance_bonus = agent.fix_rate * 0.1 if agent.total_tasks > 0 else 5  # Default bonus for new agents

            score = match_pct + performance_bonus

            agent_scores.append((agent_id, agent, score, match_pct))

        # Sort by score
        agent_scores.sort(key=lambda x: x[2], reverse=True)

        if not agent_scores:
            return {"error": "No suitable agents found"}

        best = agent_scores[0]
        alternatives = agent_scores[1:3]  # Top 2 alternatives

        return {
            "task_type": task_type,
            "required_skills": required_skills,
            "recommended": {
                "agent_id": best[0],
                "name": best[1].name,
                "team": best[1].team,
                "skill_match_pct": best[3],
                "overall_score": round(best[2], 1),
            },
            "alternatives": [
                {
                    "agent_id": alt[0],
                    "name": alt[1].name,
                    "skill_match_pct": alt[3],
                    "overall_score": round(alt[2], 1),
                }
                for alt in alternatives
            ],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # FULL HR REPORT
    # ═══════════════════════════════════════════════════════════════════════════

    def generate_full_hr_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive AI HR report.

        Returns:
            Complete HR dashboard with all sections
        """
        return {
            "generated_at": utc_now().isoformat(),
            "version": "1.0",
            "title": "AI HR Performance Report",
            "role": "Chief HR of AI Agents Officer",
            "agent_roster": self.get_agent_roster(),
            "skills_matrix": self.get_skills_matrix(),
            "performance_dashboard": self.get_performance_dashboard(),
            "skill_gap_analysis": self.analyze_skill_gaps(),
        }

    def export_hr_report(self, output_path: Optional[Path] = None) -> str:
        """
        Export HR report to JSON file.

        Args:
            output_path: Path to write JSON

        Returns:
            JSON string
        """
        report = self.generate_full_hr_report()
        json_str = json.dumps(report, indent=2)

        if output_path is None:
            output_path = METRICS_PATH / "hr-report.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str)
        return json_str


# CLI interface
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Governance Metrics & AI HR Dashboard")
    parser.add_argument('command', choices=[
        # Governance commands
        'dashboard',
        'repo',
        'autonomy',
        'tokens',
        'violations',
        'utilization',
        # AI HR commands
        'hr-report',
        'roster',
        'skills',
        'performance',
        'skill-gaps',
        'recommend',
    ])
    parser.add_argument('--repo', '-r', help='Repository name')
    parser.add_argument('--export', '-e', action='store_true', help='Export to file')
    parser.add_argument('--task-type', '-t', help='Task type for recommendation (bugfix, feature, test, etc.)')
    parser.add_argument('--skill', '-s', help='Skill ID to search')
    args = parser.parse_args()

    # Governance Dashboard commands
    if args.command in ['dashboard', 'repo', 'autonomy', 'tokens', 'violations', 'utilization']:
        dashboard = GovernanceDashboard()

        if args.command == 'dashboard':
            result = dashboard.generate_full_dashboard()
            if args.export:
                dashboard.export_dashboard()
                print(f"Dashboard exported to {METRICS_PATH / 'dashboard.json'}")
            else:
                print(json.dumps(result, indent=2))

        elif args.command == 'repo':
            if args.repo:
                result = dashboard.metrics.get_repo_metrics(args.repo)
                print(json.dumps(result.to_dict(), indent=2))
            else:
                result = dashboard.get_cross_repo_status()
                print(json.dumps(result, indent=2))

        elif args.command == 'autonomy':
            result = dashboard.get_autonomy_summary()
            print(json.dumps(result, indent=2))

        elif args.command == 'tokens':
            result = dashboard.get_token_profile()
            print(json.dumps(result, indent=2))

        elif args.command == 'violations':
            result = dashboard.get_policy_violations()
            print(json.dumps(result, indent=2))

        elif args.command == 'utilization':
            result = dashboard.get_agent_utilization()
            print(json.dumps(result, indent=2))

    # AI HR Dashboard commands
    else:
        hr = AIHRDashboard()

        if args.command == 'hr-report':
            if args.export:
                hr.export_hr_report()
                print(f"HR Report exported to {METRICS_PATH / 'hr-report.json'}")
            else:
                result = hr.generate_full_hr_report()
                print(json.dumps(result, indent=2))

        elif args.command == 'roster':
            result = hr.get_agent_roster()
            print(json.dumps(result, indent=2))

        elif args.command == 'skills':
            if args.skill:
                agents = hr.get_agent_by_skill(args.skill)
                print(f"Agents with skill '{args.skill}':")
                for agent in agents:
                    print(f"  - {agent['name']} ({agent['team']}) [{agent['authority_level']}]")
            else:
                result = hr.get_skills_matrix()
                print(json.dumps(result, indent=2))

        elif args.command == 'performance':
            result = hr.get_performance_dashboard()
            # Pretty print performance targets
            print("\n📊 AI HR Performance Dashboard")
            print("=" * 60)
            print(f"\n📈 Overall Health: {result['overall_health']}")
            print(f"\nTasks: {result['summary']['total_tasks']} total, "
                  f"{result['summary']['completed_tasks']} completed, "
                  f"{result['summary']['escalated_tasks']} escalated")
            print("\n📋 Performance Targets:")
            print("-" * 60)
            for target in result['targets']:
                print(f"  {target['status']} {target['metric_name']}: "
                      f"{target['current']}{target['unit']} "
                      f"(target: {target['target']}{target['unit']}, "
                      f"gap: {target['gap']:+.2f})")

        elif args.command == 'skill-gaps':
            result = hr.analyze_skill_gaps()
            print("\n🔍 Skill Gap Analysis")
            print("=" * 60)
            if not result['gaps']:
                print("✅ No skill gaps detected - all coverage targets met!")
            else:
                print("\n⚠️  Gaps Identified:")
                for gap in result['gaps']:
                    priority_icon = "🔴" if gap['priority'] == 'high' else "🟡" if gap['priority'] == 'medium' else "🟢"
                    print(f"\n  {priority_icon} {gap['skill_name']} ({gap['priority'].upper()} priority)")
                    print(f"     Coverage: {gap['current_coverage']}% → Target: {gap['target_coverage']}%")
                    print(f"     Gap: {gap['gap']}%")
                    print(f"     💡 {gap['remediation']}")

        elif args.command == 'recommend':
            task_type = args.task_type or 'bugfix'
            result = hr.recommend_agent_for_task("", task_type)
            print(f"\n🤖 Agent Recommendation for '{task_type}' task")
            print("=" * 60)
            print(f"\n✅ Recommended: {result['recommended']['name']}")
            print(f"   Team: {result['recommended']['team']}")
            print(f"   Skill Match: {result['recommended']['skill_match_pct']}%")
            print(f"   Overall Score: {result['recommended']['overall_score']}")
            print(f"\n   Required Skills: {', '.join(result['required_skills'])}")
            if result['alternatives']:
                print("\n📋 Alternatives:")
                for alt in result['alternatives']:
                    print(f"   - {alt['name']} (Match: {alt['skill_match_pct']}%, Score: {alt['overall_score']})")


if __name__ == "__main__":
    main()
