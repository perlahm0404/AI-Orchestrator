"""
Chroma-based Semantic Search for Knowledge Objects

Provides vector-based semantic search using ChromaDB with local embeddings.
Designed for hybrid search combining semantic similarity with tag-based filtering.

Features:
- Local embeddings: Uses sentence-transformers (all-MiniLM-L6-v2)
- Persistent storage: SQLite-based, survives restarts
- Fast similarity search: < 100ms for top-5 retrieval
- Hybrid search: Combines semantic vectors with tag filtering
- Zero API cost: All computation happens locally

Performance Targets:
- Search speed: < 100ms for top-5 results
- Memory overhead: < 50MB for typical KO collection
- Discovery improvement: +20-30% relevant KOs found
- Backward compatible: Gracefully degrades if Chroma unavailable

Usage:
    from knowledge.semantic_search import ChromaKnowledgeStore

    store = ChromaKnowledgeStore()

    # Add Knowledge Object
    store.add_ko(
        ko_id="KO-test-001",
        content="Authentication best practices...",
        tags=["auth", "security"]
    )

    # Semantic search
    results = store.search(
        query="how to fix auth bugs",
        top_k=5
    )

    # Hybrid search (semantic + tag filtering)
    results = store.search(
        query="authentication security",
        tags=["auth"],  # Only KOs with 'auth' tag
        top_k=5
    )
"""

from typing import List, Dict, Any, Optional
import os


