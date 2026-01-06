"""
Risk Classification Module

Classifies files by risk level to determine verification timing.

Usage:
    from ralph.risk import classify_risk, RiskLevel

    level = classify_risk("src/auth/login.ts")
    # Returns RiskLevel.HIGH

    if level == RiskLevel.CRITICAL:
        block_and_require_approval()
    elif level == RiskLevel.HIGH:
        verify_immediately_after_write()
"""

import fnmatch
from enum import Enum
from pathlib import Path
from typing import Optional
import yaml


def glob_match(pattern: str, path: str) -> bool:
    """
    Match a path against a glob pattern, supporting ** for recursive matching.

    Args:
        pattern: Glob pattern (e.g., "**/migrations/**")
        path: File path to match

    Returns:
        True if path matches pattern
    """
    # Normalize separators
    pattern = pattern.replace("\\", "/")
    path = path.replace("\\", "/")

    # Handle ** patterns
    if "**" in pattern:
        # Split pattern into parts
        pattern_parts = pattern.split("/")
        path_parts = path.split("/")

        return _match_parts(pattern_parts, path_parts)
    else:
        # Simple fnmatch for non-** patterns
        return fnmatch.fnmatch(path, pattern)


def _match_parts(pattern_parts: list[str], path_parts: list[str]) -> bool:
    """Recursively match pattern parts against path parts."""
    if not pattern_parts:
        return not path_parts

    if not path_parts:
        # Allow trailing ** to match empty
        return all(p == "**" for p in pattern_parts)

    p = pattern_parts[0]

    if p == "**":
        # ** can match zero or more directories
        # Try matching rest of pattern at every position
        for i in range(len(path_parts) + 1):
            if _match_parts(pattern_parts[1:], path_parts[i:]):
                return True
        return False
    elif fnmatch.fnmatch(path_parts[0], p):
        return _match_parts(pattern_parts[1:], path_parts[1:])
    else:
        return False


class RiskLevel(Enum):
    """Risk levels for file modifications."""
    CRITICAL = "critical"  # PRE-WRITE blocking
    HIGH = "high"          # IMMEDIATE verification
    MEDIUM = "medium"      # AFTER-TASK verification
    LOW = "low"            # COMMIT-TIME only


class RiskAction(Enum):
    """Actions to take based on risk level."""
    BLOCK_AND_REQUIRE_APPROVAL = "block_and_require_approval"
    VERIFY_IMMEDIATE = "verify_immediate"
    VERIFY_AFTER_TASK = "verify_after_task"
    VERIFY_AT_COMMIT = "verify_at_commit"


# Cache for loaded policy
_policy_cache: Optional[dict] = None


def load_risk_policy() -> dict:
    """Load risk level policy from YAML."""
    global _policy_cache
    if _policy_cache is not None:
        return _policy_cache

    policy_path = Path(__file__).parent / "policy" / "risk_levels.yaml"
    if not policy_path.exists():
        # Return default policy if file doesn't exist
        _policy_cache = {"default": {"level": "medium"}}
        return _policy_cache

    with open(policy_path, 'r') as f:
        _policy_cache = yaml.safe_load(f)

    return _policy_cache


def classify_risk(file_path: str) -> RiskLevel:
    """
    Classify a file's risk level based on path patterns.

    Args:
        file_path: Relative path to file from project root

    Returns:
        RiskLevel enum value
    """
    policy = load_risk_policy()

    # Normalize path
    file_path = file_path.replace("\\", "/")

    # Check each risk level in order (critical first)
    for level_name in ["critical", "high", "medium", "low"]:
        level_config = policy.get(level_name, {})
        patterns = level_config.get("patterns", [])

        for pattern in patterns:
            if glob_match(pattern, file_path):
                return RiskLevel(level_name)

    # Default
    default_level = policy.get("default", {}).get("level", "medium")
    return RiskLevel(default_level)


def get_risk_action(level: RiskLevel) -> RiskAction:
    """Get the action to take for a risk level."""
    policy = load_risk_policy()
    level_config = policy.get(level.value, {})
    action_str = level_config.get("action", "verify_after_task")
    return RiskAction(action_str)


def classify_files(file_paths: list[str]) -> dict[RiskLevel, list[str]]:
    """
    Classify multiple files and group by risk level.

    Args:
        file_paths: List of file paths

    Returns:
        Dict mapping RiskLevel to list of files at that level
    """
    result = {level: [] for level in RiskLevel}

    for path in file_paths:
        level = classify_risk(path)
        result[level].append(path)

    return result


def get_highest_risk(file_paths: list[str]) -> RiskLevel:
    """
    Get the highest risk level among a set of files.

    Args:
        file_paths: List of file paths

    Returns:
        Highest RiskLevel (CRITICAL > HIGH > MEDIUM > LOW)
    """
    if not file_paths:
        return RiskLevel.LOW

    risk_order = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]

    for level in risk_order:
        for path in file_paths:
            if classify_risk(path) == level:
                return level

    return RiskLevel.LOW


def requires_precheck(file_path: str) -> bool:
    """Check if a file requires pre-write verification (CRITICAL level)."""
    return classify_risk(file_path) == RiskLevel.CRITICAL


def requires_immediate_verification(file_path: str) -> bool:
    """Check if a file requires immediate post-write verification."""
    level = classify_risk(file_path)
    return level in [RiskLevel.CRITICAL, RiskLevel.HIGH]


# Export commonly used functions
__all__ = [
    'RiskLevel',
    'RiskAction',
    'classify_risk',
    'classify_files',
    'get_risk_action',
    'get_highest_risk',
    'requires_precheck',
    'requires_immediate_verification',
]
