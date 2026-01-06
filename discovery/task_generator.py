"""Task generator converts discovered bugs into work queue tasks.

Strategy: Group bugs by file (all errors in same file = 1 task)
Priority: Impact-based (P0=blocks users, P1=degrades UX, P2=tech debt)
"""

from collections import defaultdict
from pathlib import Path
from typing import Optional

from tasks.work_queue import Task
from .scanner import ScanResult


class TaskGenerator:
    """Generates work queue tasks from scan results."""

    def __init__(self, project_name: str):
        """
        Initialize task generator.

        Args:
            project_name: Project name (e.g., 'karematch')
        """
        self.project_name = project_name
        self.task_counter = 0

    def generate_tasks(
        self,
        scan_result: ScanResult,
        new_bugs: list[dict],
        baseline_bugs: list[dict]
    ) -> list[Task]:
        """
        Generate work queue tasks from scan results.

        Strategy: Group by file (all errors in same file = 1 task)
        Priority: New bugs = higher priority, baseline bugs = lower

        Args:
            scan_result: Full scan result
            new_bugs: Bugs not in baseline (regressions)
            baseline_bugs: Bugs in baseline (known issues)

        Returns:
            List of Task objects sorted by priority
        """
        # Group all bugs by file
        bugs_by_file = defaultdict(list)

        for bug in new_bugs:
            bugs_by_file[bug['file']].append({**bug, 'is_new': True})

        for bug in baseline_bugs:
            bugs_by_file[bug['file']].append({**bug, 'is_new': False})

        # Create one task per file
        tasks = []
        for file_path, bugs in bugs_by_file.items():
            task = self._create_task_for_file(file_path, bugs)
            if task:
                tasks.append(task)

        # Sort by priority (P0 first, then P1, then P2)
        tasks.sort(key=lambda t: (t.priority or 99, t.id))

        return tasks

    def _create_task_for_file(self, file_path: str, bugs: list[dict]) -> Optional[Task]:
        """
        Create task for all bugs in a single file.

        Args:
            file_path: Target file path
            bugs: List of bug dicts for this file

        Returns:
            Task object, or None if task cannot be created
        """
        if not bugs:
            return None

        # Determine task type and ID prefix based on error types
        error_types = set(bug['type'] for bug in bugs)

        if 'test' in error_types:
            task_prefix = 'TEST'
            completion_promise = 'TESTS_COMPLETE'
            max_iterations = 15
        elif 'typecheck' in error_types:
            task_prefix = 'TYPE'
            completion_promise = 'CODEQUALITY_COMPLETE'
            max_iterations = 20
        elif 'lint' in error_types:
            task_prefix = 'LINT'
            completion_promise = 'CODEQUALITY_COMPLETE'
            max_iterations = 20
        else:  # guardrails
            task_prefix = 'GUARD'
            completion_promise = 'CODEQUALITY_COMPLETE'
            max_iterations = 20

        # Determine priority based on impact
        priority = self._compute_priority(file_path, bugs)

        # Generate task ID
        file_name = Path(file_path).stem
        # Sanitize file name (remove special chars, limit length)
        file_name_clean = ''.join(c for c in file_name if c.isalnum() or c == '_')[:10]
        task_id = f"{task_prefix}-{file_name_clean.upper()}-{self.task_counter:03d}"
        self.task_counter += 1

        # Generate description
        description = self._generate_description(file_path, bugs)

        # Infer related test files
        test_files = self._infer_test_files(file_path)

        return Task(
            id=task_id,
            description=description,
            file=file_path,
            status='pending',
            tests=test_files,
            passes=False,
            error=None,
            attempts=0,
            last_attempt=None,
            completed_at=None,
            completion_promise=completion_promise,
            max_iterations=max_iterations,
            verification_verdict=None,
            files_actually_changed=None,
            priority=priority,
            bug_count=len(bugs),
            is_new=any(bug['is_new'] for bug in bugs)
        )

    def _compute_priority(self, file_path: str, bugs: list[dict]) -> int:
        """
        Compute priority (P0/P1/P2) based on user impact.

        P0 (blocks users):
        - Auth/payment/security failures
        - Test failures in critical paths
        - Security issues

        P1 (degrades UX):
        - Type errors in user-facing code
        - Test failures in features
        - New regressions
        - Unused imports in active code

        P2 (tech debt):
        - Linting issues (baseline)
        - Guardrail violations
        - Style/formatting

        Args:
            file_path: File path
            bugs: List of bugs in this file

        Returns:
            Priority (0=P0, 1=P1, 2=P2)
        """
        # Check if any bug is marked as new (regressions are higher priority)
        has_new_bugs = any(bug['is_new'] for bug in bugs)

        # Check file path for critical areas
        file_path_lower = file_path.lower()
        critical_paths = ['auth/', 'login', 'session', 'payment/', 'checkout', 'security/', 'api/']
        is_critical = any(path in file_path_lower for path in critical_paths)

        # Check error types
        has_test_failures = any(bug['type'] == 'test' for bug in bugs)
        has_type_errors = any(bug['type'] == 'typecheck' for bug in bugs)
        has_lint_errors = any(bug['type'] == 'lint' for bug in bugs)
        has_guardrails = any(bug['type'] == 'guardrail' for bug in bugs)

        # Check for security issues
        has_security = any(
            'security' in bug.get('rule', '').lower() or
            'eval' in bug.get('rule', '').lower() or
            'danger' in bug.get('rule', '').lower()
            for bug in bugs
        )

        # Priority logic (higher priority = lower number)

        # P0: Critical issues that block users
        if has_security:
            return 0  # Security issues always P0

        if has_test_failures and is_critical:
            return 0  # Test failures in critical paths (auth, payment, etc.)

        # P1: Issues that degrade UX or are new regressions
        if has_new_bugs:
            return 1  # Any new regression is P1

        if has_type_errors:
            return 1  # Type errors are P1 (could cause runtime issues)

        if has_test_failures:
            return 1  # Non-critical test failures are P1

        # P2: Tech debt (baseline lint/guardrail issues)
        if has_lint_errors or has_guardrails:
            return 2  # Baseline lint/guardrail issues are P2

        # Default to P1 if we can't classify
        return 1

    def _generate_description(self, file_path: str, bugs: list[dict]) -> str:
        """
        Generate human-readable task description.

        Args:
            file_path: File path
            bugs: List of bugs

        Returns:
            Description string

        Example: "Fix 3 lint error(s), 2 typecheck error(s) in src/auth/login.ts (NEW REGRESSION)"
        """
        # Count errors by type
        error_counts = defaultdict(int)
        for bug in bugs:
            error_counts[bug['type']] += 1

        # Build description parts
        parts = []
        for error_type, count in sorted(error_counts.items()):
            parts.append(f"{count} {error_type} error(s)")

        # Add status indicator
        status = "NEW REGRESSION" if any(bug['is_new'] for bug in bugs) else "baseline"

        return f"Fix {', '.join(parts)} in {file_path} ({status})"

    def _infer_test_files(self, file_path: str) -> list[str]:
        """
        Infer related test files from source file path.

        Args:
            file_path: Source file path

        Returns:
            List of test file paths (may be empty)

        Examples:
            services/auth/src/login.ts → services/auth/tests/login.test.ts
            packages/utils/index.ts → packages/utils/__tests__/index.test.ts
        """
        # If file is already a test file, return it
        if '.test.' in file_path or '__tests__' in file_path:
            return [file_path]

        test_candidates = []

        # Convert: services/auth/src/login.ts → services/auth/tests/login.test.ts
        if '/src/' in file_path:
            test_path = file_path.replace('/src/', '/tests/')
            test_path = test_path.replace('.ts', '.test.ts').replace('.tsx', '.test.tsx')
            test_candidates.append(test_path)

        # Convert: packages/utils/index.ts → packages/utils/__tests__/index.test.ts
        file_dir = Path(file_path).parent
        file_name = Path(file_path).stem
        file_ext = Path(file_path).suffix

        test_ext = '.test.ts' if file_ext == '.ts' else '.test.tsx'

        test_candidates.extend([
            str(file_dir / '__tests__' / f'{file_name}{test_ext}'),
            str(file_dir / f'{file_name}{test_ext}'),
            str(file_dir / 'tests' / f'{file_name}{test_ext}'),
        ])

        # Only return paths that might exist (we'll validate later)
        # For now, just return the first candidate as a placeholder
        return [test_candidates[0]] if test_candidates else []
