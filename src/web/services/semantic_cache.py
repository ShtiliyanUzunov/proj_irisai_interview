"""
Semantic cache using sentence-transformers embeddings and cosine similarity.

When a new request comes for computation:
1. Compute the embedding for the input text.
2. Compare against all stored embeddings via cosine similarity.
3. If similarity >= threshold, return the cached result (skip prediction).
4. Otherwise, return None (cache miss) — the caller stores the result after prediction.
"""
import logging
import threading

import numpy as np

logger = logging.getLogger("services.semantic_cache")


class SemanticCache:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.95) -> None:
        self._lock = threading.Lock()
        self._embeddings = []   # list of np.ndarray (1-D vectors)
        self._results = []      # list of dicts (prediction results)
        self._threshold = threshold
        self._model = None
        self._model_name = model_name

        logger.info(
            "SemanticCache initialized (model=%s, threshold=%.2f)",
            model_name,
            threshold,
        )

    def _ensure_model(self) -> None:
        """Lazy-load the sentence-transformers model on first use."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded")

    def eager_load(self) -> None:
        """Force-load the embedding model immediately."""
        self._ensure_model()

    def _compute_embedding(self, text: str) -> np.ndarray:
        self._ensure_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        # Normalize to unit vector for cosine similarity via dot product
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        # Both vectors are already normalized, so dot product = cosine similarity
        return float(np.dot(a, b))

    def lookup(self, text: str) -> dict | None:
        """
        Check if a semantically similar text has been cached.

        Returns the cached result dict if a match is found, or None on cache miss.
        """
        embedding = self._compute_embedding(text)

        with self._lock:
            if not self._embeddings:
                return None

            best_sim = -1.0
            best_idx = -1
            for idx, stored_emb in enumerate(self._embeddings):
                sim = self._cosine_similarity(embedding, stored_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_idx = idx

            if best_sim >= self._threshold:
                logger.debug("Cache hit (similarity=%.4f, threshold=%.2f)", best_sim, self._threshold)
                return self._results[best_idx]

        logger.debug("Cache miss (best_similarity=%.4f, threshold=%.2f)", best_sim, self._threshold)
        return None

    def store(self, text: str, result: dict) -> None:
        """Store an embedding + result pair in the cache."""
        embedding = self._compute_embedding(text)

        with self._lock:
            self._embeddings.append(embedding)
            self._results.append(result)

        logger.debug("Cached new entry (total=%d)", len(self._embeddings))
