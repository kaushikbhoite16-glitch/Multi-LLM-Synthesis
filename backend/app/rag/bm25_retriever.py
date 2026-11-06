import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.utils.logger import logger
from app.rag.vector_store import vector_store

def tokenize(text: str) -> List[str]:
    """Basic alphanumeric tokenizer preserving technical terms."""
    if not text:
        return []
    # Lowercase and split on non-alphanumeric characters while keeping numbers/words
    tokens = re.findall(r"\b[a-zA-Z0-9_\-\.\#\+]{2,}\b", text.lower())
    return tokens

class BM25Retriever:
    """
    BM25 Sparse Keyword Retriever.
    Maintains in-memory BM25Okapi indices for collections to provide high-precision lexical search.
    """
    def __init__(self):
        self._indices: Dict[str, BM25Okapi] = {}
        self._corpus_records: Dict[str, List[Dict[str, Any]]] = {}

    def index_collection(self, collection_name: str) -> int:
        """
        Loads all chunks from a ChromaDB collection and builds the BM25 index.
        """
        col = vector_store.get_collection(collection_name)
        count = col.count()
        if count == 0:
            self._indices[collection_name] = None
            self._corpus_records[collection_name] = []
            return 0

        # Fetch all records
        data = col.get(include=["documents", "metadatas"])
        ids = data.get("ids", [])
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        records = []
        tokenized_corpus = []

        for i in range(len(ids)):
            doc_text = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if i < len(metadatas) else {}
            tokens = tokenize(doc_text)
            
            records.append({
                "chunk_id": ids[i],
                "text": doc_text,
                "metadata": meta,
                "collection": collection_name
            })
            tokenized_corpus.append(tokens)

        if tokenized_corpus:
            self._indices[collection_name] = BM25Okapi(tokenized_corpus)
            self._corpus_records[collection_name] = records
            logger.info(f"BM25 index built for {collection_name} with {len(records)} chunks")
            return len(records)
        return 0

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Searches the BM25 index for the given collection.
        If the index is not yet built, attempts to build it once.
        """
        if collection_name not in self._indices:
            self.index_collection(collection_name)

        bm25 = self._indices.get(collection_name)
        records = self._corpus_records.get(collection_name, [])

        if not bm25 or not records:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Calculate scores across corpus
        scores = bm25.get_scores(query_tokens)
        
        # Pair with records and sort descending
        scored_pairs = []
        for idx, score in enumerate(scores):
            if score > 0.0:  # Only include records with at least one matching term
                scored_pairs.append((score, records[idx]))

        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        top_pairs = scored_pairs[:top_k]

        # Normalize BM25 scores between 0.0 and 1.0 relative to max score if max > 0
        max_score = top_pairs[0][0] if top_pairs else 1.0
        if max_score <= 0:
            max_score = 1.0

        results = []
        for raw_score, record in top_pairs:
            normalized_score = round(min(1.0, raw_score / max_score), 4)
            results.append({
                "chunk_id": record["chunk_id"],
                "text": record["text"],
                "metadata": record["metadata"],
                "score": normalized_score,
                "raw_bm25_score": round(float(raw_score), 4),
                "collection": collection_name
            })

        return results

    def search_dynamic_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Directly indexes and searches an ad-hoc list of chunk dicts (e.g. from web retrieval).
        """
        if not chunks:
            return []

        tokenized_corpus = [tokenize(c.get("text", "")) for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        query_tokens = tokenize(query)
        if not query_tokens:
            return chunks[:top_k]

        scores = bm25.get_scores(query_tokens)
        scored_pairs = list(zip(scores, chunks))
        scored_pairs.sort(key=lambda x: x[0], reverse=True)

        max_score = scored_pairs[0][0] if scored_pairs and scored_pairs[0][0] > 0 else 1.0
        results = []
        for raw_score, chunk in scored_pairs[:top_k]:
            c_copy = dict(chunk)
            c_copy["score"] = round(min(1.0, float(raw_score) / max_score), 4) if max_score > 0 else 0.0
            c_copy["raw_bm25_score"] = round(float(raw_score), 4)
            results.append(c_copy)
        return results

bm25_retriever = BM25Retriever()
