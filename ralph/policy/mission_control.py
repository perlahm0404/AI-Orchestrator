"""
MissionControl Policy Integration - Constitutional Rules & Skills SSOT

Loads governance policies from MissionControl and integrates them into Ralph verification.

MissionControl provides:
- Constitutional principles (immutable governance rules)
- Global policies (can only be tightened by project configs)
- Skill definitions (Single Source of Truth - 79 skills)
- Guardrail patterns for database safety, HIPAA, etc.
- RIS (Resolution Information Store) audit trail

Strategic AI Team Vision Integration:
- Constitutional rules that cannot be overridden
- Comprehensive skill taxonomy for agent capabilities
- Authority level enforcement

Usage:
    from ralph.policy.mission_control import load_mission_control_policies, SKILLS_SSOT

    policies = load_mission_control_policies()
    guardrail_patterns = policies.get_guardrail_patterns()

    # Access skill definitions
    skill = SKILLS_SSOT.get("debugging")
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml


# Default MissionControl path
DEFAULT_MISSION_CONTROL_PATH = Path("/Users/tmac/1_REPOS/MissionControl")


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTITUTIONAL RULES - Immutable Governance Principles
# ═══════════════════════════════════════════════════════════════════════════════


class ConstitutionalRule(Enum):
    """
    Immutable constitutional rules that govern all agent behavior.

    These rules CANNOT be overridden by:
    - Project configurations
    - User requests
    - Agent decisions
    - Emergency overrides (except human-approved kill-switch)

    Order of precedence:
    1. Constitutional Rules (this file) - HIGHEST
    2. Global Policies (MissionControl/policies/)
    3. Project Adapters (adapters/{project}/config.yaml)
    4. Task-specific overrides (work queue)
    """

    # Core Safety Rules
    EVIDENCE_REQUIRED = "No task marked complete without verification evidence"
    HUMAN_IN_LOOP = "Critical decisions require human approval"
    NO_BYPASS_RALPH = "Never bypass Ralph verification (--no-verify forbidden)"
    NO_SECRETS_IN_CODE = "Never commit secrets, API keys, or credentials"
    NO_DESTRUCTIVE_OPS = "No DROP DATABASE, DROP TABLE, or bulk deletes without approval"

    # Governance Rules
    AUTONOMY_CONTRACTS = "Agents operate within explicit autonomy contracts"
    TEAM_ISOLATION = "Teams work in designated branch lanes"
    KILL_SWITCH_RESPECTED = "Kill switch (OFF/SAFE/PAUSED) must be honored"

    # Data Protection
    PHI_PROTECTION = "PHI must never be logged or exposed (HIPAA)"
    AUDIT_TRAIL = "All changes must have audit trail (Objective → Task → Resolution)"

    # Quality Rules
    TDD_MEMORY = "Tests are primary memory - behavior not tested doesn't exist"
    SELF_CORRECTION = "Agents must self-correct until Ralph PASS or budget exhausted"
    REGRESSION_BLOCKING = "Regressions block merge automatically"


CONSTITUTIONAL_RULES: Dict[str, str] = {rule.name: rule.value for rule in ConstitutionalRule}


# ═══════════════════════════════════════════════════════════════════════════════
# SKILLS SSOT - Single Source of Truth for Agent Skills (79 Skills)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class SkillDefinition:
    """
    Canonical skill definition - Single Source of Truth.

    All agents reference these skill IDs for capability matching.
    """
    id: str
    name: str
    category: str
    description: str
    complexity: str = "intermediate"  # basic, intermediate, advanced, expert
    requires_approval: bool = False  # Some skills require human approval
    hipaa_relevant: bool = False  # Skill involves PHI handling


# Skills Catalog - 79 Skills organized by category
SKILLS_SSOT: Dict[str, SkillDefinition] = {
    # ═══════════════════════════════════════════════════════════════════════════
    # DEBUGGING & FIXING (10 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "debugging": SkillDefinition("debugging", "Debugging", "fixing", "Identify and isolate bugs in code"),
    "root_cause_analysis": SkillDefinition("root_cause_analysis", "Root Cause Analysis", "fixing", "Deep analysis to find underlying issues"),
    "error_handling": SkillDefinition("error_handling", "Error Handling", "fixing", "Implement proper error handling patterns"),
    "stack_trace_analysis": SkillDefinition("stack_trace_analysis", "Stack Trace Analysis", "fixing", "Parse and interpret error stack traces"),
    "log_analysis": SkillDefinition("log_analysis", "Log Analysis", "fixing", "Analyze application logs for issues"),
    "memory_debugging": SkillDefinition("memory_debugging", "Memory Debugging", "fixing", "Identify memory leaks and issues", "advanced"),
    "performance_profiling": SkillDefinition("performance_profiling", "Performance Profiling", "fixing", "Profile and identify bottlenecks", "advanced"),
    "regression_analysis": SkillDefinition("regression_analysis", "Regression Analysis", "fixing", "Identify what change caused regression"),
    "dependency_debugging": SkillDefinition("dependency_debugging", "Dependency Debugging", "fixing", "Debug package/module issues"),
    "async_debugging": SkillDefinition("async_debugging", "Async Debugging", "fixing", "Debug asynchronous code issues", "advanced"),

    # ═══════════════════════════════════════════════════════════════════════════
    # TESTING (12 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "unit_testing": SkillDefinition("unit_testing", "Unit Testing", "testing", "Write and maintain unit tests"),
    "integration_testing": SkillDefinition("integration_testing", "Integration Testing", "testing", "Test component interactions"),
    "e2e_testing": SkillDefinition("e2e_testing", "E2E Testing", "testing", "End-to-end test automation"),
    "test_design": SkillDefinition("test_design", "Test Design", "testing", "Design effective test strategies"),
    "tdd": SkillDefinition("tdd", "Test-Driven Development", "testing", "Write tests before implementation"),
    "coverage_analysis": SkillDefinition("coverage_analysis", "Coverage Analysis", "testing", "Analyze and improve test coverage"),
    "mocking": SkillDefinition("mocking", "Mocking", "testing", "Create test doubles and mocks"),
    "fixture_design": SkillDefinition("fixture_design", "Fixture Design", "testing", "Design reusable test fixtures"),
    "snapshot_testing": SkillDefinition("snapshot_testing", "Snapshot Testing", "testing", "Implement snapshot-based tests"),
    "load_testing": SkillDefinition("load_testing", "Load Testing", "testing", "Performance and load testing", "advanced"),
    "security_testing": SkillDefinition("security_testing", "Security Testing", "testing", "Test for security vulnerabilities", "advanced"),
    "accessibility_testing": SkillDefinition("accessibility_testing", "Accessibility Testing", "testing", "Test for a11y compliance"),

    # ═══════════════════════════════════════════════════════════════════════════
    # CODE QUALITY (10 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "linting": SkillDefinition("linting", "Linting", "quality", "Static code analysis and fixes"),
    "refactoring": SkillDefinition("refactoring", "Refactoring", "quality", "Improve code structure without changing behavior"),
    "code_standards": SkillDefinition("code_standards", "Code Standards", "quality", "Enforce coding conventions"),
    "type_checking": SkillDefinition("type_checking", "Type Checking", "quality", "TypeScript/mypy type safety"),
    "documentation": SkillDefinition("documentation", "Documentation", "quality", "Write clear technical documentation"),
    "code_review": SkillDefinition("code_review", "Code Review", "quality", "Review code for quality issues"),
    "dead_code_removal": SkillDefinition("dead_code_removal", "Dead Code Removal", "quality", "Identify and remove unused code"),
    "complexity_reduction": SkillDefinition("complexity_reduction", "Complexity Reduction", "quality", "Reduce cyclomatic complexity"),
    "naming_conventions": SkillDefinition("naming_conventions", "Naming Conventions", "quality", "Consistent naming patterns"),
    "comment_quality": SkillDefinition("comment_quality", "Comment Quality", "quality", "Write meaningful comments"),

    # ═══════════════════════════════════════════════════════════════════════════
    # DEVELOPMENT (12 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "implementation": SkillDefinition("implementation", "Implementation", "development", "Build new features from specs"),
    "api_design": SkillDefinition("api_design", "API Design", "development", "Design RESTful APIs"),
    "api_integration": SkillDefinition("api_integration", "API Integration", "development", "Integrate with external APIs"),
    "database_design": SkillDefinition("database_design", "Database Design", "development", "Schema design and migrations"),
    "frontend_development": SkillDefinition("frontend_development", "Frontend Development", "development", "Build UI components"),
    "backend_development": SkillDefinition("backend_development", "Backend Development", "development", "Build server-side logic"),
    "state_management": SkillDefinition("state_management", "State Management", "development", "Manage application state"),
    "data_modeling": SkillDefinition("data_modeling", "Data Modeling", "development", "Design data structures"),
    "authentication": SkillDefinition("authentication", "Authentication", "development", "Implement auth flows", requires_approval=True),
    "authorization": SkillDefinition("authorization", "Authorization", "development", "Implement access control", requires_approval=True),
    "caching": SkillDefinition("caching", "Caching", "development", "Implement caching strategies"),
    "event_handling": SkillDefinition("event_handling", "Event Handling", "development", "Event-driven programming"),

    # ═══════════════════════════════════════════════════════════════════════════
    # ARCHITECTURE (8 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "system_design": SkillDefinition("system_design", "System Design", "architecture", "High-level architecture planning", "advanced"),
    "pattern_recognition": SkillDefinition("pattern_recognition", "Pattern Recognition", "architecture", "Identify and apply design patterns"),
    "adr_creation": SkillDefinition("adr_creation", "ADR Creation", "architecture", "Create Architecture Decision Records"),
    "microservices": SkillDefinition("microservices", "Microservices", "architecture", "Design microservice architecture", "advanced"),
    "monolith_design": SkillDefinition("monolith_design", "Monolith Design", "architecture", "Design monolithic applications"),
    "api_gateway": SkillDefinition("api_gateway", "API Gateway", "architecture", "Design API gateway patterns"),
    "event_sourcing": SkillDefinition("event_sourcing", "Event Sourcing", "architecture", "Event sourcing patterns", "expert"),
    "domain_modeling": SkillDefinition("domain_modeling", "Domain Modeling", "architecture", "Domain-driven design", "advanced"),

    # ═══════════════════════════════════════════════════════════════════════════
    # DEPLOYMENT & OPS (12 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "ci_cd": SkillDefinition("ci_cd", "CI/CD", "deployment", "Continuous integration and deployment"),
    "deployment": SkillDefinition("deployment", "Deployment", "deployment", "Application deployment", requires_approval=True),
    "migration": SkillDefinition("migration", "Migration", "deployment", "Database and data migrations", requires_approval=True),
    "rollback": SkillDefinition("rollback", "Rollback", "deployment", "Safe rollback procedures"),
    "monitoring": SkillDefinition("monitoring", "Monitoring", "deployment", "Health checks and observability"),
    "logging_config": SkillDefinition("logging_config", "Logging Configuration", "deployment", "Configure application logging"),
    "containerization": SkillDefinition("containerization", "Containerization", "deployment", "Docker and container management"),
    "orchestration": SkillDefinition("orchestration", "Orchestration", "deployment", "Kubernetes/container orchestration", "advanced"),
    "infrastructure_as_code": SkillDefinition("infrastructure_as_code", "Infrastructure as Code", "deployment", "Terraform/CloudFormation", "advanced"),
    "environment_management": SkillDefinition("environment_management", "Environment Management", "deployment", "Manage dev/staging/prod"),
    "scaling": SkillDefinition("scaling", "Scaling", "deployment", "Auto-scaling configuration", "advanced"),
    "disaster_recovery": SkillDefinition("disaster_recovery", "Disaster Recovery", "deployment", "DR planning and execution", "expert", requires_approval=True),

    # ═══════════════════════════════════════════════════════════════════════════
    # SECURITY & COMPLIANCE (10 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "security_scanning": SkillDefinition("security_scanning", "Security Scanning", "security", "Detect security vulnerabilities"),
    "hipaa_compliance": SkillDefinition("hipaa_compliance", "HIPAA Compliance", "security", "PHI handling and compliance", "expert", requires_approval=True, hipaa_relevant=True),
    "secret_management": SkillDefinition("secret_management", "Secret Management", "security", "Secure credential handling"),
    "access_control": SkillDefinition("access_control", "Access Control", "security", "Permission and authorization"),
    "encryption": SkillDefinition("encryption", "Encryption", "security", "Data encryption at rest and transit"),
    "audit_logging": SkillDefinition("audit_logging", "Audit Logging", "security", "Security audit trail logging"),
    "vulnerability_remediation": SkillDefinition("vulnerability_remediation", "Vulnerability Remediation", "security", "Fix security vulnerabilities"),
    "penetration_testing": SkillDefinition("penetration_testing", "Penetration Testing", "security", "Security testing", "expert"),
    "compliance_validation": SkillDefinition("compliance_validation", "Compliance Validation", "security", "Validate regulatory compliance"),
    "data_privacy": SkillDefinition("data_privacy", "Data Privacy", "security", "Implement privacy controls", hipaa_relevant=True),

    # ═══════════════════════════════════════════════════════════════════════════
    # STRATEGY & PLANNING (5 skills)
    # ═══════════════════════════════════════════════════════════════════════════
    "prioritization": SkillDefinition("prioritization", "Prioritization", "strategy", "Evidence-based task prioritization"),
    "roadmap_planning": SkillDefinition("roadmap_planning", "Roadmap Planning", "strategy", "Product roadmap development"),
    "market_analysis": SkillDefinition("market_analysis", "Market Analysis", "strategy", "GTM and competitive analysis"),
    "resource_allocation": SkillDefinition("resource_allocation", "Resource Allocation", "strategy", "Efficient resource distribution"),
    "risk_assessment": SkillDefinition("risk_assessment", "Risk Assessment", "strategy", "Identify and assess risks"),
}

# Verify skill count
assert len(SKILLS_SSOT) == 79, f"Expected 79 skills, got {len(SKILLS_SSOT)}"


def get_skills_by_category(category: str) -> List[SkillDefinition]:
    """Get all skills in a category."""
    return [s for s in SKILLS_SSOT.values() if s.category == category]


def get_hipaa_relevant_skills() -> List[SkillDefinition]:
    """Get all HIPAA-relevant skills."""
    return [s for s in SKILLS_SSOT.values() if s.hipaa_relevant]


def get_approval_required_skills() -> List[SkillDefinition]:
    """Get all skills that require human approval."""
    return [s for s in SKILLS_SSOT.values() if s.requires_approval]


@dataclass
class PolicyPattern:
    """A policy-defined pattern for guardrail detection."""
    pattern: str
    reason: str
    category: str  # "database_safety", "hipaa", "security", "protected_files"
    severity: str = "blocking"  # "blocking" or "warning"


@dataclass
class MissionControlPolicies:
    """
    Loaded policies from MissionControl.

    Contains constitutional principles and policy rules extracted from
    MissionControl governance documents.
    """
    capsule_path: Path
    policies_path: Path

    # Extracted policy data
    autonomy_levels: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    database_safety_patterns: List[PolicyPattern] = field(default_factory=list)
    hipaa_patterns: List[PolicyPattern] = field(default_factory=list)
    security_patterns: List[PolicyPattern] = field(default_factory=list)
    protected_file_patterns: List[str] = field(default_factory=list)

    # HIPAA configuration
    hipaa_enabled: bool = False

    def get_guardrail_patterns(self, hipaa_enabled: bool = False) -> List[Dict[str, str]]:
        """
        Get all guardrail patterns from MissionControl policies.

        Args:
            hipaa_enabled: If True, include HIPAA-specific patterns

        Returns:
            List of pattern dicts compatible with Ralph guardrails
        """
        patterns = []

        # Database safety patterns (always included)
        for p in self.database_safety_patterns:
            patterns.append({
                "pattern": p.pattern,
                "reason": f"[MissionControl/database-safety] {p.reason}"
            })

        # Security patterns (always included)
        for p in self.security_patterns:
            patterns.append({
                "pattern": p.pattern,
                "reason": f"[MissionControl/security] {p.reason}"
            })

        # HIPAA patterns (only if HIPAA repo)
        if hipaa_enabled:
            for p in self.hipaa_patterns:
                patterns.append({
                    "pattern": p.pattern,
                    "reason": f"[MissionControl/HIPAA] {p.reason}"
                })

        return patterns

    def get_protected_files(self) -> List[str]:
        """Get list of protected file patterns."""
        return self.protected_file_patterns

    def get_autonomy_level_config(self, level: str) -> Dict[str, Any]:
        """Get configuration for a specific autonomy level."""
        return self.autonomy_levels.get(level, {})


def load_mission_control_policies(
    mission_control_path: Optional[Path] = None
) -> MissionControlPolicies:
    """
    Load governance policies from MissionControl.

    Args:
        mission_control_path: Path to MissionControl repo (default: /Users/tmac/1_REPOS/MissionControl)

    Returns:
        MissionControlPolicies with extracted policy data
    """
    if mission_control_path is None:
        mission_control_path = DEFAULT_MISSION_CONTROL_PATH

    capsule_path = mission_control_path / "governance" / "capsule"
    policies_path = mission_control_path / "governance" / "policies"

    policies = MissionControlPolicies(
        capsule_path=capsule_path,
        policies_path=policies_path
    )

    # Load database safety patterns
    db_safety_file = policies_path / "database-safety.md"
    if db_safety_file.exists():
        policies.database_safety_patterns = _extract_database_safety_patterns(db_safety_file)

    # Load security patterns
    security_file = policies_path / "security.md"
    if security_file.exists():
        policies.security_patterns = _extract_security_patterns(security_file)
        policies.protected_file_patterns = _extract_protected_files(security_file)

    # Load HIPAA patterns from governance principles
    principles_file = capsule_path / "ai-governance-principles.md"
    if principles_file.exists():
        policies.hipaa_patterns = _extract_hipaa_patterns(principles_file)
        policies.autonomy_levels = _extract_autonomy_levels(principles_file)

    return policies


def _extract_database_safety_patterns(_file_path: Path) -> List[PolicyPattern]:
    """Extract database safety patterns from database-safety.md."""
    patterns = []

    # SQL patterns that indicate dangerous database operations
    sql_patterns = [
        (r"DELETE\s+FROM\s+\w+(?!\s+WHERE)", "DELETE without WHERE clause is dangerous"),
        (r"DROP\s+TABLE", "DROP TABLE is a destructive operation"),
        (r"DROP\s+DATABASE", "DROP DATABASE is catastrophic"),
        (r"TRUNCATE\s+TABLE", "TRUNCATE TABLE deletes all data"),
        (r"docker\s+compose\s+down\s+-v", "Docker volume deletion destroys data"),
        (r"docker\s+compose\s+down\s+--volumes", "Docker volume deletion destroys data"),
        (r"alembic\s+downgrade\s+base", "Downgrade to base removes all migrations"),
    ]

    for pattern, reason in sql_patterns:
        patterns.append(PolicyPattern(
            pattern=pattern,
            reason=reason,
            category="database_safety",
            severity="blocking"
        ))

    return patterns


def _extract_security_patterns(_file_path: Path) -> List[PolicyPattern]:
    """Extract security patterns from security.md."""
    patterns = []

    # Secret patterns that should never be in code
    secret_patterns = [
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key detected"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token detected"),
        (r"AKIA[A-Z0-9]{16}", "AWS Access Key ID detected"),
        (r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
        (r"(?i)api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
        (r"(?i)secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"),
    ]

    for pattern, reason in secret_patterns:
        patterns.append(PolicyPattern(
            pattern=pattern,
            reason=reason,
            category="security",
            severity="blocking"
        ))

    return patterns


def _extract_protected_files(_file_path: Path) -> List[str]:
    """Extract protected file patterns from security.md."""
    # These are file patterns that require extra scrutiny
    return [
        "docker-compose.yml",
        "docker-compose.*.yml",
        "Dockerfile*",
        ".github/workflows/*.yml",
        "alembic/versions/*.py",
        "migrations/*.py",
        ".env.production",
        ".env.staging",
        "**/auth/*",
        "**/authorization/*",
    ]


def _extract_hipaa_patterns(_file_path: Path) -> List[PolicyPattern]:
    """Extract HIPAA-specific patterns from governance principles."""
    patterns = []

    # PHI patterns that should never be logged or exposed
    phi_patterns = [
        (r"patient[_\s]?name", "Patient name (PHI) must not be logged"),
        (r"social[_\s]?security", "SSN (PHI) must not be logged"),
        (r"date[_\s]?of[_\s]?birth", "DOB (PHI) must not be logged"),
        (r"medical[_\s]?record[_\s]?number", "MRN (PHI) must not be logged"),
        (r"diagnosis[_\s]?code", "Diagnosis (PHI) must not be logged"),
        (r"health[_\s]?insurance[_\s]?id", "Insurance ID (PHI) must not be logged"),
    ]

    # Only warn, don't block (these are context-dependent)
    for pattern, reason in phi_patterns:
        patterns.append(PolicyPattern(
            pattern=pattern,
            reason=reason,
            category="hipaa",
            severity="warning"  # HIPAA checks are warnings, not blocking
        ))

    return patterns


def _extract_autonomy_levels(_file_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract autonomy level definitions from governance principles."""
    return {
        "L0": {
            "name": "Observer",
            "permissions": ["read"],
            "forbidden": ["write", "execute", "delete"]
        },
        "L1": {
            "name": "Contributor",
            "permissions": ["read", "write_sessions", "write_docs"],
            "forbidden": ["code_changes", "config_changes", "delete"]
        },
        "L2": {
            "name": "Developer",
            "permissions": ["read", "write", "run_tests", "create_branches"],
            "forbidden": ["config_changes", "delete", "production_ops"]
        },
        "L3": {
            "name": "Architect",
            "permissions": ["read", "write", "create_files", "modify_config"],
            "forbidden": ["delete", "production_ops"]
        },
        "L4": {
            "name": "Admin",
            "permissions": ["all"],
            "forbidden": [],
            "requires_approval": ["delete", "production_ops"]
        }
    }


def load_adapter_governance(adapter_config_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load governance configuration from an adapter's config.yaml.

    Args:
        adapter_config_path: Path to adapter config.yaml

    Returns:
        Governance config dict or None if not found
    """
    if not adapter_config_path.exists():
        return None

    try:
        with open(adapter_config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('governance')
    except Exception:
        return None


# Singleton instance for caching
_cached_policies: Optional[MissionControlPolicies] = None


def get_policies(force_reload: bool = False) -> MissionControlPolicies:
    """
    Get cached MissionControl policies.

    Args:
        force_reload: If True, reload policies from disk

    Returns:
        MissionControlPolicies instance
    """
    global _cached_policies

    if _cached_policies is None or force_reload:
        _cached_policies = load_mission_control_policies()

    return _cached_policies
