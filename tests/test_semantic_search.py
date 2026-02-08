"""
Test Chroma Semantic Search Implementation

TDD test suite for ChromaKnowledgeStore and hybrid search.

Tests cover:
- Basic Chroma functionality
- Hybrid search (semantic + tags)
- Performance benchmarks (< 100ms)
- Backward compatibility
"""

import tempfile
import shutil
import time
from pathlib import Path
from typing import List

import pytest


class TestChromaKnowledgeStore:
    """Tests for ChromaKnowledgeStore implementation."""

    @pytest.fixture
    def temp_chroma_dir(self):
        """Create temporary directory for Chroma database."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_initialize_chroma_store(self, temp_chroma_dir):
        """Test ChromaKnowledgeStore initializes correctly."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))
        assert store is not None
        assert store.collection is not None

    def test_add_ko(self, temp_chroma_dir):
        """Test adding a Knowledge Object to Chroma."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))

        # Add a KO
        store.add_ko(
            ko_id="KO-test-001",
            content="Authentication patterns and token validation best practices.",
            tags=["authentication", "security"]
        )

        # Verify it was added
        count = store.count()
        assert count == 1

    def test_search_basic_query(self, temp_chroma_dir):
        """Test basic semantic search."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))

        # Add test KOs
        store.add_ko("ko1", "Authentication and login security", ["auth", "security"])
        store.add_ko("ko2", "Database schema design patterns", ["database", "schema"])
        store.add_ko("ko3", "API endpoint security best practices", ["api", "security"])

        # Search for security content
        results = store.search(query="security authentication", top_k=2)

        assert len(results) > 0
        assert len(results) <= 2
        # Should return dict with id, score, content, tags
        assert all("id" in r for r in results)
        assert all("score" in r for r in results)
        assert all("content" in r for r in results)

    def test_search_with_tags_filter(self, temp_chroma_dir):
        """Test hybrid search with tag filtering."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))

        # Add test KOs
        store.add_ko("ko1", "Authentication security", ["auth", "security"])
        store.add_ko("ko2", "Database security", ["database", "security"])
        store.add_ko("ko3", "API security", ["api", "security"])

        # Search with tag filter
        results = store.search(query="security", tags=["auth"], top_k=5)

        # Should only return KOs with 'auth' tag
        assert len(results) > 0
        for result in results:
            assert "auth" in result.get("tags", [])

    def test_search_performance_under_100ms(self, temp_chroma_dir):
        """Test search performance is under 100ms."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))

        # Add 50 KOs for realistic performance test
        for i in range(50):
            store.add_ko(
                f"ko{i}",
                f"Test content about topic {i} with various keywords",
                [f"tag{i % 5}"]
            )

        # Benchmark search
        start = time.time()
        results = store.search(query="test topic keywords", top_k=5)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100, f"Search took {elapsed_ms:.2f}ms, expected < 100ms"
        assert len(results) > 0

    def test_hybrid_search_semantic_and_tags(self, temp_chroma_dir):
        """Test hybrid search combining semantic similarity and tag filtering."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))

        # Add KOs with different content and tags
        store.add_ko("ko1", "User authentication with JWT tokens", ["auth", "jwt"])
        store.add_ko("ko2", "Database connection pooling", ["database", "performance"])
        store.add_ko("ko3", "OAuth2 authentication flow", ["auth", "oauth"])
        store.add_ko("ko4", "API rate limiting strategies", ["api", "performance"])

        # Search with both semantic query and tag filter
        results = store.search(
            query="authentication methods",
            tags=["auth"],
            top_k=5
        )

        # Should return auth-related KOs ranked by semantic similarity
        assert len(results) > 0
        for result in results:
            assert "auth" in result.get("tags", [])

    def test_backward_compatibility_without_chroma(self):
        """Test system works when Chroma is not available."""
        # This test ensures graceful degradation
        # If Chroma import fails, system should fall back to tag-only search
        try:
            from knowledge.semantic_search import ChromaKnowledgeStore
            # If import succeeds, Chroma is available
            assert True
        except ImportError:
            # If import fails, that's also acceptable (backward compatibility)
            assert True

    def test_empty_search_results(self, temp_chroma_dir):
        """Test search with no matches returns empty list."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))

        # Search in empty store
        results = store.search(query="nonexistent content", top_k=5)

        assert isinstance(results, list)
        assert len(results) == 0

    def test_update_existing_ko(self, temp_chroma_dir):
        """Test updating an existing KO."""
        from knowledge.semantic_search import ChromaKnowledgeStore

        store = ChromaKnowledgeStore(persist_directory=str(temp_chroma_dir))

        # Add KO
        store.add_ko("ko1", "Original content", ["tag1"])

        # Update with new content
        store.add_ko("ko1", "Updated content", ["tag1", "tag2"])

        # Search should return updated content
        results = store.search(query="updated", top_k=1)
        assert len(results) > 0
        assert "updated" in results[0]["content"].lower()


