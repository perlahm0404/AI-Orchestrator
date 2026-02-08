"""
Icebox Service Layer - CRUD operations for idea capture

Provides:
- capture_idea(): Quick capture with deduplication
- list_ideas(): Filter by project/status/category
- promote_to_parked_task(): Icebox -> Work queue (parked)
- promote_to_pending_task(): Icebox -> Work queue (pending)
- archive_idea(): Move stale to archive
- get_stale_ideas(): Find ideas > N days old
"""

import shutil
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional

from parking.icebox import IceboxIdea, generate_idea_id, IdeaCategory, EffortEstimate


# Storage paths
AIBRAIN_DIR = Path(__file__).parent.parent / ".aibrain"
ICEBOX_DIR = AIBRAIN_DIR / "icebox"
ARCHIVE_DIR = ICEBOX_DIR / "archive"

# Thread safety
_lock = threading.Lock()
_sequence_counter = 0


def _ensure_dirs() -> None:
    """Ensure icebox directories exist."""
    ICEBOX_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _get_next_sequence() -> int:
    """Get next sequence number (thread-safe)."""
    global _sequence_counter
    with _lock:
        _sequence_counter += 1
        return _sequence_counter


def _get_idea_path(idea_id: str, archived: bool = False) -> Path:
    """Get file path for an idea."""
    base_dir = ARCHIVE_DIR if archived else ICEBOX_DIR
    return base_dir / f"{idea_id}.md"


def _load_all_fingerprints() -> set[str]:
    """Load all fingerprints for deduplication."""
    fingerprints = set()
    _ensure_dirs()

    for md_file in ICEBOX_DIR.glob("*.md"):
        try:
            content = md_file.read_text()
            idea = IceboxIdea.from_markdown(content)
            fingerprints.add(idea.fingerprint)
        except Exception:
            continue

    return fingerprints


def find_duplicate(title: str, description: str, project: str) -> Optional[IceboxIdea]:
    """
    Check for duplicate ideas via fingerprint.

    Args:
        title: Idea title
        description: Idea description
        project: Project name

    Returns:
        Existing IceboxIdea if duplicate found, None otherwise
    """
    # Generate fingerprint for comparison
    import hashlib
    normalized = f"{project}:{title.lower().strip()}:{description[:100].lower().strip()}"
    fingerprint = hashlib.sha256(normalized.encode()).hexdigest()[:16]

    _ensure_dirs()
    for md_file in ICEBOX_DIR.glob("*.md"):
        try:
            content = md_file.read_text()
            idea = IceboxIdea.from_markdown(content)
            if idea.fingerprint == fingerprint:
                return idea
        except Exception:
            continue

    return None


def capture_idea(
    title: str,
    description: str,
    project: str,
    category: IdeaCategory = "improvement",
    priority: int = 2,
    effort_estimate: EffortEstimate = "M",
    dependencies: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    source: str = "human",
    discovered_by: str = "cli",
) -> Optional[IceboxIdea]:
    """
    Quick capture with deduplication.

    Args:
        title: Short, memorable title
        description: Full details
        project: Project name (credentialmate, karematch, ai-orchestrator)
        category: feature | improvement | research | tech-debt | bug
        priority: 0=urgent, 1=high, 2=medium, 3=someday
        effort_estimate: XS | S | M | L | XL
        dependencies: Task IDs or IDEA IDs this depends on
        tags: Tags for discovery
        source: human | agent | advisor | council
        discovered_by: Who captured it

    Returns:
        IceboxIdea if created, None if duplicate
    """
    _ensure_dirs()

    # Check for duplicate
    existing = find_duplicate(title, description, project)
    if existing:
        return None

    # Generate ID
    sequence = _get_next_sequence()
    idea_id = generate_idea_id(project, sequence)

    # Create idea
    idea = IceboxIdea(
        id=idea_id,
        title=title,
        description=description,
        project=project,
        category=category,
        priority=priority,
        effort_estimate=effort_estimate,
        dependencies=dependencies or [],
        tags=tags or [],
        source=source,
        discovered_by=discovered_by,
    )

    # Save to file
    idea_path = _get_idea_path(idea_id)
    with _lock:
        idea_path.write_text(idea.to_markdown())

    return idea


def get_idea(idea_id: str) -> Optional[IceboxIdea]:
    """
    Get a single idea by ID.

    Args:
        idea_id: Idea ID (e.g., IDEA-20260207-1430-001)

    Returns:
        IceboxIdea if found, None otherwise
    """
    _ensure_dirs()

    # Check active icebox
    idea_path = _get_idea_path(idea_id)
    if idea_path.exists():
        content = idea_path.read_text()
        return IceboxIdea.from_markdown(content)

    # Check archive
    archive_path = _get_idea_path(idea_id, archived=True)
    if archive_path.exists():
        content = archive_path.read_text()
        return IceboxIdea.from_markdown(content)

    return None


