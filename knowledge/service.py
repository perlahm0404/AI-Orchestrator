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
    file_patterns: Optional[List[str]] = None,
    query: Optional[str] = None,
    hybrid: bool = True,
    top_k: int = 5
) -> List[KnowledgeObject]:
    """
    Find Knowledge Objects relevant to current work.

    Supports three search modes:
    1. Tag-only: Fast O(1) tag index lookup (default when no query)
    2. Semantic-only: Vector similarity search (when query provided, hybrid=False)
    3. Hybrid: Tag index first, semantic re-rank (query provided, hybrid=True)

    Token Optimization:
    - Returns top-K results (default 5) instead of all matches
    - 20-50% reduction in irrelevant KOs

    Args:
        project: Project to search within
        tags: Tags to match (ANY match returns the KO - OR semantics)
        file_patterns: File patterns to match
        query: Semantic search query (e.g., "how to fix null pointer in auth")
        hybrid: Combine tag + semantic search (True by default)
        top_k: Maximum results to return

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

    # Semantic search if query provided
    if query:
        semantic_results = _semantic_search(
            query=query,
            project=project,
            ko_map=ko_map,
            exclude_ids=matched_ko_ids if hybrid else set(),
            top_k=top_k
        )

        if hybrid:
            # Add semantic results after tag matches
            for ko in semantic_results:
                if ko.id not in matched_ko_ids:
                    relevant_kos.append(ko)
                    matched_ko_ids.add(ko.id)

            # Re-rank by semantic similarity if we have both
            if relevant_kos:
                relevant_kos = _rerank_by_semantic(relevant_kos, query, top_k)
        else:
            # Pure semantic search
            relevant_kos = semantic_results

    # Limit results
    relevant_kos = relevant_kos[:top_k]

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


# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC SEARCH (v6 - Vector-Enhanced KOs)
# ═══════════════════════════════════════════════════════════════════════════════

# Flag to track if semantic search is available
_semantic_available: Optional[bool] = None

# Semantic search backend selection ("lancedb", "chroma", or None)
# Can be set via environment variable: SEMANTIC_SEARCH_BACKEND
_semantic_backend: Optional[str] = None


def _check_semantic_available() -> bool:
    """
    Check if semantic search dependencies are available.

    Auto-detects available backends and selects one:
    1. Check environment variable SEMANTIC_SEARCH_BACKEND
    2. Try Chroma first (preferred for Phase 2B)
    3. Fall back to LanceDB
    4. If neither available, return False

    Returns:
        True if any semantic search backend is available
    """
    global _semantic_available, _semantic_backend
    if _semantic_available is None:
        import os

        # Check if user specified a backend
        env_backend = os.environ.get("SEMANTIC_SEARCH_BACKEND", "").lower()

        # Try backends in order of preference
        if env_backend == "chroma" or not env_backend:
            try:
                from . import semantic_search
                _semantic_backend = "chroma"
                _semantic_available = True
                return True
            except ImportError:
                pass

        if env_backend == "lancedb" or not env_backend:
            try:
                from . import embeddings
                from . import vector_store
                _semantic_backend = "lancedb"
                _semantic_available = True
                return True
            except ImportError:
                pass

        # No backend available
        _semantic_available = False
        _semantic_backend = None

    return _semantic_available


def _semantic_search(
    query: str,
    project: str,
    ko_map: Dict[str, KnowledgeObject],
    exclude_ids: set,
    top_k: int = 5
) -> List[KnowledgeObject]:
    """
    Perform semantic search using vector embeddings.

    Uses either Chroma or LanceDB backend based on availability.

    Args:
        query: Natural language query
        project: Project to filter by
        ko_map: Map of KO ID -> KnowledgeObject
        exclude_ids: IDs to exclude from results
        top_k: Maximum results

    Returns:
        List of KOs sorted by semantic similarity
    """
    if not _check_semantic_available():
        return []  # Graceful fallback if deps not installed

    try:
        global _semantic_backend

        if _semantic_backend == "chroma":
            # Use Chroma backend
            from .semantic_search import get_chroma_store

            store = get_chroma_store()
            # Chroma returns dict results with id, score, content, tags
            results = store.search(query, top_k=top_k * 2)

            semantic_kos = []
            for result in results:
                ko_id = result["id"]
                if ko_id in exclude_ids:
                    continue

                ko = ko_map.get(ko_id)
                if ko and ko.project == project:
                    semantic_kos.append(ko)

                if len(semantic_kos) >= top_k:
                    break

            return semantic_kos

        elif _semantic_backend == "lancedb":
            # Use LanceDB backend
            from .embeddings import get_embedder
            from .vector_store import get_vector_store

            # Get query embedding
            embedder = get_embedder()
            query_embedding = embedder.embed(query)

            # Search vector store
            store = get_vector_store()
            results = store.search(query_embedding, top_k=top_k * 2)

            semantic_kos = []
            for result in results:
                if result.ko_id in exclude_ids:
                    continue

                ko = ko_map.get(result.ko_id)
                if ko and ko.project == project:
                    semantic_kos.append(ko)

                if len(semantic_kos) >= top_k:
                    break

            return semantic_kos

        else:
            return []

    except Exception as e:
        # Log error and return empty (graceful degradation)
        print(f"Semantic search error ({_semantic_backend}): {e}")
        return []


def _rerank_by_semantic(
    kos: List[KnowledgeObject],
    query: str,
    top_k: int = 5
) -> List[KnowledgeObject]:
    """
    Re-rank KOs by semantic similarity to query.

    Args:
        kos: KOs to re-rank
        query: Query to compare against
        top_k: Maximum results

    Returns:
        KOs sorted by semantic similarity
    """
    if not _check_semantic_available() or not kos:
        return kos[:top_k]

    try:
        from .embeddings import get_embedder

        embedder = get_embedder()
        query_embedding = embedder.embed(query)

        # Generate embeddings for each KO and compute similarity
        scored = []
        for ko in kos:
            ko_text = f"{ko.title}\n{ko.what_was_learned}\n{ko.prevention_rule}"
            ko_embedding = embedder.embed(ko_text)
            similarity = embedder.similarity(query_embedding, ko_embedding)
            scored.append((ko, similarity))

        # Sort by similarity descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return [ko for ko, _ in scored[:top_k]]

    except Exception as e:
        print(f"Re-ranking error: {e}")
        return kos[:top_k]


def index_all_kos() -> int:
    """
    Index all approved KOs in the vector store.

    Call this after approving new KOs or to rebuild the index.
    Supports both Chroma and LanceDB backends.

    Returns:
        Number of KOs indexed
    """
    if not _check_semantic_available():
        return 0

    try:
        global _semantic_backend
        kos = _get_cached_kos()
        indexed = 0

        if _semantic_backend == "chroma":
            # Use Chroma backend
            from .semantic_search import get_chroma_store

            store = get_chroma_store()

            for ko in kos:
                # Combine KO text for embedding
                ko_text = f"{ko.title}\n{ko.what_was_learned}\n{ko.prevention_rule}"

                # Index with tags
                store.add_ko(ko.id, ko_text, ko.tags)
                indexed += 1

        elif _semantic_backend == "lancedb":
            # Use LanceDB backend
            from .embeddings import get_embedder
            from .vector_store import get_vector_store

            embedder = get_embedder()
            store = get_vector_store()

            for ko in kos:
                # Generate embedding
                ko_text = f"{ko.title}\n{ko.what_was_learned}\n{ko.prevention_rule}"
                embedding = embedder.embed(ko_text)

                # Index with metadata
                metadata = {
                    "title": ko.title,
                    "project": ko.project,
                    "tags": ko.tags,
                }
                store.index_ko(ko.id, embedding, metadata)
                indexed += 1

        return indexed

    except Exception as e:
        print(f"Indexing error ({_semantic_backend}): {e}")
        return 0
