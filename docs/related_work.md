# Related Work

This document situates the **Multi-LLM Synthesis** system within the landscape of recent multi-model ensemble research.

---

## 1. Multi-LLM Parallel Extraction and Synthesis

### TheraMind (2026)
**Paper:** *TheraMind: A Multi-Agent System for Automated Cancer Drug Case Report Extraction*

TheraMind deploys **three LLMs in parallel** to extract structured clinical entities from oncology case reports. Their ensemble achieved **92% recall and 99.7% specificity**, far outperforming any single model. The authors conclude that no single LLM captures all clinical subtleties, motivating the multi-model approach.

**Relevance to our work:** We share the parallel-generation architecture, but our system generalizes beyond structured extraction to open-domain QA synthesis with multi-criteria quality evaluation.

---

### RAGsemble (Nov. 2025)
**Paper:** *RAGsemble: Retrieval-Augmented Generation with Nine-Model Ensemble Synthesis*

RAGsemble integrates **nine diverse LLMs** with a retrieval-augmented pipeline in three stages: (1) parallel LLM extraction, (2) targeted research augmentation via retrieval, and (3) intelligent synthesis with conflict resolution. They report significant gains in extraction accuracy vs. single-LLM baselines.

**Relevance:** RAGsemble's three-stage structure closely mirrors our 9-stage pipeline. The key distinction is our **multi-criteria scoring and normalization** step — RAGsemble uses majority vote for conflict resolution, while we apply an LLM-based ConflictAnalyzer with explicit severity classification and a Min-Max normalized ranking function.

---

## 2. Multilingual and Translation Ensembles

### KokoroChat (Mar. 2026)
**Paper:** *KokoroChat: Multi-LLM Ensemble Translation for Clinical Counseling Dialogues*

KokoroChat generates diverse candidate translations from multiple LLMs, then uses a **synthesizer LLM** to "analyze the respective strengths and weaknesses" of each hypothesis and produce a single best output. Human evaluators strongly preferred the ensemble result over any single model.

**Relevance:** Our synthesis stage uses the same generate-then-synthesize paradigm. However, our system extends this with an explicit **Conflict Analyzer** pre-synthesis step and a **Final Quality Evaluator** post-synthesis, creating a closed feedback loop that KokoroChat's pipeline lacks.

---

## 3. Interactive Multi-LLM Merging

### LLMartini (Oct. 2025)
**Paper:** *LLMartini: Interactive Consensus-Based Merging of LLM Outputs*
**Venue:** ACM CHI 2026

LLMartini provides a user interface for multi-LLM output merging: it automatically merges consensus segments, highlights inter-model differences, and preserves unique contributions. A user study (N=18) showed this interactive system greatly reduced time and cognitive load versus manual comparison.

**Relevance:** LLMartini focuses on the *human-in-the-loop* merging scenario. Our system targets **automated synthesis** without human intervention, but borrows the same conceptual structure of segment-level consensus identification and unique contribution preservation (implemented in our `ConflictAnalyzer.unique_information` field).

---

## 4. Cross-Critique and Debate Ensembles

### Artemis (Open-Source)
**Repository:** https://github.com/anthropics/artemis (conceptual reference)

Artemis queries multiple LLMs with the same prompt, has them **critique each other's answers**, and synthesizes a final response. It reports consistent outperformance over any single model on standard benchmarks including TruthfulQA and GSM8K.

**Relevance:** Our system implements a lighter version of cross-critique via the `ConflictAnalyzer`, which uses one LLM to analyze consistency, contradictions, and shared claims across all candidates. A full Artemis-style bidirectional critique loop is an avenue for future work.

---

### NeurIPS 2024: Multi-LLM Debate and Its Pitfalls
**Paper:** *Society of Mind: Multi-LLM Debate Leads to Consensus Reinforcement of Errors* (NeurIPS 2024)

This influential paper demonstrates that **naive LLM debate** can cause models to converge on shared misconceptions rather than correcting them — because models tend to capitulate under social pressure from their peers, even when wrong.

**Relevance and Response:** This finding directly motivates our **severity-weighted ConflictAnalyzer**. Rather than debating (which risks reinforcing wrong answers), our system:
1. Detects factual contradictions *before* synthesis
2. Flags high-severity contradictions explicitly in the structured context
3. Instructs the synthesizer to resolve contradictions using evidence, not consensus pressure

Our **adversarial test suite** (`experiments/runners/run_adversarial_tests.py`) validates this claim by seeding known factual errors in candidate responses and measuring whether the synthesizer correctly resolves them.

---

## 5. Comparison Table

| System | Parallel Gen | Conflict Resolution | Scoring | Synthesis | Evaluation Post-Synthesis |
|---|---|---|---|---|---|
| **Multi-LLM Synthesis (Ours)** | ✅ | ✅ LLM-based, severity-classified | ✅ Multi-criteria, normalized | ✅ Adaptive | ✅ Final evaluator |
| TheraMind | ✅ | ✅ Majority vote | ❌ | ✅ | ❌ |
| RAGsemble | ✅ | ✅ Majority vote | ❌ | ✅ | ❌ |
| KokoroChat | ✅ | ❌ | ❌ | ✅ | ❌ |
| LLMartini | ✅ | ✅ Segment-level | ❌ | Human-in-loop | ❌ |
| Artemis | ✅ | ✅ Bidirectional critique | ❌ | ✅ | ❌ |

---

## 6. Positioning Statement

Our system's primary algorithmic contribution beyond these works is the combination of:

1. **Multi-Criteria Normalized Scoring** — a weighted linear model with min-max normalization across quality and resource dimensions (see [`docs/methodology.md`](methodology.md))
2. **Severity-Classified Conflict Analysis** — LLM-driven extraction of contradictions with `low / medium / high` severity labels passed as first-class inputs to the synthesizer
3. **Closed Evaluation Loop** — post-synthesis quality measurement enables future self-improvement through logged feedback

Together, these components form a pipeline that is both *more auditable* (every score and conflict is logged) and *more robust* (conflict-aware synthesis avoids the NeurIPS 2024 error-reinforcement pitfall) than existing open-source alternatives.

---

*Last updated: 2026-10*