def list_ideas(
    project: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    include_archived: bool = False,
) -> List[IceboxIdea]:
    """
    List ideas with optional filters.

    Args:
        project: Filter by project
        status: Filter by status (raw, reviewed, promoted, archived)
        category: Filter by category
        include_archived: Include archived ideas

    Returns:
        List of matching IceboxIdea instances
    """
    _ensure_dirs()
    ideas = []

    # Load from active icebox
    for md_file in ICEBOX_DIR.glob("*.md"):
        try:
            content = md_file.read_text()
            idea = IceboxIdea.from_markdown(content)
            ideas.append(idea)
        except Exception:
            continue

    # Optionally load from archive
    if include_archived:
        for md_file in ARCHIVE_DIR.glob("*.md"):
            try:
                content = md_file.read_text()
                idea = IceboxIdea.from_markdown(content)
                ideas.append(idea)
            except Exception:
                continue

    # Apply filters
    if project:
        ideas = [i for i in ideas if i.project == project]
    if status:
        ideas = [i for i in ideas if i.status == status]
    if category:
        ideas = [i for i in ideas if i.category == category]

    # Sort by priority (urgent first), then by created_at (newest first)
    ideas.sort(key=lambda x: (x.priority, x.created_at), reverse=False)

    return ideas


def update_idea(idea: IceboxIdea) -> bool:
    """
    Update an existing idea.

    Args:
        idea: IceboxIdea with updated fields

    Returns:
        True if updated, False if not found
    """
    idea_path = _get_idea_path(idea.id)
    if not idea_path.exists():
        return False

    with _lock:
        idea_path.write_text(idea.to_markdown())

    return True


def archive_idea(idea_id: str, reason: str) -> bool:
    """
    Move stale idea to archive.

    Args:
        idea_id: Idea ID
        reason: Why archived (e.g., "Superseded by FEAT-123")

    Returns:
        True if archived, False if not found
    """
    _ensure_dirs()

    idea_path = _get_idea_path(idea_id)
    if not idea_path.exists():
        return False

    # Load and update idea
    content = idea_path.read_text()
    idea = IceboxIdea.from_markdown(content)
    idea.status = "archived"
    idea.archived_reason = reason
    idea.last_reviewed = datetime.now(timezone.utc).isoformat()

    # Move to archive
    archive_path = _get_idea_path(idea_id, archived=True)
    with _lock:
        archive_path.write_text(idea.to_markdown())
        idea_path.unlink()

    return True


def get_stale_ideas(days: int = 30) -> List[IceboxIdea]:
    """
    Find ideas not reviewed in N days.

    Args:
        days: Number of days threshold

    Returns:
        List of stale IceboxIdea instances
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stale = []

    for idea in list_ideas():
        # Check last_reviewed or created_at
        check_date = idea.last_reviewed or idea.created_at
        try:
            idea_date = datetime.fromisoformat(check_date.replace("Z", "+00:00"))
            if idea_date < cutoff:
                stale.append(idea)
        except Exception:
            # If date parsing fails, include as stale
            stale.append(idea)

    return stale


def promote_to_parked_task(idea_id: str, project: str) -> Optional[str]:
    """
    Promote idea to parked task in work queue.

    Args:
        idea_id: Idea ID to promote
        project: Project for work queue

    Returns:
        Task ID if promoted, None if not found
    """
    idea = get_idea(idea_id)
    if not idea:
        return None

    # Import here to avoid circular dependency
    from tasks.work_queue import WorkQueue, Task

    # Determine work queue path
    queue_path = Path(__file__).parent.parent / "tasks" / f"work_queue_{project}.json"
    if not queue_path.exists():
        return None

    # Load queue
    queue = WorkQueue.load(queue_path)

    # Generate task ID
    now = datetime.now()
    task_type = "FEAT" if idea.category == "feature" else "TASK"
    task_id = f"{task_type}-{now.strftime('%Y%m%d')}-{now.strftime('%H%M')}-{len(queue.features):03d}"

    # Create task
    task = Task(
        id=task_id,
        description=f"{idea.title}: {idea.description[:200]}",
        file="",  # Feature tasks may not have specific file
        status="parked",
        type="feature" if idea.category == "feature" else "bugfix",
        source="icebox",
        discovered_by=idea.discovered_by,
        priority=idea.priority,
        metadata={
            "icebox_id": idea.id,
            "effort_estimate": idea.effort_estimate,
            "tags": idea.tags,
            "dependencies": idea.dependencies,
        },
    )

    # Add to queue
    queue.features.append(task)
    queue.save(queue_path)

    # Update idea status
    idea.status = "promoted"
    idea.promoted_to = task_id
    idea.last_reviewed = datetime.now(timezone.utc).isoformat()
    update_idea(idea)

    return task_id


def promote_to_pending_task(idea_id: str, project: str) -> Optional[str]:
    """
    Promote idea directly to pending task in work queue.

    Args:
        idea_id: Idea ID to promote
        project: Project for work queue

    Returns:
        Task ID if promoted, None if not found
    """
    # First promote to parked
    task_id = promote_to_parked_task(idea_id, project)
    if not task_id:
        return None

    # Then unpark
    from tasks.work_queue import WorkQueue

    queue_path = Path(__file__).parent.parent / "tasks" / f"work_queue_{project}.json"
    queue = WorkQueue.load(queue_path)
    queue.unpark_task(task_id)
    queue.save(queue_path)

    return task_id
