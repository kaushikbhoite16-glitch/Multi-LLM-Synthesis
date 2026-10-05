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
    print("RUNNING MODEL DIVERSITY EXPERIMENT (RQ6)")
    print("Comparing Homogeneous Pool (Same Model x 4) vs Heterogeneous Pool")
    print("=" * 70)

    orchestrator = PipelineOrchestrator(db=None)
    query = "Explain copy-on-write (CoW) in operating systems and its impact on fork() latency and physical memory."

    # Group A: Homogeneous (Same Model x 4)
    models_homo = [
        "openai/gpt-4o-mini",
        "openai/gpt-4o-mini",
        "openai/gpt-4o-mini",
        "openai/gpt-4o-mini"
    ]

    # Group B: Heterogeneous (4 distinct providers/architectures)
    models_hetero = [
        "google/gemini-2.0-flash-001",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku",
        "meta-llama/llama-3.1-8b-instruct"
    ]

    print("\nExecuting Group A: Homogeneous Pool (GPT-4o Mini x 4)...")
    res_a = await orchestrator.execute_pipeline(
        PipelineRunRequest(query=query, models=models_homo, preferences=UserPreferenceSchema())
    )

    print("\nExecuting Group B: Heterogeneous Pool (Gemini + OpenAI + Claude + Llama)...")
    res_b = await orchestrator.execute_pipeline(
        PipelineRunRequest(query=query, models=models_hetero, preferences=UserPreferenceSchema())
    )

    print("\n" + "=" * 70)
    print(f"{'METRIC':<30} | {'HOMOGENEOUS':<15} | {'HETEROGENEOUS':<15}")
    print("-" * 70)
    print(f"{'Final Synthesized Score':<30} | {res_a.final_evaluation.overall_score:<15.2f} | {res_b.final_evaluation.overall_score:<15.2f}")
    print(f"{'Best Candidate Score':<30} | {res_a.final_evaluation.best_candidate_score:<15.2f} | {res_b.final_evaluation.best_candidate_score:<15.2f}")
    print(f"{'Synthesis Improvement %':<30} | {res_a.final_evaluation.improvement_pct:<15.2f} | {res_b.final_evaluation.improvement_pct:<15.2f}")
    print(f"{'Unique Claim Count':<30} | {len(res_a.conflicts.unique_information):<15} | {len(res_b.conflicts.unique_information):<15}")
    print(f"{'Total Cost':<30} | ${res_a.total_pipeline_cost:<14.5f} | ${res_b.total_pipeline_cost:<14.5f}")
    print("=" * 70)

    out = {
        "query": query,
        "homogeneous": {
            "score": res_a.final_evaluation.overall_score,
            "cost": res_a.total_pipeline_cost,
            "tokens": res_a.total_pipeline_tokens,
            "unique_claims": len(res_a.conflicts.unique_information)
        },
        "heterogeneous": {
            "score": res_b.final_evaluation.overall_score,
            "cost": res_b.total_pipeline_cost,
            "tokens": res_b.total_pipeline_tokens,
            "unique_claims": len(res_b.conflicts.unique_information)
        }
    }
    with open("experiments/results/model_diversity_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Saved results to experiments/results/model_diversity_results.json")

if __name__ == "__main__":
    asyncio.run(main())
