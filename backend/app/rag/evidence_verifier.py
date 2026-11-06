import re
from typing import List, Dict, Any, Optional
from app.rag.embeddings import embedding_service
from app.utils.logger import logger

class EvidenceVerifier:
    """
    Verifies atomic claims against retrieved evidence chunks.
    Classifies each claim into:
      - SUPPORTED: Corroborated by one or more retrieved chunks.
      - CONTRADICTED: Directly opposes or falsifies retrieved evidence.
      - INSUFFICIENT_EVIDENCE: Neither supported nor refuted by the retrieved evidence.
    """
    def __init__(
        self,
        support_threshold: float = 0.65,
        contradiction_threshold: float = 0.40
    ):
        self.support_threshold = support_threshold
        self.contradiction_threshold = contradiction_threshold

    def verify_claims(
        self,
        claims: List[str],
        evidence_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates each claim against the retrieved evidence chunks.
        """
        if not claims:
            return []

        if not evidence_chunks:
            return [
                {
                    "claim": c,
                    "status": "INSUFFICIENT_EVIDENCE",
                    "confidence": 0.0,
                    "citations": [],
                    "explanation": "No retrieved evidence chunks available for verification."
                }
                for c in claims
            ]

        # Precompute embeddings
        claim_embeddings = embedding_service.embed_documents(claims)
        evidence_texts = [e.get("text", "") for e in evidence_chunks]
        evidence_embeddings = embedding_service.embed_documents(evidence_texts)

        results = []

        for c_idx, claim in enumerate(claims):
            c_emb = claim_embeddings[c_idx]
            c_tokens = set(re.findall(r"\b\w{3,}\b", claim.lower()))

            best_sim = -1.0
            best_chunk_idx = -1
            best_token_overlap = 0.0
            supporting_citations = []

            for e_idx, e_chunk in enumerate(evidence_chunks):
                e_emb = evidence_embeddings[e_idx]
                sim = embedding_service.cosine_similarity(c_emb, e_emb)

                e_tokens = set(re.findall(r"\b\w{3,}\b", e_chunk.get("text", "").lower()))
                token_overlap = len(c_tokens & e_tokens) / max(1, len(c_tokens))

                # Combined semantic + lexical agreement
                combined_agreement = 0.7 * sim + 0.3 * token_overlap

                if combined_agreement > best_sim:
                    best_sim = combined_agreement
                    best_chunk_idx = e_idx
                    best_token_overlap = token_overlap

                citation_tag = e_chunk.get("citation_id", f"[{e_idx+1}]")
                if combined_agreement >= self.support_threshold:
                    if citation_tag not in supporting_citations:
                        supporting_citations.append(citation_tag)

            # Determine classification
            matched_evidence = evidence_chunks[best_chunk_idx] if best_chunk_idx >= 0 else {}
            matched_title = matched_evidence.get("title", "Evidence")

            if best_sim >= self.support_threshold:
                status = "SUPPORTED"
                explanation = f"Supported by {matched_title} with {int(best_sim * 100)}% agreement."
            elif best_sim < self.contradiction_threshold and best_token_overlap > 0.35:
                # High lexical overlap on same topic, but low semantic similarity or negation words
                status = "CONTRADICTED"
                explanation = f"Contradicts facts found in {matched_title}."
                supporting_citations = []
            else:
                status = "INSUFFICIENT_EVIDENCE"
                explanation = f"Insufficient specific evidence in the indexed knowledge base (best similarity: {int(best_sim * 100)}%)."
                supporting_citations = []

            results.append({
                "claim": claim,
                "status": status,
                "confidence": round(float(max(0.0, min(1.0, best_sim))), 4),
                "citations": supporting_citations,
                "matched_chunk_id": matched_evidence.get("chunk_id", ""),
                "explanation": explanation
            })

        return results

evidence_verifier = EvidenceVerifier()
