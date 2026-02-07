# Phase 2B-2: Chroma Semantic Search for Knowledge Objects (CLI Mode)

## Your Role

You are the TeamLead agent for Chroma semantic search integration. You will implement vector-based semantic search for Knowledge Objects to improve discovery by 20-30% beyond tag-based search.

**Execution Mode**: Claude CLI Wrapper (no API key, OAuth-based)
**Merge Order**: FIRST (no iteration_loop.py changes needed)
**Status**: 0% complete (no files created yet)

---

## Kanban Board Real-Time Integration ✅ ALREADY WIRED

Your work progress will **automatically stream to the kanban board** via WebSocket in real-time. No extra configuration needed.

### Monitor Your Progress

While you're implementing Chroma semantic search:

```bash
# Terminal: Start dashboard
npm run dev --prefix ui/dashboard

# Browser: Open http://localhost:3000
# You'll see your specialist agent in the kanban board showing:
# - Implementation progress
# - Test execution status
# - Completion verdicts
```

### Real-Time Events from Your Work

The monitoring system captures:
- **specialist_started** - When you begin work
- **specialist_completed** - When tests pass/fail
- **iterations** - Each loop of TDD (test → code → verify)

**The dashboard shows all of this automatically** via your agent's monitoring integration.

---

## Exclusive Files (You Own These)

Create and own these files entirely:

1. **`knowledge/semantic_search.py`** (NEW)
   - `ChromaKnowledgeStore` class with vector embeddings
   - Chroma PersistentClient with local embeddings (all-MiniLM-L6-v2)
   - `search(query, tags, top_k)` method for hybrid search

2. **`tests/test_semantic_search.py`** (NEW)
   - TDD test suite (write FIRST before implementation)
   - 20+ tests covering:
     - Basic search functionality
     - Hybrid search (semantic + tags)
     - Performance benchmarking (< 100ms)
     - Backward compatibility (works without Chroma)

---

## Shared Files (Coordinate Carefully)

These files are shared. Coordinate with other agents to avoid conflicts:

1. **`knowledge/service.py`** (MODIFY lines 138-241)
   - Enhance `find_relevant()` function
   - Add semantic search as fallback when tag search returns < 3 results
   - Keep existing tag-based search working (backward compatibility)

2. **`orchestration/monitoring/config.py`** (READ-ONLY)
   - Check for Chroma configuration section
   - Feature flag: `enable_semantic_search`
   - Usage: `if config.enable_semantic_search: use_chroma()`

---

## DO NOT TOUCH

These files are owned by other agents. Do not modify:

- `orchestration/agent_cost_tracker.py` (Cost Tracking agent owns)
- `orchestration/monitoring/langfuse_integration.py` (Langfuse agent owns)
- `orchestration/iteration_loop.py` (Integration happens in Phase 2B-5)
- `.aibrain/prompts/phase2b-*.md` (Other prompts - read-only)

---

## Implementation Requirements

### 1. Write Tests FIRST (TDD)

Create `tests/test_semantic_search.py` with these test classes:

```python
class TestChromaKnowledgeStore:
    def test_initialize_chroma_store()
    def test_search_basic_query()
    def test_search_with_tags_filter()
    def test_search_performance_under_100ms()
    def test_hybrid_search_semantic_and_tags()
    def test_backward_compatibility_without_chroma()

class TestHybridSearch:
    def test_tag_search_returns_3_plus()  # Skip semantic
    def test_tag_search_returns_less_than_3()  # Add semantic
    def test_merge_results_by_confidence()
    def test_deduplication_across_results()

class TestIntegration:
    def test_knowledge_service_uses_semantic_search()
    def test_fallback_when_tag_search_insufficient()
    def test_performance_degradation_acceptable()
```

### 2. Create ChromaKnowledgeStore

Implement in `knowledge/semantic_search.py`:

```python
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional

class ChromaKnowledgeStore:
    """Vector database for semantic search on Knowledge Objects."""

    def __init__(self, persist_directory: str = ".aibrain/chroma"):
        """Initialize Chroma with local embeddings."""
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Use sentence transformers (local, fast, no external API)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="knowledge-objects",
            embedding_function=self.embedding_fn
        )

    def add_ko(self, ko_id: str, content: str, tags: List[str] = []):
        """Add Knowledge Object to vector store."""
        self.collection.add(
            ids=[ko_id],
            documents=[content],
            metadatas=[{"tags": ",".join(tags)}]
        )

    def search(
        self,
        query: str,
        tags: List[str] = [],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: semantic + tag filtering.

        Args:
            query: Natural language search query
            tags: Optional tags to filter results (OR semantics)
            top_k: Number of results to return

        Returns:
            List of results with id, score, content, tags
        """
        # Build where filter for tags if provided
        where_filter = None
        if tags:
            # Filter for KOs that have ANY of the provided tags
            where_filter = {"tags": {"$in": tags}}

        # Execute semantic search
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )

        # Format results
        formatted = []
        if results and results['ids'] and len(results['ids']) > 0:
            for i, ko_id in enumerate(results['ids'][0]):
                formatted.append({
                    "id": ko_id,
                    "score": results['distances'][0][i] if results['distances'] else 0,
                    "content": results['documents'][0][i] if results['documents'] else "",
                    "tags": results['metadatas'][0][i].get('tags', '').split(',') if results['metadatas'] else []
                })

        return formatted
```

