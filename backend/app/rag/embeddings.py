import os
from typing import List, Any
from app.config import settings
from app.utils.logger import logger

class EmbeddingService:
    _instance = None
    _embedding_fn = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        try:
            from chromadb.utils import embedding_functions
            logger.info("Initializing ONNX all-MiniLM-L6-v2 embedding function for ChromaDB...")
            self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ONNX embedding function: {e}. Falling back to deterministic pseudo-embeddings.")
            self._embedding_fn = None

    def embed_query(self, text: str) -> List[float]:
        """Generates a 384-dimensional vector embedding for a query string."""
        if self._embedding_fn is not None:
            try:
                embeddings = self._embedding_fn([text])
                return embeddings[0]
            except Exception as e:
                logger.warning(f"Embedding error: {e}. Falling back.")
        return self._fallback_embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for multiple document chunks in batch."""
        if not texts:
            return []
        if self._embedding_fn is not None:
            try:
                return self._embedding_fn(texts)
            except Exception as e:
                logger.warning(f"Batch embedding error: {e}. Falling back.")
        return [self._fallback_embed(t) for t in texts]

    def _fallback_embed(self, text: str) -> List[float]:
        """Deterministic pseudo-embedding fallback for testing without external models."""
        import hashlib
        import math
        vec = []
        for i in range(384):
            seed = f"{text}_{i}".encode('utf-8')
            h = int(hashlib.md5(seed).hexdigest(), 16)
            val = (h % 2000 - 1000) / 1000.0
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def cosine_similarity(self, vec_a: Any, vec_b: Any) -> float:
        """Calculates cosine similarity between two normalized vectors."""
        import numpy as np
        try:
            a = np.asarray(vec_a, dtype=float)
            b = np.asarray(vec_b, dtype=float)
            if a.size == 0 or b.size == 0 or a.shape != b.shape:
                return 0.0
            dot = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(np.clip(dot / (norm_a * norm_b), -1.0, 1.0))
        except Exception:
            return 0.0


embedding_service = EmbeddingService()

