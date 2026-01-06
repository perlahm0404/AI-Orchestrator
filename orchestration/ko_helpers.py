"""
Knowledge Object Helper Functions

Utilities for extracting tags, learning insights, and formatting Knowledge Objects.

Used by IterationLoop to:
- Consult KOs before starting work (tag extraction)
- Create draft KOs after successful multi-iteration fixes (learning extraction)
- Display KOs to users (formatting)
"""

import re
from typing import List, Dict, Any


def extract_tags_from_task(task_description: str) -> List[str]:
    """
    Extract tags from task description using simple heuristics.

    Extraction strategy:
    1. Look for file extensions (e.g., ".ts" → "typescript")
    2. Look for common keywords (auth, test, api, db, etc.)
    3. Look for technology names (react, drizzle, vitest, etc.)
    4. Extract words from file paths

    Args:
        task_description: Task description text

    Returns:
        List of extracted tags (lowercase, sorted)

    Example:
        >>> extract_tags_from_task("Fix auth bug in login.ts")
        ['auth', 'login', 'typescript']

        >>> extract_tags_from_task("Fix bug in packages/api/src/auth.ts")
        ['api', 'auth', 'typescript']
    """
    if not task_description:
        return []

    tags = set()
    desc_lower = task_description.lower()

    # File extension mapping
    ext_map = {
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.py': 'python',
        '.sql': 'sql',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml'
    }

    for ext, tag in ext_map.items():
        if ext in desc_lower:
            tags.add(tag)

    # Common keywords (domain-specific)
    keywords = [
        'auth', 'authentication', 'login', 'password', 'jwt', 'token',
        'test', 'testing', 'spec', 'coverage',
        'api', 'endpoint', 'route', 'rest', 'graphql',
        'db', 'database', 'sql', 'query', 'migration',
        'type', 'typescript', 'interface', 'generic',
        'null', 'undefined', 'error', 'exception',
        'dependency', 'dependencies', 'package', 'npm', 'version',
        'drizzle', 'orm', 'vitest', 'playwright', 'jest',
        'monorepo', 'workspace', 'pnpm', 'yarn',
        'react', 'vue', 'svelte', 'next',
        'fastapi', 'django', 'flask',
        'validation', 'schema', 'zod',
        'middleware', 'hook', 'util', 'helper',
        'component', 'service', 'controller', 'model',
        'bug', 'fix', 'refactor', 'feature'
    ]

    for keyword in keywords:
        if re.search(r'\b' + keyword + r'\b', desc_lower):
            tags.add(keyword)

    # Extract words from file paths
    # e.g., "packages/api/src/auth.ts" → extract "packages", "api", "src", "auth"
    path_matches = re.findall(r'[\w-]+(?=/)', task_description)
    for word in path_matches:
        if len(word) > 2 and word.lower() not in ['src', 'lib', 'bin', 'dist', 'node_modules']:
            tags.add(word.lower())

    # Extract filename without extension
    # e.g., "auth.ts" → "auth", "login-form.tsx" → "login-form"
    filename_matches = re.findall(r'([\w-]+)\.\w+', task_description)
    for filename in filename_matches:
        if len(filename) > 2:
            # Handle kebab-case: "login-form" → ["login", "form"]
            parts = filename.lower().split('-')
            tags.update(p for p in parts if len(p) > 2)

    return sorted(list(tags))


def format_ko_for_display(ko: Any) -> str:
    """
    Format a Knowledge Object for console display.

    Shows a concise summary suitable for displaying multiple KOs in a list.

    Args:
        ko: KnowledgeObject instance to format

    Returns:
        Formatted string for display

    Example output:
        📖 KO-km-001: Drizzle ORM version mismatches cause type errors
           Tags: typescript, drizzle-orm, dependencies
           Learned: When multiple packages use different drizzle-orm versions...
           Prevention: Enforce single drizzle-orm version across monorepo...
    """
    # Truncate long strings
    learned_truncated = ko.what_was_learned[:100] + ('...' if len(ko.what_was_learned) > 100 else '')
    prevention_truncated = ko.prevention_rule[:100] + ('...' if len(ko.prevention_rule) > 100 else '')

    lines = []
    lines.append(f"📖 {ko.id}: {ko.title}")
    lines.append(f"   Tags: {', '.join(ko.tags)}")
    lines.append(f"   Learned: {learned_truncated}")
    lines.append(f"   Prevention: {prevention_truncated}")

    return '\n'.join(lines)


