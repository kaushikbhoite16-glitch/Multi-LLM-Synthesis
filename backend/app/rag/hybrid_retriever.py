import asyncio
import re
from typing import List, Dict, Any, Optional
from app.rag.sources.general_kb import general_kb
from app.rag.sources.academic_kb import academic_kb
from app.rag.sources.dynamic_web import dynamic_web
from app.rag.fusion import rerank_and_fuse
from app.utils.logger import logger

ACADEMIC_KEYWORDS = [
    "paper", "research", "study", "survey", "author", "published", "venue", 
    "arxiv", "conference", "neurips", "iclr", "acl", "cvpr", "icml", "citation", "literature"
]

DYNAMIC_WEB_KEYWORDS = [
    "latest", "news", "current", "2025", "2026", "today", "yesterday", "recent",
    "price", "release date", "weather", "update", "now"
]

class HybridRetriever:
    """
    Coordinates multi-source hybrid retrieval (Dense + Sparse BM25 + Web)
    across General Knowledge Base, Academic Knowledge Base, and Dynamic Web.
    """
    def __init__(self):
        pass

    def detect_sources(self, query: str) -> List[str]:
        """Heuristically selects relevant knowledge bases based on query semantics."""
        query_lower = query.lower()
        sources = ["general"]

        # Check for academic intent
        if any(re.search(rf"\b{kw}\b", query_lower) for kw in ACADEMIC_KEYWORDS):
            sources.append("academic")

        # Check for web freshness intent
        if any(re.search(rf"\b{kw}\b", query_lower) for kw in DYNAMIC_WEB_KEYWORDS):
            sources.append("dynamic_web")

        # By default for technical exploration, also search academic knowledge
        if "academic" not in sources:
            sources.append("academic")

        return sources

    async def retrieve_evidence(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval across specified sources and returns unified evidence chunks.
        """
        if not sources:
            sources = self.detect_sources(query)

        logger.info(f"Hybrid retrieval triggered for query: '{query}' across sources: {sources}")

        tasks = []
        source_labels = []

        if "general" in sources:
            # Sync search wrapped in executor
            tasks.append(asyncio.to_thread(general_kb.search, query, top_k * 2))
            source_labels.append("general")

        if "academic" in sources:
            tasks.append(asyncio.to_thread(academic_kb.search, query, top_k * 2))
            source_labels.append("academic")

        if "dynamic_web" in sources or "web" in sources:
            tasks.append(dynamic_web.search_and_cache(query, max_results=top_k * 2))
            source_labels.append("dynamic_web")

        if not tasks:
            tasks.append(asyncio.to_thread(general_kb.search, query, top_k * 2))
            source_labels.append("general")

        gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

        candidate_chunks: List[Dict[str, Any]] = []
        for idx, res in enumerate(gathered_results):
            src_label = source_labels[idx]
            if isinstance(res, Exception):
                logger.warning(f"Retrieval error from source {src_label}: {res}")
                continue
            if isinstance(res, list):
                for chunk in res:
                    chunk["source_category"] = src_label
                    candidate_chunks.append(chunk)

        if not candidate_chunks:
            logger.info(f"No evidence found across sources for query: '{query}'")
            return []

        # Rerank and deduplicate candidate chunks across sources
        # We pass dense_results as the candidate list and an empty sparse list to let rerank_and_fuse
        # apply source authority weights, deduplicate shingles, and sort descending
        fused = rerank_and_fuse(
            dense_results=candidate_chunks,
            sparse_results=[],
            top_k=top_k,
            dense_weight=1.0,
            sparse_weight=0.0,
            query=query
        )


        evidence_list = []
        for i, chunk in enumerate(fused, start=1):
            meta = chunk.get("metadata", {})
            evidence_list.append({
                "citation_id": f"[{i}]",
                "citation_index": i,
                "chunk_id": chunk.get("chunk_id", f"chunk_{i}"),
                "title": meta.get("title", f"Source {i}"),
                "text": chunk.get("text", "").strip(),
                "source_type": chunk.get("source_category", meta.get("source_type", "general")),
                "url": meta.get("url", ""),
                "relevance_score": chunk.get("final_score", 0.5),
                "author": meta.get("authors", ""),
                "year": meta.get("year", "")
            })

        logger.info(f"Retrieved {len(evidence_list)} evidence chunks for query '{query}'")
        return evidence_list

hybrid_retriever = HybridRetriever()
