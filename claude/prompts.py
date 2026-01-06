"""
Prompt templates for different task types

Generates context-rich prompts for Claude Code CLI based on:
- Task type (bug fix, quality improvement, feature)
- Available context (tests, documentation, related files)
- Project conventions
"""

from typing import Optional, List
from pathlib import Path


def generate_bugfix_prompt(
    bug_description: str,
    file_path: str,
    test_files: Optional[List[str]] = None,
    context: Optional[str] = None
) -> str:
    """
    Generate prompt for bug fix tasks

    Args:
        bug_description: Description of the bug to fix
        file_path: Path to file containing the bug
        test_files: Optional list of related test files
        context: Optional additional context

    Returns:
        Context-aware prompt for bug fixing
    """
    prompt = f"""Fix this bug: {bug_description}

**File to fix**: {file_path}

**Test files**: {', '.join(test_files) if test_files else 'None'}

**Requirements**:
1. Read the file and understand the current implementation
2. Fix the bug described above
3. Ensure all existing tests still pass
4. Do NOT add new features or refactor unrelated code
5. Keep changes minimal and focused

"""

    if context:
        prompt += f"**Additional Context**:\n{context}\n\n"

    prompt += """**Verification**:
- Run tests after fixing
- Verify lint and typecheck pass
- Ensure behavior is preserved

**IMPORTANT - Completion Signal**:
When the bug is fully fixed and all tests pass, output exactly:
<promise>BUGFIX_COMPLETE</promise>

This signals task completion to the iteration loop.

Begin by reading the file, then make your fix."""

    return prompt


def generate_quality_prompt(
    issue_description: str,
    file_path: str,
    issue_type: str = "general"
) -> str:
    """
    Generate prompt for code quality tasks

    Args:
        issue_description: Description of the quality issue
        file_path: Path to file with quality issue
        issue_type: Type of quality issue (console_error, unused_import, type_annotation, etc.)

    Returns:
        Context-aware prompt for quality improvement
    """
    prompts = {
        "console_error": f"""Remove console.error from {file_path}

**Task**: {issue_description}

**Requirements**:
1. Find all console.error statements
2. Replace with proper error logging
3. Use project's logging utility if available
4. Preserve error information
5. Don't change other logging (console.log, etc.)

**Completion Signal**:
When complete and all tests pass, output exactly:
<promise>CODEQUALITY_COMPLETE</promise>

Make the change and verify tests still pass.""",

        "unused_import": f"""Remove unused import from {file_path}

**Task**: {issue_description}

**Requirements**:
1. Identify the unused import
2. Remove it cleanly
3. Verify no other code uses it
4. Run linter to confirm

**Completion Signal**:
When complete and linter passes, output exactly:
<promise>CODEQUALITY_COMPLETE</promise>

Make the change.""",

        "type_annotation": f"""Fix type annotation in {file_path}

**Task**: {issue_description}

**Requirements**:
1. Add or fix the type annotation
2. Use proper TypeScript types
3. Avoid 'any' unless necessary
4. Run typecheck to verify

**Completion Signal**:
When complete and typecheck passes, output exactly:
<promise>CODEQUALITY_COMPLETE</promise>

Make the change.""",

        "lint": f"""Fix linting issues in {file_path}

**Task**: {issue_description}

**Requirements**:
1. Read the file and identify linting issues
2. Fix them according to project's linting rules
3. Run linter to verify all issues resolved
4. Don't change functionality

**Completion Signal**:
When complete and linter passes, output exactly:
<promise>CODEQUALITY_COMPLETE</promise>

Make the changes.""",

        "test_failure": f"""Fix failing test in {file_path}

**Task**: {issue_description}

**Requirements**:
1. Read the test file and understand what's being tested
2. Identify why the test is failing
3. Fix either the test or the implementation (whichever is wrong)
4. Ensure test passes
5. Don't break other tests

**Completion Signal**:
When complete and all tests pass, output exactly:
<promise>TESTS_COMPLETE</promise>

Fix the test."""
    }

    return prompts.get(issue_type, f"""Fix code quality issue in {file_path}

**Task**: {issue_description}

**Requirements**:
1. Understand the issue
2. Fix it cleanly
3. Verify tests and checks pass

**Completion Signal**:
When complete and all checks pass, output exactly:
<promise>CODEQUALITY_COMPLETE</promise>

Make the change.""")


