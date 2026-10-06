# Ablation Study Design and Results

This document describes the ablation experiments that quantify each
pipeline component's contribution to synthesis quality.

---

## Motivation

The reviewer concern addressed here:

> *"Top-tier venues expect ablation studies showing what each component contributes. Without them, it is unclear whether the multi-criteria scoring and conflict analysis actually help."*

---

## Experimental Setup

- **Queries:** 10 representative benchmark queries spanning 5 domains (CS theory, algorithms, systems, ML, networking)
- **Models:** `openai/gpt-4o-mini` + `meta-llama/llama-3.1-8b-instruct`
- **Metric:** Final synthesized response quality score (0–10) from independent evaluator
- **Runner:** [`experiments/runners/run_ablation_study.py`](../experiments/runners/run_ablation_study.py)

---

## Ablation Configurations

| ID | Configuration | What is Disabled |
|---|---|---|
| A0 | **Full System** | Nothing — all stages active |
| A1 | **No Conflict Analysis** | ConflictAnalyzer replaced with empty result; synthesizer receives no conflict signals |
| A2 | **No Multi-Criteria Scoring** | All 8 evaluation criteria weighted equally (0.125 each) instead of user-specified weights |
| A3 | **No Evaluation-Guided Context** | Structured context replaced with plain concatenation of raw responses (no scores, no rankings) |
| A4 | **Best-of-N Only** | No synthesis; highest-ranked candidate response returned directly |

---

## Expected Outcomes

Based on system design, we predict the following quality drops when removing each component:

| Removed Component | Predicted Effect | Reasoning |
|---|---|---|
| Conflict Analysis | Moderate drop (−0.3 to −0.8) | Synthesizer may blend contradictory claims without knowing they conflict |
| Multi-Criteria Scoring | Small drop (−0.1 to −0.4) | Equal weights reduce signal quality but all criteria still evaluated |
| Evaluation-Guided Context | Larger drop (−0.5 to −1.2) | Synthesizer receives no ranked signal; may give equal weight to poor candidates |
| Synthesis (Best-of-N) | Largest drop (−1.0 to −2.0) | Discards all multi-model complementary information |

---

## How to Run

```powershell
# From project root
cd c:\LLM\backend
..\backend\venv\Scripts\python.exe ..\experiments\runners\run_ablation_study.py
```

Results are saved to `experiments/results/ablation_results.json`.

Then run statistical analysis:

```powershell
..\backend\venv\Scripts\python.exe ..\experiments\analysis\statistical_analysis.py
```

---

## Results Interpretation

The `statistical_analysis.py` module generates an **ablation table** with:

- Mean quality score per configuration
- 95% confidence interval (parametric)
- Paired t-test p-value vs. Full System
- Cohen's d effect size (`small / medium / large`)

**Example output format:**

```
Configuration                            Mean     Std   CI_Lo   CI_Hi   vs Full (p)
------------------------------------------------------------------------------------
Full System                             8.9100  0.4200  8.6600  9.1600           —
No Conflict Analysis                    8.5300  0.5100  8.2100  8.8500   0.0412 *
No Multi-Criteria Scoring               8.7200  0.4600  8.4400  9.0000   0.1830
No Evaluation-Guided Context            8.1800  0.6300  7.8000  8.5600   0.0038 *
Best-of-N Only (No Synthesis)           7.8400  0.7200  7.4000  8.2800   0.0009 *
```

*(Actual values filled in after running experiments)*

---

## Theoretical Grounding

The ablation design follows the principle of **systematic component isolation** (as used in NeurIPS 2024 ablation benchmarks):

1. One component is removed at a time — all others remain unchanged
2. The same query set and models are used across all configurations — controlling for prompt/model variance
3. Quality scores are compared using **paired t-tests** because each configuration runs on the **same queries** (reducing noise from query difficulty variance)

This isolates the **causal effect** of each component rather than correlational association.

---

## Limitations

- Small query set (n=10) reduces statistical power; p-values should be interpreted with confidence intervals
- Only 2 candidate models used; larger model pools may show different component contributions
- Quality evaluation itself uses an LLM evaluator, introducing evaluator bias (see [`docs/methodology.md`](methodology.md) §5)

---

*Last updated: 2026-10*
