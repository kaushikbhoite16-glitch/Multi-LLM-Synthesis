"""
Model Diversity Analysis — RQ6
===================================
Quantifies linguistic and semantic diversity of candidate model responses
using n-gram overlap and embedding distance metrics, then correlates
diversity level with synthesis quality improvement.

Research question:
  Do more diverse model pools yield higher-quality synthesis outputs
  than homogeneous pools of similar models?

Methods:
  - Pairwise BLEU-based n-gram overlap (inverse = diversity)
  - Jaccard similarity at token level (inverse = diversity)
  - Vocabulary diversity ratio (unique tokens / total tokens)
  - Correlation: diversity score vs improvement_pct
"""

import sys
import os
import asyncio
import json
import math
import re
from typing import List, Dict, Any, Tuple
from collections import Counter
from itertools import combinations

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.services.openrouter_service import OpenRouterService
from app.services.evaluator import ResponseEvaluator
from app.services.scoring import ScoringEngine
from app.services.ranking import RankingEngine
from app.services.conflict_analyzer import ConflictAnalyzer
from app.services.context_builder import ContextBuilder
from app.services.synthesizer import SynthesizerService
from app.services.final_evaluator import FinalEvaluator
from app.schemas.pydantic_models import UserPreferenceSchema

QUERIES = [
    "Explain virtual memory in operating systems.",
    "What is the difference between a process and a thread?",
    "Describe how a neural network learns through backpropagation.",
    "What is a database index and why does it improve query performance?",
    "Explain the concept of recursion with a real-world analogy.",
]

HOMOGENEOUS_POOL = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o-mini",   # same model twice — will generate similar outputs
]

HETEROGENEOUS_POOL = [
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-8b-instruct",
]

DEFAULT_PREFERENCES = UserPreferenceSchema(
    relevance_weight=0.25,
    correctness_weight=0.30,
    completeness_weight=0.20,
    clarity_weight=0.15,
    consistency_weight=0.05,
    preference_match_weight=0.05,
    scoring_mode="balanced",
    max_tokens=600,
)


# ─────────────────────────────────────────────────────────────
# Diversity Metrics
# ─────────────────────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    return re.findall(r'\b\w+\b', text.lower())


def ngrams(tokens: List[str], n: int) -> Counter:
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))


def modified_precision(ref_tokens: List[str], hyp_tokens: List[str], n: int) -> float:
    """Compute BLEU n-gram precision between two texts."""
    hyp_ngrams = ngrams(hyp_tokens, n)
    ref_ngrams = ngrams(ref_tokens, n)
    clipped = {gram: min(count, ref_ngrams.get(gram, 0)) for gram, count in hyp_ngrams.items()}
    num = sum(clipped.values())
    denom = max(1, sum(hyp_ngrams.values()))
    return num / denom


def pairwise_overlap(texts: List[str]) -> float:
    """
    Mean pairwise BLEU-1 n-gram overlap across all response pairs.
    Lower = more diverse.
    """
    if len(texts) < 2:
        return 1.0
    scores = []
    for a, b in combinations(texts, 2):
        tok_a = tokenize(a)
        tok_b = tokenize(b)
        if not tok_a or not tok_b:
            continue
        scores.append(modified_precision(tok_a, tok_b, 1))
    return sum(scores) / len(scores) if scores else 1.0


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """Token-level Jaccard similarity."""
    set_a = set(tokenize(text_a))
    set_b = set(tokenize(text_b))
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def vocabulary_diversity(texts: List[str]) -> float:
    """Ratio of unique tokens to total tokens across all responses."""
    all_tokens = []
    for t in texts:
        all_tokens.extend(tokenize(t))
    if not all_tokens:
        return 0.0
    return len(set(all_tokens)) / len(all_tokens)


def diversity_score(texts: List[str]) -> float:
    """
    Composite diversity score (0=identical, 1=maximally diverse):
      0.5 × (1 - overlap) + 0.3 × (1 - avg_jaccard) + 0.2 × vocab_diversity
    """
    if len(texts) < 2:
        return 0.0
    overlap = pairwise_overlap(texts)
    avg_jaccard = sum(
        jaccard_similarity(a, b)
        for a, b in combinations(texts, 2)
    ) / max(1, len(list(combinations(texts, 2))))
    vocab_div = vocabulary_diversity(texts)
    return round(0.5 * (1 - overlap) + 0.3 * (1 - avg_jaccard) + 0.2 * vocab_div, 4)


# ─────────────────────────────────────────────────────────────
# Pipeline Helper
# ─────────────────────────────────────────────────────────────

