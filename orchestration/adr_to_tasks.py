"""
ADR to Tasks Extractor

Parses ADR Implementation Notes and automatically extracts tasks.
Registers tasks with work queue using TASK-ADR{N}-{SEQ} format.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from tasks.work_queue import WorkQueue

logger = logging.getLogger(__name__)


# Task type keywords for classification
TASK_TYPE_KEYWORDS = {
    "migration": ["migration", "migrate", "alembic", "schema change", "database"],
    "test": ["test", "spec", "coverage", "pytest", "vitest"],
    "refactor": ["refactor", "restructure", "reorganize", "clean up"],
    "codequality": ["lint", "quality", "cleanup", "format"],
    "feature": ["create", "add", "implement", "build", "develop"],
    "bugfix": ["fix", "bug", "error", "issue"],
}


@dataclass
class ExtractedTask:
    """Task extracted from ADR markdown."""
    description: str
    file_path: Optional[str] = None
    task_type: Optional[str] = None
    phase: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)


def extract_tasks_from_adr(
    adr_path: Path,
    adr_number: str,
    project: str
) -> List[Dict[str, Any]]:
    """
    Parse ADR markdown and extract tasks from Implementation Notes.

    Looks for:
    - "## Implementation Notes" section
    - Bullet lists with task indicators (Create, Add, Update, Fix, Test)
    - Numbered lists (1. 2. 3.)
    - Checkboxes (- [ ] Task)

    Args:
        adr_path: Path to ADR markdown file
        adr_number: ADR number (e.g., "ADR-006" or "6")
        project: Project name

    Returns:
        List of task dictionaries with description, file, type, phase
    """
    if not adr_path.exists():
        logger.error(f"ADR file not found: {adr_path}")
        return []

    # Read ADR content
    content = adr_path.read_text()

    # Extract Implementation Notes section
    impl_section = parse_implementation_section(content)
    if not impl_section:
        logger.warning(f"No Implementation Notes section found in {adr_path}")
        return []

    # Extract tasks from section
    tasks = []

    # Pattern 1: Bullet points (- Task or * Task)
    bullet_pattern = r'^[\*\-]\s+(?:\[\s*\]\s+)?(.+)$'
    for match in re.finditer(bullet_pattern, impl_section, re.MULTILINE):
        task_text = match.group(1).strip()
        if _is_task_line(task_text):
            task = _parse_task_line(task_text, impl_section)
            if task:
                tasks.append(task)

    # Pattern 2: Numbered lists (1. Task)
    numbered_pattern = r'^\d+\.\s+(.+)$'
    for match in re.finditer(numbered_pattern, impl_section, re.MULTILINE):
        task_text = match.group(1).strip()
        if _is_task_line(task_text):
            task = _parse_task_line(task_text, impl_section)
            if task:
                tasks.append(task)

    # Convert ExtractedTask objects to dicts
    result = []
    for task in tasks:
        result.append({
            "description": task.description,
            "file": task.file_path,
            "type": task.task_type or "feature",
            "phase": task.phase,
            "dependencies": task.dependencies
        })

    logger.info(f"Extracted {len(result)} tasks from {adr_path.name}")
    return result


def parse_implementation_section(markdown: str) -> Optional[str]:
    """
    Extract Implementation Notes section from ADR markdown.

    Returns:
        Section content or None if not found
    """
    # Look for "## Implementation Notes" heading
    match = re.search(
        r'##\s+Implementation\s+Notes\s*\n(.+?)(?=\n##|\Z)',
        markdown,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


def _is_task_line(line: str) -> bool:
    """Determine if a line represents a task."""
    # Skip empty lines
    if not line.strip():
        return False

    # Skip section headers
    if line.startswith('#'):
        return False

    # Skip YAML blocks
    if line.startswith('```'):
        return False

    # Look for action verbs
    action_verbs = [
        "create", "add", "update", "fix", "implement", "build",
        "develop", "write", "test", "refactor", "migrate", "setup",
        "configure", "deploy", "install", "remove", "delete"
    ]

    first_word = line.split()[0].lower() if line.split() else ""
    return any(verb in first_word or verb in line.lower() for verb in action_verbs)


def _parse_task_line(line: str, context: str) -> Optional[ExtractedTask]:
    """Parse a single task line to extract metadata."""
    # Extract description (remove leading markers)
    description = re.sub(r'^\[\s*\]\s*', '', line).strip()

    # Infer file path from description or context
    file_path = _infer_file_path(description, context)

    # Infer task type
    task_type = _infer_task_type(description)

    # Extract phase if mentioned
    phase = _extract_phase(line, context)

    # Extract dependencies
    dependencies = _extract_dependencies(description)

    return ExtractedTask(
        description=description,
        file_path=file_path,
        task_type=task_type,
        phase=phase,
        dependencies=dependencies
    )


def _infer_file_path(description: str, context: str) -> Optional[str]:
    """
    Attempt to infer file path from task description.

    Patterns:
    - "in {file_path}"
    - "Update {file_path}"
    - "`{file_path}`"
    - "{file_path} ..."

    Returns:
        File path or None if ambiguous
    """
    # Look for backtick-quoted paths
    backtick_match = re.search(r'`([^`]+\.[a-z]+)`', description)
    if backtick_match:
        return backtick_match.group(1)

    # Look for "in file_path" pattern
    in_pattern = re.search(r'\bin\s+([a-zA-Z0-9_/\.\-]+\.[a-z]+)', description)
    if in_pattern:
        return in_pattern.group(1)

    # Look for file extensions
    ext_pattern = re.search(r'([a-zA-Z0-9_/\.\-]+\.(py|ts|tsx|js|jsx|md|sql|yaml|json))', description)
    if ext_pattern:
        return ext_pattern.group(1)

    # Check context for file hints
    # Look backwards from current line for file mentions
    context_files = re.findall(r'([a-zA-Z0-9_/\.\-]+\.(py|ts|tsx|js|jsx|md|sql|yaml|json))', context)
    if context_files:
        # Return most recent file mention
        return context_files[-1][0]

    return None


def _infer_task_type(description: str) -> str:
    """
    Infer task type from description keywords.

    Returns:
        Task type: "migration", "test", "refactor", "codequality", "feature", or "bugfix"
    """
    desc_lower = description.lower()

    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        if any(keyword in desc_lower for keyword in keywords):
            return task_type

    # Default to feature
    return "feature"


def _extract_phase(line: str, context: str) -> Optional[int]:
    """
    Extract phase number if mentioned.

    Looks for: "Phase X", "Step X", "### Phase X:"
    """
    # Check line itself
    phase_match = re.search(r'(?:phase|step)\s+(\d+)', line, re.IGNORECASE)
    if phase_match:
        return int(phase_match.group(1))

    # Check context (look backwards for phase heading)
    # Find all phase headings before this line
    phase_headings = re.findall(r'###\s+Phase\s+(\d+)', context, re.IGNORECASE)
    if phase_headings:
        # Return most recent phase
        return int(phase_headings[-1])

    return None


def _extract_dependencies(description: str) -> List[str]:
    """
    Extract dependencies from description.

    Looks for: "depends on", "requires", "after", "following"
    """
    dependencies = []

    # Pattern: "depends on X, Y"
    depends_match = re.search(
        r'(?:depends\s+on|requires|after|following)\s+([^\.]+)',
        description,
        re.IGNORECASE
    )

    if depends_match:
        # Parse comma-separated items
        items = depends_match.group(1).split(',')
        for item in items:
            item = item.strip()
            # Look for task references or descriptions
            if item:
                dependencies.append(item)

    return dependencies


def register_tasks_with_queue(
    tasks: List[Dict[str, Any]],
    adr_number: str,
    work_queue: WorkQueue,
    project_root: Path
) -> List[str]:
    """
    Register extracted tasks with work queue.

    Task ID format: TASK-ADR{N}-{SEQ:03d}
    Example: TASK-ADR006-001, TASK-ADR006-002

    Args:
        tasks: List of task dicts from extract_tasks_from_adr()
        adr_number: ADR number (e.g., "ADR-006" or "6")
        work_queue: WorkQueue instance
        project_root: Project root path

    Returns:
        List of created task IDs
    """
    # Normalize ADR number
    if adr_number.startswith("ADR-"):
        adr_num = int(adr_number.replace("ADR-", ""))
    else:
        adr_num = int(adr_number)

    created_ids = []
    seq = 1

    for task_dict in tasks:
        # Generate task ID
        task_id = f"TASK-ADR{adr_num:03d}-{seq:03d}"

        # Infer test files if not provided
        test_files = _infer_test_files(task_dict.get("file")) if task_dict.get("file") else None

        # Register with work queue using standard method
        # Note: We can't use register_discovered_task() because it generates timestamped IDs
        # Instead, create task manually
        from tasks.work_queue import Task

        task = Task(
            id=task_id,
            description=task_dict["description"],
            file=task_dict.get("file") or "TBD",  # File path or placeholder
            status="pending",
            tests=test_files or [],
            passes=False,
            completion_promise=_get_completion_promise(task_dict.get("type", "feature")),
            max_iterations=_get_max_iterations(task_dict.get("type", "feature")),
            priority=_compute_priority(task_dict.get("type", "feature")),
            type=task_dict.get("type", "feature"),
            agent=_infer_agent(task_dict.get("type", "feature")),
            source=f"ADR-{adr_num:03d}",
            discovered_by="adr-extractor"
        )

        # Check for duplicates by description
        is_duplicate = any(
            existing.description == task.description
            for existing in work_queue.features
        )

        if not is_duplicate:
            work_queue.features.append(task)
            created_ids.append(task_id)
            seq += 1
        else:
            logger.debug(f"Skipping duplicate task: {task.description}")

    logger.info(f"Registered {len(created_ids)} tasks from ADR-{adr_num:03d}")
    return created_ids


def _infer_test_files(file_path: Optional[str]) -> Optional[List[str]]:
    """Infer test file paths from source file."""
    if not file_path or file_path == "TBD":
        return None

    path = Path(file_path)

    # Common test patterns
    test_patterns = [
        f"tests/{path.stem}_test{path.suffix}",
        f"tests/test_{path.stem}{path.suffix}",
        f"{path.parent}/tests/{path.stem}_test{path.suffix}",
        f"{path.parent}/__tests__/{path.stem}.test{path.suffix}",
    ]

    return test_patterns


def _get_completion_promise(task_type: str) -> str:
    """Get completion promise for task type."""
    promises = {
        "bugfix": "BUGFIX_COMPLETE",
        "codequality": "CODEQUALITY_COMPLETE",
        "feature": "FEATURE_COMPLETE",
        "test": "TESTS_COMPLETE",
        "migration": "MIGRATION_COMPLETE",
        "refactor": "REFACTOR_COMPLETE",
    }
    return promises.get(task_type, "FEATURE_COMPLETE")


def _get_max_iterations(task_type: str) -> int:
    """Get max iterations for task type."""
    iterations = {
        "bugfix": 15,
        "codequality": 20,
        "feature": 50,
        "test": 15,
        "migration": 20,
        "refactor": 20,
    }
    return iterations.get(task_type, 50)


def _compute_priority(task_type: str) -> int:
    """Compute priority based on task type."""
    # P0 = blocks users, P1 = degrades UX, P2 = tech debt
    priorities = {
        "bugfix": 0,  # P0 - blocks users
        "migration": 1,  # P1 - needed for features
        "feature": 1,  # P1 - new functionality
        "test": 2,  # P2 - improves quality
        "refactor": 2,  # P2 - tech debt
        "codequality": 2,  # P2 - tech debt
    }
    return priorities.get(task_type, 1)


def _infer_agent(task_type: str) -> str:
    """Infer agent type from task type."""
    agents = {
        "bugfix": "BugFix",
        "codequality": "CodeQuality",
        "test": "TestWriter",
        "feature": "FeatureBuilder",
        "migration": "FeatureBuilder",  # Migrations are features
        "refactor": "FeatureBuilder",  # Refactors are features
    }
    return agents.get(task_type, "FeatureBuilder")