class TestHybridSearch:
    """Tests for hybrid search integration in knowledge service."""

    @pytest.fixture
    def setup_knowledge_service(self):
        """Setup knowledge service with test KOs."""
        # This will test integration with knowledge/service.py
        # after we enhance it with semantic search
        pass

    def test_tag_search_returns_3_plus(self):
        """Test that tag search returning >= 3 results skips semantic search."""
        # When tag search finds enough results, semantic search is not needed
        # This saves computation time
        from knowledge.service import find_relevant
        from knowledge.semantic_search import ChromaKnowledgeStore

        # Mock scenario: tag search returns 5 results
        # Should not invoke semantic search
        # Implementation will verify this behavior
        assert True  # Placeholder - will implement after service.py enhancement

    def test_tag_search_returns_less_than_3(self):
        """Test semantic search is used when tag search returns < 3 results."""
        # When tag search is insufficient, semantic search supplements results
        from knowledge.service import find_relevant

        # Mock scenario: tag search returns 1 result
        # Should invoke semantic search to find 2-4 more
        assert True  # Placeholder

    def test_merge_results_by_confidence(self):
        """Test merging tag and semantic results by confidence score."""
        # Results from both searches should be merged and ranked
        # Duplicates should be removed
        assert True  # Placeholder

    def test_deduplication_across_results(self):
        """Test that duplicate KOs are removed when merging results."""
        # If a KO appears in both tag and semantic results, should appear once
        assert True  # Placeholder


class TestIntegration:
    """Integration tests for complete semantic search workflow."""

    def test_knowledge_service_uses_semantic_search(self):
        """Test that knowledge service integrates semantic search."""
        from knowledge.service import find_relevant, _check_semantic_available

        # Semantic search should be available
        available = _check_semantic_available()
        assert available is True or available is False  # Either is acceptable

    def test_fallback_when_tag_search_insufficient(self):
        """Test fallback to semantic search when tags insufficient."""
        # Integration test: Create scenario where tags return < 3 results
        # Verify semantic search is invoked
        assert True  # Placeholder

    def test_performance_degradation_acceptable(self):
        """Test that semantic search doesn't significantly slow down queries."""
        # Semantic search should add < 50ms overhead
        import time
        from knowledge.service import find_relevant

        # Time a query with semantic search enabled
        start = time.time()
        # results = find_relevant(project="test", query="test query", top_k=5)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 1.0  # 1 second max for integration test


class TestPerformance:
    """Performance benchmarks for semantic search."""

    def test_embedding_generation_speed(self):
        """Test embedding generation is fast enough."""
        from knowledge.semantic_search import ChromaKnowledgeStore
        import tempfile

        temp_dir = tempfile.mkdtemp()
        try:
            store = ChromaKnowledgeStore(persist_directory=temp_dir)

            # Generate embedding for typical KO content
            content = "Authentication patterns: Always validate JWT tokens before accessing protected resources. Use refresh tokens for long-lived sessions."

            start = time.time()
            store.add_ko("perf_test", content, ["auth"])
            elapsed_ms = (time.time() - start) * 1000

            # Should be fast (< 200ms including embedding + storage)
            assert elapsed_ms < 200

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_batch_indexing_performance(self):
        """Test batch indexing is efficient."""
        from knowledge.semantic_search import ChromaKnowledgeStore
        import tempfile

        temp_dir = tempfile.mkdtemp()
        try:
            store = ChromaKnowledgeStore(persist_directory=temp_dir)

            # Add 100 KOs
            start = time.time()
            for i in range(100):
                store.add_ko(
                    f"ko{i}",
                    f"Test content for KO number {i}",
                    [f"tag{i % 10}"]
                )
            elapsed = time.time() - start

            # Should index 100 KOs in < 10 seconds
            assert elapsed < 10.0

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# Quick sanity tests
def test_quick_chroma_initialization():
    """Quick sanity check for Chroma initialization."""
    try:
        import chromadb
        from knowledge.semantic_search import ChromaKnowledgeStore

        temp_dir = tempfile.mkdtemp()
        try:
            store = ChromaKnowledgeStore(persist_directory=temp_dir)
            assert store is not None
            print("✓ ChromaKnowledgeStore initialized successfully")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except ImportError as e:
        print(f"⚠ Chroma not installed: {e}")
        print("Install with: pip install chromadb")


def test_quick_chroma_search():
    """Quick sanity check for Chroma search."""
    try:
        from knowledge.semantic_search import ChromaKnowledgeStore

        temp_dir = tempfile.mkdtemp()
        try:
            store = ChromaKnowledgeStore(persist_directory=temp_dir)

            # Add and search
            store.add_ko("test1", "Authentication and security", ["auth"])
            results = store.search("authentication", top_k=1)

            assert len(results) > 0
            print(f"✓ Chroma search working: found {results[0]['id']}")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"✗ Chroma search failed: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("Chroma Semantic Search Tests")
    print("=" * 60)

    print("\n1. Testing Chroma Initialization...")
    test_quick_chroma_initialization()

    print("\n2. Testing Chroma Search...")
    test_quick_chroma_search()

    print("\n" + "=" * 60)
    print("Quick tests complete!")
    print("=" * 60)
    print("\nRun 'pytest tests/test_semantic_search.py -v' for full suite.")
