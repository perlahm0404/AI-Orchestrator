"""
Knowledge Object Service

CRUD operations, matching, and consultation for Knowledge Objects.

Implementation: Phase 2 MVP - Markdown-based storage

Usage:
    from knowledge import service

    # Consult before starting work
    relevant = service.find_relevant(
        project="karematch",
        tags=["auth", "null-check"],
        file_patterns=["src/auth/*"]
    )

    # Create draft after resolution
    ko = service.create_draft(
        project="karematch",
        title="Always check for null in auth middleware",
        what_was_learned="...",
        why_it_matters="...",
        prevention_rule="...",
        tags=["auth", "null-check"]
    )

    # Approve draft
    service.approve(ko.id)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import glob
import time
import threading


# Directories for Knowledge Objects
KO_DRAFTS_DIR = Path(__file__).parent / "drafts"
KO_APPROVED_DIR = Path(__file__).parent / "approved"

# Ensure directories exist
KO_DRAFTS_DIR.mkdir(exist_ok=True)
KO_APPROVED_DIR.mkdir(exist_ok=True)


# In-memory cache for approved KOs
# Provides 10-100x speedup for repeated queries
_ko_cache: Optional[Dict[str, Any]] = None
_tag_index: Optional[Dict[str, List[str]]] = None  # tag → list of KO IDs
_cache_lock = threading.Lock()
_cache_expiry_seconds = 300  # 5 minutes

def _get_cached_kos() -> List[KnowledgeObject]:
    """
    Get approved KOs from cache or rebuild cache if stale.

    Also builds tag index for O(1) tag lookup.
    Cache is invalidated after 5 minutes or when approve() is called.
    Thread-safe for concurrent access.

    Returns:
        List of all approved KnowledgeObject instances
    """
    global _ko_cache, _tag_index

    with _cache_lock:
        # Check if cache exists and is valid
        if _ko_cache and (time.time() - _ko_cache['timestamp']) < _cache_expiry_seconds:
            return _ko_cache['kos']

        # Rebuild cache from disk
        all_kos = []
        tag_index = {}  # tag → list of KO IDs

        for ko_file in KO_APPROVED_DIR.glob("*.md"):
            ko = _load_ko_from_file(ko_file)
            if ko:
                all_kos.append(ko)

                # Build tag index: tag → KO IDs
                for tag in ko.tags:
                    if tag not in tag_index:
                        tag_index[tag] = []
                    tag_index[tag].append(ko.id)

        # Update cache and index
        _ko_cache = {
            'kos': all_kos,
            'timestamp': time.time()
        }
        _tag_index = tag_index

        return all_kos

def invalidate_cache():
    """
    Invalidate the KO cache and tag index.

    Call this after modifying KO files (approve, edit, delete).
    """
    global _ko_cache, _tag_index
    with _cache_lock:
        _ko_cache = None
        _tag_index = None


@dataclass
class KnowledgeObject:
    """
    A Knowledge Object captures institutional learning.

    Simplified for MVP - stored as markdown with frontmatter.
    """
    id: str                    # e.g., "KO-km-001"
    project: str               # e.g., "karematch"
    title: str                 # Short, memorable name
    what_was_learned: str      # The core lesson (1-3 sentences)
    why_it_matters: str        # Impact if ignored
    prevention_rule: str       # How to prevent recurrence
    tags: List[str]            # For pattern matching
    status: str                # "draft" | "approved"
    created_at: str           # ISO timestamp
    approved_at: Optional[str] = None
    detection_pattern: str = ""  # Regex/glob for matching
    file_patterns: List[str] = None  # File patterns this applies to

    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = []


def find_relevant(
    project: str,
    tags: Optional[List[str]] = None,
    file_patterns: Optional[List[str]] = None
) -> List[KnowledgeObject]:
    """
    Find Knowledge Objects relevant to current work.

    Uses tag-based matching (no vector embeddings in v1).
    Uses in-memory cache + tag index for fast O(1) tag lookups.

    Args:
        project: Project to search within
        tags: Tags to match (ANY match returns the KO - OR semantics)
        file_patterns: File patterns to match

    Returns:
        List of relevant approved Knowledge Objects
    """
    global _tag_index

    relevant_kos = []
    matched_ko_ids = set()  # Track which KOs we've already matched

    # Load all approved KOs from cache (also builds tag index)
    all_kos = _get_cached_kos()

    # Build KO lookup map for fast access by ID
    ko_map = {ko.id: ko for ko in all_kos}

    # Fast tag matching using index (O(1) per tag instead of O(n))
    if tags and _tag_index:
        for tag in tags:
            if tag in _tag_index:
                # Get all KO IDs with this tag from index
                for ko_id in _tag_index[tag]:
                    if ko_id not in matched_ko_ids:
                        ko = ko_map.get(ko_id)
                        # Filter by project
                        if ko and ko.project == project:
                            relevant_kos.append(ko)
                            matched_ko_ids.add(ko_id)

    # File pattern matching (slower, but rare)
    if file_patterns:
        for ko in all_kos:
            # Skip if already matched by tags
            if ko.id in matched_ko_ids:
                continue

            # Filter by project
            if ko.project != project:
                continue

            # Match file patterns
            if any(pattern in ko.file_patterns for pattern in file_patterns):
                relevant_kos.append(ko)
                matched_ko_ids.add(ko.id)

    # Update consultation metrics
    # Legacy: Log to file
    for ko in relevant_kos:
        _increment_consultation_count(ko.id)

    return relevant_kos


def create_draft(
    project: str,
    title: str,
    what_was_learned: str,
    why_it_matters: str,
    prevention_rule: str,
    tags: List[str],
    detection_pattern: str = "",
    file_patterns: Optional[List[str]] = None
) -> KnowledgeObject:
    """
    Create a draft Knowledge Object.

    Saves to knowledge/drafts/ as markdown.

    Returns:
        The created KnowledgeObject with status="draft"
    """
    # Generate ID
    ko_id = _generate_ko_id(project)

    ko = KnowledgeObject(
        id=ko_id,
        project=project,
        title=title,
        what_was_learned=what_was_learned,
        why_it_matters=why_it_matters,
        prevention_rule=prevention_rule,
        tags=tags,
        status="draft",
        created_at=datetime.now().isoformat(),
        detection_pattern=detection_pattern,
        file_patterns=file_patterns or []
    )

    # Save to drafts directory
    _save_ko_to_file(ko, KO_DRAFTS_DIR)

    return ko


def approve(ko_id: str) -> Optional[KnowledgeObject]:
    """
    Approve a draft Knowledge Object.

    Moves from drafts/ to approved/ and invalidates cache.

    Returns:
        The approved KnowledgeObject, or None if not found
    """
    draft_file = KO_DRAFTS_DIR / f"{ko_id}.md"

    if not draft_file.exists():
        return None

    # Load draft
    ko = _load_ko_from_file(draft_file)
    if ko is None:
        return None

    # Update status
    ko.status = "approved"
    ko.approved_at = datetime.now().isoformat()

    # Move to approved directory
    _save_ko_to_file(ko, KO_APPROVED_DIR)

    # Remove from drafts
    draft_file.unlink()

    # Invalidate cache so next query picks up new KO
    invalidate_cache()

    return ko


def list_drafts() -> List[KnowledgeObject]:
    """
    List all draft Knowledge Objects.

    Returns:
        List of draft KOs
    """
    drafts = []
    for ko_file in KO_DRAFTS_DIR.glob("*.md"):
        ko = _load_ko_from_file(ko_file)
        if ko:
            drafts.append(ko)
    return drafts


def list_approved(project: Optional[str] = None) -> List[KnowledgeObject]:
    """
    List all approved Knowledge Objects.

    Uses in-memory cache for fast repeated queries.

    Args:
        project: Optional project filter

    Returns:
        List of approved KOs
    """
    # Load from cache
    all_kos = _get_cached_kos()

    # Filter by project if specified
    if project is None:
        return all_kos
    else:
        return [ko for ko in all_kos if ko.project == project]


# Private helpers

def _generate_ko_id(project: str) -> str:
    """
    Generate next KO ID for a project.

    Format: KO-{project_abbrev}-{seq}
    e.g., KO-km-001, KO-km-002, etc.
    """
    # Project abbreviations
    abbrev_map = {
        "karematch": "km",
        "credentialmate": "cm"
    }
    abbrev = abbrev_map.get(project, project[:2])

    # Find highest existing sequence number
    pattern = f"KO-{abbrev}-*.md"
    existing = list(KO_DRAFTS_DIR.glob(pattern)) + list(KO_APPROVED_DIR.glob(pattern))

    max_seq = 0
    for file_path in existing:
        try:
            # Extract sequence number from filename like KO-km-001.md
            seq_str = file_path.stem.split("-")[-1]
            seq = int(seq_str)
            max_seq = max(max_seq, seq)
        except (ValueError, IndexError):
            continue

    # Next sequence
    next_seq = max_seq + 1

    return f"KO-{abbrev}-{next_seq:03d}"


def _save_ko_to_file(ko: KnowledgeObject, directory: Path) -> None:
    """Save KO as markdown with JSON frontmatter."""
    file_path = directory / f"{ko.id}.md"

    # Convert to dict for frontmatter
    ko_dict = asdict(ko)

    # Create markdown content
    content = f"""---
{json.dumps(ko_dict, indent=2)}
---

