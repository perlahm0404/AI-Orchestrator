"""
Test Vector Search Components

Tests for:
- knowledge/embeddings.py - Local embedding generation
- knowledge/vector_store.py - LanceDB vector storage
- knowledge/service.py - Hybrid search
"""

import tempfile
import shutil
from pathlib import Path

import pytest


class TestKnowledgeEmbedder:
    """Tests for local embedding generation."""

    def test_embedder_initialization(self):
        """Test embedder initializes with lazy loading."""
        from knowledge.embeddings import KnowledgeEmbedder

        embedder = KnowledgeEmbedder()
        # Model should not be loaded yet
        assert embedder._model is None

    def test_embed_single_text(self):
        """Test embedding a single text."""
        from knowledge.embeddings import KnowledgeEmbedder

        embedder = KnowledgeEmbedder()
        text = "This is a test sentence for embedding."

        embedding = embedder.embed(text)

        # Should return a list of floats
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # MiniLM produces 384-dim vectors
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_batch(self):
        """Test embedding multiple texts."""
        from knowledge.embeddings import KnowledgeEmbedder

        embedder = KnowledgeEmbedder()
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]

        embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_similarity_calculation(self):
        """Test cosine similarity between embeddings."""
        from knowledge.embeddings import KnowledgeEmbedder

        embedder = KnowledgeEmbedder()

        # Similar texts should have high similarity
        text1 = "The quick brown fox jumps over the lazy dog."
        text2 = "A fast brown fox leaps over a sleepy dog."
        text3 = "Python is a programming language."

        emb1 = embedder.embed(text1)
        emb2 = embedder.embed(text2)
        emb3 = embedder.embed(text3)

        sim_12 = embedder.similarity(emb1, emb2)
        sim_13 = embedder.similarity(emb1, emb3)

        # Similar sentences should have higher similarity
        assert sim_12 > sim_13
        assert sim_12 > 0.5  # Should be reasonably similar
        assert sim_13 < 0.5  # Should be less similar


class TestKOVectorStore:
    """Tests for LanceDB vector storage."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir) / "test_vectors"
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_store_initialization(self, temp_db_path):
        """Test vector store initializes correctly."""
        from knowledge.vector_store import KOVectorStore

        store = KOVectorStore(db_path=temp_db_path)
        assert store is not None

    def test_index_and_search(self, temp_db_path):
        """Test indexing and searching vectors."""
        from knowledge.vector_store import KOVectorStore
        from knowledge.embeddings import KnowledgeEmbedder

        store = KOVectorStore(db_path=temp_db_path)
        embedder = KnowledgeEmbedder()

        # Index some test data
        texts = [
            ("ko1", "Authentication and login system"),
            ("ko2", "Database schema and migrations"),
            ("ko3", "User interface components"),
            ("ko4", "API endpoint security"),
        ]

        for ko_id, text in texts:
            embedding = embedder.embed(text)
            store.index_ko(
                ko_id=ko_id,
                embedding=embedding,
                metadata={"text": text, "project": "test"}
            )

        # Search for security-related content
        query = "security and authentication"
        query_embedding = embedder.embed(query)

        results = store.search(query_embedding, top_k=2)

        assert len(results) <= 2
        # Security/auth related items should rank higher
        result_ids = [r.ko_id for r in results]
        assert "ko1" in result_ids or "ko4" in result_ids

    def test_delete_ko(self, temp_db_path):
        """Test deleting a KO from the store."""
        from knowledge.vector_store import KOVectorStore
        from knowledge.embeddings import KnowledgeEmbedder

        store = KOVectorStore(db_path=temp_db_path)
        embedder = KnowledgeEmbedder()

        # Index a KO
        embedding = embedder.embed("Test content")
        store.index_ko("test_ko", embedding, {"text": "Test"})

        # Verify it exists
        results = store.search(embedding, top_k=1)
        assert len(results) == 1
        assert results[0].ko_id == "test_ko"

        # Delete it
        store.delete("test_ko")

        # Should not find it anymore (or find with very low score)
        results = store.search(embedding, top_k=1)
        if results:
            assert results[0].ko_id != "test_ko"


class TestHybridSearch:
    """Tests for hybrid search in knowledge service."""

    @pytest.fixture
    def temp_ko_dir(self):
        """Create temporary KO directory with test files."""
        temp_dir = tempfile.mkdtemp()
        ko_dir = Path(temp_dir) / "knowledge_objects"
        ko_dir.mkdir(parents=True)

        # Create test KO files
        ko1 = ko_dir / "auth_patterns.md"
        ko1.write_text("""---