def extract_learning_from_iterations(
    task_description: str,
    iteration_history: List[Dict[str, Any]],
    verdict: Any,
    changes: List[str]
) -> Dict[str, Any]:
    """
    Extract learning from iteration history to populate KO fields.

    Analyzes the iteration progression to identify what was learned,
    why it matters, and how to prevent recurrence.

    Args:
        task_description: Original task description
        iteration_history: List of iteration records (each with iteration, verdict, changes)
        verdict: Final Ralph verdict (may be None)
        changes: List of changed files

    Returns:
        Dict with KO fields:
        - title: Short, memorable title (max 60 chars)
        - what_was_learned: Core lesson (1-3 sentences)
        - why_it_matters: Impact if ignored
        - prevention_rule: How to prevent recurrence
        - tags: List of tags
        - detection_pattern: Optional regex pattern (from test failures)
        - file_patterns: List of file patterns

    Example:
        >>> extract_learning_from_iterations(
        ...     "Fix auth bug",
        ...     [{"iteration": 1, "verdict": "FAIL"}, {"iteration": 2, "verdict": "PASS"}],
        ...     verdict,
        ...     ["src/auth.ts"]
        ... )
        {
            'title': 'Fix auth bug',
            'what_was_learned': 'After 2 iterations, resolved: Fix auth bug...',
            'why_it_matters': 'This pattern (self-correction) required...',
            'prevention_rule': 'When working on similar tasks (tags: auth)...',
            'tags': ['auth', 'bug', 'fix'],
            'detection_pattern': '',
            'file_patterns': ['src/*.ts']
        }
    """
    # Analyze iteration progression
    iterations = len(iteration_history)

    # Count failures (verdicts that are not PASS)
    fail_count = 0
    for iteration in iteration_history:
        verdict_value = iteration.get('verdict')
        if verdict_value:
            # Handle both string verdicts and Verdict objects
            if hasattr(verdict_value, 'type'):
                # Verdict object
                verdict_type = str(verdict_value.type).split('.')[-1]  # Extract enum value
                if verdict_type != 'PASS':
                    fail_count += 1
            elif isinstance(verdict_value, str):
                # String verdict
                if verdict_value != 'PASS':
                    fail_count += 1

    # Extract tags from task description
    tags = extract_tags_from_task(task_description)

    # Determine learning type based on iteration patterns
    if fail_count > 0:
        learning_type = "self-correction"
    else:
        learning_type = "iterative-refinement"

    # Generate title (truncate task description if too long)
    title = task_description[:60] + ('...' if len(task_description) > 60 else '')

    # Generate what_was_learned
    if fail_count > 0:
        what_was_learned = (
            f"After {iterations} iteration(s), resolved: {task_description}. "
            f"Required {fail_count} correction(s) to fix failures before passing verification."
        )
    else:
        what_was_learned = (
            f"After {iterations} iteration(s), resolved: {task_description}. "
            f"Multiple iterations were needed to complete this task successfully."
        )

    # Generate why_it_matters
    why_it_matters = (
        f"This {learning_type} pattern required {iterations} attempt(s), "
        f"indicating a non-obvious issue that may recur. "
        f"Understanding the resolution helps prevent similar problems."
    )

    # Generate prevention_rule
    if tags:
        top_tags = ', '.join(tags[:3])  # Show first 3 tags
        prevention_rule = (
            f"When working on similar tasks (tags: {top_tags}), "
            f"review this pattern to avoid the {fail_count} failure(s) encountered in this session. "
            f"Check for similar code patterns in the affected files."
        )
    else:
        prevention_rule = (
            f"Review the resolution approach when encountering similar issues. "
            f"This pattern required {iterations} iteration(s) to resolve correctly."
        )

    # Extract file patterns from changes
    file_patterns = []
    for change in changes:
        # Extract directory pattern (e.g., "src/auth/login.ts" → "src/auth/*.ts")
        parts = change.split('/')
        if len(parts) > 1:
            # Get directory path and add wildcard with extension
            dir_path = '/'.join(parts[:-1])
            filename = parts[-1]
            ext = '.' + filename.split('.')[-1] if '.' in filename else ''
            pattern = f"{dir_path}/*{ext}"
            if pattern not in file_patterns:
                file_patterns.append(pattern)
        else:
            # Single file, extract just the extension pattern
            ext = '.' + change.split('.')[-1] if '.' in change else ''
            if ext:
                pattern = f"*{ext}"
                if pattern not in file_patterns:
                    file_patterns.append(pattern)

    # Detection pattern (extract from test failures if available)
    detection_pattern = ""
    if verdict and hasattr(verdict, 'steps'):
        # Look for test step failures
        for step in verdict.steps:
            if hasattr(step, 'passed') and not step.passed and hasattr(step, 'output'):
                # Extract first few lines of error output
                output = step.output
                error_lines = output.split('\n')[:3]
                # Clean up lines (remove excessive whitespace)
                cleaned_lines = [line.strip() for line in error_lines if line.strip()]
                if cleaned_lines:
                    detection_pattern = ' '.join(cleaned_lines[:2])  # First 2 non-empty lines
                    break

    return {
        'title': title,
        'what_was_learned': what_was_learned,
        'why_it_matters': why_it_matters,
        'prevention_rule': prevention_rule,
        'tags': tags,
        'detection_pattern': detection_pattern,
        'file_patterns': file_patterns[:5]  # Limit to 5 patterns
    }
