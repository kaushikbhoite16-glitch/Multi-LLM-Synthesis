# Research Methodology

## Research Question

> Can a response-level, multi-criteria evaluation and synthesis system produce answers that better satisfy user-specific requirements than individual LLM responses, while accounting for response quality, token usage, API cost, latency, and user preferences?

---

## Experimental Design

### Baseline Architectures

Four baselines are implemented for rigorous comparison:

| Baseline | Architecture | Description |
|----------|-------------|-------------|
| B1 | Single LLM | One model → response |
| B2 | Best Response Selection | N models → evaluate → select top response |
| B3 | Simple Multi-LLM Synthesis | N models → raw concat → synthesize |
| B4 | Evaluation-Guided Synthesis | N models → score → provide scores to synthesizer |
| **Proposed** | **Adaptive Multi-Criteria Synthesis** | N models → full pipeline → adaptive synthesis |

### Benchmark Dataset

- **200 queries** across 5 domains:
  - Computer Science (40 queries)
  - Coding / Algorithms (40 queries)
  - Mathematics & Reasoning (40 queries)
  - General Knowledge (40 queries)
  - Creative & Explanatory (40 queries)
- Three difficulty levels: beginner, intermediate, advanced

### Evaluation Metrics

**Automated (primary)**:
- Overall quality score (0-10) — composite of 8 criteria
- Relevance, correctness, completeness, clarity, consistency, preference match, conciseness, technical depth
- API cost (USD), total tokens, latency (ms)
- Improvement % over best candidate baseline

**Human (secondary)**:
- Pairwise preference (A / B / equal)
- Likert scales (1-5) on relevance, correctness, clarity, completeness, preference match
- Blind evaluation — model identities masked

---

## Research Questions and Experimental Designs

### RQ1: Multi-LLM Synthesis vs Single LLM
- **Design**: Run proposed system and B1 on all 200 queries
- **Metric**: Mean overall quality score, t-test for significance
- **Expected result**: Proposed system outperforms single LLM

### RQ2: Evaluation-Guided vs Simple Synthesis
- **Design**: Compare B3 vs B4 vs Proposed on same query set
- **Metric**: Mean quality, correctness, completeness
- **Expected result**: Evaluation guidance prevents hallucination propagation

### RQ3: User Preference Impact
- **Design**: Run pipeline with equal weights vs user-specified domain weights
- **Metric**: Human preference rating of preference_match criterion
- **Expected result**: Customized weights yield higher satisfaction

### RQ4: Quality-Cost Scaling Curve
- **Design**: Run pipeline with k=1,2,3,4,5 candidate models, measure quality and cost
- **Metric**: Quality score, total pipeline cost, diminishing returns threshold
- **Expected result**: Diminishing returns appear beyond k=4

### RQ5: Evaluator Bias Analysis
- **Design**: Evaluate same candidates using 3 different evaluator models
- **Metric**: Spearman rank correlation, ranking agreement, score variance
- **Expected result**: Moderate inter-rater correlation (>0.75); bias exists but is manageable

### RQ6: Model Diversity (Homo vs Hetero Ensemble)
- **Design**: Compare 4× same model vs 4× different providers
- **Metric**: Quality, unique claim count, synthesis completeness
- **Expected result**: Heterogeneous ensembles produce more distinct useful information

---

## Statistical Analysis

All comparisons use:
- **Mean ± Standard Deviation**
- **95% Confidence Intervals** (1.96 × SD / √n)
- **Paired t-test** for significance testing where applicable (α = 0.05)
- **Spearman rank correlation** for evaluator bias analysis

---

## Pareto Analysis

A response is Pareto-optimal if no other response simultaneously:
- Achieves higher quality AND
- Incurs lower API cost

The Pareto frontier is computed and visualized in the Analytics dashboard, identifying the cost-efficiency boundary for model selection decisions.

---

## Threats to Validity

1. **Evaluator bias**: LLM-based evaluation may systematically favour certain response styles — mitigated by multi-evaluator comparison (RQ5)
2. **Domain coverage**: 200 queries may not capture all prompt types — mitigated by 5-domain stratification
3. **Model availability**: OpenRouter model availability may vary — all models should be tested for availability before large-scale experiments
4. **Cost constraints**: Full experiments with GPT-4o and Claude Sonnet are expensive — use cost-aware scoring mode and smaller batches for initial validation
5. **Simulation mode validity**: Simulation responses are domain-aware heuristics, not real LLM outputs — all research claims must be validated with real API calls

---

## Reproducibility

- All experiment inputs (query, models, preferences, evaluator, synthesis model) are stored in the `experiments` table
- All intermediate outputs (model runs, evaluations, synthesis) are stored in separate tables
- `experiment_id` links all results to the originating configuration
- Export to JSON/CSV available from the Analytics dashboard