tags: [authentication, security, patterns]
project: test
---
# Authentication Patterns
Best practices for user authentication.
""")

        ko2 = ko_dir / "database_design.md"
        ko2.write_text("""---
tags: [database, schema, design]
project: test
---
# Database Design
Guidelines for database schema design.
""")

        ko3 = ko_dir / "api_security.md"
        ko3.write_text("""---
tags: [api, security, endpoints]
project: test
---
# API Security
Securing REST API endpoints.
""")

        yield ko_dir
        shutil.rmtree(temp_dir, ignore_errors=True)


# Quick sanity test that can run standalone
def test_quick_embedding():
    """Quick sanity test for embeddings."""
    from knowledge.embeddings import KnowledgeEmbedder

    embedder = KnowledgeEmbedder()
    result = embedder.embed("Hello world")

    assert len(result) == 384
    print(f"✓ Embedding generated: {len(result)} dimensions")
    print(f"✓ Sample values: {result[:5]}")


def test_quick_vector_store():
    """Quick sanity test for vector store."""
    from knowledge.vector_store import KOVectorStore
    from knowledge.embeddings import KnowledgeEmbedder

    temp_dir = tempfile.mkdtemp()
    try:
        store = KOVectorStore(db_path=Path(temp_dir) / "test_db")
        embedder = KnowledgeEmbedder()

        # Index
        emb = embedder.embed("Test content about authentication")
        store.index_ko("test1", emb, {"text": "auth test"})

        # Search
        query_emb = embedder.embed("authentication")
        results = store.search(query_emb, top_k=1)

        assert len(results) == 1
        print(f"✓ Vector store working: found {results[0].ko_id}")
        print(f"✓ Similarity score: {results[0].score:.4f}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_hybrid_search_available():
    """Test that hybrid search components are available."""
    from knowledge.service import _check_semantic_available

    result = _check_semantic_available()
    assert result is True, "Semantic search should be available"
    print("✓ Hybrid search dependencies available")


def test_rerank_function():
    """Test the semantic re-ranking function."""
    from knowledge.service import _rerank_by_semantic, KnowledgeObject

    # Create test KOs
    kos = [
        KnowledgeObject(
            id="ko1", project="test", title="Authentication Bug",
            what_was_learned="Always validate tokens", why_it_matters="Security",
            prevention_rule="Add token validation", tags=["auth"],
            status="approved", created_at="2025-01-01"
        ),
        KnowledgeObject(
            id="ko2", project="test", title="Database Optimization",
            what_was_learned="Use indexes", why_it_matters="Performance",
            prevention_rule="Add indexes", tags=["database"],
            status="approved", created_at="2025-01-01"
        ),
    ]

    # Re-rank with auth-related query
    reranked = _rerank_by_semantic(kos, "authentication token validation", top_k=2)

    assert len(reranked) == 2
    # Auth-related KO should be first after re-ranking
    assert reranked[0].id == "ko1"
    print("✓ Semantic re-ranking working correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("Vector Search Component Tests")
    print("=" * 60)

    print("\n1. Testing Embeddings...")
    test_quick_embedding()

    print("\n2. Testing Vector Store...")
    test_quick_vector_store()

    print("\n3. Testing Hybrid Search...")
    test_hybrid_search_available()

    print("\n4. Testing Semantic Re-ranking...")
    test_rerank_function()

    print("\n" + "=" * 60)
    print("All quick tests passed! ✓")
    print("=" * 60)
    print("\nRun 'pytest tests/test_vector_search.py -v' for full test suite.")
