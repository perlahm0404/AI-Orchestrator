"""
Agent Factory - Create agents with proper configuration for Wiggum integration

This factory creates agent instances with AgentConfig that includes:
- Project name
- Agent type
- Expected completion signal (promise tag)
- Max iterations (iteration budget)

Usage:
    from agents.factory import create_agent

    agent = create_agent(
        task_type="bugfix",
        project_name="karematch",
        completion_promise="BUGFIX_COMPLETE",  # Optional override
        max_iterations=15                        # Optional override
    )
"""

import os
from typing import Optional, Any

from agents.base import AgentConfig


# Feature flag for SDK usage (environment variable override)
def _get_use_sdk_default() -> bool:
    """
    Get default use_sdk value from environment variable.

    Set AI_ORCHESTRATOR_USE_SDK=false to disable SDK and use CLI wrapper.
    This is useful for quick rollback if SDK issues are encountered.

    Returns:
        True (use SDK) unless AI_ORCHESTRATOR_USE_SDK=false
    """
    env_value = os.environ.get("AI_ORCHESTRATOR_USE_SDK", "true")
    return env_value.strip().lower() not in ("false", "0", "no")


from agents.bugfix import BugFixAgent
from agents.codequality import CodeQualityAgent
from agents.featurebuilder import FeatureBuilderAgent
from agents.testwriter import TestWriterAgent
from agents.admin.adr_creator import ADRCreatorAgent
from agents.coordinator.product_manager import ProductManagerAgent
from agents.coordinator.cmo_agent import CMOAgent
from agents.editorial import EditorialAgent
from adapters import get_adapter


# Default completion promises by agent type
# These are the exact strings agents should output in <promise> tags
COMPLETION_PROMISES = {
    "bugfix": "BUGFIX_COMPLETE",
    "codequality": "CODEQUALITY_COMPLETE",
    "feature": "FEATURE_COMPLETE",
    "test": "TESTS_COMPLETE",
    "admin": "ADR_CREATE_COMPLETE",
    "editorial": "EDITORIAL_COMPLETE",

    # Meta-agents (v6.0)
    "product_management": "PM_REVIEW_COMPLETE",
    "cmo": "CMO_REVIEW_COMPLETE",
}

# Default iteration budgets by agent type
# Based on complexity and expected retry needs
ITERATION_BUDGETS = {
    "bugfix": 15,        # Bugs should be fixable with reasonable attempts
    "codequality": 20,   # Quality improvements may need refinement
    "feature": 50,       # Features are complex, need exploration
    "test": 15,         # Tests are straightforward
    "admin": 3,         # Admin tasks are straightforward
    "editorial": 20,    # Content creation needs research + iteration

    # Meta-agents (v6.0)
    "product_management": 5,   # PM validation is quick
    "cmo": 5,                  # CMO review is quick
}


def create_agent(
    task_type: str,
    project_name: str,
    completion_promise: Optional[str] = None,
    max_iterations: Optional[int] = None,
    use_sdk: Optional[bool] = None,
) -> Any:
    """
    Create agent instance with proper Wiggum configuration.

    Args:
        task_type: Agent type (bugfix, codequality, feature, test)
        project_name: Project name (karematch, credentialmate)
        completion_promise: Override default completion promise
        max_iterations: Override default iteration budget
        use_sdk: Use Claude Agent SDK (True) or CLI wrapper (False).
                 If None, uses AI_ORCHESTRATOR_USE_SDK env var (default: True).

    Returns:
        Configured agent instance (BugFixAgent, CodeQualityAgent, etc.)

    Raises:
        ValueError: If unknown agent type or project

    Example:
        # Create bugfix agent with SDK (default)
        agent = create_agent("bugfix", "karematch")

        # Create bugfix agent with CLI wrapper (fallback)
        agent = create_agent("bugfix", "karematch", use_sdk=False)

        # Create bugfix agent with custom settings
        agent = create_agent(
            "bugfix",
            "karematch",
            completion_promise="BUG_FIXED",
            max_iterations=10,
            use_sdk=True
        )
    """
    # Load adapter for project
    adapter = get_adapter(project_name)

    # Determine SDK usage (explicit override > environment variable > default True)
    effective_use_sdk = use_sdk if use_sdk is not None else _get_use_sdk_default()

    # Create agent config
    config = AgentConfig(
        project_name=project_name,
        agent_name=task_type,
        expected_completion_signal=completion_promise or COMPLETION_PROMISES.get(task_type, "COMPLETE"),
        max_iterations=max_iterations or ITERATION_BUDGETS.get(task_type, 10),
        use_sdk=effective_use_sdk,
    )

    # Create appropriate agent type
    if task_type == "bugfix":
        return BugFixAgent(adapter, config)
    elif task_type == "codequality":
        return CodeQualityAgent(adapter, config)
    elif task_type == "feature":
        return FeatureBuilderAgent(adapter, config)
    elif task_type == "test":
        return TestWriterAgent(adapter, config)
    elif task_type == "admin":
        return ADRCreatorAgent(adapter, config)
    elif task_type == "editorial":
        return EditorialAgent(adapter, config)
    # Meta-agents (v6.0)
    elif task_type == "product_management":
        return ProductManagerAgent(adapter, config)
    elif task_type == "cmo":
        return CMOAgent(adapter, config)
    else:
        raise ValueError(
            f"Unknown agent type: {task_type}. "
            f"Valid types: {', '.join(COMPLETION_PROMISES.keys())}"
        )


def infer_agent_type(task_id: str) -> str:
    """
    Infer agent type from task ID prefix.

    Task ID format: {TYPE}-{COMPONENT}-{NUMBER}
    Examples:
        BUG-APT-001 → bugfix
        QUALITY-CODE-002 → codequality
        FEATURE-AUTH-003 → feature
        TEST-API-004 → test

    Args:
        task_id: Task identifier

    Returns:
        Agent type string (bugfix, codequality, feature, test)

    Raises:
        ValueError: If task ID format is invalid
    """
    parts = task_id.split('-')
    if not parts:
        raise ValueError(f"Invalid task ID format: {task_id}")

    prefix = parts[0].upper()

    # Map task ID prefix to agent type
    type_map = {
        "BUG": "bugfix",
        "BUGFIX": "bugfix",
        "FIX": "bugfix",
        "QUALITY": "codequality",
        "CODE": "codequality",
        "REFACTOR": "codequality",
        "FEATURE": "feature",
        "FEAT": "feature",
        "PROVIDER": "feature",  # Provider onboarding tasks
        "TEST": "test",
        "TESTS": "test",
        "ADMIN": "admin",
        "ADR": "admin",
        "EDITORIAL": "editorial",
        "CONTENT": "editorial",
        "BLOG": "editorial",
    }

    agent_type = type_map.get(prefix)
    if not agent_type:
        # Default to bugfix if unknown
        return "bugfix"

    return agent_type
