"""
Local Embeddings for Knowledge Objects

Uses sentence-transformers for local embedding generation.
Zero API cost - all computation happens locally.

Model: all-MiniLM-L6-v2 (22M parameters, fast)
- 384 dimensional embeddings
- ~100 embeddings/second on CPU
- Works well for semantic similarity

Token Optimization:
- Local embeddings = 0 token cost
- Lazy model loading (only load when semantic search used)
- Batch processing for efficiency

Usage:
    from knowledge.embeddings import KnowledgeEmbedder

    embedder = KnowledgeEmbedder()  # Model loaded lazily

    # Generate embedding for a single text
    embedding = embedder.embed("How to fix auth bugs")

    # Batch embedding for efficiency
    embeddings = embedder.embed_batch([
        "Auth null check failure",
        "Database connection timeout",
        "API rate limiting issue"
    ])

    # Compute similarity
    similarity = embedder.similarity(embedding1, embedding2)
"""

from typing import List, Optional, Union
import numpy as np


class KnowledgeEmbedder:
    """
    Local embedding generator using sentence-transformers.

    Key Features:
    - Lazy loading: Model only loaded when first embedding requested
    - Zero API cost: All computation local
    - Fast: ~100 embeddings/second on CPU
    - Compact: 384-dimensional vectors

    Uses all-MiniLM-L6-v2 by default:
    - 22M parameters
    - 384 dimensions
    - Trained on 1B sentence pairs
    - Good balance of speed and quality
    """

    # Default model - small, fast, and effective
    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None  # "cpu", "cuda", or None (auto)
    ):
        """
        Initialize embedder with lazy model loading.

        Args:
            model_name: HuggingFace model name for sentence-transformers
            device: Device to run model on ("cpu", "cuda", or None for auto)
        """
        self._model_name = model_name
        self._device = device
        self._model = None  # Lazy loaded

    @property
    def model(self):
        """
        Get the sentence-transformer model, loading if necessary.

        Lazy loading saves ~2-3 seconds startup time when embeddings
        aren't needed (e.g., tag-only searches).
        """
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self._model_name,
                    device=self._device
                )
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension (384 for MiniLM)."""
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str, normalize: bool = True) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            normalize: Whether to L2-normalize the embedding (recommended for cosine similarity)

        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )
        return embedding.tolist()

    def embed_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        More efficient than calling embed() multiple times due to
        batched processing.

        Args:
            texts: List of texts to embed
            normalize: Whether to L2-normalize embeddings
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar

        Returns:
            List of embeddings (each is a list of floats)
        """
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=show_progress
        )
        return [e.tolist() for e in embeddings]

    def similarity(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score (0-1 for normalized embeddings)
        """
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_most_similar(
        self,
        query_embedding: Union[List[float], np.ndarray],
        candidate_embeddings: List[Union[List[float], np.ndarray]],
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar embeddings to a query.

        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return

        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)

        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            if isinstance(candidate, list):
                candidate = np.array(candidate)
            sim = self.similarity(query_embedding, candidate)
            similarities.append((i, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def embed_ko(self, ko_content: str, ko_title: str = "", ko_tags: List[str] = None) -> List[float]:
        """
        Generate embedding optimized for Knowledge Object search.

        Combines title, tags, and content for better retrieval.

        Args:
            ko_content: Main KO content (what_was_learned, prevention_rule)
            ko_title: KO title
            ko_tags: KO tags

        Returns:
            Embedding for the KO
        """
        # Combine KO fields for embedding
        tags_str = ", ".join(ko_tags) if ko_tags else ""
        combined = f"{ko_title}\n{tags_str}\n{ko_content}"

        return self.embed(combined)


# Singleton instance for efficiency
_default_embedder: Optional[KnowledgeEmbedder] = None


def get_embedder() -> KnowledgeEmbedder:
    """
    Get the default embedder instance.

    Uses singleton pattern to avoid loading model multiple times.
    """
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = KnowledgeEmbedder()
    return _default_embedder


def embed_text(text: str) -> List[float]:
    """Convenience function to embed a single text."""
    return get_embedder().embed(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convenience function to embed multiple texts."""
    return get_embedder().embed_batch(texts)
