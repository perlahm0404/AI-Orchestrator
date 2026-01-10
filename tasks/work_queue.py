"""
Work Queue System - Simple JSON-based task queue

Replaces complex orchestration with Anthropic's proven pattern:
- Tasks stored in work_queue.json
- Simple get_next() interface
- Status tracking: pending, in_progress, complete, blocked

v5.7: Added autonomous task registration (ADR-003)
- register_discovered_task() for programmatic task creation
- SHA256 fingerprint deduplication
- Timestamped task IDs: {YYYYMMDD}-{HHMM}-{TYPE}-{SOURCE}-{SEQ}
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone


TaskStatus = Literal["pending", "in_progress", "complete", "blocked"]


@dataclass
class Task:
    """Individual task in the work queue"""
    id: str
    description: str
    file: str
    status: TaskStatus
    tests: list[str]
    passes: bool
    error: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[str] = None
    completed_at: Optional[str] = None
    # Wiggum integration fields
    completion_promise: Optional[str] = None  # Expected completion signal (e.g., "BUGFIX_COMPLETE")
    max_iterations: Optional[int] = None      # Override default iteration budget per task
    # Verification audit trail
    verification_verdict: Optional[str] = None  # "PASS", "FAIL", "BLOCKED", or None
    files_actually_changed: Optional[list[str]] = None  # What files were actually modified
    # Bug discovery fields
    priority: Optional[int] = None       # 0=P0 (blocks users), 1=P1 (degrades UX), 2=P2 (tech debt)
    bug_count: Optional[int] = None      # How many bugs in this file
    is_new: Optional[bool] = None        # True if any bugs are new regressions (not in baseline)
    # Dev Team / Feature development fields (v5.4)
    type: str = "bugfix"                 # "bugfix" | "feature" | "test"
    branch: Optional[str] = None         # Branch name (e.g., "feature/matching-algorithm")
    agent: Optional[str] = None          # Agent type: "BugFix" | "FeatureBuilder" | "TestWriter"
    requires_approval: Optional[list[str]] = None  # Items requiring human approval (e.g., ["new_api_endpoint"])
    # Autonomous task registration fields (v5.7 / ADR-003)
    source: Optional[str] = None         # Where task came from: "ADR-002", "manual", "advisor", "RETRY-ESCALATION"
    discovered_by: Optional[str] = None  # Who discovered: "app-advisor", "cli", "cost-guardian"
    fingerprint: Optional[str] = None    # SHA256 fingerprint for deduplication


@dataclass
class WorkQueue:
    """Work queue containing tasks for a project"""
    project: str
    features: list[Task]
    # ADR-003: Autonomous task registration
    sequence: int = field(default=0)          # Task sequence counter for ID generation
    fingerprints: set[str] = field(default_factory=set)  # SHA256 fingerprints for deduplication

    @classmethod
    def load(cls, path: Path) -> "WorkQueue":
        """Load work queue from JSON file"""
        if not path.exists():
            raise FileNotFoundError(f"Work queue not found: {path}")

        data = json.loads(path.read_text())
        features = [Task(**f) for f in data["features"]]

        # Load ADR-003 fields (backwards compatible)
        sequence = data.get("sequence", len(features))  # Default to current task count
        fingerprints = set(data.get("fingerprints", []))

        # Rebuild fingerprints from existing tasks if not stored
        if not fingerprints:
            for task in features:
                if task.fingerprint:
                    fingerprints.add(task.fingerprint)

        queue = cls(
            project=data["project"],
            features=features,
            sequence=sequence,
            fingerprints=fingerprints,
        )
        return queue

    def save(self, path: Path) -> None:
        """Save work queue to JSON file"""
        data = {
            "project": self.project,
            "sequence": self.sequence,
            "fingerprints": list(self.fingerprints),  # Convert set to list for JSON
            "features": [asdict(task) for task in self.features]
        }
        path.write_text(json.dumps(data, indent=2))

    def get_next_pending(self) -> Optional[Task]:
        """Get next pending task"""
        for task in self.features:
            if task.status == "pending":
                return task
        return None

    def get_in_progress(self) -> Optional[Task]:
        """Get currently in-progress task"""
        for task in self.features:
            if task.status == "in_progress":
                return task
        return None

    def mark_in_progress(self, task_id: str) -> None:
        """Mark task as in progress"""
        for task in self.features:
            if task.id == task_id:
                task.status = "in_progress"
                task.attempts += 1
                task.last_attempt = datetime.now().isoformat()
                break

    def mark_complete(self, task_id: str, verdict: Optional[str] = None, files_changed: Optional[list[str]] = None) -> None:
        """
        Mark task as complete with verification verdict.

        Args:
            task_id: Task identifier
            verdict: Verification verdict ("PASS", "FAIL", "BLOCKED", or None)
            files_changed: List of files that were actually modified
        """
        for task in self.features:
            if task.id == task_id:
                task.status = "complete"
                task.passes = (verdict == "PASS") if verdict else True
                task.verification_verdict = verdict
                task.files_actually_changed = files_changed
                task.completed_at = datetime.now().isoformat()
                break

    def mark_blocked(self, task_id: str, error: str) -> None:
        """Mark task as blocked"""
        for task in self.features:
            if task.id == task_id:
                task.status = "blocked"
                task.error = error
                break

    def update_progress(self, task_id: str, error: Optional[str] = None) -> None:
        """Update task progress (failed attempt but can retry)"""
        for task in self.features:
            if task.id == task_id:
                task.error = error
                # Keep status as in_progress so it can retry
                break

    def get_stats(self) -> dict[str, int]:
        """Get queue statistics"""
        return {
            "total": len(self.features),
            "pending": sum(1 for t in self.features if t.status == "pending"),
            "in_progress": sum(1 for t in self.features if t.status == "in_progress"),
            "complete": sum(1 for t in self.features if t.status == "complete"),
            "blocked": sum(1 for t in self.features if t.status == "blocked"),
        }

    def validate_tasks(self, project_dir: Path) -> list[str]:
        """
        Validate that task file paths and test files exist.

        Args:
            project_dir: Root directory of the project

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        for task in self.features:
            # Feature tasks are allowed to CREATE files, so skip existence check
            # FeatureBuilder agent creates new files, so don't require them to exist
            is_feature_task = (
                task.type == "feature" or
                task.agent == "FeatureBuilder" or
                task.id.startswith("FEAT-")
            )

            # Check if target file exists (required for non-feature tasks)
            file_path = project_dir / task.file
            if not file_path.exists() and not is_feature_task:
                errors.append(f"Task {task.id}: Target file not found: {task.file}")

            # Check if test files exist (only for TEST tasks)
            # For LINT/TYPE tasks, test files are optional
            is_test_task = task.id.startswith("TEST-")
            for test_file in task.tests:
                test_path = project_dir / test_file
                if not test_path.exists() and is_test_task:
                    # Only error for missing test files if this is a TEST task
                    errors.append(f"Task {task.id}: Test file not found: {test_file}")

        return errors

    # =========================================================================
    # ADR-003: Autonomous Task Registration
    # =========================================================================

    def register_discovered_task(
        self,
        source: str,
        description: str,
        file: str,
        discovered_by: str,
        priority: Optional[int] = None,
        task_type: Optional[str] = None,
        test_files: Optional[list[str]] = None,
    ) -> Optional[str]:
        """
        Register a task discovered during agent work.

        Enables agents to programmatically add tasks without losing focus.
        Uses SHA256 fingerprinting for deduplication.

        Args:
            source: Where this came from ("ADR-002", "manual", "advisor", "RETRY-ESCALATION")
            description: Human-readable task description
            file: Target file path
            discovered_by: Agent that discovered this ("app-advisor", "cli", "cost-guardian")
            priority: 0=P0, 1=P1, 2=P2 (auto-computed if None)
            task_type: "bugfix"|"feature"|"refactor"|"test"|"codequality" (auto-inferred if None)
            test_files: Related test files (auto-inferred if None)

        Returns:
            Task ID if created, None if duplicate

        Example:
            queue.register_discovered_task(
                source="ADR-002",
                description="Fix cycle calculation precision - use relativedelta",
                file="apps/backend-api/app/calculators/cycle.py",
                discovered_by="app-advisor"
            )
            # Returns: "20260110-0832-BUG-ADR002-001"
        """
        # Deduplication via fingerprint
        fingerprint = self._compute_fingerprint(file, description)
        if fingerprint in self.fingerprints:
            return None  # Duplicate

        # Auto-classify if not provided
        if task_type is None:
            task_type = self._infer_task_type(description)

        # Get completion promise from task type
        completion_promise = self._get_completion_promise(task_type)
        max_iterations = self._get_max_iterations(task_type)

        # Auto-compute priority if not provided
        if priority is None:
            priority = self._compute_priority(file, task_type, description)

        # Generate task ID with timestamp
        task_id = self._generate_task_id(source, task_type)

        # Infer test files if not provided
        if test_files is None:
            test_files = self._infer_test_files(file)

        # Create task
        task = Task(
            id=task_id,
            description=description,
            file=file,
            status="pending",
            tests=test_files,
            passes=False,
            completion_promise=completion_promise,
            max_iterations=max_iterations,
            priority=priority,
            type=task_type,
            agent=self._infer_agent(task_type),
            # ADR-003 metadata
            source=source,
            discovered_by=discovered_by,
            fingerprint=fingerprint,
        )

        self.features.append(task)
        self.fingerprints.add(fingerprint)
        self.sequence += 1

        return task_id

    def _compute_fingerprint(self, file: str, description: str) -> str:
        """
        SHA256 fingerprint for deduplication.

        Format: SHA256(file:normalized_description)[:16]
        """
        # Normalize description (lowercase, strip whitespace)
        normalized = description.lower().strip()
        key = f"{file}:{normalized}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _generate_task_id(self, source: str, task_type: str) -> str:
        """
        Generate unique task ID with timestamp.

        Format: {YYYYMMDD}-{HHMM}-{TYPE}-{SOURCE}-{SEQ}
        Example: 20260110-0832-BUG-ADR002-001
        """
        now = datetime.now(timezone.utc)
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M")

        prefix_map = {
            "bugfix": "BUG",
            "feature": "FEAT",
            "refactor": "REF",
            "test": "TEST",
            "codequality": "QUAL",
        }
        type_prefix = prefix_map.get(task_type, "TASK")

        # Sanitize source (first 6 chars, alphanumeric only)
        source_clean = ''.join(c for c in source if c.isalnum())[:6].upper()
        if not source_clean:
            source_clean = "MANUAL"

        return f"{date_part}-{time_part}-{type_prefix}-{source_clean}-{self.sequence:03d}"

    def _compute_priority(self, file: str, task_type: str, description: str) -> int:
        """Compute priority based on file path and task type."""
        file_lower = file.lower()
        desc_lower = description.lower()

        # P0: Critical paths
        critical_paths = ['auth/', 'payment/', 'session/', 'security/', 'hipaa', 'phi/']
        if any(path in file_lower for path in critical_paths):
            return 0

        # P0: Security keywords
        if any(word in desc_lower for word in ['security', 'vulnerability', 'exploit', 'injection']):
            return 0

        # P0: Retry escalation (failed multiple times)
        if 'retry' in desc_lower or 'escalat' in desc_lower:
            return 0

        # P1: Test failures, type errors, bugs
        if task_type in ['test', 'bugfix']:
            return 1

        # P2: Quality, refactoring
        if task_type in ['codequality', 'refactor']:
            return 2

        return 1  # Default P1

    def _get_max_iterations(self, task_type: str) -> int:
        """Get iteration budget by task type."""
        budgets = {
            "bugfix": 15,
            "codequality": 20,
            "feature": 50,
            "test": 15,
            "refactor": 20,
        }
        return budgets.get(task_type, 15)

    def _get_completion_promise(self, task_type: str) -> str:
        """Get completion promise signal by task type."""
        promises = {
            "bugfix": "BUGFIX_COMPLETE",
            "codequality": "CODEQUALITY_COMPLETE",
            "feature": "FEATURE_COMPLETE",
            "test": "TESTS_COMPLETE",
            "refactor": "REFACTOR_COMPLETE",
        }
        return promises.get(task_type, "TASK_COMPLETE")

    def _infer_task_type(self, description: str) -> str:
        """
        Infer task type from description.

        Mirrors logic from orchestration/signal_templates.py:infer_task_type()
        """
        desc_lower = description.lower()

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

    def _infer_agent(self, task_type: str) -> str:
        """Infer agent from task type."""
        agent_map = {
            "bugfix": "BugFix",
            "feature": "FeatureBuilder",
            "test": "TestWriter",
            "codequality": "CodeQuality",
            "refactor": "CodeQuality",
        }
        return agent_map.get(task_type, "BugFix")

    def _infer_test_files(self, file: str) -> list[str]:
        """
        Infer test file paths from source file.

        Handles common patterns:
        - src/foo.ts → tests/foo.test.ts
        - app/foo.py → tests/foo_test.py
        """
        # If it's already a test file, return it
        if '.test.' in file or '__tests__' in file or '/tests/' in file or '_test.' in file:
            return [file]

        test_candidates = []

        # TypeScript/JavaScript patterns
        if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
            if '/src/' in file:
                test_path = file.replace('/src/', '/tests/')
                test_path = test_path.replace('.ts', '.test.ts').replace('.tsx', '.test.tsx')
                test_path = test_path.replace('.js', '.test.js').replace('.jsx', '.test.jsx')
                test_candidates.append(test_path)

        # Python patterns
        if file.endswith('.py'):
            if '/app/' in file or '/src/' in file:
                test_path = file.replace('/app/', '/tests/').replace('/src/', '/tests/')
                test_path = test_path.replace('.py', '_test.py')
                test_candidates.append(test_path)

        return test_candidates[:1] if test_candidates else []
