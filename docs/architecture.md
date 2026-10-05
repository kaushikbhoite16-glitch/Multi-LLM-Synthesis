# Architecture Documentation

## System Overview

The **Multi-LLM Response Evaluation and Adaptive Answer Synthesis System** is a RAG-like response synthesis architecture where the retrieval corpus consists of evaluated LLM responses rather than external documents.

---

## Core Pipeline Components

### 1. OpenRouter Service (`services/openrouter_service.py`)
- Single gateway abstraction for all LLM providers
- Parallel async generation using `asyncio.gather()`
- API-provided token/cost extraction from `usage` objects
- Graceful timeout and error recovery (failed models don't terminate the pipeline)
- Realistic domain-aware simulation fallback when API key is absent

### 2. Query Analyzer (`services/query_analyzer.py`)
- LLM-powered structured classification of query type, domain, difficulty, style
- Deterministic heuristic fallback via keyword pattern matching
- Output: `QueryAnalysisResult` (Pydantic model)

### 3. Response Evaluator (`services/evaluator.py`)
- Parallel async evaluation of all candidates by a designated evaluator LLM
- 8 semantic criteria: relevance, correctness, completeness, clarity, consistency, preference_match, conciseness, technical_depth
- Structured JSON output with automatic parse validation and retry
- Text-heuristic fallback protocol with model-aware adjustments

### 4. Scoring Engine (`services/scoring.py`)
- Configurable weighted quality score: `Q = Σ(w_i × C_i)` where `Σw_i = 1.0`
- Min-max normalized resource penalties (cost, tokens, latency)
- 4 scoring modes: quality-first, balanced, cost-aware, user-customized
- Composite: `S = clamp(0,10, (Q × α) - Penalty + (1-α)×5)`

### 5. Ranking Engine (`services/ranking.py`)
- Sorts candidates by composite scores (descending)
- Note: Rank #1 is **input to synthesis** — NOT automatically the final answer

### 6. Conflict Analyzer (`services/conflict_analyzer.py`)
- LLM-based cross-validation of candidate claims
- Identifies: shared consensus, unique contributions, factual contradictions, uncertainty zones
- Severity classification: low / medium / high
- Heuristic fallback with domain-specific claim patterns

### 7. Context Builder (`services/context_builder.py`)
- Constructs structured synthesis prompt with clearly delineated sections:
  - User Query, User Preferences, Candidate Responses (with scores + metrics)
  - Agreement analysis, Contradiction catalogue, Synthesis instructions
- Explicit guidance to resolve conflicts and avoid blindly following consensus

### 8. Synthesizer (`services/synthesizer.py`)
- Receives the full structured context
- Generates a single coherent user-tailored answer
- Does NOT expose internal evaluation metadata in output

### 9. Final Evaluator (`services/final_evaluator.py`)
- Evaluates the synthesized response using identical criteria as candidates
- Computes `improvement_pct = ((final_score - best_candidate_score) / best_candidate_score) × 100`
- Enables direct empirical comparison for research

### 10. Pipeline Orchestrator (`services/pipeline.py`)
- Coordinates all 9 stages sequentially (with parallel sub-stages where safe)
- Persists all data to database for research reproducibility
- Returns complete `PipelineRunResponse` for frontend and API consumers

---

## Data Flow

```
PipelineRunRequest {query, models, preferences}
        │
        ├── QueryAnalyzer → QueryAnalysisResult
        │
        ├── OpenRouter.generate_parallel_responses()
        │   └── [NormalizedResponse × N]  (tokens, cost, latency from API)
        │
        ├── ResponseEvaluator.evaluate_candidates_parallel()
        │   └── [EvaluationResult × N]
        │
        ├── ScoringEngine.calculate_composite_scores()
        │   └── [{quality_score, resource_penalty, overall_score} × N]
        │
        ├── RankingEngine.rank_responses()
        │   └── [RankedResponse × N]  (sorted desc by score)
        │
        ├── ConflictAnalyzer.analyze_conflicts()
        │   └── ConflictAnalysisResult {shared, unique, contradictions}
        │
        ├── ContextBuilder.build_structured_context()
        │   └── str  (formatted structured synthesis prompt)
        │
        ├── SynthesizerService.synthesize()
        │   └── SynthesisResult {final_response, tokens, cost, latency}
        │
        ├── FinalEvaluator.evaluate_final_response()
        │   └── FinalEvaluationResult {scores, improvement_pct}
        │
        └── PipelineOrchestrator → DB persist + PipelineRunResponse
```

---

## Database Schema (SQLite / PostgreSQL)

```
users              → id, created_at
preferences        → id, user_id, [criteria weights], max_cost, scoring_mode
queries            → id, user_id, query_text, domain, difficulty, created_at
model_runs         → id, query_id, model, provider, response_text, tokens, cost, latency_ms, status
evaluations        → id, model_run_id, evaluator_model, [8 criteria scores], overall_score, reasoning
conflicts          → id, query_id, topic, severity, agreement_points, conflict_points
synthesis_runs     → id, query_id, synthesis_model, context, final_response, tokens, cost, latency_ms
final_evaluations  → id, synthesis_run_id, evaluator_model, [8 scores], improvement_pct
experiments        → id, name, description, configuration
experiment_results → id, experiment_id, query_id, method, quality_score, cost, tokens, latency
human_evaluations  → id, query_id, preferred_choice, [likert scores], notes
```

---

## Frontend Page Architecture

| Page                   | Purpose                                                             |
|------------------------|---------------------------------------------------------------------|
| Dashboard              | KPI cards, Pareto frontier scatter, per-model performance table     |
| Query & Synthesize     | Query input, model selection, preference sliders, live pipeline     |
| Final Result           | 6-tab view: answer, candidates, evaluation, conflicts, context, cost|
| Candidate Comparison   | Sortable table with inspection modal                                |
| Analytics & Pareto     | Quality vs cost charts, model comparison bars, CSV/JSON export      |
| Benchmark Suite        | Baseline comparison matrix, RQ1-RQ6 research findings              |
| Model Pool             | Enable/disable models, assign roles, add custom models              |
| Eval Config            | Criteria definitions, scoring formula, weight explanations         |
| Human Eval             | Blind pairwise evaluation interface with Likert rating scales       |

---

## Simulation / Demo Mode

All components degrade gracefully when the OpenRouter API key is absent:

```
OpenRouter.has_api_key() → False
→ _generate_mock_response()    (realistic latencies, domain-aware text)
→ _heuristic_evaluate()        (model-aware heuristics, keyword overlap)
→ _heuristic_analyze_conflicts() (domain-specific claim patterns)
→ _fallback_synthesis()        (comprehensive domain synthesis)
```

All mock data is clearly annotated with `is_mock: true` in API responses and displayed with "SIMULATION / DEMO MODE" banners in the UI.