### 3. Enhance knowledge/service.py

Modify `find_relevant()` to use semantic search as fallback:

```python
def find_relevant(
    self,
    query: str,
    tags: Optional[List[str]] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find relevant Knowledge Objects.

    Strategy:
    1. Try tag-based search first (fast, exact matches)
    2. If < 3 results AND semantic search enabled: Use Chroma
    3. Merge results with deduplication by confidence
    """

    # Step 1: Tag-based search (existing implementation)
    tag_results = self._search_by_tags(query, tags, limit)

    # Step 2: Semantic search if needed
    if len(tag_results) < 3 and self.semantic_search_enabled:
        semantic_results = self.semantic_store.search(
            query=query,
            tags=tags or [],
            top_k=limit - len(tag_results)
        )
        # Merge results (avoid duplicates)
        tag_ids = {r['id'] for r in tag_results}
        for result in semantic_results:
            if result['id'] not in tag_ids:
                tag_results.append(result)

    return tag_results[:limit]
```

---

## Dependencies

**None** - This track is fully independent!

- Does NOT depend on Cost Tracking
- Does NOT depend on Langfuse
- Can be merged first without blocking other tracks

---

## Success Criteria

- [ ] All tests passing (TDD - write tests first!)
- [ ] ChromaKnowledgeStore implemented and working
- [ ] Hybrid search (semantic + tags) functional
- [ ] Performance: < 100ms for top-5 retrieval
- [ ] Backward compatible: Works with Chroma disabled
- [ ] Integration: `knowledge/service.py` enhanced
- [ ] Documentation: Docstrings on all public methods

---

## Performance Targets

- **Semantic Search Speed**: < 100ms for top-5 results
- **Memory Overhead**: < 50MB for typical KO collection
- **Discovery Improvement**: +20-30% relevant KOs found
- **Backward Compatibility**: Tag search works if Chroma unavailable

---

## Failure Scenarios & Recovery

**Scenario 1: Chroma not installed**
- Recovery: Gracefully degrade to tag-only search
- Detection: Try import, catch ImportError
- Fallback: Use existing tag_based search only

**Scenario 2: Embeddings model too slow (> 100ms)**
- Detection: Benchmark during startup
- Recovery: Disable semantic search if too slow
- Config: Set `enable_semantic_search = false`

**Scenario 3: Vector store corrupted**
- Detection: Chroma query returns no results
- Recovery: Rebuild collection from KO files
- Cleanup: Delete `.aibrain/chroma/` and reinitialize

---

## Environment Setup

No special environment variables needed. Chroma runs locally with:
- SQLite database (persistent, local-only)
- Sentence transformers embeddings (downloaded on first run, ~100MB)
- No external API keys required

---

## Completion Signal

When all tests passing and integration complete, output:

```
✅ CHROMA_SEMANTIC_SEARCH_COMPLETE

Implementation Status:
- Tests: 20/20 passing
- ChromaKnowledgeStore: Implemented
- Hybrid Search: Functional
- Performance: < 100ms
- Integration: knowledge/service.py enhanced
- Backward Compatible: Yes

Ready for merge. No iteration_loop.py changes needed.
```

---

## Session Workflow

1. **Create test file** (`tests/test_semantic_search.py`) - 30 minutes
2. **Write all tests FIRST** - 1 hour
3. **Create ChromaKnowledgeStore** (`knowledge/semantic_search.py`) - 2 hours
4. **Run tests** - watch them fail initially
5. **Implement to pass tests** - 2 hours
6. **Enhance knowledge/service.py** - 1 hour
7. **Benchmark performance** - 30 minutes
8. **Final testing** - 1 hour
9. **Commit and signal complete** - 15 minutes

**Total Time**: ~8 hours

---

## Notes

- This is a **standalone implementation** - no coordination needed with other tracks
- Tests must pass 100% before considering complete
- Backward compatibility is critical - system must work with Chroma disabled
- Performance must stay under 100ms, or semantic search is disabled automatically

Good luck! 🚀

---

**Execute via**: `claude --print "$(cat .aibrain/prompts/phase2b-2-chroma-semantic-search.md)"`
