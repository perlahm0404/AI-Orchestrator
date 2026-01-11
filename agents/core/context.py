"""Agent context detection system.

This module provides context detection to help agents understand whether they
are operating in a CODE_REPO (execution mode) or KNOWLEDGE_VAULT (knowledge management mode).
"""
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional


class AgentContext(Enum):
    """Agent operating context."""
    CODE_REPO = "code_repo"
    KNOWLEDGE_VAULT = "knowledge_vault"
    UNKNOWN = "unknown"


def detect_context() -> AgentContext:
    """Detect agent context based on current working directory.

    Returns:
        AgentContext: The detected context (CODE_REPO, KNOWLEDGE_VAULT, or UNKNOWN)

    Examples:
        >>> # In /Users/tmac/1_REPOS/AI_Orchestrator/
        >>> detect_context()
        <AgentContext.CODE_REPO: 'code_repo'>

        >>> # In /Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/
        >>> detect_context()
        <AgentContext.KNOWLEDGE_VAULT: 'knowledge_vault'>
    """
    cwd = Path.cwd().resolve()
    cwd_str = str(cwd)

    if "/1_REPOS/" in cwd_str:
        return AgentContext.CODE_REPO
    elif "iCloud~md~obsidian/Documents/Knowledge_Vault" in cwd_str:
        return AgentContext.KNOWLEDGE_VAULT
    else:
        return AgentContext.UNKNOWN


def load_context_protocol(context: AgentContext) -> Dict[str, Any]:
    """Load appropriate protocol based on context.

    Args:
        context: The agent context

    Returns:
        Dict with protocol configuration including:
        - mode: Operating mode name
        - allowed_actions: List of permitted actions
        - forbidden_actions: List of forbidden actions
        - verify_with_ralph: Whether to run Ralph verification
        - enforce_contracts: Whether to enforce governance contracts

    Examples:
        >>> protocol = load_context_protocol(AgentContext.CODE_REPO)
        >>> protocol['mode']
        'execution'
        >>> protocol['verify_with_ralph']
        True

        >>> protocol = load_context_protocol(AgentContext.KNOWLEDGE_VAULT)
        >>> protocol['mode']
        'knowledge_management'
        >>> protocol['verify_with_ralph']
        False
    """
    if context == AgentContext.CODE_REPO:
        return {
            "mode": "execution",
            "allowed_actions": [
                "execute",
                "test",
                "commit",
                "deploy",
                "pr",
                "read_files",
                "write_files",
                "run_ralph",
                "run_tests",
            ],
            "forbidden_actions": [
                "create_vault_notes",
                "modify_vault",
            ],
            "verify_with_ralph": True,
            "enforce_contracts": True,
        }
    elif context == AgentContext.KNOWLEDGE_VAULT:
        return {
            "mode": "knowledge_management",
            "allowed_actions": [
                "read",
                "create_notes",
                "link",
                "summarize",
                "organize",
                "search",
                "tag",
            ],
            "forbidden_actions": [
                "execute_code",
                "run_tests",
                "git_commit",
                "deploy",
                "modify_code",
            ],
            "verify_with_ralph": False,
            "enforce_contracts": False,
        }
    else:
        return {
            "mode": "interactive",
            "allowed_actions": [
                "ask_user",
            ],
            "forbidden_actions": [],
            "verify_with_ralph": False,
            "enforce_contracts": False,
        }


def get_vault_path(context: AgentContext) -> Optional[str]:
    """Get the vault path for the current context.

    Args:
        context: The agent context

    Returns:
        Path to the vault section, or None if not in a code repo

    Examples:
        >>> # When in /Users/tmac/1_REPOS/AI_Orchestrator/
        >>> get_vault_path(AgentContext.CODE_REPO)
        '/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering/01-AI-Orchestrator/'
    """
    if context != AgentContext.CODE_REPO:
        return None

    cwd = Path.cwd().resolve()
    cwd_str = str(cwd)

    base_vault = "/Users/tmac/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Vault/AI-Engineering"

    if "AI_Orchestrator" in cwd_str:
        return f"{base_vault}/01-AI-Orchestrator/"
    elif "karematch" in cwd_str:
        return f"{base_vault}/02-KareMatch/"
    elif "credentialmate" in cwd_str:
        return f"{base_vault}/03-CredentialMate/"
    else:
        return None


def should_verify_with_ralph() -> bool:
    """Check if Ralph verification should be run in current context.

    Returns:
        True if in CODE_REPO context, False otherwise
    """
    context = detect_context()
    protocol = load_context_protocol(context)
    return bool(protocol["verify_with_ralph"])


def should_enforce_contracts() -> bool:
    """Check if governance contracts should be enforced in current context.

    Returns:
        True if in CODE_REPO context, False otherwise
    """
    context = detect_context()
    protocol = load_context_protocol(context)
    return bool(protocol["enforce_contracts"])


if __name__ == "__main__":
    """Command-line test of context detection."""
    context = detect_context()
    protocol = load_context_protocol(context)
    vault_path = get_vault_path(context)

    print(f"Current working directory: {Path.cwd()}")
    print(f"Detected context: {context.value}")
    print(f"Operating mode: {protocol['mode']}")
    print(f"Verify with Ralph: {protocol['verify_with_ralph']}")
    print(f"Enforce contracts: {protocol['enforce_contracts']}")

    if vault_path:
        print(f"Associated vault path: {vault_path}")

    print(f"\nAllowed actions:")
    for action in protocol['allowed_actions']:
        print(f"  ✓ {action}")

    print(f"\nForbidden actions:")
    for action in protocol['forbidden_actions']:
        print(f"  ✗ {action}")
