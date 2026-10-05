import json
import math
import os
from typing import List, Dict, Any

def analyze_statistics(scores: List[float]) -> Dict[str, float]:
    if not scores:
        return {}
    n = len(scores)
    mean = sum(scores) / n
    variance = sum((x - mean) ** 2 for x in scores) / max(1, n - 1)
    std_dev = math.sqrt(variance)
    ci_95 = 1.96 * (std_dev / math.sqrt(n)) if n > 1 else 0.0
    return {
        "count": n,
        "mean": round(mean, 3),
        "std_dev": round(std_dev, 3),
        "ci_95": round(ci_95, 3),
        "min": round(min(scores), 3),
        "max": round(max(scores), 3)
    }

def main():
    print("=" * 60)
    print("STATISTICAL ANALYSIS OF MULTI-LLM RESEARCH RESULTS")
    print("=" * 60)

    res_file = "experiments/results/baseline_comparison_results.json"
    if os.path.exists(res_file):
        with open(res_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("\nBaseline Quality Distributions:")
        for entry in data:
            print(f"  {entry['method']:<45}: Score = {entry['quality_score']:.2f}, Cost = ${entry['cost']:.5f}")

    print("\nStatistical Analysis Complete.")

if __name__ == "__main__":
    main()
