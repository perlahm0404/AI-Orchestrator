"""
Meta-coordinator agents for v6.0+ architecture.

Strategic AI Team Vision:
- CITOInterface: Chief Information & Technology Officer + AI HR (NEW)
- AIHRDashboard: Agent performance management (NEW)

C-Suite Meta-Agents:
- ProductManagerAgent: Evidence-driven feature prioritization
- CMOAgent: GTM strategy, market positioning validation
- PMAgent: Cross-repo coordination and prioritization

Infrastructure:
- VibeKanbanIntegration: Objective → ADR → Task decomposition
- ParallelExecutor: Multi-agent parallel execution
- TraceabilityEngine: End-to-end audit trail
- MetricsCollector: Task and performance metrics
- GovernanceDashboard: Cross-repo governance monitoring

Note: GovernanceAgent sunsetted in Phase 2A (2026-01-10)
      - Replaced by governance/risk_keywords.py (utility module)
      - AI HR Dashboard now provides oversight (Phase 2B)
"""

from agents.coordinator.product_manager import ProductManagerAgent
from agents.coordinator.cmo_agent import CMOAgent
from agents.coordinator.pm_agent import PMAgent
from agents.coordinator.vibe_kanban_integration import VibeKanbanIntegration
from agents.coordinator.parallel_executor import ParallelExecutor
from agents.coordinator.traceability import TraceabilityEngine
from agents.coordinator.metrics import (
    MetricsCollector,
    GovernanceDashboard,
    AIHRDashboard,
    AGENT_ROSTER,
    SKILLS_CATALOG,
)
from agents.coordinator.cito import CITOInterface

__all__ = [
    # Strategic Layer
    "CITOInterface",
    "AIHRDashboard",
    # C-Suite Meta-Agents
    "ProductManagerAgent",
    "CMOAgent",
    "PMAgent",
    # Infrastructure
    "VibeKanbanIntegration",
    "ParallelExecutor",
    "TraceabilityEngine",
    "MetricsCollector",
    "GovernanceDashboard",
    # Data
    "AGENT_ROSTER",
    "SKILLS_CATALOG",
]