# {ko.title}

## What Was Learned

{ko.what_was_learned}

## Why It Matters

{ko.why_it_matters}

## Prevention Rule

{ko.prevention_rule}

## Tags

{', '.join(ko.tags)}

## Detection Pattern

```
{ko.detection_pattern or 'N/A'}
```

## File Patterns

{', '.join(ko.file_patterns) if ko.file_patterns else 'N/A'}

---

**Status**: {ko.status}
**Project**: {ko.project}
**Created**: {ko.created_at}
{f'**Approved**: {ko.approved_at}' if ko.approved_at else ''}
"""

    file_path.write_text(content)


def _load_ko_from_file(file_path: Path) -> Optional[KnowledgeObject]:
    """Load KO from markdown file with JSON frontmatter."""
    try:
        content = file_path.read_text()

        # Extract frontmatter (between --- markers)
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter_json = parts[1].strip()
        ko_dict = json.loads(frontmatter_json)

        return KnowledgeObject(**ko_dict)

    except (json.JSONDecodeError, TypeError, FileNotFoundError):
        return None


def _increment_consultation_count(ko_id: str) -> None:
    """
    Increment consultation count for a KO.

    In MVP, this just logs the consultation.
    In production, would update database.
    """
    # For MVP, just log to a file
    metrics_file = Path(__file__).parent / "consultation_metrics.log"
    with open(metrics_file, "a") as f:
        f.write(f"{datetime.now().isoformat()},{ko_id},consulted\n")
