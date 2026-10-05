import os
import sys
import json
import asyncio

sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("backend"))
from experiments.baselines.baselines import BaselineSuite

async def main():
    print("=" * 70)
    print("RUNNING MULTI-BASELINE RESEARCH EXPERIMENT")
    print("=" * 70)
    
    suite = BaselineSuite()
    query = "Explain virtual memory in operating systems, paging mechanisms, and page fault handling."
    models = [
        "google/gemini-2.0-flash-001",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    synth_model = "anthropic/claude-3.5-sonnet"

    print(f"\nQuery: {query}")
    print(f"Candidate Models ({len(models)}): {', '.join(models)}")
    print(f"Synthesizer Model: {synth_model}\n")

    print("Running Baseline 1 (Single LLM)...")
    b1 = await suite.run_baseline_1_single(query)

    print("Running Baseline 2 (Best Response Selection)...")
    b2 = await suite.run_baseline_2_best_selection(query, models)

    print("Running Baseline 3 (Simple Multi-LLM Synthesis)...")
    b3 = await suite.run_baseline_3_simple_synthesis(query, models, synth_model)

    print("Running Baseline 4 (Evaluation-Guided Synthesis)...")
    b4 = await suite.run_baseline_4_eval_guided_synthesis(query, models, synth_model)

    print("Running Proposed System (Adaptive Multi-Criteria Synthesis)...")
    proposed = await suite.run_proposed_system(query, models, synth_model)

    results = [b1, b2, b3, b4, proposed]

    print("\n" + "=" * 80)
    print(f"{'METHOD':<48} | {'QUALITY':<7} | {'COST':<10} | {'TOKENS':<6} | {'LATENCY'}")
    print("-" * 80)
    for r in results:
        print(f"{r['method']:<48} | {r['quality_score']:<7.2f} | ${r['cost']:<9.5f} | {r['tokens']:<6} | {r['latency_ms']}ms")
    print("=" * 80)

    # Save to experiments/results/baseline_comparison_results.json
    os.makedirs("experiments/results", exist_ok=True)
    with open("experiments/results/baseline_comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nResults successfully saved to experiments/results/baseline_comparison_results.json")

if __name__ == "__main__":
    asyncio.run(main())
