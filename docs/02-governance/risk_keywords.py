"""
Risk Keyword Patterns - Extracted from GovernanceAgent

Simple keyword-based risk detection patterns for task analysis.
Useful for flagging tasks that may require additional review.

NOTE: These patterns are heuristics only. They should be used as
preliminary filters, not as authoritative security/compliance tools.

For production HIPAA compliance, use:
- credentialmate's phi_detector.py (ML-based PHI detection)
- Formal compliance audit tools
- Human review for critical decisions

Extracted: 2026-01-10 (Phase 2A cleanup)
Source: agents/coordinator/governance_agent.py (deprecated)
"""

import re
from typing import List, Tuple


# ==============================================================================
# KEYWORD LISTS (for simple string matching in task descriptions)
# ==============================================================================

PHI_KEYWORDS: List[str] = [
    "phi",
    "patient",
    "health information",
    "license number",
    "npi",
    "medical record"
]

AUTH_KEYWORDS: List[str] = [
    "auth",
    "authentication",
    "authorization",
    "login",
    "password",
    "session",
    "token",
    "jwt"
]

BILLING_KEYWORDS: List[str] = [
    "billing",
    "payment",
    "stripe",
    "charge",
    "invoice",
    "subscription"
]

INFRASTRUCTURE_KEYWORDS: List[str] = [
    "infrastructure",
    "deploy",
    "aws",
    "lambda",
    "s3",
    "database",
    "migration",
    "production"
]

STATE_EXPANSION_KEYWORDS: List[str] = [
    "new state",
    "add state",
    "state support",
    "expand to"
]


# ==============================================================================
# PHI DETECTION PATTERNS (basic regex - NOT production-grade)
# ==============================================================================

PHI_PATTERNS: List[Tuple[str, str]] = [
    (r'\b\d{3}-\d{2}-\d{4}\b', "SSN"),
    (r'\b[A-Z]{2}\d{5,8}\b', "License Number (e.g., CA12345)"),
    (r'\bNPI\s*:?\s*\d{10}\b', "NPI Number"),
    (r'\b\d{2}/\d{2}/\d{4}\b', "Date (potential DOB)"),
]


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def check_keywords(text: str, keyword_list: List[str]) -> bool:
    """
    Check if any keyword from the list appears in text (case-insensitive).

    Args:
        text: Text to search
        keyword_list: List of keywords to check for

    Returns:
        True if any keyword found, False otherwise
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keyword_list)


def detect_phi_patterns(text: str) -> List[str]:
    """
    Detect potential PHI in text using regex patterns.

    WARNING: This is a simple regex-based detector for preliminary screening only.
    Use ML-based PHI detection (e.g., credentialmate's phi_detector.py) for
    production HIPAA compliance.

    Args:
        text: Text to scan for PHI patterns

    Returns:
        List of detected pattern descriptions (empty if none found)
    """
    detected = []
    for pattern, description in PHI_PATTERNS:
        if re.search(pattern, text):
            detected.append(description)
    return detected


def assess_task_risk(description: str, files: List[str] = None) -> dict:
    """
    Simple risk assessment based on keyword matching.

    This is a basic heuristic for preliminary flagging. For authoritative
    decisions, use proper governance tools and human review.

    Args:
        description: Task description text
        files: Optional list of file paths involved

    Returns:
        Dict with risk indicators:
        {
            "phi_risk": bool,
            "auth_risk": bool,
            "billing_risk": bool,
            "infra_risk": bool,
            "state_expansion": bool,
            "phi_detected": List[str],  # Detected PHI pattern types
            "requires_review": bool
        }
    """
    result = {
        "phi_risk": check_keywords(description, PHI_KEYWORDS),
        "auth_risk": check_keywords(description, AUTH_KEYWORDS),
        "billing_risk": check_keywords(description, BILLING_KEYWORDS),
        "infra_risk": check_keywords(description, INFRASTRUCTURE_KEYWORDS),
        "state_expansion": check_keywords(description, STATE_EXPANSION_KEYWORDS),
        "phi_detected": detect_phi_patterns(description),
        "requires_review": False
    }

    # Check file paths if provided
    if files:
        for file_path in files:
            file_lower = file_path.lower()
            if "auth" in file_lower or "session" in file_lower:
                result["auth_risk"] = True
            if "billing" in file_lower or "payment" in file_lower:
                result["billing_risk"] = True

    # Set requires_review flag if any high-risk indicator
    result["requires_review"] = any([
        result["phi_risk"],
        result["auth_risk"],
        result["billing_risk"],
        result["infra_risk"],
        bool(result["phi_detected"])
    ])

    return result


# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    # Example 1: Check task description for risk indicators
    task_desc = "Update authentication timeout logic in session management"
    risk = assess_task_risk(task_desc)
    print(f"Risk assessment: {risk}")
    # Output: {'auth_risk': True, 'requires_review': True, ...}

    # Example 2: Detect PHI in text
    sample_text = "Patient SSN: 123-45-6789 needs update"
    phi = detect_phi_patterns(sample_text)
    print(f"PHI detected: {phi}")
    # Output: ['SSN']
