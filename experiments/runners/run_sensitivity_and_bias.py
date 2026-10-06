"""
Weight Sensitivity & Evaluator Bias Analysis
=============================================
RQ3 — Sensitivity: How much does the final answer change as preference
       weights vary (e.g., relevance 10% → 50%)?

RQ5 — Evaluator Bias: Does the evaluator model choice systematically
       bias candidate rankings? Measures Spearman rank correlation
       between rankings produced by different evaluator models.

This addresses the reviewer concern:
  "If relevance is weighted 50% vs 10%, does the answer change?"
"""

import sys
import os
import asyncio
import json
import math
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.services.openrouter_service import OpenRouterService
from app.services.evaluator import ResponseEvaluator
from app.services.scoring import ScoringEngine
from app.services.ranking import RankingEngine
from app.schemas.pydantic_models import UserPreferenceSchema, NormalizedResponse

SENSITIVITY_QUERY = "Explain the difference between synchronous and asynchronous programming."

MODELS = [
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-8b-instruct",
]

EVALUATOR_MODELS = [
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-8b-instruct",
]

# Weight configurations sweeping relevance from 10% to 50%
WEIGHT_CONFIGS = [
    ("Relevance=10%",  UserPreferenceSchema(relevance_weight=0.10, correctness_weight=0.35, completeness_weight=0.25, clarity_weight=0.20, consistency_weight=0.05, preference_match_weight=0.05, scoring_mode="balanced")),
    ("Relevance=20%",  UserPreferenceSchema(relevance_weight=0.20, correctness_weight=0.30, completeness_weight=0.20, clarity_weight=0.20, consistency_weight=0.05, preference_match_weight=0.05, scoring_mode="balanced")),
    ("Relevance=30%",  UserPreferenceSchema(relevance_weight=0.30, correctness_weight=0.25, completeness_weight=0.20, clarity_weight=0.15, consistency_weight=0.05, preference_match_weight=0.05, scoring_mode="balanced")),
    ("Relevance=40%",  UserPreferenceSchema(relevance_weight=0.40, correctness_weight=0.20, completeness_weight=0.15, clarity_weight=0.15, consistency_weight=0.05, preference_match_weight=0.05, scoring_mode="balanced")),
    ("Relevance=50%",  UserPreferenceSchema(relevance_weight=0.50, correctness_weight=0.15, completeness_weight=0.15, clarity_weight=0.10, consistency_weight=0.05, preference_match_weight=0.05, scoring_mode="balanced")),
    ("Correctness=50%",UserPreferenceSchema(relevance_weight=0.15, correctness_weight=0.50, completeness_weight=0.15, clarity_weight=0.10, consistency_weight=0.05, preference_match_weight=0.05, scoring_mode="balanced")),
    ("Cost-Aware",     UserPreferenceSchema(relevance_weight=0.20, correctness_weight=0.20, completeness_weight=0.15, clarity_weight=0.15, consistency_weight=0.05, preference_match_weight=0.05, cost_weight=0.15, token_weight=0.05, latency_weight=0.0, scoring_mode="cost-aware")),
    ("Quality-First",  UserPreferenceSchema(relevance_weight=0.25, correctness_weight=0.30, completeness_weight=0.20, clarity_weight=0.15, consistency_weight=0.05, preference_match_weight=0.05, scoring_mode="quality-first")),
]


def spearman_rho(x: List[float], y: List[float]) -> float:
    n = len(x)
    if n < 2:
        return 0.0
    def rank(lst):
        sorted_idx = sorted(range(n), key=lambda i: lst[i])
        r = [0.0] * n
        for rank_pos, orig_idx in enumerate(sorted_idx):
            r[orig_idx] = rank_pos + 1
        return r
    rx, ry = rank(x), rank(y)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - (6 * d2) / (n * (n * n - 1))


