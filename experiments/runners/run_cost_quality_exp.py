import os
import sys
import json
import asyncio

sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("backend"))

from app.services.pipeline import PipelineOrchestrator
from app.schemas.pydantic_models import PipelineRunRequest, UserPreferenceSchema

async def main():
    print("=" * 70)
    print("RUNNING COST-QUALITY TRADEOFF & SCALING EXPERIMENT (RQ4)")
    print("Evaluating scaling behavior: 1, 2, 3, 4, and 5 candidate models")
    print("=" * 70)

    orchestrator = PipelineOrchestrator(db=None)
    query = "Explain the mechanics of page thrashing in virtual memory and how working set algorithms prevent it."
    
    all_models = [
        "google/gemini-2.0-flash-001",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku",
        "meta-llama/llama-3.1-8b-instruct",
        "mistralai/mistral-7b-instruct"
    ]

    scaling_results = []

    for k in range(1, len(all_models) + 1):
        subset = all_models[:k]
        print(f"\nTesting with k={k} models: {subset[-1]}")
        res = await orchestrator.execute_pipeline(
            PipelineRunRequest(query=query, models=subset, preferences=UserPreferenceSchema())
        )
        scaling_results.append({
            "k_models": k,
            "models": subset,
            "quality_score": res.final_evaluation.overall_score,
            "best_candidate_score": res.final_evaluation.best_candidate_score,
            "cost": res.total_pipeline_cost,
            "tokens": res.total_pipeline_tokens,
            "latency_ms": res.total_pipeline_latency_ms
        })

    print("\n" + "=" * 70)
    print(f"{'K MODELS':<10} | {'FINAL QUALITY':<15} | {'PIPELINE COST':<15} | {'TOKENS':<10} | {'LATENCY'}")
    print("-" * 70)
    for r in scaling_results:
        print(f"{r['k_models']:<10} | {r['quality_score']:<15.2f} | ${r['cost']:<14.5f} | {r['tokens']:<10} | {r['latency_ms']}ms")
    print("=" * 70)

    with open("experiments/results/cost_quality_scaling_results.json", "w", encoding="utf-8") as f:
        json.dump(scaling_results, f, indent=2)
    print("Saved results to experiments/results/cost_quality_scaling_results.json")

if __name__ == "__main__":
    asyncio.run(main())
