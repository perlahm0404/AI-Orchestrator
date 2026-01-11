"""
Meta-coordinator agents for v6.0 architecture.

Agents:
- ProductManagerAgent: Evidence-driven feature prioritization
- CMOAgent: GTM strategy, market positioning validation

Note: GovernanceAgent sunsetted in Phase 2A (2026-01-10)
      - Replaced by governance/risk_keywords.py (utility module)
      - New oversight system coming in Phase 2B (COO + HR metrics)
"""

from agents.coordinator.product_manager import ProductManagerAgent
from agents.coordinator.cmo_agent import CMOAgent

__all__ = ["ProductManagerAgent", "CMOAgent"]
