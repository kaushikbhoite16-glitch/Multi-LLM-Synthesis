"""
Ablation Study Runner — RQ (Ablation)
=========================================
Turns off one pipeline component at a time to measure each component's
contribution to the final synthesized answer quality.

Ablation configurations tested:
  1. Full System                   (all components active)
  2. No Conflict Analysis          (skip ConflictAnalyzer, use empty conflicts)
  3. No Multi-Criteria Scoring     (use equal weights for all criteria)
  4. No Response Normalization     (use raw scores without min-max)
  5. No Evaluation-Guided Context  (concatenate raw responses without scores)
  6. Best-of-N only                (no synthesis, pick top-scored candidate)

Each configuration is run on 10 representative benchmark queries and the
quality score of the final answer is recorded.
"""

import sys
import os
import asyncio
import json
import random
import time
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.services.openrouter_service import OpenRouterService
from app.services.evaluator import ResponseEvaluator
from app.services.scoring import ScoringEngine
from app.services.ranking import RankingEngine
from app.services.conflict_analyzer import ConflictAnalyzer
from app.services.context_builder import ContextBuilder
from app.services.synthesizer import SynthesizerService
from app.services.final_evaluator import FinalEvaluator
from app.schemas.pydantic_models import (
    PipelineRunRequest, UserPreferenceSchema, NormalizedResponse,
    ConflictAnalysisResult
)
from app.utils.logger import log_stage

ABLATION_QUERIES = [
    "Explain virtual memory in operating systems.",
    "What is the difference between a stack and a queue?",
    "Describe the key principles of object-oriented programming.",
    "What is gradient descent and how is it used in machine learning?",
    "Explain what happens when you type a URL in a browser.",
    "What is the CAP theorem in distributed systems?",
    "Describe the concept of recursion with an example.",
    "What is a hash table and when should you use one?",
    "Explain the difference between TCP and UDP protocols.",
    "What is Bayes' theorem and give a real-world application.",
]

MODELS = [
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-8b-instruct",
]

SYNTH_MODEL = "openai/gpt-4o-mini"

# Empty conflict result for the "No Conflict Analysis" ablation
EMPTY_CONFLICTS = ConflictAnalysisResult(
    topic="N/A",
    shared_information=["(Conflict analysis disabled for ablation)"],
    unique_information={},
    contradictions=[],
    potential_uncertainty=[],
    consensus_level="high"
)

# Equal-weight preferences for "No Multi-Criteria Scoring" ablation
EQUAL_PREFERENCES = UserPreferenceSchema(
    relevance_weight=0.125,
    correctness_weight=0.125,
    completeness_weight=0.125,
    clarity_weight=0.125,
    consistency_weight=0.125,
    preference_match_weight=0.125,
    conciseness_weight=0.125,
    technical_depth_weight=0.125,
    scoring_mode="quality-first"
)

DEFAULT_PREFERENCES = UserPreferenceSchema(
    relevance_weight=0.25,
    correctness_weight=0.30,
    completeness_weight=0.20,
    clarity_weight=0.15,
    consistency_weight=0.05,
    preference_match_weight=0.05,
    scoring_mode="balanced"
)


async def run_full_pipeline(
    query: str,
    openrouter: OpenRouterService,
    evaluator: ResponseEvaluator,
    conflict_analyzer: ConflictAnalyzer,
    synthesizer: SynthesizerService,
    final_evaluator: FinalEvaluator,
    preferences: UserPreferenceSchema,
    use_conflict: bool = True,
    use_scoring_weights: bool = True,
    use_evaluation_context: bool = True,
    best_of_n_only: bool = False,
) -> Dict[str, Any]:
    messages = [{"role": "user", "content": query}]

    # Stage 1: Generate candidates in parallel
    candidates = await openrouter.generate_parallel_responses(
        models=MODELS, messages=messages, max_tokens=600
    )
    valid = [c for c in candidates if c.status == "success"]
    if not valid:
        return {"quality_score": 0.0, "error": "all candidates failed"}

    # Stage 2: Evaluate
    prefs = preferences if use_scoring_weights else EQUAL_PREFERENCES
    evaluations = await evaluator.evaluate_candidates_parallel(
        query=query, preferences=prefs, candidates=valid,
        evaluator_model=SYNTH_MODEL
    )

    # Best-of-N ablation: skip synthesis entirely
    if best_of_n_only:
        best_eval = max(evaluations, key=lambda e: e.overall_score)
        return {
            "quality_score": round(best_eval.overall_score, 4),
            "tokens": sum(c.total_tokens for c in valid),
            "cost": sum(c.cost for c in valid),
        }

    # Stage 3: Rank
    ranked = RankingEngine.rank_responses(
        candidates=valid, evaluations=evaluations, preferences=prefs
    )

    # Stage 4: Conflict analysis (or skip)
    conflicts = EMPTY_CONFLICTS
    if use_conflict:
        conflicts = await conflict_analyzer.analyze_conflicts(
            query=query, candidates=valid, model=SYNTH_MODEL
        )

    # Stage 5: Context
    if use_evaluation_context:
        context = ContextBuilder.build_structured_context(
            query=query, ranked_candidates=ranked,
            conflicts=conflicts, preferences=prefs
        )
    else:
        # Minimal raw concatenation — no scores or ranks shown
        context = f"USER QUERY:\n{query}\n\nCANDIDATE RESPONSES:\n"
        for i, c in enumerate(valid):
            context += f"\nResponse {i+1}:\n{c.response_text}\n"
        context += "\nSynthesize the best possible answer."

    # Stage 6: Synthesize
    synthesis = await synthesizer.synthesize(
        query_id=0, query=query,
        structured_context=context, synthesis_model=SYNTH_MODEL, preferences=prefs
    )

    # Stage 7: Final eval
    final_eval = await final_evaluator.evaluate_final_response(
        query=query, synthesis=synthesis,
        ranked_candidates=ranked, preferences=prefs, evaluator_model=SYNTH_MODEL
    )

    return {
        "quality_score": round(final_eval.overall_score, 4),
        "tokens": sum(c.total_tokens for c in valid) + synthesis.total_tokens,
        "cost": round(sum(c.cost for c in valid) + synthesis.cost, 6),
        "improvement_pct": round(final_eval.improvement_pct, 2),
    }


