import time
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.schemas.pydantic_models import (
    PipelineRunRequest,
    PipelineRunResponse,
    UserPreferenceSchema,
    QueryAnalysisResult,
    NormalizedResponse,
    EvaluationResult,
    RankedResponse,
    ConflictAnalysisResult,
    SynthesisResult,
    FinalEvaluationResult
)
from app.services.openrouter_service import OpenRouterService
from app.services.query_analyzer import QueryAnalyzer
from app.services.evaluator import ResponseEvaluator
from app.services.ranking import RankingEngine
from app.services.conflict_analyzer import ConflictAnalyzer
from app.services.context_builder import ContextBuilder
from app.services.synthesizer import SynthesizerService
from app.services.final_evaluator import FinalEvaluator
from app.models.entities import (
    Query as QueryEntity,
    Preference as PreferenceEntity,
    ModelRun as ModelRunEntity,
    Evaluation as EvaluationEntity,
    Conflict as ConflictEntity,
    SynthesisRun as SynthesisRunEntity,
    FinalEvaluation as FinalEvaluationEntity
)
from app.utils.logger import log_stage

class PipelineOrchestrator:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.openrouter = OpenRouterService()
        self.query_analyzer = QueryAnalyzer(self.openrouter)
        self.evaluator = ResponseEvaluator(self.openrouter)
        self.conflict_analyzer = ConflictAnalyzer(self.openrouter)
        self.synthesizer = SynthesizerService(self.openrouter)
        self.final_evaluator = FinalEvaluator(self.evaluator)

    async def execute_pipeline(self, req: PipelineRunRequest) -> PipelineRunResponse:
        total_pipeline_start = time.perf_counter()
        
        # 1. Models and Preferences Selection
        models = req.models or settings.DEFAULT_CANDIDATE_MODELS
        evaluator_model = req.evaluator_model or settings.DEFAULT_EVALUATOR_MODEL
        synthesis_model = req.synthesis_model or settings.DEFAULT_SYNTHESIS_MODEL
        preferences = req.preferences or UserPreferenceSchema()
        if req.scoring_mode:
            preferences.scoring_mode = req.scoring_mode

        # 2. Query Analysis
        analysis: QueryAnalysisResult = await self.query_analyzer.analyze(
            query=req.query,
            model=evaluator_model
        )

        # 3. Parallel Multi-LLM Generation via OpenRouter
        log_stage("pipeline", "Executing parallel model calls", count=len(models))
        messages = [
            {"role": "user", "content": req.query}
        ]
        candidates: List[NormalizedResponse] = await self.openrouter.generate_parallel_responses(
            models=models,
            messages=messages,
            max_tokens=preferences.max_tokens or 1500
        )

        # Filter out hard failures for evaluation, but keep error records
        valid_candidates = [c for c in candidates if c.status == "success" and c.response_text]
        if not valid_candidates:
            raise RuntimeError("All candidate models failed to generate valid responses.")

        # 4. Multi-Criteria Semantic Evaluation
        log_stage("pipeline", "Evaluating candidate outputs")
        evaluations: List[EvaluationResult] = await self.evaluator.evaluate_candidates_parallel(
            query=req.query,
            preferences=preferences,
            candidates=valid_candidates,
            evaluator_model=evaluator_model
        )

        # 5. Multi-Criteria Scoring & Ranking with Resource Penalties
        log_stage("pipeline", "Ranking candidates with composite scoring")
        ranked_candidates: List[RankedResponse] = RankingEngine.rank_responses(
            candidates=valid_candidates,
            evaluations=evaluations,
            preferences=preferences
        )

        # 6. Agreement & Conflict Analysis
        log_stage("pipeline", "Performing conflict and consensus analysis")
        conflicts: ConflictAnalysisResult = await self.conflict_analyzer.analyze_conflicts(
            query=req.query,
            candidates=valid_candidates,
            model=evaluator_model
        )

        # 7. Structured Context Formation
        log_stage("pipeline", "Forming structured synthesis context")
        structured_context = ContextBuilder.build_structured_context(
            query=req.query,
            ranked_candidates=ranked_candidates,
            conflicts=conflicts,
            preferences=preferences
        )

        # 8. Adaptive Synthesis via Final LLM
        query_id_placeholder = int(time.time() * 1000) % 1_000_000
        synthesis: SynthesisResult = await self.synthesizer.synthesize(
            query_id=query_id_placeholder,
            query=req.query,
            structured_context=structured_context,
            synthesis_model=synthesis_model,
            preferences=preferences
        )

        # 9. Final Response Evaluation
        final_eval: FinalEvaluationResult = await self.final_evaluator.evaluate_final_response(
            query=req.query,
            synthesis=synthesis,
            ranked_candidates=ranked_candidates,
            preferences=preferences,
            evaluator_model=evaluator_model
        )

        # Total Resource Aggregates
        pipeline_tokens = sum(c.total_tokens for c in candidates) + synthesis.total_tokens
        pipeline_cost = round(sum(c.cost for c in candidates) + synthesis.cost, 6)
        total_latency_ms = int((time.perf_counter() - total_pipeline_start) * 1000)

        # 10. Research Storage in Database
        if self.db:
            try:
                # Query Record
                q_entity = QueryEntity(
                    query_text=req.query,
                    query_type=analysis.query_type,
                    domain=analysis.domain,
                    difficulty=analysis.difficulty,
                    expected_style=analysis.expected_style,
                    recommended_criteria=analysis.recommended_criteria
                )
                self.db.add(q_entity)
                await self.db.flush()

                # Preference Record
                pref_entity = PreferenceEntity(
                    user_id=None,
                    relevance_weight=preferences.relevance_weight,
                    correctness_weight=preferences.correctness_weight,
                    completeness_weight=preferences.completeness_weight,
                    clarity_weight=preferences.clarity_weight,
                    consistency_weight=preferences.consistency_weight,
                    preference_match_weight=preferences.preference_match_weight,
                    conciseness_weight=preferences.conciseness_weight,
                    technical_depth_weight=preferences.technical_depth_weight,
                    creativity_weight=preferences.creativity_weight,
                    cost_weight=preferences.cost_weight,
                    token_weight=preferences.token_weight,
                    latency_weight=preferences.latency_weight,
                    scoring_mode=preferences.scoring_mode
                )
                self.db.add(pref_entity)

                # Model Runs and Evaluations
                eval_dict = {e.response_id: e for e in evaluations}
                for c in candidates:
                    m_entity = ModelRunEntity(
                        query_id=q_entity.id,
                        model=c.model,
                        provider=c.provider,
                        response_text=c.response_text,
                        input_tokens=c.input_tokens,
                        output_tokens=c.output_tokens,
                        total_tokens=c.total_tokens,
                        cost=c.cost,
                        latency_ms=c.latency_ms,
                        status=c.status,
                        generation_id=c.generation_id,
                        error_message=c.error_message
                    )
                    self.db.add(m_entity)
                    await self.db.flush()

                    if c.response_id in eval_dict:
                        ev = eval_dict[c.response_id]
                        ev_entity = EvaluationEntity(
                            model_run_id=m_entity.id,
                            evaluator_model=ev.evaluator_model,
                            relevance=ev.relevance,
                            correctness=ev.correctness,
                            completeness=ev.completeness,
                            clarity=ev.clarity,
                            consistency=ev.consistency,
                            preference_match=ev.preference_match,
                            conciseness=ev.conciseness,
                            technical_depth=ev.technical_depth,
                            overall_score=ev.overall_score,
                            reasoning=ev.reasoning
                        )
                        self.db.add(ev_entity)

                # Conflict Record
                conf_entity = ConflictEntity(
                    query_id=q_entity.id,
                    topic=conflicts.topic,
                    description=f"{len(conflicts.contradictions)} contradictions identified. Consensus: {conflicts.consensus_level}",
                    severity="high" if any(c.severity == "high" for c in conflicts.contradictions) else "medium",
                    supporting_responses={"count": len(valid_candidates)},
                    agreement_points=conflicts.shared_information,
                    conflict_points=[c.model_dump() for c in conflicts.contradictions]
                )
                self.db.add(conf_entity)

                # Synthesis Run Record
                synth_entity = SynthesisRunEntity(
                    query_id=q_entity.id,
                    synthesis_model=synthesis.synthesis_model,
                    context=structured_context,
                    final_response=synthesis.final_response,
                    input_tokens=synthesis.input_tokens,
                    output_tokens=synthesis.output_tokens,
                    total_tokens=synthesis.total_tokens,
                    cost=synthesis.cost,
                    latency_ms=synthesis.latency_ms,
                    status=synthesis.status
                )
                self.db.add(synth_entity)
                await self.db.flush()

                # Final Evaluation Record
                fev_entity = FinalEvaluationEntity(
                    synthesis_run_id=synth_entity.id,
                    evaluator_model=final_eval.evaluator_model,
                    relevance=final_eval.relevance,
                    correctness=final_eval.correctness,
                    completeness=final_eval.completeness,
                    clarity=final_eval.clarity,
                    consistency=final_eval.consistency,
                    preference_match=final_eval.preference_match,
                    conciseness=final_eval.conciseness,
                    technical_depth=final_eval.technical_depth,
                    overall_score=final_eval.overall_score,
                    reasoning=final_eval.reasoning,
                    best_candidate_model=final_eval.best_candidate_model,
                    best_candidate_score=final_eval.best_candidate_score,
                    improvement_pct=final_eval.improvement_pct
                )
                self.db.add(fev_entity)
                await self.db.commit()
                query_id_placeholder = q_entity.id
            except Exception as e:
                log_stage("pipeline", f"Database persistence note: {e}")
                await self.db.rollback()

        log_stage("pipeline", "Complete pipeline finished successfully", elapsed=f"{total_latency_ms}ms")

        return PipelineRunResponse(
            query_id=query_id_placeholder,
            query_text=req.query,
            analysis=analysis,
            candidate_responses=candidates,
            evaluations=evaluations,
            ranking=ranked_candidates,
            conflicts=conflicts,
            structured_context=structured_context,
            synthesis=synthesis,
            final_evaluation=final_eval,
            total_pipeline_tokens=pipeline_tokens,
            total_pipeline_cost=pipeline_cost,
            total_pipeline_latency_ms=total_latency_ms,
            is_mock=not self.openrouter.has_api_key() or settings.MOCK_MODE
        )
