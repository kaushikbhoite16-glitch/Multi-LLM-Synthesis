"""
Enhanced Statistical Analysis Module
Implements: paired t-tests, bootstrap CIs, effect sizes, inter-rater agreement
"""
import json
import math
import os
import random
from typing import List, Dict, Any, Tuple, Optional

try:
    import numpy as np
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("[WARN] scipy not available — falling back to pure-Python statistics")


# ─────────────────────────────────────────────────────────────
# 1. Descriptive Statistics
# ─────────────────────────────────────────────────────────────

def describe(scores: List[float], label: str = "") -> Dict[str, float]:
    """Full descriptive statistics with 95% CI."""
    if not scores:
        return {}
    n = len(scores)
    mean = sum(scores) / n
    variance = sum((x - mean) ** 2 for x in scores) / max(1, n - 1)
    std_dev = math.sqrt(variance)
    se = std_dev / math.sqrt(n) if n > 1 else 0.0
    ci_95 = 1.96 * se
    return {
        "label":   label,
        "n":       n,
        "mean":    round(mean, 4),
        "std":     round(std_dev, 4),
        "se":      round(se, 4),
        "ci_95_lo": round(mean - ci_95, 4),
        "ci_95_hi": round(mean + ci_95, 4),
        "min":     round(min(scores), 4),
        "max":     round(max(scores), 4),
        "median":  round(sorted(scores)[n // 2], 4),
    }


# ─────────────────────────────────────────────────────────────
# 2. Paired t-Test (RQ1, RQ2)
# ─────────────────────────────────────────────────────────────

def paired_ttest(a: List[float], b: List[float]) -> Dict[str, Any]:
    """
    Paired two-tailed t-test between two matched score vectors.
    Returns t-statistic, p-value, Cohen's d effect size.
    """
    assert len(a) == len(b), "Paired vectors must have equal length"
    n = len(a)
    diffs = [x - y for x, y in zip(a, b)]
    mean_diff = sum(diffs) / n
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / max(1, n - 1)
    std_diff = math.sqrt(var_diff)
    se_diff = std_diff / math.sqrt(n)
    t_stat = mean_diff / se_diff if se_diff > 0 else 0.0

    # p-value via scipy or approx
    if SCIPY_AVAILABLE:
        _, p_val = stats.ttest_rel(a, b)
    else:
        # Approximate p from t distribution using two-tail
        df = n - 1
        # Simple approximation for large n
        p_val = 2 * (1 - _t_cdf(abs(t_stat), df))

    # Cohen's d
    pooled_std = math.sqrt((sum((x - sum(a)/n)**2 for x in a) +
                            sum((x - sum(b)/n)**2 for x in b)) / (2 * n - 2))
    cohens_d = (sum(a)/n - sum(b)/n) / pooled_std if pooled_std > 0 else 0.0

    return {
        "n": n,
        "mean_a": round(sum(a)/n, 4),
        "mean_b": round(sum(b)/n, 4),
        "mean_diff": round(mean_diff, 4),
        "t_stat": round(t_stat, 4),
        "p_value": round(float(p_val), 6),
        "significant_at_0.05": float(p_val) < 0.05,
        "significant_at_0.01": float(p_val) < 0.01,
        "cohens_d": round(cohens_d, 4),
        "effect_size": "large" if abs(cohens_d) > 0.8 else ("medium" if abs(cohens_d) > 0.5 else "small"),
    }


def _t_cdf(t: float, df: int) -> float:
    """Approximation of t-distribution CDF for fallback."""
    x = df / (df + t * t)
    # Regularized incomplete beta approximation
    return 1.0 - 0.5 * _ibeta(x, df / 2, 0.5)


def _ibeta(x: float, a: float, b: float) -> float:
    """Very rough regularized incomplete beta approximation."""
    # Use normal approximation for large df
    return max(0.0, min(1.0, x ** a * (1 - x) ** b))


# ─────────────────────────────────────────────────────────────
# 3. Bootstrap Confidence Intervals
# ─────────────────────────────────────────────────────────────

def bootstrap_ci(scores: List[float], n_boot: int = 2000, alpha: float = 0.05,
                 seed: int = 42) -> Dict[str, float]:
    """
    Non-parametric bootstrap 95% CI of the mean.
    Robust even when normality cannot be assumed.
    """
    random.seed(seed)
    n = len(scores)
    boot_means = []
    for _ in range(n_boot):
        sample = [random.choice(scores) for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo_idx = int(n_boot * (alpha / 2))
    hi_idx = int(n_boot * (1 - alpha / 2))
    return {
        "mean":       round(sum(scores) / n, 4),
        "boot_ci_lo": round(boot_means[lo_idx], 4),
        "boot_ci_hi": round(boot_means[hi_idx], 4),
        "n_bootstrap": n_boot,
    }


# ─────────────────────────────────────────────────────────────
# 4. Spearman Rank Correlation (RQ5: Evaluator Bias)
# ─────────────────────────────────────────────────────────────

def spearman_correlation(x: List[float], y: List[float]) -> Dict[str, float]:
    """Spearman rank correlation between two ranking vectors."""
    assert len(x) == len(y)
    n = len(x)

    def rank(lst):
        sorted_lst = sorted(enumerate(lst), key=lambda t: t[1])
        r = [0] * n
        for rank_idx, (orig_idx, _) in enumerate(sorted_lst):
            r[orig_idx] = rank_idx + 1
        return r

    rx = rank(x)
    ry = rank(y)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    rho = 1 - (6 * d2) / (n * (n * n - 1)) if n > 2 else 0.0
    return {
        "spearman_rho": round(rho, 4),
        "interpretation": "strong" if abs(rho) > 0.7 else ("moderate" if abs(rho) > 0.4 else "weak"),
    }


# ─────────────────────────────────────────────────────────────
# 5. Cohen's Kappa (Inter-Rater Agreement for Human Eval)
# ─────────────────────────────────────────────────────────────

def cohens_kappa(rater_a: List[int], rater_b: List[int], categories: int = 3) -> Dict[str, Any]:
    """
    Cohen's Kappa for categorical agreement.
    For human eval: 0=baseline_better, 1=equal, 2=synthesis_better
    """
    n = len(rater_a)
    assert n == len(rater_b)
    # Observed agreement
    p_o = sum(1 for a, b in zip(rater_a, rater_b) if a == b) / n
    # Expected agreement
    p_e = 0.0
    for cat in range(categories):
        p_a = rater_a.count(cat) / n
        p_b = rater_b.count(cat) / n
        p_e += p_a * p_b
    kappa = (p_o - p_e) / (1 - p_e) if (1 - p_e) > 0 else 1.0
    return {
        "observed_agreement": round(p_o, 4),
        "expected_agreement": round(p_e, 4),
        "kappa": round(kappa, 4),
        "interpretation": "substantial" if kappa > 0.6 else ("moderate" if kappa > 0.4 else "fair"),
    }


# ─────────────────────────────────────────────────────────────
# 6. Ablation Statistical Comparison Table
# ─────────────────────────────────────────────────────────────

def ablation_table(results: Dict[str, List[float]]) -> str:
    """
    Produces a formatted ablation table comparing components.
    results = {"Full System": [scores], "No Conflict Analysis": [scores], ...}
    """
    lines = []
    lines.append(f"\n{'Configuration':<40} {'Mean':>7} {'Std':>7} {'CI_Lo':>7} {'CI_Hi':>7} {'vs Full (p)':>12}")
    lines.append("-" * 84)
    full_scores = results.get("Full System", [])
    for name, scores in results.items():
        s = describe(scores, name)
        if name != "Full System" and full_scores:
            ttest = paired_ttest(full_scores[:len(scores)], scores)
            p_str = f"{ttest['p_value']:.4f}" + (" *" if ttest["significant_at_0.05"] else "")
        else:
            p_str = "—"
        lines.append(
            f"{name:<40} {s['mean']:>7.4f} {s['std']:>7.4f} "
            f"{s['ci_95_lo']:>7.4f} {s['ci_95_hi']:>7.4f} {p_str:>12}"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 7. Main: Analyse Saved Baseline Results
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("MULTI-LLM SYNTHESIS: STATISTICAL ANALYSIS REPORT")
    print("=" * 70)

    res_file = os.path.join(os.path.dirname(__file__), "..", "results", "baseline_comparison_results.json")
    ablation_file = os.path.join(os.path.dirname(__file__), "..", "results", "ablation_results.json")
    diversity_file = os.path.join(os.path.dirname(__file__), "..", "results", "diversity_results.json")
    bias_file      = os.path.join(os.path.dirname(__file__), "..", "results", "evaluator_bias_results.json")

    # ── 1. Baseline Quality Comparison ──────────────────────
    if os.path.exists(res_file):
        with open(res_file, "r") as f:
            data = json.load(f)
        print("\n[1] BASELINE QUALITY COMPARISON")
        print("-" * 70)
        for entry in data:
            print(f"  {entry['method']:<45} Q={entry['quality_score']:.4f}  Cost=${entry['cost']:.6f}")

        quality_scores = {e["method"]: e["quality_score"] for e in data}
        proposed_score = quality_scores.get("Proposed System", None)
        baseline1_score = list(quality_scores.values())[0] if quality_scores else None

        if proposed_score and baseline1_score:
            improvement = ((proposed_score - baseline1_score) / baseline1_score) * 100
            print(f"\n  Proposed vs Single LLM improvement: {improvement:+.2f}%")

    # ── 2. Bootstrap CI on Live Pipeline Scores ─────────────
    print("\n[2] BOOTSTRAP CONFIDENCE INTERVALS (from live run data)")
    print("-" * 70)
    live_scores = {
        "google/gemini-2.5-flash":           [8.91],
        "openai/gpt-4o-mini":                [8.84],
        "meta-llama/llama-3.1-8b-instruct":  [9.01],
        "Synthesized Response":              [9.29],
    }
    for model, scores in live_scores.items():
        print(f"  {model:<45}: Mean={scores[0]:.4f}  (n=1, bootstrap meaningful with ≥10 runs)")

    # ── 3. Ablation Results ──────────────────────────────────
    if os.path.exists(ablation_file):
        with open(ablation_file, "r") as f:
            ablation = json.load(f)
        print("\n[3] ABLATION STUDY RESULTS")
        print("-" * 70)
        configs = {}
        for entry in ablation:
            configs.setdefault(entry["configuration"], []).append(entry["quality_score"])
        print(ablation_table(configs))

    # ── 4. Evaluator Bias (Spearman Correlation) ────────────
    if os.path.exists(bias_file):
        with open(bias_file, "r") as f:
            bias = json.load(f)
        print("\n[4] EVALUATOR BIAS ANALYSIS (Spearman Rank Correlation)")
        print("-" * 70)
        evaluators = list(set(e["evaluator"] for e in bias))
        if len(evaluators) >= 2:
            e1_scores = [e["score"] for e in bias if e["evaluator"] == evaluators[0]]
            e2_scores = [e["score"] for e in bias if e["evaluator"] == evaluators[1]]
            min_len = min(len(e1_scores), len(e2_scores))
            corr = spearman_correlation(e1_scores[:min_len], e2_scores[:min_len])
            print(f"  {evaluators[0]} vs {evaluators[1]}: ρ={corr['spearman_rho']} ({corr['interpretation']} agreement)")

    # ── 5. Diversity Results ─────────────────────────────────
    if os.path.exists(diversity_file):
        with open(diversity_file, "r") as f:
            div = json.load(f)
        print("\n[5] MODEL DIVERSITY vs QUALITY CORRELATION")
        print("-" * 70)
        for entry in div[:5]:
            print(f"  Diversity score={entry.get('avg_diversity',0):.3f} → Quality={entry.get('quality_score',0):.3f}")

    print("\n" + "=" * 70)
    print("STATISTICAL ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
