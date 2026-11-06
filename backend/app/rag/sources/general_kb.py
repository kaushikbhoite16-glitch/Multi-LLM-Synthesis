import uuid
import datetime
from typing import List, Dict, Any, Optional
from app.rag.vector_store import vector_store, GENERAL_COLLECTION
from app.rag.chunking import SemanticChunker
from app.rag.document_loader import document_loader
from app.rag.bm25_retriever import bm25_retriever
from app.rag.fusion import rerank_and_fuse
from app.utils.logger import logger

class GeneralKnowledgeBase:
    """
    Manages general technical and educational knowledge base stored in ChromaDB.
    Supports PDF/TXT/HTML ingestion, semantic chunking, and hybrid search.
    """
    def __init__(self):
        self.chunker = SemanticChunker()

    def ingest_text(
        self,
        text: str,
        title: str,
        category: str = "general_knowledge",
        source_url: str = "",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ingests raw text directly into the general knowledge collection."""
        if not text or not text.strip():
            raise ValueError("Document text cannot be empty.")

        doc_id = f"doc_gen_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.datetime.utcnow().isoformat()
        
        base_meta = {
            "document_id": doc_id,
            "title": title,
            "category": category,
            "url": source_url,
            "source_type": "general",
            "created_at": now_iso
        }
        if extra_metadata:
            base_meta.update(extra_metadata)

        chunks = self.chunker.chunk_document(doc_id, text, base_meta)
        if not chunks:
            return {"document_id": doc_id, "chunk_count": 0, "status": "empty"}

        chunk_ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        vector_store.add_chunks(GENERAL_COLLECTION, chunk_ids, documents, metadatas)
        # Update BM25 index
        bm25_retriever.index_collection(GENERAL_COLLECTION)

        logger.info(f"Ingested '{title}' into general knowledge base: {len(chunks)} chunks")
        return {
            "document_id": doc_id,
            "title": title,
            "chunk_count": len(chunks),
            "status": "indexed"
        }

    def ingest_file(self, file_path: str, title: Optional[str] = None, category: str = "general_knowledge") -> Dict[str, Any]:
        """Loads and indexes a PDF, TXT, or HTML file."""
        doc_data = document_loader.load_file(file_path)
        doc_title = title or doc_data.get("metadata", {}).get("title") or "General Document"
        
        return self.ingest_text(
            text=doc_data["text"],
            title=doc_title,
            category=category,
            source_url=file_path,
            extra_metadata=doc_data.get("metadata", {})
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Executes dense + BM25 hybrid search over general knowledge."""
        dense_results = vector_store.search_vector(GENERAL_COLLECTION, query, top_k=top_k * 2)
        sparse_results = bm25_retriever.search(GENERAL_COLLECTION, query, top_k=top_k * 2)

        return rerank_and_fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            top_k=top_k,
            dense_weight=0.6,
            sparse_weight=0.4,
            query=query
        )


    def count(self) -> int:
        return vector_store.get_collection(GENERAL_COLLECTION).count()

general_kb = GeneralKnowledgeBase()
