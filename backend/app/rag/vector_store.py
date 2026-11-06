import os
import datetime
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.utils.logger import logger
from app.rag.embeddings import embedding_service

GENERAL_COLLECTION = "general_knowledge"
ACADEMIC_COLLECTION = "academic_knowledge"
DYNAMIC_WEB_COLLECTION = "dynamic_web_cache"

ALL_COLLECTIONS = [GENERAL_COLLECTION, ACADEMIC_COLLECTION, DYNAMIC_WEB_COLLECTION]

class ChromaVectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaVectorStore, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        logger.info(f"Initializing persistent ChromaDB client at: {settings.CHROMA_PERSIST_DIR}")
        
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Ensure the 3 standard collections exist
        self.collections: Dict[str, Any] = {}
        for col_name in ALL_COLLECTIONS:
            self.collections[col_name] = self.client.get_or_create_collection(
                name=col_name,
                metadata={"hnsw:space": "cosine"}
            )
        logger.info("ChromaDB initialized with collections: general_knowledge, academic_knowledge, dynamic_web_cache")

    def get_collection(self, name: str):
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        return self.collections[name]

    def add_chunks(
        self,
        collection_name: str,
        chunk_ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> int:
        """Adds or updates chunks in the specified collection."""
        if not chunk_ids:
            return 0
            
        col = self.get_collection(collection_name)
        if embeddings is None:
            embeddings = embedding_service.embed_documents(documents)

        # Sanitize metadata to scalar types supported by ChromaDB (str, int, float, bool)
        clean_metadatas = []
        for m in metadatas:
            clean_m = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_m[k] = v
                elif v is None:
                    clean_m[k] = ""
                else:
                    clean_m[k] = str(v)
            clean_metadatas.append(clean_m)

        col.upsert(
            ids=chunk_ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_metadatas
        )
        return len(chunk_ids)

    def search_vector(
        self,
        collection_name: str,
        query_text: str,
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Executes dense vector search on a single collection."""
        col = self.get_collection(collection_name)
        count = col.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        query_embedding = embedding_service.embed_query(query_text)

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": actual_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        try:
            results = col.query(**kwargs)
        except Exception as e:
            logger.warning(f"ChromaDB search error in {collection_name}: {e}")
            return []

        out = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]

            for i in range(len(ids)):
                # Convert cosine distance to cosine similarity (0 to 1)
                dist = dists[i] if i < len(dists) else 1.0
                similarity = max(0.0, 1.0 - dist)
                out.append({
                    "chunk_id": ids[i],
                    "text": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "score": round(similarity, 4),
                    "collection": collection_name
                })
        return out

    def prune_expired_web_records(self) -> int:
        """Deletes expired web cache entries where expires_at <= current timestamp."""
        col = self.get_collection(DYNAMIC_WEB_COLLECTION)
        if col.count() == 0:
            return 0

        now_iso = datetime.datetime.utcnow().isoformat()
        try:
            # Query items where expires_at is set and <= now_iso
            expired_res = col.get(
                where={"expires_at": {"$lte": now_iso}},
                include=["metadatas"]
            )
            expired_ids = expired_res.get("ids", [])
            if expired_ids:
                col.delete(ids=expired_ids)
                logger.info(f"Pruned {len(expired_ids)} expired records from {DYNAMIC_WEB_COLLECTION}")
                return len(expired_ids)
        except Exception as e:
            logger.warning(f"Error during expired cache pruning: {e}")
        return 0

    def delete_document_chunks(self, collection_name: str, document_id: str) -> int:
        """Deletes all chunks associated with a specific document ID."""
        col = self.get_collection(collection_name)
        try:
            res = col.get(where={"document_id": document_id})
            ids_to_del = res.get("ids", [])
            if ids_to_del:
                col.delete(ids=ids_to_del)
                return len(ids_to_del)
        except Exception as e:
            logger.warning(f"Failed to delete document chunks for {document_id}: {e}")
        return 0

    def get_collection_stats(self) -> Dict[str, int]:
        """Returns the number of indexed records across all collections."""
        return {
            col_name: self.get_collection(col_name).count()
            for col_name in ALL_COLLECTIONS
        }

vector_store = ChromaVectorStore()
