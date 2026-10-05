from typing import List, Optional
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
        preferences: Optional[UserPreferenceSchema] = None
    ) -> List[RankedResponse]:
        """
        Ranks candidate responses descending by their multi-criteria composite score.
        """
        scored_items = ScoringEngine.calculate_composite_scores(candidates, evaluations, preferences)
        
        # Sort descending by composite overall_score
        sorted_items = sorted(scored_items, key=lambda x: x["overall_score"], reverse=True)
        
        ranked_responses: List[RankedResponse] = []
        for idx, item in enumerate(sorted_items):
            cand: NormalizedResponse = item["candidate"]
            ev: EvaluationResult = item["evaluation"]
            
            crit_scores = {
                "relevance": ev.relevance,
                "correctness": ev.correctness,
                "completeness": ev.completeness,
                "clarity": ev.clarity,
                "consistency": ev.consistency,
                "preference_match": ev.preference_match,
                "conciseness": ev.conciseness,
                "technical_depth": ev.technical_depth
            }

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
                reasoning=ev.reasoning
            ))
            
        return ranked_responses
