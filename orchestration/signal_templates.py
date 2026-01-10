"""
Completion Signal Templates for Wiggum Agents.

Provides standard promise strings and prompts for different task types.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class SignalTemplate:
    """Template for completion signals."""
    promise: str          # The promise string to match
    prompt_suffix: str    # Instructions to add to prompt
    description: str      # What this signal means


# CRITICAL: Guardrail rules that apply to ALL tasks
# These prevent agents from using suppression comments that trigger Ralph blocks
GUARDRAIL_RULES = """
CRITICAL RULES - DO NOT VIOLATE:
1. NEVER add `# noqa` comments to suppress lint errors - FIX the actual issue
2. NEVER add `# type: ignore` comments - FIX the type error properly
3. NEVER add `@pytest.mark.skip` to skip tests - FIX the failing test
4. NEVER add `// @ts-ignore` or `// @ts-nocheck` - FIX the TypeScript error
5. NEVER add `eslint-disable` comments - FIX the lint issue

For E402 errors (module import not at top of file):
- MOVE the import to the top of the file
- If sys.path modification is needed, create a separate config module
- Or refactor to use lazy imports inside functions

For F401 errors (unused imports):
- REMOVE the unused import entirely

For F541 errors (f-string missing placeholders):
- Either add placeholders {var} or convert to regular string

These suppression patterns will cause the build to be BLOCKED.
"""


# Standard templates by task type
TEMPLATES = {
    "bugfix": SignalTemplate(
        promise="BUGFIX_COMPLETE",
        prompt_suffix="""
When the bug is fixed and all tests pass, output:
<promise>BUGFIX_COMPLETE</promise>
""",
        description="Bug is fixed, tests passing, no regressions"
    ),

    "codequality": SignalTemplate(
        promise="CODEQUALITY_COMPLETE",
        prompt_suffix="""
When code quality improvements are complete and linting/type checks pass, output:
<promise>CODEQUALITY_COMPLETE</promise>
""",
        description="Code quality improved, lint/type checks passing"
    ),

    "feature": SignalTemplate(
        promise="FEATURE_COMPLETE",
        prompt_suffix="""
When the feature is fully implemented with tests and documentation, output:
<promise>FEATURE_COMPLETE</promise>
""",
        description="Feature implemented, tested, documented"
    ),

    "test": SignalTemplate(
        promise="TESTS_COMPLETE",
        prompt_suffix="""
When all tests are written and passing, output:
<promise>TESTS_COMPLETE</promise>
""",
        description="Tests written and passing"
    ),

    "refactor": SignalTemplate(
        promise="REFACTOR_COMPLETE",
        prompt_suffix="""
When refactoring is complete and all tests still pass, output:
<promise>REFACTOR_COMPLETE</promise>
""",
        description="Refactoring complete, tests still passing"
    ),
}


def get_template(task_type: str) -> Optional[SignalTemplate]:
    """
    Get completion signal template for task type.

    Args:
        task_type: Task type (bugfix, codequality, feature, test, refactor)

    Returns:
        SignalTemplate or None if not found
    """
    return TEMPLATES.get(task_type.lower())


def build_prompt_with_signal(base_prompt: str, task_type: str) -> str:
    """
    Add completion signal instructions and guardrail rules to prompt.

    Args:
        base_prompt: Base task prompt
        task_type: Task type for template lookup

    Returns:
        Enhanced prompt with guardrail rules and signal instructions
    """
    template = get_template(task_type)

    # Always include guardrail rules to prevent suppression comments
    prompt_parts = [base_prompt, GUARDRAIL_RULES]

    if template is not None:
        prompt_parts.append(template.prompt_suffix)

    return "\n\n".join(prompt_parts)


def infer_task_type(task_description: str) -> str:
    """
    Infer task type from description.

    Args:
        task_description: Task description string

    Returns:
        Inferred task type (defaults to "bugfix")
    """
    desc_lower = task_description.lower()

    # Check in priority order (more specific checks first)
    if any(word in desc_lower for word in ["test", "spec", "coverage"]):
        return "test"
    elif any(word in desc_lower for word in ["refactor", "restructure", "reorganize"]):
        return "refactor"
    elif any(word in desc_lower for word in ["quality", "lint", "clean", "improve"]):
        return "codequality"
    elif any(word in desc_lower for word in ["feature", "add", "implement", "build", "create"]):
        return "feature"
    elif any(word in desc_lower for word in ["bug", "fix", "error", "issue", "failing"]):
        return "bugfix"
    else:
        return "bugfix"  # Default
