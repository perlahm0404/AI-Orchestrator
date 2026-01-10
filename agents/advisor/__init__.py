"""
Advisor Agent Package
Version: 3.0
Part of: AI Team (AI-TEAM-SPEC-V3)

Provides domain-specific expertise with conditional autonomy.
Users invoke advisors via @data-advisor, @app-advisor, @uiux-advisor.
"""

from .base_advisor import (
    BaseAdvisor,
    AdvisorConfig,
    AdvisorDecision,
    ConfidenceScore,
    DecisionType,
)
from .data_advisor import DataAdvisor
from .app_advisor import AppAdvisor
from .uiux_advisor import UIUXAdvisor

__all__ = [
    # Base classes
    "BaseAdvisor",
    "AdvisorConfig",
    "AdvisorDecision",
    "ConfidenceScore",
    "DecisionType",
    # Specialist advisors
    "DataAdvisor",
    "AppAdvisor",
    "UIUXAdvisor",
]