async def main():
    openrouter = OpenRouterService()
    evaluator = ResponseEvaluator(openrouter)
    conflict_analyzer = ConflictAnalyzer(openrouter)
    synthesizer = SynthesizerService(openrouter)
    final_eval_svc = FinalEvaluator(evaluator)

    ABLATION_CONFIGS = [
        {"name": "Full System",                  "use_conflict": True,  "use_scoring_weights": True,  "use_evaluation_context": True,  "best_of_n_only": False},
        {"name": "No Conflict Analysis",         "use_conflict": False, "use_scoring_weights": True,  "use_evaluation_context": True,  "best_of_n_only": False},
        {"name": "No Multi-Criteria Scoring",    "use_conflict": True,  "use_scoring_weights": False, "use_evaluation_context": True,  "best_of_n_only": False},
        {"name": "No Evaluation-Guided Context", "use_conflict": True,  "use_scoring_weights": True,  "use_evaluation_context": False, "best_of_n_only": False},
        {"name": "Best-of-N Only (No Synthesis)","use_conflict": False, "use_scoring_weights": True,  "use_evaluation_context": False, "best_of_n_only": True},
    ]

    all_results = []

    print("=" * 60)
    print("ABLATION STUDY — Component Contribution Analysis")
    print("=" * 60)
    print(f"Queries: {len(ABLATION_QUERIES)} | Models: {MODELS}")
    print()

    for config in ABLATION_CONFIGS:
        name = config["name"]
        config_scores = []
        print(f"\n[CONFIG] {name}")

        for qi, query in enumerate(ABLATION_QUERIES):
            print(f"  Query {qi+1:02d}/{len(ABLATION_QUERIES)}: {query[:50]}...")
            try:
                result = await run_full_pipeline(
                    query=query,
                    openrouter=openrouter,
                    evaluator=evaluator,
                    conflict_analyzer=conflict_analyzer,
                    synthesizer=synthesizer,
                    final_evaluator=final_eval_svc,
                    preferences=DEFAULT_PREFERENCES,
                    use_conflict=config["use_conflict"],
                    use_scoring_weights=config["use_scoring_weights"],
                    use_evaluation_context=config["use_evaluation_context"],
                    best_of_n_only=config["best_of_n_only"],
                )
                score = result.get("quality_score", 0.0)
                config_scores.append(score)
                all_results.append({
                    "configuration": name,
                    "query": query,
                    "quality_score": score,
                    "tokens": result.get("tokens", 0),
                    "cost": result.get("cost", 0.0),
                    "improvement_pct": result.get("improvement_pct", 0.0),
                })
                print(f"    → Score: {score:.4f}")
            except Exception as e:
                print(f"    [ERROR] {e}")

        if config_scores:
            mean_q = sum(config_scores) / len(config_scores)
            print(f"\n  → Mean Quality Score for '{name}': {mean_q:.4f}")

    # Save results
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ablation_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n\nResults saved to: {out_path}")

    # Print summary table
    print("\n" + "=" * 60)
    print("ABLATION SUMMARY TABLE")
    print(f"{'Configuration':<45} {'Mean Q':>8} {'#Samples':>10}")
    print("-" * 65)
    from collections import defaultdict
    config_agg = defaultdict(list)
    for r in all_results:
        config_agg[r["configuration"]].append(r["quality_score"])
    for cfg_name, scores in config_agg.items():
        print(f"{cfg_name:<45} {sum(scores)/len(scores):>8.4f} {len(scores):>10}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
