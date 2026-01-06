"""
Guardrail Pattern Detection

Scans code for forbidden patterns that bypass governance.

Patterns detected:
- TypeScript: @ts-ignore, @ts-nocheck, @ts-expect-error
- JavaScript: eslint-disable, eslint-disable-next-line
- Testing: .skip(, .only(, test.todo
- Python: # type: ignore, # noqa, @pytest.mark.skip

Implementation: Phase 0 Week 1 Day 5
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class GuardrailViolation:
    """A detected guardrail violation."""
    file_path: str
    line_number: int
    pattern: str
    line_content: str
    reason: str


# Forbidden patterns by language
PATTERNS = {
    "typescript": [
        {
            "pattern": r"@ts-ignore",
            "reason": "TypeScript suppressions bypass type safety"
        },
        {
            "pattern": r"@ts-nocheck",
            "reason": "TypeScript suppressions bypass type safety"
        },
        {
            "pattern": r"@ts-expect-error",
            "reason": "TypeScript suppressions bypass type safety"
        },
    ],
    "javascript": [
        {
            "pattern": r"eslint-disable",
            "reason": "ESLint suppressions bypass lint rules"
        },
        {
            "pattern": r"eslint-disable-next-line",
            "reason": "ESLint suppressions bypass lint rules"
        },
    ],
    "testing": [
        {
            "pattern": r"\.skip\s*\(",
            "reason": "Skipped tests indicate incomplete verification"
        },
        {
            "pattern": r"\.only\s*\(",
            "reason": "Focused tests exclude other tests from running"
        },
        {
            "pattern": r"test\.todo",
            "reason": "TODO tests indicate incomplete implementation"
        },
        {
            "pattern": r"it\.skip\s*\(",
            "reason": "Skipped tests indicate incomplete verification"
        },
        {
            "pattern": r"describe\.skip\s*\(",
            "reason": "Skipped test suites indicate incomplete verification"
        },
    ],
    "python": [
        {
            "pattern": r"#\s*type:\s*ignore",
            "reason": "Type ignore comments bypass type checking"
        },
        {
            "pattern": r"#\s*noqa",
            "reason": "Noqa comments bypass lint rules"
        },
        {
            "pattern": r"@pytest\.mark\.skip",
            "reason": "Skipped tests indicate incomplete verification"
        },
    ],
}


def parse_git_diff(project_path: Path, staged: bool = True) -> Dict[str, Set[int]]:
    """
    Parse git diff to extract line numbers that were added or modified.

    Args:
        project_path: Root path of project
        staged: If True, parse staged changes (--cached). If False, parse unstaged.

    Returns:
        Dict mapping file paths to sets of changed line numbers
        Example: {"tests/foo.test.ts": {10, 11, 25, 30}}
    """
    changed_lines = {}

    # Get git diff with line numbers
    cmd = ["git", "diff", "--unified=0"]
    if staged:
        cmd.append("--cached")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        # No git repo or no changes
        return changed_lines

    current_file = None

    for line in result.stdout.split('\n'):
        # Match file path: diff --git a/path/to/file b/path/to/file
        if line.startswith('diff --git'):
            parts = line.split(' b/')
            if len(parts) == 2:
                current_file = parts[1]
                changed_lines[current_file] = set()

        # Match hunk header: @@ -10,5 +12,7 @@
        # Format: @@ -old_start,old_count +new_start,new_count @@
        elif line.startswith('@@') and current_file:
            # Extract new line numbers (the +new_start,new_count part)
            match = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1

                # Add all line numbers in this hunk to the set
                for line_num in range(start, start + count):
                    changed_lines[current_file].add(line_num)

    return changed_lines


def scan_for_violations(
    project_path: Path,
    changed_files: List[str] = None,
    source_paths: List[str] = None,
    check_only_changed_lines: bool = True
) -> List[GuardrailViolation]:
    """
    Scan files for guardrail violations.

    Args:
        project_path: Root path of project
        changed_files: Specific files to scan (if None, scans all source files)
        source_paths: Source directories to scan (e.g., ["src", "tests"])
        check_only_changed_lines: If True, only scan lines modified in git diff (default)

    Returns:
        List of GuardrailViolation objects
    """
    violations = []

    # Get changed lines from git diff (NEW)
    changed_lines_map = {}
    if check_only_changed_lines:
        changed_lines_map = parse_git_diff(project_path, staged=True)
        if not changed_lines_map:
            # Fallback: try unstaged changes
            changed_lines_map = parse_git_diff(project_path, staged=False)

    # Determine which files to scan
    if changed_files:
        files_to_scan = [project_path / f for f in changed_files if _is_scannable(f)]
    elif source_paths:
        files_to_scan = []
        for src_path in source_paths:
            src_dir = project_path / src_path
            if src_dir.exists() and src_dir.is_dir():
                files_to_scan.extend(_get_files_recursive(src_dir))
    else:
        # Default: scan common source directories
        files_to_scan = []
        for common_dir in ["src", "lib", "tests", "test"]:
            common_path = project_path / common_dir
            if common_path.exists() and common_path.is_dir():
                files_to_scan.extend(_get_files_recursive(common_path))

    # Scan each file
    for file_path in files_to_scan:
        if not file_path.exists():
            continue

        # Determine language from extension
        language = _detect_language(file_path)
        if not language:
            continue

        # Get relative path for changed_lines lookup
        rel_path = str(file_path.relative_to(project_path))

        # Get changed lines for this file (NEW)
        changed_lines = changed_lines_map.get(rel_path, None)

        # Skip file if no changes and we're only checking changed lines (NEW)
        if check_only_changed_lines and changed_lines is not None and len(changed_lines) == 0:
            continue

        # Get patterns for this language
        patterns_to_check = []
        if language in PATTERNS:
            patterns_to_check.extend(PATTERNS[language])
        # Always check testing patterns for test files
        if _is_test_file(file_path):
            patterns_to_check.extend(PATTERNS["testing"])

        # Scan file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    # MODIFIED: Only scan if line was changed or we're scanning all lines
                    if check_only_changed_lines:
                        if changed_lines is not None and line_num not in changed_lines:
                            continue  # Skip this line - it wasn't changed

                    for pattern_def in patterns_to_check:
                        pattern = pattern_def["pattern"]
                        reason = pattern_def["reason"]

                        if re.search(pattern, line):
                            violations.append(GuardrailViolation(
                                file_path=rel_path,
                                line_number=line_num,
                                pattern=pattern,
                                line_content=line.strip(),
                                reason=reason
                            ))
        except Exception:
            # Skip files that can't be read (binary, permission issues, etc.)
            continue

    return violations


def _is_scannable(file_path: str) -> bool:
    """Check if file should be scanned."""
    # Skip non-code files
    skip_extensions = ['.json', '.md', '.txt', '.yml', '.yaml', '.lock', '.svg', '.png', '.jpg']
    return not any(file_path.endswith(ext) for ext in skip_extensions)


def _detect_language(file_path: Path) -> str:
    """Detect language from file extension."""
    ext = file_path.suffix.lower()

    if ext in ['.ts', '.tsx']:
        return 'typescript'
    elif ext in ['.js', '.jsx']:
        return 'javascript'
    elif ext in ['.py']:
        return 'python'

    return None


def _is_test_file(file_path: Path) -> bool:
    """Check if file is a test file."""
    path_str = str(file_path).lower()
    return (
        'test' in path_str or
        'spec' in path_str or
        path_str.endswith('.test.ts') or
        path_str.endswith('.test.js') or
        path_str.endswith('.spec.ts') or
        path_str.endswith('.spec.js')
    )


def _get_files_recursive(directory: Path) -> List[Path]:
    """Get all scannable files in directory recursively."""
    files = []
    try:
        for item in directory.rglob('*'):
            if item.is_file() and _is_scannable(str(item)):
                files.append(item)
    except Exception:
        pass
    return files
