"""
Base Advisor for AI Team
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Provides base functionality for domain-specific advisors:
- Confidence scoring
- ADR alignment checking
- Decision autonomy logic
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import re
import yaml


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS AND CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionType(Enum):
    """Type of decision being made."""
    STRATEGIC = "strategic"    # Requires human approval
    TACTICAL = "tactical"      # Can be auto-decided if confident


class DomainType(Enum):
    """Advisor domain specialization."""
    DATA = "data"              # Schema, migrations, database
    APP = "app"                # Architecture, APIs, patterns
    UIUX = "uiux"              # Components, accessibility, design


# Strategic domains always require human approval
STRATEGIC_DOMAINS = {
    "database_migrations",
    "api_versioning",
    "authentication_flow",
    "data_model_changes",
    "external_integrations",
    "security_policies",
    "hipaa_compliance",
    "breaking_changes",
}

# Tactical domains can be auto-decided if confident
TACTICAL_DOMAINS = {
    "component_structure",
    "utility_functions",
    "test_organization",
    "code_formatting",
    "internal_refactoring",
    "documentation",
    "error_messages",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConfidenceScore:
    """
    Confidence scoring for advisor decisions.

    Components:
    - pattern_match: How well the question matches known patterns (0-1)
    - adr_alignment: How aligned the answer is with existing ADRs (0-1)
    - historical_success: Past success rate for similar decisions (0-1)
    - domain_certainty: How certain advisor is about domain applicability (0-1)

    Weights:
    - pattern_match: 30%
    - adr_alignment: 30%
    - historical_success: 25%
    - domain_certainty: 15%
    """

    pattern_match: float = 0.0
    adr_alignment: float = 0.0
    historical_success: float = 0.0
    domain_certainty: float = 1.0

    # Weights for each component
    WEIGHTS = {
        "pattern_match": 0.30,
        "adr_alignment": 0.30,
        "historical_success": 0.25,
        "domain_certainty": 0.15,
    }

    @property
    def total(self) -> float:
        """Calculate weighted total confidence score."""
        return (
            self.pattern_match * self.WEIGHTS["pattern_match"] +
            self.adr_alignment * self.WEIGHTS["adr_alignment"] +
            self.historical_success * self.WEIGHTS["historical_success"] +
            self.domain_certainty * self.WEIGHTS["domain_certainty"]
        )

    @property
    def is_confident(self) -> bool:
        """Check if confidence meets threshold (85%)."""
        return self.total >= 0.85

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_match": round(self.pattern_match, 3),
            "adr_alignment": round(self.adr_alignment, 3),
            "historical_success": round(self.historical_success, 3),
            "domain_certainty": round(self.domain_certainty, 3),
            "total": round(self.total, 3),
            "is_confident": self.is_confident,
        }


@dataclass
class DiscoveredTask:
    """
    Task discovered during advisor analysis (ADR-003).

    When advisors discover issues during their work, they can report them
    via this dataclass. The coordinator will register these as tasks.
    """

    source: str                           # Where discovered: "ADR-002", "consultation"
    description: str                      # Human-readable task description
    file: str                             # Target file path
    priority: Optional[int] = None        # 0=P0, 1=P1, 2=P2 (auto-computed if None)
    task_type: Optional[str] = None       # "bugfix"|"feature"|"test" (auto-inferred if None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "description": self.description,
            "file": self.file,
            "priority": self.priority,
            "task_type": self.task_type,
        }


@dataclass
class AdvisorDecision:
    """
    Represents a decision made by an advisor.
    """

    advisor: str
    question: str
    recommendation: str
    confidence: ConfidenceScore
    decision_type: DecisionType

    # ADR references
    aligned_adrs: List[str] = field(default_factory=list)
    conflicting_adrs: List[str] = field(default_factory=list)

    # Autonomy
    auto_approved: bool = False
    escalated: bool = False
    escalation_reason: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=utc_now)
    domain_tags: List[str] = field(default_factory=list)

    # ADR-003: Tasks discovered during analysis
    discovered_tasks: List[DiscoveredTask] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "advisor": self.advisor,
            "question": self.question,
            "recommendation": self.recommendation,
            "confidence": self.confidence.to_dict(),
            "decision_type": self.decision_type.value,
            "aligned_adrs": self.aligned_adrs,
            "conflicting_adrs": self.conflicting_adrs,
            "auto_approved": self.auto_approved,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
            "timestamp": self.timestamp.isoformat(),
            "domain_tags": self.domain_tags,
            "discovered_tasks": [t.to_dict() for t in self.discovered_tasks],
        }


@dataclass
class AdvisorConfig:
    """Configuration for an advisor."""

    name: str
    domain: DomainType
    description: str

    # Confidence thresholds
    auto_approve_threshold: float = 0.85
    escalation_threshold: float = 0.60

    # Domain patterns for matching
    domain_patterns: List[str] = field(default_factory=list)

    # Tags this advisor handles
    handled_tags: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# BASE ADVISOR
# ═══════════════════════════════════════════════════════════════════════════════

class BaseAdvisor(ABC):
    """
    Base class for domain-specific advisors.

    Advisors provide expert recommendations on specific domains.
    They can auto-approve decisions when:
    1. Confidence >= 85%
    2. Decision is tactical (not strategic)
    3. No ADR conflicts exist
    """

    def __init__(self, project_root: Path, config: AdvisorConfig):
        """
        Initialize advisor.

        Args:
            project_root: Path to project root
            config: Advisor configuration
        """
        self.project_root = Path(project_root)
        self.config = config
        self.adr_cache: Dict[str, Dict[str, Any]] = {}
        self.history: List[AdvisorDecision] = []

        # Load ADRs for alignment checking
        self._load_adrs()

    # ───────────────────────────────────────────────────────────────────────────
    # Abstract Methods (implement in subclasses)
    # ───────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def analyze(self, question: str, context: Dict[str, Any]) -> AdvisorDecision:
        """
        Analyze a question and provide recommendation.

        Args:
            question: The question to analyze
            context: Additional context (files, code, etc.)

        Returns:
            AdvisorDecision with recommendation
        """
        pass

    @abstractmethod
    def get_domain_patterns(self) -> List[str]:
        """
        Get regex patterns for domain-specific matching.

        Returns:
            List of regex patterns
        """
        pass

    # ───────────────────────────────────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────────────────────────────────

    def consult(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        on_escalate: Optional[Callable[[AdvisorDecision], None]] = None,
    ) -> AdvisorDecision:
        """
        Consult the advisor with a question.

        This is the main entry point. It:
        1. Analyzes the question
        2. Calculates confidence
        3. Checks ADR alignment
        4. Decides whether to auto-approve or escalate

        Args:
            question: The question to ask
            context: Additional context
            on_escalate: Callback if escalation needed

        Returns:
            AdvisorDecision
        """
        context = context or {}

        # Get analysis from subclass
        decision = self.analyze(question, context)

        # Check for ADR conflicts
        if decision.conflicting_adrs:
            decision.escalated = True
            decision.escalation_reason = "ADR_CONFLICT"
            if on_escalate:
                on_escalate(decision)
            return decision

        # Check if strategic domain
        if self._is_strategic_domain(decision.domain_tags):
            decision.decision_type = DecisionType.STRATEGIC
            decision.escalated = True
            decision.escalation_reason = "STRATEGIC_DOMAIN"
            if on_escalate:
                on_escalate(decision)
            return decision

        # Check confidence threshold
        if not decision.confidence.is_confident:
            if decision.confidence.total < self.config.escalation_threshold:
                decision.escalated = True
                decision.escalation_reason = "LOW_CONFIDENCE"
                if on_escalate:
                    on_escalate(decision)
            return decision

        # Auto-approve tactical decisions with high confidence
        if (decision.decision_type == DecisionType.TACTICAL and
            decision.confidence.is_confident and
            not decision.conflicting_adrs):
            decision.auto_approved = True

        # Record in history
        self.history.append(decision)

        return decision

    def get_historical_success_rate(self, tags: List[str]) -> float:
        """
        Get historical success rate for similar decisions.

        Args:
            tags: Domain tags to match

        Returns:
            Success rate (0-1)
        """
        if not self.history:
            return 0.7  # Default for no history

        # Find similar decisions
        similar = [
            d for d in self.history
            if any(t in d.domain_tags for t in tags)
        ]

        if not similar:
            return 0.7

        # Calculate success rate (auto-approved = success, escalated = neutral)
        successful = len([d for d in similar if d.auto_approved])
        return successful / len(similar)

    # ───────────────────────────────────────────────────────────────────────────
    # Confidence Scoring
    # ───────────────────────────────────────────────────────────────────────────

    def calculate_confidence(
        self,
        question: str,
        recommendation: str,
        domain_tags: List[str],
    ) -> ConfidenceScore:
        """
        Calculate confidence score for a decision.

        Args:
            question: The original question
            recommendation: The proposed recommendation
            domain_tags: Tags for this decision

        Returns:
            ConfidenceScore
        """
        return ConfidenceScore(
            pattern_match=self._calculate_pattern_match(question),
            adr_alignment=self._calculate_adr_alignment(recommendation, domain_tags),
            historical_success=self.get_historical_success_rate(domain_tags),
            domain_certainty=self._calculate_domain_certainty(question),
        )

    def _calculate_pattern_match(self, question: str) -> float:
        """Calculate how well question matches known patterns."""
        patterns = self.get_domain_patterns()
        if not patterns:
            return 0.5

        matches = 0
        for pattern in patterns:
            if re.search(pattern, question, re.IGNORECASE):
                matches += 1

        return min(1.0, matches / max(len(patterns) * 0.3, 1))

    def _calculate_adr_alignment(
        self,
        recommendation: str,
        domain_tags: List[str],
    ) -> float:
        """Calculate alignment with existing ADRs."""
        if not self.adr_cache:
            return 0.7  # Default when no ADRs

        relevant_adrs = self._find_relevant_adrs(domain_tags)
        if not relevant_adrs:
            return 0.7

        # Check for keyword alignment
        alignment_score = 0.0
        for adr_id, adr in relevant_adrs.items():
            decision = adr.get("decision", "").lower()
            if any(word in recommendation.lower() for word in decision.split()[:10]):
                alignment_score += 1

        return min(1.0, alignment_score / len(relevant_adrs))

    def _calculate_domain_certainty(self, question: str) -> float:
        """Calculate certainty that question is in advisor's domain."""
        patterns = self.config.domain_patterns
        if not patterns:
            return 0.8

        matches = sum(
            1 for p in patterns
            if re.search(p, question, re.IGNORECASE)
        )

        return min(1.0, 0.5 + (matches / len(patterns)) * 0.5)

    # ───────────────────────────────────────────────────────────────────────────
    # ADR Management
    # ───────────────────────────────────────────────────────────────────────────

    def _load_adrs(self) -> None:
        """Load ADRs from decisions directory."""
        adr_dir = self.project_root / "AI-Team-Plans" / "decisions"
        if not adr_dir.exists():
            return

        for adr_file in adr_dir.glob("ADR-*.md"):
            try:
                content = adr_file.read_text()
                adr_data = self._parse_adr(content)
                if adr_data:
                    self.adr_cache[adr_data["id"]] = adr_data
            except Exception:
                continue

    def _parse_adr(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse ADR markdown content."""
        # Extract ID from title
        id_match = re.search(r"# (ADR-\d+)", content)
        if not id_match:
            return None

        adr_id = id_match.group(1)

        # Extract status
        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
        status = status_match.group(1) if status_match else "unknown"

        # Extract decision section
        decision_match = re.search(
            r"## Decision\s*\n\n(.+?)(?=\n## |\n---|\Z)",
            content,
            re.DOTALL
        )
        decision = decision_match.group(1).strip() if decision_match else ""

        # Extract tags from system section
        tags: List[str] = []
        yaml_match = re.search(r"```yaml\n_system:\n(.+?)```", content, re.DOTALL)
        if yaml_match:
            try:
                system_data = yaml.safe_load(yaml_match.group(1))
                tags = system_data.get("domain_tags", [])
            except yaml.YAMLError:
                pass

        return {
            "id": adr_id,
            "status": status,
            "decision": decision,
            "tags": tags,
        }

    def _find_relevant_adrs(self, domain_tags: List[str]) -> Dict[str, Dict[str, Any]]:
        """Find ADRs relevant to given domain tags."""
        relevant = {}
        for adr_id, adr in self.adr_cache.items():
            if adr.get("status") != "accepted":
                continue
            adr_tags = adr.get("tags", [])
            if any(t in adr_tags for t in domain_tags):
                relevant[adr_id] = adr
        return relevant

    def check_adr_conflicts(
        self,
        recommendation: str,
        domain_tags: List[str],
    ) -> List[str]:
        """
        Check if recommendation conflicts with existing ADRs.

        Args:
            recommendation: Proposed recommendation
            domain_tags: Domain tags for the decision

        Returns:
            List of conflicting ADR IDs
        """
        conflicts = []
        relevant = self._find_relevant_adrs(domain_tags)

        # Simple conflict detection: check for opposing keywords
        opposing_pairs = [
            ("use", "avoid"),
            ("enable", "disable"),
            ("add", "remove"),
            ("require", "optional"),
        ]

        rec_lower = recommendation.lower()

        for adr_id, adr in relevant.items():
            decision = adr.get("decision", "").lower()
            for pos, neg in opposing_pairs:
                if pos in rec_lower and neg in decision:
                    conflicts.append(adr_id)
                    break
                if neg in rec_lower and pos in decision:
                    conflicts.append(adr_id)
                    break

        return conflicts

    def find_aligned_adrs(self, domain_tags: List[str]) -> List[str]:
        """Find ADRs aligned with domain tags."""
        return list(self._find_relevant_adrs(domain_tags).keys())

    # ───────────────────────────────────────────────────────────────────────────
    # Domain Classification
    # ───────────────────────────────────────────────────────────────────────────

    def _is_strategic_domain(self, domain_tags: List[str]) -> bool:
        """Check if any domain tags are strategic."""
        return any(tag in STRATEGIC_DOMAINS for tag in domain_tags)

    def classify_domain(self, question: str) -> List[str]:
        """
        Classify question into domain tags.

        Args:
            question: The question to classify

        Returns:
            List of domain tags
        """
        tags = []
        q_lower = question.lower()

        # Check for strategic domains
        if any(kw in q_lower for kw in ["migration", "schema change", "alter table"]):
            tags.append("database_migrations")
        if any(kw in q_lower for kw in ["api version", "breaking change", "deprecated"]):
            tags.append("api_versioning")
        if any(kw in q_lower for kw in ["authentication", "login", "session", "jwt"]):
            tags.append("authentication_flow")
        if any(kw in q_lower for kw in ["hipaa", "phi", "patient data", "health record"]):
            tags.append("hipaa_compliance")
        if any(kw in q_lower for kw in ["security", "permission", "access control"]):
            tags.append("security_policies")

        # Check for tactical domains
        if any(kw in q_lower for kw in ["component", "react", "vue", "ui element"]):
            tags.append("component_structure")
        if any(kw in q_lower for kw in ["utility", "helper", "util function"]):
            tags.append("utility_functions")
        if any(kw in q_lower for kw in ["test", "spec", "coverage"]):
            tags.append("test_organization")
        if any(kw in q_lower for kw in ["refactor", "cleanup", "reorganize"]):
            tags.append("internal_refactoring")

        return tags if tags else ["general"]


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("BaseAdvisor is an abstract class. Use DataAdvisor, AppAdvisor, or UIUXAdvisor.")
