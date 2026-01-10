"""
Advisor Integration for Autonomous Loop
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Integrates domain advisors with the autonomous agent loop:
- Auto-detects when tasks need advisor consultation
- Routes questions to appropriate advisors
- Incorporates advisor recommendations into agent context
- Tracks advisor decisions for learning
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import re
import json


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS (deferred to avoid circular imports)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_data_advisor(project_root: Path):
    """Lazy import DataAdvisor."""
    from agents.advisor.data_advisor import DataAdvisor
    return DataAdvisor(project_root)


def _get_app_advisor(project_root: Path):
    """Lazy import AppAdvisor."""
    from agents.advisor.app_advisor import AppAdvisor
    return AppAdvisor(project_root)


def _get_uiux_advisor(project_root: Path):
    """Lazy import UIUXAdvisor."""
    from agents.advisor.uiux_advisor import UIUXAdvisor
    return UIUXAdvisor(project_root)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class AdvisorType(Enum):
    """Available advisor types."""
    DATA = "data"
    APP = "app"
    UIUX = "uiux"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AdvisorConsultation:
    """Record of an advisor consultation."""

    task_id: str
    advisor_type: AdvisorType
    question: str
    recommendation: str
    confidence: float
    auto_approved: bool
    escalated: bool
    escalation_reason: Optional[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "advisor_type": self.advisor_type.value,
            "question": self.question,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "auto_approved": self.auto_approved,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TaskAnalysis:
    """Analysis of a task to determine advisor needs."""

    task_id: str
    description: str
    needs_advisor: bool
    suggested_advisors: List[AdvisorType]
    detected_domains: List[str]
    priority: str  # "required", "recommended", "optional"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "needs_advisor": self.needs_advisor,
            "suggested_advisors": [a.value for a in self.suggested_advisors],
            "detected_domains": self.detected_domains,
            "priority": self.priority,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TASK ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class TaskAnalyzer:
    """
    Analyzes tasks to determine if they need advisor consultation.

    Uses pattern matching to detect domain-specific concerns.
    """

    # Patterns that suggest data advisor
    DATA_PATTERNS = [
        r"database|db|schema|table|column",
        r"migration|migrate|alter",
        r"query|sql|select|join|index",
        r"postgresql|postgres|sqlite|mysql",
        r"model.*change|data.*model",
        r"foreign key|relationship|constraint",
        r"prisma|drizzle|sqlalchemy|alembic",
    ]

    # Patterns that suggest app advisor
    APP_PATTERNS = [
        r"api|endpoint|route",
        r"architecture|pattern|design",
        r"authentication|auth|login|session",
        r"integration|external|third.?party",
        r"service|controller|handler",
        r"middleware|interceptor",
        r"fastapi|express|nextjs|flask",
    ]

    # Patterns that suggest UI/UX advisor
    UIUX_PATTERNS = [
        r"component|ui|ux|interface",
        r"accessibility|a11y|wcag|aria",
        r"form|input|validation|error",
        r"responsive|mobile|layout",
        r"react|vue|svelte|angular",
        r"style|css|tailwind|design",
        r"modal|dialog|toast|notification",
    ]

    # Strategic patterns that REQUIRE advisor (not optional)
    STRATEGIC_PATTERNS = [
        r"migration|schema.*change|alter.*table",
        r"breaking.*change|deprecat",
        r"hipaa|phi|patient.*data|health",
        r"security|permission|access.*control",
        r"authentication.*flow|oauth|jwt",
        r"api.*version|backward.*compat",
    ]

    def analyze(self, task_id: str, description: str, file_path: Optional[str] = None) -> TaskAnalysis:
        """
        Analyze a task to determine advisor needs.

        Args:
            task_id: Task identifier
            description: Task description
            file_path: Optional file path being modified

        Returns:
            TaskAnalysis with suggested advisors
        """
        text = f"{description} {file_path or ''}".lower()

        suggested = []
        domains = []
        is_strategic = False

        # Check for strategic patterns first
        for pattern in self.STRATEGIC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                is_strategic = True
                domains.append("strategic")
                break

        # Check data patterns
        for pattern in self.DATA_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if AdvisorType.DATA not in suggested:
                    suggested.append(AdvisorType.DATA)
                    domains.append("data")
                break

        # Check app patterns
        for pattern in self.APP_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if AdvisorType.APP not in suggested:
                    suggested.append(AdvisorType.APP)
                    domains.append("app")
                break

        # Check UI/UX patterns
        for pattern in self.UIUX_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if AdvisorType.UIUX not in suggested:
                    suggested.append(AdvisorType.UIUX)
                    domains.append("uiux")
                break

        # Determine priority
        if is_strategic:
            priority = "required"
        elif len(suggested) > 0:
            priority = "recommended"
        else:
            priority = "optional"

        return TaskAnalysis(
            task_id=task_id,
            description=description,
            needs_advisor=len(suggested) > 0,
            suggested_advisors=suggested,
            detected_domains=domains,
            priority=priority,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ADVISOR ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

class AdvisorRouter:
    """
    Routes questions to appropriate advisors and manages consultations.
    """

    def __init__(self, project_root: Path):
        """
        Initialize router.

        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root)
        self.analyzer = TaskAnalyzer()
        self.consultations: List[AdvisorConsultation] = []

        # Lazy-loaded advisors
        self._advisors: Dict[AdvisorType, Any] = {}

    def _get_advisor(self, advisor_type: AdvisorType):
        """Get or create advisor instance."""
        if advisor_type not in self._advisors:
            if advisor_type == AdvisorType.DATA:
                self._advisors[advisor_type] = _get_data_advisor(self.project_root)
            elif advisor_type == AdvisorType.APP:
                self._advisors[advisor_type] = _get_app_advisor(self.project_root)
            elif advisor_type == AdvisorType.UIUX:
                self._advisors[advisor_type] = _get_uiux_advisor(self.project_root)
        return self._advisors[advisor_type]

    def analyze_task(self, task_id: str, description: str, file_path: Optional[str] = None) -> TaskAnalysis:
        """
        Analyze a task to determine if advisors are needed.

        Args:
            task_id: Task identifier
            description: Task description
            file_path: Optional file path

        Returns:
            TaskAnalysis
        """
        return self.analyzer.analyze(task_id, description, file_path)

    def consult(
        self,
        task_id: str,
        advisor_type: AdvisorType,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        on_escalate: Optional[Callable] = None,
    ) -> AdvisorConsultation:
        """
        Consult a specific advisor.

        Args:
            task_id: Task identifier
            advisor_type: Type of advisor to consult
            question: Question to ask
            context: Additional context
            on_escalate: Callback for escalations

        Returns:
            AdvisorConsultation record
        """
        advisor = self._get_advisor(advisor_type)
        decision = advisor.consult(question, context or {}, on_escalate)

        consultation = AdvisorConsultation(
            task_id=task_id,
            advisor_type=advisor_type,
            question=question,
            recommendation=decision.recommendation,
            confidence=decision.confidence.total,
            auto_approved=decision.auto_approved,
            escalated=decision.escalated,
            escalation_reason=decision.escalation_reason,
        )

        self.consultations.append(consultation)
        return consultation

    def consult_all(
        self,
        task_id: str,
        analysis: TaskAnalysis,
        context: Optional[Dict[str, Any]] = None,
        on_escalate: Optional[Callable] = None,
    ) -> List[AdvisorConsultation]:
        """
        Consult all suggested advisors for a task.

        Args:
            task_id: Task identifier
            analysis: Task analysis with suggested advisors
            context: Additional context
            on_escalate: Callback for escalations

        Returns:
            List of consultations
        """
        results = []

        for advisor_type in analysis.suggested_advisors:
            consultation = self.consult(
                task_id=task_id,
                advisor_type=advisor_type,
                question=analysis.description,
                context=context,
                on_escalate=on_escalate,
            )
            results.append(consultation)

        return results

    def get_task_consultations(self, task_id: str) -> List[AdvisorConsultation]:
        """Get all consultations for a task."""
        return [c for c in self.consultations if c.task_id == task_id]

    def get_escalated_consultations(self) -> List[AdvisorConsultation]:
        """Get all escalated consultations."""
        return [c for c in self.consultations if c.escalated]

    def save_consultations(self, path: Path) -> None:
        """Save consultations to file."""
        data = [c.to_dict() for c in self.consultations]
        path.write_text(json.dumps(data, indent=2))

    def load_consultations(self, path: Path) -> None:
        """Load consultations from file."""
        if not path.exists():
            return

        data = json.loads(path.read_text())
        for item in data:
            self.consultations.append(AdvisorConsultation(
                task_id=item["task_id"],
                advisor_type=AdvisorType(item["advisor_type"]),
                question=item["question"],
                recommendation=item["recommendation"],
                confidence=item["confidence"],
                auto_approved=item["auto_approved"],
                escalated=item["escalated"],
                escalation_reason=item.get("escalation_reason"),
                timestamp=datetime.fromisoformat(item["timestamp"]),
            ))


