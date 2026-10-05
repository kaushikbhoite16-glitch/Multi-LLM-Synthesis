import os
import sys
import json
import asyncio

sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("backend"))

from app.services.openrouter_service import OpenRouterService
from app.services.evaluator import ResponseEvaluator
from app.schemas.pydantic_models import NormalizedResponse

async def main():
    print("=" * 70)
    print("RUNNING EVALUATOR BIAS & INTER-RATER RELIABILITY EXPERIMENT (RQ5)")
    print("=" * 70)

    openrouter = OpenRouterService()
    evaluator = ResponseEvaluator(openrouter)

    query = "Explain the mechanics of the Translation Lookaside Buffer (TLB) and address translation."
    candidate_models = [
        "google/gemini-2.0-flash-001",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    evaluators = [
        "google/gemini-2.0-flash-001",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku"
    ]

    print(f"Generating candidate responses for {len(candidate_models)} models...")
    messages = [{"role": "user", "content": query}]
    candidates = await openrouter.generate_parallel_responses(models=candidate_models, messages=messages)

    evaluator_rankings = {}
    evaluator_scores = {}

    for ev_model in evaluators:
        print(f"Running evaluation with {ev_model}...")
        results = await evaluator.evaluate_candidates_parallel(
            query=query,
            preferences=None,
            candidates=candidates,
            evaluator_model=ev_model
        )
        sorted_res = sorted(results, key=lambda x: x.overall_score, reverse=True)
        evaluator_rankings[ev_model] = [r.model for r in sorted_res]
        evaluator_scores[ev_model] = {r.model: r.overall_score for r in sorted_res}

    print("\n" + "=" * 70)
    print("EVALUATOR RANKING COMPARISON MATRIX")
    print("=" * 70)
    for ev_model, ranking in evaluator_rankings.items():
        print(f"\nEvaluator: {ev_model}")
        for rank, m in enumerate(ranking, 1):
            score = evaluator_scores[ev_model][m]
            print(f"  Rank #{rank}: {m:<35} | Score: {score}")

    # Compute agreement
    top_picks = [ranking[0] for ranking in evaluator_rankings.values()]
    consensus = len(set(top_picks)) == 1
    print("\n" + "-" * 70)
    print(f"Consensus on Top-Ranked Candidate: {'Unanimous' if consensus else 'Divergent'}")
    print(f"Top Candidate Selections: {top_picks}")
    print("=" * 70)

    out_data = {
        "query": query,
        "evaluators": evaluators,
        "rankings": evaluator_rankings,
        "scores": evaluator_scores,
        "consensus_on_top": consensus
    }
    with open("experiments/results/evaluator_bias_results.json", "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
    print("Saved results to experiments/results/evaluator_bias_results.json")

if __name__ == "__main__":
    asyncio.run(main())
