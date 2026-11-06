import uuid
import datetime
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
from app.rag.vector_store import vector_store, ACADEMIC_COLLECTION
from app.rag.chunking import SemanticChunker
from app.rag.bm25_retriever import bm25_retriever
from app.rag.fusion import rerank_and_fuse
from app.utils.logger import logger

class AcademicKnowledgeBase:
    """
    Manages peer-reviewed academic papers, conference publications, and preprints.
    Integrates 4 academic providers:
      1. arXiv API
      2. OpenAlex API
      3. Crossref API
      4. Semantic Scholar API
    Stores structured academic metadata (DOI, authors, year, venue) and provides hybrid search.
    """
    def __init__(self):
        self.chunker = SemanticChunker(chunk_size=400, chunk_overlap=60)

    def ingest_paper(
        self,
        title: str,
        abstract: str,
        authors: str,
        year: int,
        full_text: str = "",
        venue: str = "",
        doi: str = "",
        arxiv_id: str = "",
        url: str = "",
        provider: str = "academic"
    ) -> Dict[str, Any]:
        """Ingests an academic paper with structured metadata into ChromaDB."""
        if not title or not (abstract or full_text):
            raise ValueError("Paper must have a title and abstract/text.")

        doc_id = f"doc_acad_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.datetime.utcnow().isoformat()

        content = f"# {title}\n**Authors:** {authors} ({year})\n**Venue:** {venue or 'Academic Publication'}\n\n## Abstract\n{abstract}"
        if full_text:
            content += f"\n\n## Body\n{full_text}"

        base_meta = {
            "document_id": doc_id,
            "title": title,
            "authors": authors,
            "year": int(year),
            "venue": venue or "Academic",
            "doi": doi or "",
            "arxiv_id": arxiv_id or "",
            "url": url or f"https://doi.org/{doi}" if doi else "",
            "source_type": "academic",
            "provider": provider,
            "created_at": now_iso
        }

        chunks = self.chunker.chunk_document(doc_id, content, base_meta)
        if not chunks:
            return {"document_id": doc_id, "chunk_count": 0, "status": "empty"}

        chunk_ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        vector_store.add_chunks(ACADEMIC_COLLECTION, chunk_ids, documents, metadatas)
        bm25_retriever.index_collection(ACADEMIC_COLLECTION)

        logger.info(f"Ingested academic paper '{title}' ({year}) from {provider}: {len(chunks)} chunks")
        return {
            "document_id": doc_id,
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi,
            "venue": venue,
            "provider": provider,
            "url": url,
            "chunk_count": len(chunks),
            "status": "indexed"
        }

    # -------------------------------------------------------------
    # Provider 1: arXiv API
    # -------------------------------------------------------------
    async def fetch_and_ingest_arxiv(self, search_query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Queries arXiv Atom API and ingests matching preprints."""
        url = f"https://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={max_results}"
        ingested = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"arXiv API returned status {resp.status_code}")
                    return []

                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

                for entry in root.findall("atom:entry", ns):
                    title_elem = entry.find("atom:title", ns)
                    summary_elem = entry.find("atom:summary", ns)
                    published_elem = entry.find("atom:published", ns)
                    id_elem = entry.find("atom:id", ns)

                    title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "Untitled"
                    abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else ""
                    pub_date = published_elem.text if published_elem is not None and published_elem.text else "2024"
                    year = int(pub_date[:4]) if len(pub_date) >= 4 and pub_date[:4].isdigit() else 2024
                    paper_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""

                    authors = []
                    for author in entry.findall("atom:author", ns):
                        name_elem = author.find("atom:name", ns)
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())
                    author_str = ", ".join(authors) if authors else "Unknown Authors"

                    res = self.ingest_paper(
                        title=title,
                        abstract=abstract,
                        authors=author_str,
                        year=year,
                        venue="arXiv",
                        arxiv_id=paper_url.split("/")[-1] if paper_url else "",
                        url=paper_url,
                        provider="arxiv"
                    )
                    ingested.append(res)
        except Exception as e:
            logger.warning(f"Error querying arXiv for '{search_query}': {e}")
        return ingested

    # -------------------------------------------------------------
    # Provider 2: OpenAlex API
    # -------------------------------------------------------------
    async def fetch_and_ingest_openalex(self, search_query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Queries OpenAlex Open API (https://api.openalex.org/works)."""
        url = f"https://api.openalex.org/works?search={search_query}&per-page={max_results}"
        headers = {"User-Agent": "Multi-LLM-Synthesis-Research/2.1.0 (mailto:admin@example.edu)"}
        ingested = []
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("results", []):
                        title = item.get("display_name") or "Untitled Paper"
                        year = item.get("publication_year") or 2024
                        doi = (item.get("doi") or "").replace("https://doi.org/", "")
                        landing_page = item.get("doi") or item.get("id") or ""

                        # Extract authors
                        authors = []
                        for auth in item.get("authorships", []):
                            name = auth.get("author", {}).get("display_name")
                            if name:
                                authors.append(name)
                        author_str = ", ".join(authors[:5]) if authors else "Academic Researchers"

                        # Extract or rebuild abstract from inverted index if present
                        abstract = ""
                        inv_index = item.get("abstract_inverted_index")
                        if inv_index and isinstance(inv_index, dict):
                            word_positions = []
                            for word, positions in inv_index.items():
                                for pos in positions:
                                    word_positions.append((pos, word))
                            word_positions.sort(key=lambda x: x[0])
                            abstract = " ".join([w for _, w in word_positions])[:1000]

                        if not abstract:
                            abstract = f"Research paper exploring {title} published in {year}."

                        venue = item.get("primary_location", {}).get("source", {}).get("display_name") or "OpenAlex"

                        res = self.ingest_paper(
                            title=title,
                            abstract=abstract,
                            authors=author_str,
                            year=int(year),
                            venue=venue,
                            doi=doi,
                            url=landing_page,
                            provider="openalex"
                        )
                        ingested.append(res)
                else:
                    logger.warning(f"OpenAlex API returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error querying OpenAlex for '{search_query}': {e}")
        return ingested

    # -------------------------------------------------------------
    # Provider 3: Crossref API
    # -------------------------------------------------------------
    async def fetch_and_ingest_crossref(self, search_query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Queries Crossref REST API (https://api.crossref.org/works)."""
        url = f"https://api.crossref.org/works?query={search_query}&rows={max_results}"
        headers = {"User-Agent": "Multi-LLM-Synthesis-Research/2.1.0 (mailto:admin@example.edu)"}
        ingested = []
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("message", {}).get("items", [])
                    for item in items:
                        titles = item.get("title", [])
                        title = titles[0] if titles else "Untitled Crossref Article"
                        doi = item.get("DOI", "")
                        paper_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

                        # Publication year
                        year = 2024
                        published = item.get("published-print") or item.get("published-online") or item.get("created")
                        if published and published.get("date-parts") and published["date-parts"][0]:
                            year = int(published["date-parts"][0][0])

                        # Authors
                        authors = []
                        for a in item.get("author", []):
                            family = a.get("family", "")
                            given = a.get("given", "")
                            if family or given:
                                authors.append(f"{given} {family}".strip())
                        author_str = ", ".join(authors[:5]) if authors else "Crossref Authors"

                        container = item.get("container-title", [])
                        venue = container[0] if container else "Crossref Journal"

                        abstract = item.get("abstract") or f"Scholarly publication: {title} ({venue}, {year})."
                        # Strip XML tags if present in Crossref abstract
                        import re
                        abstract = re.sub(r"<[^>]+>", "", abstract).strip()

                        res = self.ingest_paper(
                            title=title,
                            abstract=abstract,
                            authors=author_str,
                            year=int(year),
                            venue=venue,
                            doi=doi,
                            url=paper_url,
                            provider="crossref"
                        )
                        ingested.append(res)
                else:
                    logger.warning(f"Crossref API returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error querying Crossref for '{search_query}': {e}")
        return ingested

    # -------------------------------------------------------------
    # Provider 4: Semantic Scholar API
    # -------------------------------------------------------------
    async def fetch_and_ingest_semantic_scholar(self, search_query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Queries Semantic Scholar Graph API (https://api.semanticscholar.org/graph/v1/paper/search)."""
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={search_query}&limit={max_results}&fields=title,authors,year,abstract,venue,url,externalIds"
        headers = {"User-Agent": "Multi-LLM-Synthesis-Research/2.1.0"}
        ingested = []
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for paper in data.get("data", []):
                        title = paper.get("title") or "Untitled Paper"
                        abstract = paper.get("abstract") or f"Semantic Scholar indexed work: {title}."
                        year = paper.get("year") or 2024
                        venue = paper.get("venue") or "Semantic Scholar"
                        paper_url = paper.get("url") or ""
                        ext_ids = paper.get("externalIds") or {}
                        doi = ext_ids.get("DOI") or ""
                        arxiv_id = ext_ids.get("ArXiv") or ""

                        authors = [a.get("name") for a in paper.get("authors", []) if a.get("name")]
                        author_str = ", ".join(authors[:5]) if authors else "Semantic Scholar Researchers"

                        res = self.ingest_paper(
                            title=title,
                            abstract=abstract,
                            authors=author_str,
                            year=int(year),
                            venue=venue,
                            doi=doi,
                            arxiv_id=arxiv_id,
                            url=paper_url,
                            provider="semantic_scholar"
                        )
                        ingested.append(res)
                elif resp.status_code == 429:
                    logger.warning("Semantic Scholar rate limited (HTTP 429). Will rely on arXiv/OpenAlex/Crossref.")
                else:
                    logger.warning(f"Semantic Scholar API returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error querying Semantic Scholar for '{search_query}': {e}")
        return ingested

    async def fetch_and_ingest_all_providers(
        self,
        search_query: str,
        providers: Optional[List[str]] = None,
        max_results_per_provider: int = 2
    ) -> Dict[str, Any]:
        """
        Coordinates academic ingestion across all 4 providers: arXiv, OpenAlex, Crossref, Semantic Scholar.
        """
        if not providers:
            providers = ["arxiv", "openalex", "crossref", "semantic_scholar"]

        results = {}
        total_ingested = 0

        for prov in providers:
            prov_lower = prov.lower().strip()
            if prov_lower == "arxiv":
                res = await self.fetch_and_ingest_arxiv(search_query, max_results=max_results_per_provider)
                results["arxiv"] = res
                total_ingested += len(res)
            elif prov_lower == "openalex":
                res = await self.fetch_and_ingest_openalex(search_query, max_results=max_results_per_provider)
                results["openalex"] = res
                total_ingested += len(res)
            elif prov_lower == "crossref":
                res = await self.fetch_and_ingest_crossref(search_query, max_results=max_results_per_provider)
                results["crossref"] = res
                total_ingested += len(res)
            elif prov_lower in ("semantic_scholar", "semanticscholar", "s2"):
                res = await self.fetch_and_ingest_semantic_scholar(search_query, max_results=max_results_per_provider)
                results["semantic_scholar"] = res
                total_ingested += len(res)

        return {
            "query": search_query,
            "total_papers_ingested": total_ingested,
            "provider_breakdown": {p: len(items) for p, items in results.items()},
            "papers": results
        }

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Executes dense + BM25 hybrid search over academic knowledge."""
        dense_results = vector_store.search_vector(ACADEMIC_COLLECTION, query, top_k=top_k * 2)
        sparse_results = bm25_retriever.search(ACADEMIC_COLLECTION, query, top_k=top_k * 2)

        return rerank_and_fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            top_k=top_k,
            dense_weight=0.6,
            sparse_weight=0.4,
            query=query
        )


    def count(self) -> int:
        return vector_store.get_collection(ACADEMIC_COLLECTION).count()

academic_kb = AcademicKnowledgeBase()
