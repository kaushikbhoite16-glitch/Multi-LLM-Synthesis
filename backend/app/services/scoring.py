from typing import List, Dict, Tuple, Optional, Any
from app.schemas.pydantic_models import (
    NormalizedResponse,
    EvaluationResult,
    UserPreferenceSchema
)

class ScoringEngine:
    @staticmethod
    def normalize_min_max(values: List[float]) -> List[float]:
        """Min-max normalizes a list of values to [0.0, 1.0], safely handling edge cases"""
        if not values:
            return []
        min_v = min(values)
        max_v = max(values)
        if max_v - min_v < 1e-9:
            return [0.0 for _ in values]
        return [(v - min_v) / (max_v - min_v) for v in values]

    @classmethod
    def calculate_composite_scores(
        cls,
        candidates: List[NormalizedResponse],
        evaluations: List[EvaluationResult],
        preferences: Optional[UserPreferenceSchema] = None
    ) -> List[Dict[str, Any]]:
        """
        Combines semantic quality scores with normalized objective resource metrics (cost, tokens, latency)
        based on the active scoring mode (quality-first, balanced, cost-aware, user-customized).
        """
        eval_map = {e.response_id: e for e in evaluations}
        valid_candidates = [c for c in candidates if c.response_id in eval_map]
        
        if not valid_candidates:
            return []

        costs = [c.cost for c in valid_candidates]
        tokens = [float(c.total_tokens) for c in valid_candidates]
        latencies = [float(c.latency_ms) for c in valid_candidates]

        norm_costs = cls.normalize_min_max(costs)
        norm_tokens = cls.normalize_min_max(tokens)
        norm_latencies = cls.normalize_min_max(latencies)

        scoring_mode = preferences.scoring_mode if preferences else "quality-first"
        
        # Determine resource penalty weights based on scoring mode
        if scoring_mode == "quality-first":
            w_cost, w_tokens, w_latency = 0.0, 0.0, 0.0
            quality_multiplier = 1.0
        elif scoring_mode == "balanced":
            w_cost, w_tokens, w_latency = 0.08, 0.04, 0.04
            quality_multiplier = 0.84
        elif scoring_mode == "cost-aware":
            w_cost, w_tokens, w_latency = 0.20, 0.05, 0.05
            quality_multiplier = 0.70
        else: # user-customized
            w_cost = preferences.cost_weight if preferences else 0.0
            w_tokens = preferences.token_weight if preferences else 0.0
            w_latency = preferences.latency_weight if preferences else 0.0
            res_total = w_cost + w_tokens + w_latency
            quality_multiplier = max(0.4, 1.0 - res_total)

        results = []
        for i, cand in enumerate(valid_candidates):
            ev = eval_map[cand.response_id]
            quality_score = ev.overall_score
            
            # Resource penalty scaled from 0-10
            resource_penalty = (
                norm_costs[i] * w_cost +
                norm_tokens[i] * w_tokens +
                norm_latencies[i] * w_latency
            ) * 10.0

            # Composite final score
            final_score = round(max(0.0, min(10.0, (quality_score * quality_multiplier) - resource_penalty + (1.0 - quality_multiplier) * 5.0)), 2)

            results.append({
                "candidate": cand,
                "evaluation": ev,
                "quality_score": round(quality_score, 2),
                "resource_penalty": round(resource_penalty, 3),
                "overall_score": final_score,
                "norm_cost": norm_costs[i],
                "norm_tokens": norm_tokens[i],
                "norm_latency": norm_latencies[i]
            })

        return results
