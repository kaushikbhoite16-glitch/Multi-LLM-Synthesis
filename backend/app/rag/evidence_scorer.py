import re
from typing import List, Dict, Any, Optional
from app.rag.embeddings import embedding_service
from app.rag.claim_extractor import claim_extractor
from app.rag.evidence_verifier import evidence_verifier
from app.utils.logger import logger

class EvidenceScorer:
    """
    Computes evidence-grounded evaluation and multi-criteria scoring for candidate responses.
    Implements the weighted formula:
      Final Score = 0.30 * Relevance + 0.40 * Evidence Support + 0.15 * Completeness + 0.10 * Clarity + 0.05 * Consistency
    """
    def __init__(self):
        pass

    def calculate_relevance(self, query: str, response_text: str) -> float:
        """
        Calculates relevance of candidate response to the query on a 0.0 to 10.0 scale.
        Penalizes responses that discuss an unrelated subject.
        """
        if not response_text or not response_text.strip():
            return 0.0

        query_tokens = set(re.findall(r"\b\w{3,}\b", query.lower()))
        response_tokens = set(re.findall(r"\b\w{3,}\b", response_text.lower()))

        # 1. Lexical query coverage
        if query_tokens:
            overlap = len(query_tokens & response_tokens) / len(query_tokens)
        else:
            overlap = 1.0

        # 2. Semantic embedding similarity
        q_emb = embedding_service.embed_query(query)
        r_emb = embedding_service.embed_query(response_text[:1000])
        semantic_sim = embedding_service.cosine_similarity(q_emb, r_emb)

        # Scaled score
        raw = 0.5 * semantic_sim + 0.5 * overlap
        # If semantic similarity is very low (< 0.25), heavily penalize
        if semantic_sim < 0.25 and overlap < 0.2:
            return round(max(1.0, raw * 4.0), 2)

        score = 2.0 + 8.0 * max(0.0, min(1.0, raw))
        return round(score, 2)

    def calculate_evidence_support(self, verified_claims: List[Dict[str, Any]]) -> float:
        """
        Calculates evidence support on a 0.0 to 10.0 scale based on verified atomic claims.
        """
        if not verified_claims:
            return 5.0

        n = len(verified_claims)
        supported = sum(1 for c in verified_claims if c["status"] == "SUPPORTED")
        contradicted = sum(1 for c in verified_claims if c["status"] == "CONTRADICTED")
        insufficient = sum(1 for c in verified_claims if c["status"] == "INSUFFICIENT_EVIDENCE")

        raw_ratio = (1.0 * supported - 1.5 * contradicted + 0.2 * insufficient) / n
        clamped_ratio = max(0.0, min(1.0, raw_ratio))

        score = round(clamped_ratio * 10.0, 2)
        return score

    def calculate_structural_metrics(self, response_text: str) -> Dict[str, float]:
        """Calculates completeness, clarity, and consistency on 0.0 to 10.0 scales."""
        words = response_text.split()
        wc = len(words)

        # Completeness (depth, presence of examples, coverage)
        if wc < 30:
            completeness = 4.0
        elif wc < 100:
            completeness = 7.0
        elif wc <= 500:
            completeness = 9.0
        else:
            completeness = 8.5

        if any(kw in response_text.lower() for kw in ["for example", "e.g.", "such as", "syntax"]):
            completeness = min(10.0, completeness + 0.5)

        # Clarity (formatting, headings, code blocks, lists)
        clarity = 8.0
        if any(h in response_text for h in ["###", "1.", "2.", "-", "*", "`"]):
            clarity += 1.0
        if wc > 800:
            clarity -= 0.8  # verbose penalty
        clarity = min(10.0, max(2.0, clarity))

        # Consistency (internal coherence)
        consistency = 9.0

        return {
            "completeness": round(completeness, 2),
            "clarity": round(clarity, 2),
            "consistency": round(consistency, 2)
        }

    def evaluate_response(
        self,
        query: str,
        response_text: str,
        model_name: str,
        response_id: str,
        evidence_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates an individual candidate response against retrieved evidence.
        """
        claims = claim_extractor.extract_claims(response_text)
        verified_claims = evidence_verifier.verify_claims(claims, evidence_chunks)

        relevance = self.calculate_relevance(query, response_text)
        evidence_support = self.calculate_evidence_support(verified_claims)
        
        # Guardrail: If candidate response has negligible relevance to user query,
        # it cannot receive a high evidence support score for the user query
        if relevance < 3.5:
            evidence_support = min(evidence_support, relevance)

        metrics = self.calculate_structural_metrics(response_text)

        completeness = metrics["completeness"]
        clarity = metrics["clarity"]
        consistency = metrics["consistency"]

        # Weighted formula:
        # Final Score = 0.30 * Relevance + 0.40 * Evidence Support + 0.15 * Completeness + 0.10 * Clarity + 0.05 * Consistency
        final_score = (
            0.30 * relevance +
            0.40 * evidence_support +
            0.15 * completeness +
            0.10 * clarity +
            0.05 * consistency
        )
        final_score = round(max(0.0, min(10.0, final_score)), 2)

        # Identify all citations referenced by supported claims
        used_citations = []
        for vc in verified_claims:
            for cit in vc.get("citations", []):
                if cit not in used_citations:
                    used_citations.append(cit)

        return {
            "response_id": response_id,
            "model": model_name,
            "final_score": final_score,
            "breakdown": {
                "relevance": relevance,
                "evidence_support": evidence_support,
                "completeness": completeness,
                "clarity": clarity,
                "consistency": consistency
            },
            "claims_count": len(claims),
            "supported_count": sum(1 for c in verified_claims if c["status"] == "SUPPORTED"),
            "contradicted_count": sum(1 for c in verified_claims if c["status"] == "CONTRADICTED"),
            "verified_claims": verified_claims,
            "citations": used_citations
        }

    def rank_candidates(
        self,
        query: str,
        candidates: List[Any],
        evidence_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates and ranks all candidate responses based on evidence-grounded scoring.
        """
        evaluations = []
        for cand in candidates:
            text = getattr(cand, "response_text", "") or cand.get("response_text", "")
            model = getattr(cand, "model", "") or cand.get("model", "unknown")
            rid = getattr(cand, "response_id", "") or cand.get("response_id", "unknown")

            ev = self.evaluate_response(
                query=query,
                response_text=text,
                model_name=model,
                response_id=rid,
                evidence_chunks=evidence_chunks
            )
            evaluations.append(ev)

        # Sort descending by final score
        evaluations.sort(key=lambda x: x["final_score"], reverse=True)
        for rank_idx, ev in enumerate(evaluations, start=1):
            ev["rank"] = rank_idx

        return evaluations

evidence_scorer = EvidenceScorer()
