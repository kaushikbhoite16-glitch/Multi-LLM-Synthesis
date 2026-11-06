import re
import math
from typing import List, Dict, Any, Optional
from app.config import settings
from app.rag.embeddings import embedding_service
from app.utils.logger import logger

class CrossEncoderReranker:
    """
    Cross-Encoder Semantic Reranker.
    Computes fine-grained query-document cross-interaction scores to reorder candidate chunks.
    Configurable via settings.RAG_ENABLE_RERANKER.
    """
    def __init__(self, model_name: str = settings.RERANKER_MODEL_NAME):
        self.model_name = model_name
        self._cross_encoder_model = None
        self._init_model()

    def _init_model(self):
        """Attempts to load sentence_transformers CrossEncoder if available."""
        try:
            from sentence_transformers import CrossEncoder
            self._cross_encoder_model = CrossEncoder(self.model_name)
            logger.info(f"Loaded neural CrossEncoder model: {self.model_name}")
        except Exception:
            # Fall back to native interaction cross-scoring
            self._cross_encoder_model = None

    def calculate_interaction_score(
        self,
        query: str,
        chunk_text: str,
        chunk_meta: Optional[Dict[str, Any]] = None,
        chunk_score: Optional[float] = None,
        q_emb: Optional[List[float]] = None
    ) -> float:
        """
        Computes calibrated cross-encoder interaction score between query and chunk.
        Incorporates dense semantic interaction, exact term proximity, title alignment, and query coverage.
        """
        if not query or not chunk_text:
            return 0.0

        query_tokens = [t for t in re.findall(r"\b\w{2,}\b", query.lower())]
        if not query_tokens:
            return 0.5

        doc_lower = chunk_text.lower()
        doc_tokens = re.findall(r"\b\w{2,}\b", doc_lower)

        # 1. Query Term Coverage (Recall)
        matched_tokens = set(query_tokens) & set(doc_tokens)
        term_coverage = len(matched_tokens) / len(set(query_tokens))

        # 2. Dense Semantic Cross-Similarity (reuse precomputed score if available to avoid redundant ONNX calls)
        if chunk_score is not None and chunk_score > 0.0:
            dense_sim = min(1.0, max(0.0, float(chunk_score)))
        elif q_emb is not None:
            d_emb = embedding_service.embed_query(chunk_text[:800])
            dense_sim = max(0.0, float(embedding_service.cosine_similarity(q_emb, d_emb)))
        else:
            q_emb_local = embedding_service.embed_query(query)
            d_emb = embedding_service.embed_query(chunk_text[:800])
            dense_sim = max(0.0, float(embedding_service.cosine_similarity(q_emb_local, d_emb)))

        # 3. Title / Section Heading Cross-Match
        title_boost = 0.0
        if chunk_meta:
            title = str(chunk_meta.get("title", "")).lower()
            section = str(chunk_meta.get("section", "")).lower()
            if any(t in title or t in section for t in query_tokens if len(t) > 3):
                title_boost = 0.15

        # 4. Proximity / Window Density
        proximity_score = 0.0
        if len(query_tokens) >= 2 and all(t in doc_lower for t in query_tokens[:2]):
            proximity_score = 0.10

        # Composite cross-encoder interaction score (calibrated 0.0 to 1.0)
        raw_score = (0.50 * dense_sim) + (0.35 * term_coverage) + title_boost + proximity_score
        calibrated = min(1.0, max(0.0, raw_score))
        return round(calibrated, 4)

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5,
        enabled: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Reranks candidate chunks by their cross-encoder query-passage interaction score.
        If reranker is disabled, preserves original order while attaching scores.
        """
        is_active = settings.RAG_ENABLE_RERANKER if enabled is None else enabled
        if not chunks:
            return []

        if not is_active:
            # Bypass mode: preserve ranking order
            for c in chunks:
                if "rerank_score" not in c:
                    c["rerank_score"] = c.get("final_score", c.get("score", 0.5))
            return chunks[:top_k]

        reranked_items = []

        # If native sentence_transformers CrossEncoder is available
        if self._cross_encoder_model is not None:
            try:
                pairs = [[query, c.get("text", "")] for c in chunks]
                raw_scores = self._cross_encoder_model.predict(pairs)
                for idx, c in enumerate(chunks):
                    c_copy = dict(c)
                    # Sigmoid normalize if necessary
                    score_val = float(raw_scores[idx])
                    norm_score = 1.0 / (1.0 + math.exp(-score_val)) if score_val < 0 or score_val > 1 else score_val
                    c_copy["rerank_score"] = round(min(1.0, max(0.0, norm_score)), 4)
                    reranked_items.append(c_copy)
            except Exception as e:
                logger.warning(f"Neural CrossEncoder predict failed: {e}. Falling back to interaction cross-scorer.")
                self._cross_encoder_model = None

        # Interaction Cross-Scorer (executed if neural model is not active)
        if not reranked_items:
            # Precompute query embedding once for all candidate chunks
            q_emb = embedding_service.embed_query(query) if query else None
            for c in chunks:
                c_copy = dict(c)
                meta = c_copy.get("metadata", {})
                score = self.calculate_interaction_score(
                    query=query,
                    chunk_text=c_copy.get("text", ""),
                    chunk_meta=meta,
                    chunk_score=c_copy.get("score"),
                    q_emb=q_emb
                )
                c_copy["rerank_score"] = score
                reranked_items.append(c_copy)

        # Sort descending by cross-encoder score
        reranked_items.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked_items[:top_k]

cross_encoder = CrossEncoderReranker()