# ═══════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS LOOP INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class AutonomousAdvisorIntegration:
    """
    Integration layer between autonomous loop and advisors.

    Provides hooks for the autonomous loop to:
    1. Pre-analyze tasks for advisor needs
    2. Consult advisors before agent execution
    3. Inject recommendations into agent context
    4. Track consultation outcomes
    """

    def __init__(self, project_root: Path):
        """
        Initialize integration.

        Args:
            project_root: Path to project root
        """
        self.router = AdvisorRouter(project_root)
        self.project_root = Path(project_root)

        # Load previous consultations if they exist
        consultation_path = self.project_root / ".aibrain" / "advisor_consultations.json"
        if consultation_path.exists():
            self.router.load_consultations(consultation_path)

    def pre_task_analysis(
        self,
        task_id: str,
        description: str,
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze task before agent execution.

        Returns enriched context with advisor recommendations.

        Args:
            task_id: Task identifier
            description: Task description
            file_path: Optional file path

        Returns:
            Dict with:
            - needs_advisor: bool
            - analysis: TaskAnalysis
            - recommendations: List[str] if consulted
            - escalations: List[str] if any
        """
        analysis = self.router.analyze_task(task_id, description, file_path)

        result = {
            "needs_advisor": analysis.needs_advisor,
            "analysis": analysis.to_dict(),
            "recommendations": [],
            "escalations": [],
            "context_enrichment": "",
        }

        # If strategic (required) or has suggested advisors, consult them
        if analysis.priority == "required" or analysis.needs_advisor:
            consultations = self.router.consult_all(task_id, analysis)

            for c in consultations:
                if c.escalated:
                    result["escalations"].append(
                        f"[{c.advisor_type.value.upper()}] {c.escalation_reason}: {c.question[:50]}..."
                    )
                else:
                    result["recommendations"].append(c.recommendation)

            # Build context enrichment for agent
            if result["recommendations"]:
                result["context_enrichment"] = self._build_context_enrichment(consultations)

        return result

    def _build_context_enrichment(self, consultations: List[AdvisorConsultation]) -> str:
        """Build context enrichment string for agent."""
        lines = ["## Advisor Recommendations\n"]

        for c in consultations:
            if not c.escalated:
                lines.append(f"### {c.advisor_type.value.upper()} Advisor")
                lines.append(f"**Confidence:** {c.confidence:.0%}")
                lines.append(f"**Recommendation:**\n{c.recommendation}")
                lines.append("")

        return "\n".join(lines)

    def on_task_complete(self, task_id: str, success: bool) -> None:
        """
        Called when a task completes.

        Updates consultation records with outcome.

        Args:
            task_id: Task identifier
            success: Whether task succeeded
        """
        # Save consultations
        consultation_path = self.project_root / ".aibrain" / "advisor_consultations.json"
        consultation_path.parent.mkdir(parents=True, exist_ok=True)
        self.router.save_consultations(consultation_path)

    def get_pending_escalations(self) -> List[Dict[str, Any]]:
        """Get all pending escalations that need human review."""
        return [c.to_dict() for c in self.router.get_escalated_consultations()]


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_advisor_integration(project_root: Path) -> AutonomousAdvisorIntegration:
    """Create an advisor integration instance."""
    return AutonomousAdvisorIntegration(project_root)


def analyze_task_for_advisors(
    project_root: Path,
    task_id: str,
    description: str,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Quick function to analyze a task for advisor needs.

    Args:
        project_root: Path to project root
        task_id: Task identifier
        description: Task description
        file_path: Optional file path

    Returns:
        Analysis result dict
    """
    integration = create_advisor_integration(project_root)
    return integration.pre_task_analysis(task_id, description, file_path)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python advisor_integration.py <project_root> <task_description>")
        print("\nExample:")
        print('  python advisor_integration.py /path/to/project "Add index to users table"')
        sys.exit(1)

    project_root = Path(sys.argv[1])
    description = sys.argv[2]

    # Analyze task
    result = analyze_task_for_advisors(
        project_root=project_root,
        task_id="CLI-001",
        description=description,
    )

    print("\n" + "="*60)
    print("TASK ANALYSIS")
    print("="*60)
    print(f"\nDescription: {description}")
    print(f"Needs Advisor: {result['needs_advisor']}")
    print(f"Priority: {result['analysis']['priority']}")
    print(f"Suggested Advisors: {result['analysis']['suggested_advisors']}")
    print(f"Detected Domains: {result['analysis']['detected_domains']}")

    if result['recommendations']:
        print("\n" + "-"*60)
        print("RECOMMENDATIONS")
        print("-"*60)
        for rec in result['recommendations']:
            print(f"\n{rec}")

    if result['escalations']:
        print("\n" + "-"*60)
        print("ESCALATIONS (Need Human Review)")
        print("-"*60)
        for esc in result['escalations']:
            print(f"  - {esc}")

    if result['context_enrichment']:
        print("\n" + "-"*60)
        print("AGENT CONTEXT ENRICHMENT")
        print("-"*60)
        print(result['context_enrichment'])