def generate_feature_prompt(
    feature_description: str,
    files: List[str],
    acceptance_criteria: Optional[List[str]] = None,
    context: Optional[str] = None
) -> str:
    """
    Generate prompt for feature implementation

    Args:
        feature_description: Description of feature to implement
        files: List of files involved in feature
        acceptance_criteria: Optional list of acceptance criteria
        context: Optional additional context

    Returns:
        Context-aware prompt for feature development
    """
    prompt = f"""Implement this feature: {feature_description}

**Files involved**: {', '.join(files) if files else 'Not specified'}

"""

    if acceptance_criteria:
        prompt += "**Acceptance Criteria**:\n"
        for i, criteria in enumerate(acceptance_criteria, 1):
            prompt += f"{i}. {criteria}\n"
        prompt += "\n"

    if context:
        prompt += f"**Additional Context**:\n{context}\n\n"

    prompt += """**Requirements**:
1. Read existing code to understand patterns
2. Implement the feature following project conventions
3. Write tests for new functionality
4. Ensure all tests pass
5. Update any relevant documentation

**IMPORTANT - Completion Signal**:
When the feature is fully implemented and all tests pass, output exactly:
<promise>FEATURE_COMPLETE</promise>

This signals task completion to the iteration loop.

Begin by reading the related files, then implement the feature."""

    return prompt


def detect_task_type(task_id: str) -> str:
    """
    Detect task type from task ID prefix

    Args:
        task_id: Task identifier (e.g., BUG-001, QUALITY-002, FEATURE-003)

    Returns:
        Task type: 'bug', 'quality', 'feature', or 'unknown'
    """
    task_id_upper = task_id.upper()

    if task_id_upper.startswith("BUG-"):
        return "bug"
    elif task_id_upper.startswith("QUALITY-"):
        return "quality"
    elif task_id_upper.startswith("FEATURE-"):
        return "feature"
    elif task_id_upper.startswith("TEST-"):
        return "test"
    else:
        return "unknown"


def detect_quality_issue_type(description: str) -> str:
    """
    Detect quality issue type from description

    Args:
        description: Task description

    Returns:
        Issue type: 'console_error', 'unused_import', 'type_annotation', 'lint', 'test_failure', or 'general'
    """
    desc_lower = description.lower()

    if "console.error" in desc_lower or "remove console" in desc_lower:
        return "console_error"
    elif "unused import" in desc_lower or "remove import" in desc_lower:
        return "unused_import"
    elif "type annotation" in desc_lower or "type error" in desc_lower or "typescript" in desc_lower:
        return "type_annotation"
    elif "lint" in desc_lower or "linting" in desc_lower:
        return "lint"
    elif "test fail" in desc_lower or "failing test" in desc_lower:
        return "test_failure"
    else:
        return "general"


def generate_smart_prompt(
    task_id: str,
    description: str,
    file_path: str,
    test_files: Optional[List[str]] = None,
    context: Optional[str] = None
) -> str:
    """
    Generate smart prompt based on task type

    Args:
        task_id: Task identifier
        description: Task description
        file_path: Path to primary file
        test_files: Optional list of test files
        context: Optional additional context

    Returns:
        Context-aware prompt tailored to task type
    """
    task_type = detect_task_type(task_id)

    if task_type == "bug":
        return generate_bugfix_prompt(
            bug_description=description,
            file_path=file_path,
            test_files=test_files,
            context=context
        )
    elif task_type == "quality" or task_type == "test":
        issue_type = detect_quality_issue_type(description)
        return generate_quality_prompt(
            issue_description=description,
            file_path=file_path,
            issue_type=issue_type
        )
    elif task_type == "feature":
        return generate_feature_prompt(
            feature_description=description,
            files=[file_path] if file_path else [],
            context=context
        )
    else:
        # Fallback to simple prompt - detect appropriate completion signal
        completion_signal = "COMPLETE"
        if "bug" in task_id.lower() or "fix" in task_id.lower():
            completion_signal = "BUGFIX_COMPLETE"
        elif "test" in task_id.lower():
            completion_signal = "TESTS_COMPLETE"
        elif "feature" in task_id.lower() or "feat" in task_id.lower():
            completion_signal = "FEATURE_COMPLETE"

        return f"""{description}

**File**: {file_path}

**Requirements**:
Please make the necessary changes and ensure all tests pass.

**IMPORTANT - Completion Signal**:
When the task is fully complete and all tests pass, output exactly:
<promise>{completion_signal}</promise>

This signals task completion to the iteration loop."""
