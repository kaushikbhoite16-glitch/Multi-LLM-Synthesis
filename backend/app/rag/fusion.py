import re
from typing import List, Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger

# Source authority weights
SOURCE_AUTHORITY_WEIGHTS = {
    "academic": 1.15,
    "academic_knowledge": 1.15,
    "general": 1.05,
    "general_knowledge": 1.05,
    "dynamic_web": 0.95,
    "dynamic_web_cache": 0.95,
    "default": 1.0
}

def get_source_authority_weight(source_type: str, metadata: Optional[Dict[str, Any]] = None) -> float:
    base = SOURCE_AUTHORITY_WEIGHTS.get(source_type.lower(), 1.0)
    if metadata:
        url = str(metadata.get("url", "")).lower()
        if ".edu" in url or ".gov" in url or "arxiv.org" in url or "doi.org" in url:
            base = max(base, 1.15)
        elif "wikipedia.org" in url or "python.org" in url or "docs." in url:
            base = max(base, 1.05)
    return base

def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    weights: Optional[List[float]] = None,
    k: int = settings.RAG_RRF_K
) -> List[Dict[str, Any]]:
    """
    Applies Reciprocal Rank Fusion (RRF) over multiple ranked retrieval lists.
    Formula: RRF_score(d) = SUM_i ( weight_i / (k + rank_i(d)) )
    """
    if not ranked_lists:
        return []

    if weights is None or len(weights) != len(ranked_lists):
        weights = [1.0] * len(ranked_lists)

    chunk_map: Dict[str, Dict[str, Any]] = {}
    rrf_scores: Dict[str, float] = {}

    for list_idx, result_list in enumerate(ranked_lists):
        w = weights[list_idx]
        for rank, item in enumerate(result_list, start=1):
            chunk_id = item.get("chunk_id") or item.get("id") or str(hash(item.get("text", "")[:100]))
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = dict(item)
                rrf_scores[chunk_id] = 0.0

            rrf_scores[chunk_id] += w / (k + rank)

    # Sort chunks by accumulated RRF score descending
    sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

    max_rrf = rrf_scores[sorted_chunk_ids[0]] if sorted_chunk_ids else 1.0
    if max_rrf <= 0:
        max_rrf = 1.0

    merged = []
    for cid in sorted_chunk_ids:
        chunk = chunk_map[cid]
        # Normalize RRF score between 0.0 and 1.0
        normalized_rrf = min(1.0, rrf_scores[cid] / max_rrf)
        chunk["rrf_score"] = round(normalized_rrf, 4)
        merged.append(chunk)

    return merged

def deduplicate_chunks(chunks: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Deduplicates chunks based on chunk_id and lexical 5-gram Jaccard similarity.
    """
    seen_ids = set()
    unique_chunks: List[Dict[str, Any]] = []

    def get_shingles(text: str) -> set:
        words = re.findall(r"\w+", text.lower())
        if len(words) < 5:
            return set(words)
        return {" ".join(words[i:i+5]) for i in range(len(words) - 4)}

    chunk_shingles = []

    for chunk in chunks:
        cid = chunk.get("chunk_id", "")
        if cid and cid in seen_ids:
            continue

        text = chunk.get("text", "").strip()
        if not text:
            continue

        shingles = get_shingles(text)
        is_dup = False

        for existing_shingles in chunk_shingles:
            if not shingles or not existing_shingles:
                continue
            intersection = len(shingles & existing_shingles)
            union = len(shingles | existing_shingles)
            if union > 0 and (intersection / union) >= similarity_threshold:
                is_dup = True
                break

        if not is_dup:
            if cid:
                seen_ids.add(cid)
            chunk_shingles.append(shingles)
            unique_chunks.append(chunk)

    return unique_chunks

def rerank_and_fuse(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[Dict[str, Any]],
    top_k: int = 5,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
    query: str = ""
) -> List[Dict[str, Any]]:
    """
    Performs hybrid fusion (Dense + BM25), incorporates source authority weighting,
    deduplicates candidate chunks, and executes Cross-Encoder semantic reranking.
    """
    from app.rag.cross_encoder import cross_encoder

    # 1. Reciprocal Rank Fusion between Dense and Sparse
    fused_chunks = reciprocal_rank_fusion(
        ranked_lists=[dense_results, sparse_results],
        weights=[dense_weight, sparse_weight]
    )

    # 2. Deduplicate
    deduped = deduplicate_chunks(fused_chunks)

    # 3. Apply Source Authority & Semantic Composite Scoring
    final_scored = []
    for chunk in deduped:
        rrf = chunk.get("rrf_score", 0.5)
        raw_dense = chunk.get("score", 0.5)  # Cosine similarity if present
        collection = chunk.get("collection", "default")
        meta = chunk.get("metadata", {})
        
        auth_weight = get_source_authority_weight(collection, meta)
        
        # Composite score
        composite = (0.5 * rrf + 0.5 * raw_dense) * auth_weight
        final_score = round(min(1.0, max(0.0, composite)), 4)

        chunk_copy = dict(chunk)
        chunk_copy["final_score"] = final_score
        chunk_copy["source_authority"] = auth_weight
        final_scored.append(chunk_copy)

    # 4. Sort descending by initial composite score
    final_scored.sort(key=lambda x: x["final_score"], reverse=True)

    # 5. Cross-Encoder Semantic Reranking (if query provided)
    if query:
        return cross_encoder.rerank(query=query, chunks=final_scored, top_k=top_k)

    return final_scored[:top_k]