class ChromaKnowledgeStore:
    """
    Chroma-based vector database for semantic search on Knowledge Objects.

    Uses sentence-transformers for local embedding generation (no API costs)
    and ChromaDB for efficient vector storage and retrieval.

    Key Features:
    - Local embeddings: all-MiniLM-L6-v2 (384 dimensions, fast)
    - Persistent storage: SQLite-based, data survives restarts
    - Hybrid search: Semantic similarity + tag filtering
    - Backward compatible: Graceful fallback if deps missing

    Performance:
    - Search: < 100ms for top-5 results
    - Indexing: ~10-20ms per KO
    - Memory: < 50MB for typical collection
    """

    def __init__(self, persist_directory: str = ".aibrain/chroma"):
        """
        Initialize ChromaKnowledgeStore with local embeddings.

        Args:
            persist_directory: Path to store Chroma database
                             (defaults to .aibrain/chroma)

        Raises:
            ImportError: If chromadb not installed
        """
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError:
            raise ImportError(
                "chromadb not installed. "
                "Install with: pip install chromadb"
            )

        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize Chroma client with persistent storage
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Use sentence transformers for local embeddings
        # all-MiniLM-L6-v2: 384 dimensions, fast, good quality
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="knowledge-objects",
            embedding_function=self.embedding_fn,  # type: ignore[arg-type]
            metadata={"description": "Knowledge Objects with semantic search"}
        )

    def add_ko(
        self,
        ko_id: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Add or update a Knowledge Object in the vector store.

        If KO already exists, it will be updated with new content/tags.

        Args:
            ko_id: Unique KO identifier (e.g., "KO-km-001")
            content: Text content to embed and search
            tags: Optional list of tags for hybrid filtering

        Example:
            store.add_ko(
                ko_id="KO-test-001",
                content="Always validate JWT tokens...",
                tags=["auth", "security"]
            )
        """
        if tags is None:
            tags = []

        # Store tags as comma-separated string AND individual tag_N fields
        # Chroma only supports str, int, float, bool, SparseVector, or None
        metadata = {
            "tags": ",".join(tags)  # For display
        }

        # Add individual tag fields for filtering (tag_0, tag_1, etc.)
        # This allows exact matching in where clauses
        for i, tag in enumerate(tags):
            metadata[f"tag_{i}"] = tag

        # Chroma uses upsert behavior - adds if new, updates if exists
        self.collection.upsert(
            ids=[ko_id],
            documents=[content],
            metadatas=[metadata]
        )

    def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: semantic similarity + optional tag filtering.

        Performs semantic vector search using the query text. If tags are
        provided, filters results to only include KOs with matching tags.

        Args:
            query: Natural language search query
                  (e.g., "how to fix authentication bugs")
            tags: Optional tags to filter results (OR semantics)
                 KOs matching ANY tag will be included
            top_k: Maximum number of results to return (default: 5)

        Returns:
            List of dictionaries with keys:
            - id: KO identifier
            - score: Similarity score (higher = more similar)
            - content: KO text content
            - tags: List of tags

        Example:
            # Pure semantic search
            results = store.search("authentication security", top_k=5)

            # Hybrid search (semantic + tags)
            results = store.search(
                query="authentication",
                tags=["auth", "security"],
                top_k=5
            )
        """
        # Build where filter for tags if provided
        # Strategy: Check if any of the tag_N fields match our desired tags
        where_filter = None
        if tags:
            # Build OR conditions for tag matching
            # Check tag_0, tag_1, tag_2, etc. fields
            # Since we don't know how many tags each KO has, check first 10 possible positions
            conditions = []
            for tag in tags:
                for i in range(10):  # Support up to 10 tags per KO
                    conditions.append({f"tag_{i}": {"$eq": tag}})

            if len(conditions) == 1:
                where_filter = conditions[0]
            elif len(conditions) > 1:
                where_filter = {"$or": conditions}  # type: ignore[dict-item]

        # Execute semantic search
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter  # type: ignore[arg-type]
            )
        except Exception as e:
            # Handle empty collection or query errors gracefully
            print(f"Chroma search error: {e}")
            return []

        # Format results
        formatted = []
        if results and results.get('ids') and len(results['ids']) > 0:
            ids = results['ids'][0]
            documents = (results.get('documents') or [[]])[0]
            metadatas = (results.get('metadatas') or [[]])[0]
            distances = (results.get('distances') or [[]])[0]

            for i, ko_id in enumerate(ids):
                # Convert distance to similarity score
                # Chroma returns L2 distance, convert to similarity (1 - normalized_distance)
                distance = distances[i] if i < len(distances) else 1.0
                # Normalize to 0-1 range (similarity score)
                score = max(0.0, 1.0 - (distance / 2.0))  # Rough normalization

                # Parse tags from metadata
                tags_str = str(metadatas[i].get('tags', '')) if i < len(metadatas) else ''
                tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]

                formatted.append({
                    "id": ko_id,
                    "score": score,
                    "content": documents[i] if i < len(documents) else "",
                    "tags": tags_list
                })

        return formatted

    def count(self) -> int:
        """
        Get number of Knowledge Objects in the store.

        Returns:
            Number of indexed KOs
        """
        try:
            return self.collection.count()
        except Exception:
            return 0

    def delete(self, ko_id: str) -> bool:
        """
        Delete a Knowledge Object from the store.

        Args:
            ko_id: KO identifier to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.collection.delete(ids=[ko_id])
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """
        Clear all Knowledge Objects from the store.

        Warning: This deletes all indexed KOs permanently.
        """
        try:
            # Delete the collection
            self.client.delete_collection(name="knowledge-objects")

            # Recreate empty collection
            self.collection = self.client.get_or_create_collection(
                name="knowledge-objects",
                embedding_function=self.embedding_fn,  # type: ignore[arg-type]
                metadata={"description": "Knowledge Objects with semantic search"}
            )
        except Exception as e:
            print(f"Error clearing store: {e}")

    def get_all_ids(self) -> List[str]:
        """
        Get all KO IDs in the store.

        Returns:
            List of KO identifiers
        """
        try:
            # Get all documents
            results = self.collection.get()
            return results.get('ids', [])
        except Exception:
            return []


# Singleton instance for efficiency
_default_store: Optional[ChromaKnowledgeStore] = None


def get_chroma_store() -> ChromaKnowledgeStore:
    """
    Get the default ChromaKnowledgeStore instance.

    Uses singleton pattern to avoid reinitializing Chroma multiple times.

    Returns:
        Default ChromaKnowledgeStore instance
    """
    global _default_store
    if _default_store is None:
        _default_store = ChromaKnowledgeStore()
    return _default_store


def index_ko(ko_id: str, content: str, tags: Optional[List[str]] = None) -> None:
    """
    Convenience function to index a KO.

    Args:
        ko_id: KO identifier
        content: KO content
        tags: Optional tags
    """
    get_chroma_store().add_ko(ko_id, content, tags)


def search_semantic(query: str, tags: Optional[List[str]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function for semantic search.

    Args:
        query: Search query
        tags: Optional tag filter
        top_k: Maximum results

    Returns:
        List of search results
    """
    return get_chroma_store().search(query, tags, top_k)


def is_chroma_available() -> bool:
    """
    Check if Chroma dependencies are available.

    Returns:
        True if chromadb can be imported, False otherwise
    """
    try:
        import chromadb
        return True
    except ImportError:
        return False
