import uuid
import datetime
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from app.config import settings
from app.rag.vector_store import vector_store, DYNAMIC_WEB_COLLECTION
from app.rag.chunking import SemanticChunker
from app.rag.bm25_retriever import bm25_retriever
from app.rag.fusion import rerank_and_fuse
from app.utils.logger import logger

class DynamicWebRetriever:
    """
    Retrieves live web information via Tavily API or DuckDuckGo/Wikipedia fallback,
    chunks content, and maintains a TTL-cached store in dynamic_web_cache.
    """
    def __init__(self):
        self.chunker = SemanticChunker(chunk_size=350, chunk_overlap=50)

    async def search_and_cache(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """
        Fetches live web results, chunks them, saves to dynamic_web_cache,
        and returns the formatted evidence chunks.
        """
        # 1. Prune any expired web records first
        vector_store.prune_expired_web_records()

        # 2. Check if we already have non-expired cached chunks for this query
        existing = self.search_cache(query, top_k=max_results)
        if existing and len(existing) >= max_results:
            logger.info(f"Using {len(existing)} cached web results for '{query}'")
            return existing

        # 3. Retrieve raw web items
        raw_items = []
        if settings.TAVILY_API_KEY and settings.TAVILY_API_KEY.strip():
            raw_items = await self._search_tavily(query, max_results=max_results)

        if not raw_items:
            raw_items = await self._search_duckduckgo_fallback(query, max_results=max_results)

        if not raw_items:
            raw_items = await self._search_wikipedia_fallback(query, max_results=max_results)

        if not raw_items:
            logger.info(f"No web results found for '{query}'")
            return []

        # 4. Chunk and save to ChromaDB cache with TTL
        now = datetime.datetime.utcnow()
        expires_at = (now + datetime.timedelta(hours=settings.DYNAMIC_WEB_EXPIRATION_HOURS)).isoformat()
        now_iso = now.isoformat()

        all_chunks = []
        for idx, item in enumerate(raw_items):
            doc_id = f"web_{uuid.uuid4().hex[:10]}"
            domain = urlparse(item.get("url", "")).netloc or "web"
            base_meta = {
                "document_id": doc_id,
                "title": item.get("title", f"Web Search Result {idx+1}"),
                "url": item.get("url", ""),
                "domain": domain,
                "source_type": "dynamic_web",
                "crawled_at": now_iso,
                "expires_at": expires_at,
                "query": query
            }

            chunks = self.chunker.chunk_document(doc_id, item.get("content", ""), base_meta)
            all_chunks.extend(chunks)

        if all_chunks:
            chunk_ids = [c["chunk_id"] for c in all_chunks]
            documents = [c["text"] for c in all_chunks]
            metadatas = [c["metadata"] for c in all_chunks]

            vector_store.add_chunks(DYNAMIC_WEB_COLLECTION, chunk_ids, documents, metadatas)
            bm25_retriever.index_collection(DYNAMIC_WEB_COLLECTION)
            logger.info(f"Cached {len(all_chunks)} web chunks for query: '{query}' (expires {expires_at})")

        # 5. Return hybrid search from dynamic_web_cache
        return self.search_cache(query, top_k=max_results)

    def search_cache(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches the dynamic web cache collection using dense + BM25 hybrid search."""
        dense_results = vector_store.search_vector(DYNAMIC_WEB_COLLECTION, query, top_k=top_k * 2)
        sparse_results = bm25_retriever.search(DYNAMIC_WEB_COLLECTION, query, top_k=top_k * 2)

        return rerank_and_fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            top_k=top_k,
            dense_weight=0.6,
            sparse_weight=0.4,
            query=query
        )


    async def _search_tavily(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """Queries Tavily Search API."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.TAVILY_API_KEY,
                        "query": query,
                        "search_depth": "basic",
                        "include_answer": True,
                        "max_results": max_results
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for r in data.get("results", []):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", "")
                        })
                    return results
                else:
                    logger.warning(f"Tavily API responded with status {res.status_code}")
        except Exception as e:
            logger.warning(f"Tavily search exception: {e}")
        return []

    async def _search_duckduckgo_fallback(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """Queries DuckDuckGo HTML endpoint as resilient fallback."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            async with httpx.AsyncClient(timeout=6.0, headers=headers) as client:
                res = await client.get(f"https://html.duckduckgo.com/html/?q={query}")
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    results = []
                    for el in soup.find_all("div", class_="result__body")[:max_results]:
                        title_tag = el.find("a", class_="result__snippet") or el.find("a", class_="result__url")
                        snippet_tag = el.find("a", class_="result__snippet")
                        url_tag = el.find("a", class_="result__url")

                        title = el.find("h2").get_text(strip=True) if el.find("h2") else "Search Result"
                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        url = url_tag.get("href", "") if url_tag else ""

                        if snippet:
                            results.append({
                                "title": title,
                                "url": url,
                                "content": snippet
                            })
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"DuckDuckGo fallback search exception: {e}")
        return []

    async def _search_wikipedia_fallback(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Queries Wikipedia API as high-reliability educational fallback."""
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                # Search Wikipedia API
                url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    search_results = data.get("query", {}).get("search", [])[:max_results]
                    items = []
                    for item in search_results:
                        title = item.get("title", "")
                        clean_snippet = BeautifulSoup(item.get("snippet", ""), "html.parser").get_text()
                        page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        items.append({
                            "title": title,
                            "url": page_url,
                            "content": f"{title}: {clean_snippet}"
                        })
                    return items
        except Exception as e:
            logger.warning(f"Wikipedia fallback search exception: {e}")
        return []

dynamic_web = DynamicWebRetriever()
