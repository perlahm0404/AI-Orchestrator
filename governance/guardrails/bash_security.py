"""
Bash Command Security Guardrail

Validates bash commands against an allowlist before execution.

Usage:
    from governance.guardrails import bash_security

    result = bash_security.check(command="rm -rf /")
    if result.blocked:
        agent.halt(result.reason)

Implementation: Phase 0
"""

from dataclasses import dataclass


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    blocked: bool
    reason: str | None = None


# Commands that are always allowed
ALLOWED_COMMANDS = [
    "npm test",
    "npm run lint",
    "npm run typecheck",
    "npm run build",
    "pytest",
    "git status",
    "git diff",
    "git add",
    "git commit",
    "git checkout",
    "git branch",
    "ls",
    "cat",
    "head",
    "tail",
]

# Patterns that are always blocked
BLOCKED_PATTERNS = [
    "rm -rf",
    "rm -r /",
    "> /dev/",
    "chmod 777",
    "curl | bash",
    "wget | bash",
    "sudo",
    "su -",
    "DROP TABLE",
    "DELETE FROM",
    "TRUNCATE",
]


def check(command: str) -> GuardrailResult:
    """
    Check if a bash command is allowed.

    Args:
        command: The bash command to validate

    Returns:
        GuardrailResult with blocked=True if command should be blocked
    """
    # TODO: Implement in Phase 0
    raise NotImplementedError("Bash security guardrail not yet implemented")
