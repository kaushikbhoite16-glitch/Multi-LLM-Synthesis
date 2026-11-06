from typing import List, Optional, Dict, Any
from app.schemas.pydantic_models import (
    NormalizedResponse,
    EvaluationResult,
    RankedResponse,
    UserPreferenceSchema
)
from app.services.scoring import ScoringEngine

class RankingEngine:
    @staticmethod
    def rank_responses(
        candidates: List[NormalizedResponse],
        evaluations: List[EvaluationResult],
        preferences: Optional[UserPreferenceSchema] = None,
        evidence_evaluations: Optional[List[Dict[str, Any]]] = None
    ) -> List[RankedResponse]:
        """
        Ranks candidate responses descending by their multi-criteria composite score,
        incorporating evidence support, verified claims, and citations when RAG is active.
        """
        scored_items = ScoringEngine.calculate_composite_scores(candidates, evaluations, preferences)
        
        # Build lookup for evidence evaluations by response_id or model
        ev_map = {}
        if evidence_evaluations:
            for ee in evidence_evaluations:
                rid = ee.get("response_id")
                model = ee.get("model")
                if rid:
                    ev_map[str(rid)] = ee
                if model:
                    ev_map[str(model)] = ee

        # Merge evidence evaluation metrics into scored items
        for item in scored_items:
            cand = item["candidate"]
            ee = ev_map.get(str(cand.response_id)) or ev_map.get(str(cand.model))
            if ee:
                item["evidence_score"] = ee.get("breakdown", {}).get("evidence_support", 5.0)
                item["verified_claims"] = ee.get("verified_claims", [])
                item["citations"] = ee.get("citations", [])
                item["evidence_breakdown"] = ee.get("breakdown", {})
                
                # Apply evidence-grounded score formula:
                # Final Score = 0.30 * Relevance + 0.40 * Evidence Support + 0.15 * Completeness + 0.10 * Clarity + 0.05 * Consistency
                base_quality = ee.get("final_score", item["quality_score"])
                item["quality_score"] = base_quality
                penalty = item.get("resource_penalty", 0.0)
                item["overall_score"] = round(max(0.0, base_quality - penalty), 2)
            else:
                item["evidence_score"] = None
                item["verified_claims"] = []
                item["citations"] = []
                item["evidence_breakdown"] = {}

        # Sort descending by composite overall_score
        sorted_items = sorted(scored_items, key=lambda x: x["overall_score"], reverse=True)
        
        ranked_responses: List[RankedResponse] = []
        for idx, item in enumerate(sorted_items):
            cand: NormalizedResponse = item["candidate"]
            ev: EvaluationResult = item["evaluation"]
            
            crit_scores = {
                "relevance": item["evidence_breakdown"].get("relevance", ev.relevance),
                "correctness": ev.correctness,
                "completeness": item["evidence_breakdown"].get("completeness", ev.completeness),
                "clarity": item["evidence_breakdown"].get("clarity", ev.clarity),
                "consistency": item["evidence_breakdown"].get("consistency", ev.consistency),
                "preference_match": ev.preference_match,
                "conciseness": ev.conciseness,
                "technical_depth": ev.technical_depth
            }
            if item.get("evidence_score") is not None:
                crit_scores["evidence_support"] = item["evidence_score"]

            ranked_responses.append(RankedResponse(
                rank=idx + 1,
                response_id=cand.response_id,
                model=cand.model,
                provider=cand.provider,
                response_text=cand.response_text,
                overall_score=item["overall_score"],
                quality_score=item["quality_score"],
                resource_penalty=item["resource_penalty"],
                cost=cand.cost,
                tokens=cand.total_tokens,
                latency_ms=cand.latency_ms,
                criteria_scores=crit_scores,
                reasoning=ev.reasoning,
                evidence_score=item.get("evidence_score"),
                verified_claims=item.get("verified_claims"),
                citations=item.get("citations")
            ))
            
        return ranked_responses

