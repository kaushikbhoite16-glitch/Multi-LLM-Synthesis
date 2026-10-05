import sys
import os
import asyncio
from typing import Dict, Any, List

sys.path.append(os.path.abspath("backend"))

from app.services.openrouter_service import OpenRouterService
from app.services.evaluator import ResponseEvaluator
from app.services.pipeline import PipelineOrchestrator
from app.schemas.pydantic_models import PipelineRunRequest, UserPreferenceSchema, NormalizedResponse, EvaluationResult

class BaselineSuite:
    def __init__(self):
        self.openrouter = OpenRouterService()
        self.evaluator = ResponseEvaluator(self.openrouter)
        self.orchestrator = PipelineOrchestrator(db=None)

    async def run_baseline_1_single(self, query: str, model: str = "openai/gpt-4o-mini") -> Dict[str, Any]:
        """Baseline 1: Single LLM Query"""
        messages = [{"role": "user", "content": query}]
        resp = await self.openrouter.generate_response(model=model, messages=messages)
        eval_res = await self.evaluator.evaluate_single(query=query, preferences=None, response=resp)
        return {
            "method": "Baseline 1: Single LLM",
            "quality_score": eval_res.overall_score,
            "cost": resp.cost,
            "tokens": resp.total_tokens,
            "latency_ms": resp.latency_ms,
            "response": resp.response_text
        }

    async def run_baseline_2_best_selection(self, query: str, models: List[str]) -> Dict[str, Any]:
        """Baseline 2: Best Response Selection from Multiple LLMs"""
        messages = [{"role": "user", "content": query}]
        candidates = await self.openrouter.generate_parallel_responses(models=models, messages=messages)
        evals = await self.evaluator.evaluate_candidates_parallel(query=query, preferences=None, candidates=candidates)
        
        # Select highest quality score
        best_eval = max(evals, key=lambda e: e.overall_score)
        best_cand = next(c for c in candidates if c.response_id == best_eval.response_id)
        
        total_cost = sum(c.cost for c in candidates)
        total_tokens = sum(c.total_tokens for c in candidates)
        max_latency = max(c.latency_ms for c in candidates)
        
        return {
            "method": "Baseline 2: Best Response Selection",
            "quality_score": best_eval.overall_score,
            "cost": total_cost,
            "tokens": total_tokens,
            "latency_ms": max_latency,
            "selected_model": best_cand.model,
            "response": best_cand.response_text
        }

    async def run_baseline_3_simple_synthesis(self, query: str, models: List[str], synth_model: str) -> Dict[str, Any]:
        """Baseline 3: Simple Multi-LLM Synthesis (Raw Concatenation without Evaluation or Conflict Analysis)"""
        messages = [{"role": "user", "content": query}]
        candidates = await self.openrouter.generate_parallel_responses(models=models, messages=messages)
        
        raw_concat = "\n\n".join([f"Model {c.model}:\n{c.response_text}" for c in candidates])
        synth_messages = [
            {"role": "system", "content": "Synthesize a single response to the query using these candidate answers."},
            {"role": "user", "content": f"Query: {query}\n\nCandidate Answers:\n{raw_concat}"}
        ]
        synth_resp = await self.openrouter.generate_response(model=synth_model, messages=synth_messages)
        eval_res = await self.evaluator.evaluate_single(query=query, preferences=None, response=synth_resp)
        
        total_cost = sum(c.cost for c in candidates) + synth_resp.cost
        total_tokens = sum(c.total_tokens for c in candidates) + synth_resp.total_tokens
        latency = max(c.latency_ms for c in candidates) + synth_resp.latency_ms
        
        return {
            "method": "Baseline 3: Simple Multi-LLM Synthesis",
            "quality_score": eval_res.overall_score,
            "cost": round(total_cost, 6),
            "tokens": total_tokens,
            "latency_ms": latency,
            "response": synth_resp.response_text
        }

    async def run_baseline_4_eval_guided_synthesis(self, query: str, models: List[str], synth_model: str) -> Dict[str, Any]:
        """Baseline 4: Evaluation-Guided Synthesis (Candidate Scores Provided, but No Conflict Resolution)"""
        messages = [{"role": "user", "content": query}]
        candidates = await self.openrouter.generate_parallel_responses(models=models, messages=messages)
        evals = await self.evaluator.evaluate_candidates_parallel(query=query, preferences=None, candidates=candidates)
        
        scored_context = "\n\n".join([
            f"Model {c.model} (Score: {e.overall_score}/10):\n{c.response_text}"
            for c, e in zip(candidates, evals)
        ])
        synth_messages = [
            {"role": "system", "content": "Synthesize a response using these evaluated candidate responses. Focus on higher-scoring responses."},
            {"role": "user", "content": f"Query: {query}\n\n{scored_context}"}
        ]
        synth_resp = await self.openrouter.generate_response(model=synth_model, messages=synth_messages)
        eval_res = await self.evaluator.evaluate_single(query=query, preferences=None, response=synth_resp)
        
        total_cost = sum(c.cost for c in candidates) + synth_resp.cost
        total_tokens = sum(c.total_tokens for c in candidates) + synth_resp.total_tokens
        latency = max(c.latency_ms for c in candidates) + synth_resp.latency_ms
        
        return {
            "method": "Baseline 4: Evaluation-Guided Synthesis",
            "quality_score": eval_res.overall_score,
            "cost": round(total_cost, 6),
            "tokens": total_tokens,
            "latency_ms": latency,
            "response": synth_resp.response_text
        }

    async def run_proposed_system(self, query: str, models: List[str], synth_model: str) -> Dict[str, Any]:
        """Proposed System: Full Multi-LLM Evaluation, Conflict Resolution, and Adaptive Answer Synthesis"""
        req = PipelineRunRequest(
            query=query,
            models=models,
            synthesis_model=synth_model,
            preferences=UserPreferenceSchema(scoring_mode="balanced")
        )
        res = await self.orchestrator.execute_pipeline(req)
        return {
            "method": "Proposed System (Adaptive Synthesis)",
            "quality_score": res.final_evaluation.overall_score,
            "cost": res.total_pipeline_cost,
            "tokens": res.total_pipeline_tokens,
            "latency_ms": res.total_pipeline_latency_ms,
            "improvement_pct": res.final_evaluation.improvement_pct,
            "conflicts_count": len(res.conflicts.contradictions),
            "response": res.synthesis.final_response
        }