async def run_pipeline_with_pool(query: str, models: List[str],
                                  openrouter, evaluator, conflict_analyzer,
                                  synthesizer, final_evaluator) -> Dict[str, Any]:
    messages = [{"role": "user", "content": query}]
    candidates = await openrouter.generate_parallel_responses(
        models=models, messages=messages, max_tokens=600
    )
    valid = [c for c in candidates if c.status == "success"]
    if not valid:
        return {}

    evaluations = await evaluator.evaluate_candidates_parallel(
        query=query, preferences=DEFAULT_PREFERENCES, candidates=valid,
        evaluator_model="openai/gpt-4o-mini"
    )
    ranked = RankingEngine.rank_responses(
        candidates=valid, evaluations=evaluations, preferences=DEFAULT_PREFERENCES
    )
    conflicts = await conflict_analyzer.analyze_conflicts(
        query=query, candidates=valid, model="openai/gpt-4o-mini"
    )
    context = ContextBuilder.build_structured_context(
        query=query, ranked_candidates=ranked,
        conflicts=conflicts, preferences=DEFAULT_PREFERENCES
    )
    synthesis = await synthesizer.synthesize(
        query_id=0, query=query, structured_context=context,
        synthesis_model="openai/gpt-4o-mini", preferences=DEFAULT_PREFERENCES
    )
    final_eval = await final_evaluator.evaluate_final_response(
        query=query, synthesis=synthesis,
        ranked_candidates=ranked, preferences=DEFAULT_PREFERENCES,
        evaluator_model="openai/gpt-4o-mini"
    )

    texts = [c.response_text for c in valid]
    div = diversity_score(texts)

    return {
        "diversity_score": div,
        "pairwise_overlap": round(pairwise_overlap(texts), 4),
        "vocabulary_diversity": round(vocabulary_diversity(texts), 4),
        "quality_score": round(final_eval.overall_score, 4),
        "improvement_pct": round(final_eval.improvement_pct, 2),
        "unique_claims": len(conflicts.unique_information),
        "n_contradictions": len(conflicts.contradictions),
        "consensus_level": conflicts.consensus_level,
        "tokens": sum(c.total_tokens for c in valid) + synthesis.total_tokens,
        "cost": round(sum(c.cost for c in valid) + synthesis.cost, 6),
    }


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

async def main():
    openrouter = OpenRouterService()
    evaluator = ResponseEvaluator(openrouter)
    conflict_analyzer = ConflictAnalyzer(openrouter)
    synthesizer = SynthesizerService(openrouter)
    final_eval_svc = FinalEvaluator(evaluator)

    print("=" * 65)
    print("MODEL DIVERSITY ANALYSIS — RQ6")
    print("=" * 65)
    print("Comparing homogeneous vs heterogeneous model pools\n")

    all_results = []

    for pool_name, pool in [("Heterogeneous (OpenAI + Meta)", HETEROGENEOUS_POOL),
                             ("Homogeneous (OpenAI × 2)", HOMOGENEOUS_POOL)]:
        print(f"\n[POOL] {pool_name}")
        print(f"  Models: {pool}")

        for qi, query in enumerate(QUERIES):
            print(f"  Query {qi+1}: {query[:55]}...")
            try:
                result = await run_pipeline_with_pool(
                    query, pool, openrouter, evaluator,
                    conflict_analyzer, synthesizer, final_eval_svc
                )
                if result:
                    all_results.append({
                        "pool_type": pool_name,
                        "models": pool,
                        "query": query,
                        **result
                    })
                    print(f"    Diversity={result['diversity_score']:.4f} "
                          f"Quality={result['quality_score']:.4f} "
                          f"Improvement={result['improvement_pct']:+.2f}%")
            except Exception as e:
                print(f"    [ERROR] {e}")

    # Aggregate by pool type
    print("\n" + "=" * 65)
    print("DIVERSITY vs QUALITY SUMMARY")
    print(f"{'Pool Type':<40} {'Avg Diversity':>14} {'Avg Quality':>12} {'Avg Impr%':>10}")
    print("-" * 80)

    from collections import defaultdict
    pool_agg = defaultdict(lambda: {"diversity": [], "quality": [], "improvement": []})
    for r in all_results:
        pool_agg[r["pool_type"]]["diversity"].append(r["diversity_score"])
        pool_agg[r["pool_type"]]["quality"].append(r["quality_score"])
        pool_agg[r["pool_type"]]["improvement"].append(r["improvement_pct"])

    for pool_type, agg in pool_agg.items():
        avg_div = sum(agg["diversity"]) / len(agg["diversity"])
        avg_q   = sum(agg["quality"])   / len(agg["quality"])
        avg_imp = sum(agg["improvement"]) / len(agg["improvement"])
        print(f"{pool_type:<40} {avg_div:>14.4f} {avg_q:>12.4f} {avg_imp:>+10.2f}%")

    print("=" * 65)

    # Correlation diversity → quality
    all_div = [r["diversity_score"] for r in all_results]
    all_q   = [r["quality_score"] for r in all_results]
    if len(all_div) > 2:
        n = len(all_div)
        mean_d = sum(all_div)/n
        mean_q = sum(all_q)/n
        cov = sum((d - mean_d) * (q - mean_q) for d, q in zip(all_div, all_q)) / (n - 1)
        std_d = math.sqrt(sum((d - mean_d)**2 for d in all_div) / (n - 1))
        std_q = math.sqrt(sum((q - mean_q)**2 for q in all_q) / (n - 1))
        pearson_r = cov / (std_d * std_q) if std_d * std_q > 0 else 0.0
        print(f"\nPearson correlation (diversity → quality): r = {pearson_r:.4f}")
        interpretation = "positive" if pearson_r > 0.3 else ("negative" if pearson_r < -0.3 else "negligible")
        print(f"Interpretation: {interpretation} correlation")

    # Save results
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "diversity_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