async def main():
    openrouter = OpenRouterService()
    evaluator = ResponseEvaluator(openrouter)

    print("=" * 65)
    print("WEIGHT SENSITIVITY & EVALUATOR BIAS ANALYSIS")
    print("=" * 65)

    # ─── Step 1: Generate candidates once ──────────────────
    print(f"\nGenerating candidates for:\n  {SENSITIVITY_QUERY}\n")
    messages = [{"role": "user", "content": SENSITIVITY_QUERY}]
    candidates = await openrouter.generate_parallel_responses(
        models=MODELS, messages=messages, max_tokens=600
    )
    valid = [c for c in candidates if c.status == "success"]
    print(f"  Candidates generated: {len(valid)}\n")

    all_results = []

    # ─── Step 2: Weight Sensitivity (RQ3) ─────────────────
    print("[RQ3] WEIGHT SENSITIVITY ANALYSIS")
    print("-" * 65)
    print(f"  Evaluator: {EVALUATOR_MODELS[0]}")

    reference_ranking = None
    sensitivity_results = []

    for config_name, prefs in WEIGHT_CONFIGS:
        evals = await evaluator.evaluate_candidates_parallel(
            query=SENSITIVITY_QUERY, preferences=prefs,
            candidates=valid, evaluator_model=EVALUATOR_MODELS[0]
        )
        ranked = RankingEngine.rank_responses(
            candidates=valid, evaluations=evals, preferences=prefs
        )
        rank_order = [r.model for r in ranked]
        scores = [r.overall_score for r in ranked]

        if reference_ranking is None:
            reference_ranking = rank_order

        rank_changed = rank_order != reference_ranking
        entry = {
            "config": config_name,
            "rank_order": rank_order,
            "scores": [round(s, 4) for s in scores],
            "rank_changed_vs_reference": rank_changed,
        }
        sensitivity_results.append(entry)
        all_results.append({"type": "sensitivity", **entry})

        print(f"  {config_name:<22}: {rank_order} | Scores={[round(s,3) for s in scores]} | Rank changed={rank_changed}")

    changes = sum(1 for r in sensitivity_results if r["rank_changed_vs_reference"])
    print(f"\n  Ranking changed in {changes}/{len(sensitivity_results)} configurations")
    print(f"  Sensitivity: {'HIGH' if changes >= 3 else ('MEDIUM' if changes >= 1 else 'LOW')}")

    # ─── Step 3: Evaluator Bias (RQ5) ─────────────────────
    print("\n[RQ5] EVALUATOR BIAS ANALYSIS")
    print("-" * 65)
    print(f"  Evaluator models: {EVALUATOR_MODELS}")

    default_prefs = UserPreferenceSchema(
        relevance_weight=0.25, correctness_weight=0.30,
        completeness_weight=0.20, clarity_weight=0.15,
        consistency_weight=0.05, preference_match_weight=0.05,
        scoring_mode="balanced"
    )

    evaluator_rankings = {}
    evaluator_scores   = {}

    for eval_model in EVALUATOR_MODELS:
        print(f"\n  Evaluator: {eval_model}")
        evals = await evaluator.evaluate_candidates_parallel(
            query=SENSITIVITY_QUERY, preferences=default_prefs,
            candidates=valid, evaluator_model=eval_model
        )
        ranked = RankingEngine.rank_responses(
            candidates=valid, evaluations=evals, preferences=default_prefs
        )
        scores = {r.model: r.overall_score for r in ranked}
        rank_order = [r.model for r in ranked]
        evaluator_rankings[eval_model] = rank_order
        evaluator_scores[eval_model]   = scores

        for r in ranked:
            print(f"    #{r.rank} {r.model:<45} Score={r.overall_score:.4f}")
        all_results.append({
            "type": "evaluator_bias",
            "evaluator": eval_model,
            "rank_order": rank_order,
            "scores": {m: round(s, 4) for m, s in scores.items()},
        })

    # Compute Spearman correlation between evaluators
    if len(EVALUATOR_MODELS) >= 2:
        models_in_common = list(valid[0].model if valid else [])
        all_models = [c.model for c in valid]

        e1 = EVALUATOR_MODELS[0]
        e2 = EVALUATOR_MODELS[1]
        s1 = [evaluator_scores[e1].get(m, 0) for m in all_models]
        s2 = [evaluator_scores[e2].get(m, 0) for m in all_models]
        rho = spearman_rho(s1, s2)
        print(f"\n  Spearman rank correlation ({e1} vs {e2}): ρ = {rho:.4f}")
        print(f"  Evaluator agreement: {'strong (ρ>0.7)' if rho > 0.7 else ('moderate (0.4<ρ<0.7)' if rho > 0.4 else 'weak (ρ<0.4)')}")
        all_results.append({
            "type": "spearman_correlation",
            "evaluator_1": e1,
            "evaluator_2": e2,
            "spearman_rho": round(rho, 4),
        })

    # ─── Save ───────────────────────────────────────────────
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)

    sensitivity_path = os.path.join(out_dir, "sensitivity_results.json")
    bias_path        = os.path.join(out_dir, "evaluator_bias_results.json")

    with open(sensitivity_path, "w") as f:
        json.dump([r for r in all_results if r["type"] == "sensitivity"], f, indent=2)
    with open(bias_path, "w") as f:
        json.dump([r for r in all_results if r["type"] in ("evaluator_bias", "spearman_correlation")], f, indent=2)

    print(f"\nSaved:\n  {sensitivity_path}\n  {bias_path}")
    print("\n" + "=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
