from typing import Optional, List
from app.schemas.pydantic_models import (
    NormalizedResponse,
    SynthesisResult,
    RankedResponse,
    FinalEvaluationResult,
    UserPreferenceSchema,
    EvaluationResult
)
from app.services.evaluator import ResponseEvaluator
from app.utils.logger import log_stage

class FinalEvaluator:
    def __init__(self, evaluator: ResponseEvaluator):
        self.evaluator = evaluator

    async def evaluate_final_response(
        self,
        query: str,
        synthesis: SynthesisResult,
        ranked_candidates: List[RankedResponse],
        preferences: Optional[UserPreferenceSchema] = None,
        evaluator_model: str = "google/gemini-2.0-flash-001"
    ) -> FinalEvaluationResult:
        """
        Evaluates the final synthesized response under the exact same multi-criteria protocol
        and performs direct empirical comparison against the top-ranked candidate model.
        """
        log_stage("eval", "Evaluating final synthesized response", model=synthesis.synthesis_model)

        # Wrap synthesis into a NormalizedResponse structure for evaluation
        norm_synthesis = NormalizedResponse(
            response_id=9999,
            model=synthesis.synthesis_model,
            provider="Synthesizer",
            response_text=synthesis.final_response,
            input_tokens=synthesis.input_tokens,
            output_tokens=synthesis.output_tokens,
            total_tokens=synthesis.total_tokens,
            cost=synthesis.cost,
            latency_ms=synthesis.latency_ms,
            status=synthesis.status
        )

        eval_result: EvaluationResult = await self.evaluator.evaluate_single(
            query=query,
            preferences=preferences,
            response=norm_synthesis,
            evaluator_model=evaluator_model
        )

        # Baseline: Best Candidate
        best_candidate = ranked_candidates[0] if ranked_candidates else None
        best_model = best_candidate.model if best_candidate else "None"
        best_score = best_candidate.quality_score if best_candidate else 0.0

        # Calculate improvement percentage
        final_score = eval_result.overall_score
        improvement_pct = 0.0
        if best_score > 0:
            improvement_pct = round(((final_score - best_score) / best_score) * 100, 2)

        return FinalEvaluationResult(
            evaluator_model=eval_result.evaluator_model,
            relevance=eval_result.relevance,
            correctness=eval_result.correctness,
            completeness=eval_result.completeness,
            clarity=eval_result.clarity,
            consistency=eval_result.consistency,
            preference_match=eval_result.preference_match,
            conciseness=eval_result.conciseness,
            technical_depth=eval_result.technical_depth,
            overall_score=final_score,
            reasoning=eval_result.reasoning,
            best_candidate_model=best_model,
            best_candidate_score=round(best_score, 2),
            improvement_pct=improvement_pct
        )
