# REST API Documentation

The Multi-LLM Response Evaluation and Adaptive Answer Synthesis System provides a comprehensive RESTful API built on FastAPI.

Interactive Swagger/OpenAPI documentation is available at `http://localhost:8000/docs` and Redoc at `http://localhost:8000/redoc`.

---

## Base URL

```
http://localhost:8000/api
```

---

## Endpoints

### 1. Health & Status

#### `GET /health`
Verifies backend connectivity and configuration state.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "Multi-LLM Evaluation and Synthesis System",
  "has_openrouter_key": false,
  "database": "sqlite+aiosqlite"
}
```

---

### 2. Pipeline Execution

#### `POST /api/run`
Executes the full 9-stage evaluation and synthesis pipeline for a given user query and preference configuration.

**Request Body:**
```json
{
  "query": "Explain virtual memory in operating systems.",
  "models": [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001"
  ],
  "preferences": {
    "relevance_weight": 0.25,
    "correctness_weight": 0.30,
    "completeness_weight": 0.20,
    "clarity_weight": 0.15,
    "consistency_weight": 0.05,
    "preference_match_weight": 0.05,
    "conciseness_weight": 0.0,
    "technical_depth_weight": 0.0,
    "creativity_weight": 0.0,
    "cost_weight": 0.0,
    "token_weight": 0.0,
    "latency_weight": 0.0,
    "max_cost": 0.50,
    "max_tokens": 2000,
    "max_latency_ms": 15000,
    "scoring_mode": "balanced"
  }
}
```

**Response (200 OK):**
```json
{
  "query_id": 1,
  "analysis": {
    "query_type": "educational",
    "domain": "computer_science",
    "difficulty": "intermediate",
    "expected_style": "structured_technical",
    "recommended_criteria": ["correctness", "clarity", "completeness"]
  },
  "candidate_responses": [
    {
      "model": "anthropic/claude-3.5-sonnet",
      "provider": "Anthropic",
      "response_text": "...",
      "input_tokens": 420,
      "output_tokens": 680,
      "total_tokens": 1100,
      "cost": 0.0078,
      "latency_ms": 1420,
      "status": "success"
    }
  ],
  "evaluations": [
    {
      "model": "anthropic/claude-3.5-sonnet",
      "evaluator_model": "google/gemini-2.0-flash-001",
      "scores": {
        "relevance": 9.4,
        "correctness": 9.2,
        "completeness": 9.1,
        "clarity": 9.5,
        "consistency": 9.0,
        "preference_match": 8.8,
        "conciseness": 8.0,
        "technical_depth": 9.2
      },
      "overall_score": 9.15,
      "reasoning": "Comprehensive explanation covering MMU, TLB, page tables, and demand paging."
    }
  ],
  "ranking": [
    {
      "rank": 1,
      "model": "anthropic/claude-3.5-sonnet",
      "overall_score": 9.15,
      "tokens": 1100,
      "cost": 0.0078,
      "latency_ms": 1420
    }
  ],
  "conflicts": {
    "shared_agreements": ["MMU translates virtual to physical addresses using page tables."],
    "unique_points": ["Claude 3.5 Sonnet detailed translation lookaside buffer (TLB) caching."],
    "contradictions": [],
    "uncertainties": []
  },
  "structured_context": "=== USER QUERY === ...",
  "synthesis": {
    "synthesis_model": "anthropic/claude-3.5-sonnet",
    "final_response": "...",
    "input_tokens": 1500,
    "output_tokens": 650,
    "total_tokens": 2150,
    "cost": 0.0125,
    "latency_ms": 1850
  },
  "final_evaluation": {
    "evaluator_model": "google/gemini-2.0-flash-001",
    "scores": {
      "relevance": 9.6,
      "correctness": 9.5,
      "completeness": 9.4,
      "clarity": 9.6,
      "consistency": 9.5,
      "preference_match": 9.2,
      "conciseness": 8.8,
      "technical_depth": 9.4
    },
    "overall_score": 9.35,
    "improvement_pct": 2.19,
    "reasoning": "Synthesized response unified terminology and resolved slight paging model discrepancies."
  },
  "total_pipeline_tokens": 3250,
  "total_pipeline_cost": 0.0203,
  "total_pipeline_latency_ms": 3270,
  "is_mock": false
}
```

---

### 3. Modular Pipeline Endpoints

#### `POST /api/query`
Analyze a query without executing downstream generation.

**Request Body:**
```json
{
  "query": "Write a quicksort implementation in Python."
}
```

#### `POST /api/generate`
Generate responses from candidate models in parallel without evaluating or synthesizing.

**Request Body:**
```json
{
  "query": "Explain quantum entanglement.",
  "models": ["openai/gpt-4o-mini", "google/gemini-2.0-flash-001"]
}
```

#### `POST /api/evaluate`
Evaluate candidate responses across the 8 criteria using a specified evaluator model.

---

### 4. Model Pool Management

#### `GET /api/models`
Retrieve all models in the active pool with their roles, provider, and status.

**Response (200 OK):**
```json
[
  {
    "id": "anthropic/claude-3.5-sonnet",
    "name": "Claude 3.5 Sonnet",
    "provider": "Anthropic",
    "role": "candidate",
    "enabled": true,
    "max_tokens": 4096,
    "cost_per_m_in": 3.0,
    "cost_per_m_out": 15.0
  }
]
```

#### `POST /api/models`
Add a new model or update an existing model configuration.

---

### 5. Analytics & Research Data

#### `GET /api/analytics`
Fetches global KPIs, per-model aggregation statistics, and Pareto frontier coordinates.

#### `GET /api/experiments`
Lists completed benchmark experiments.

#### `GET /api/experiments/{id}`
Returns baseline comparison data for a specific experiment run (B1, B2, B3, B4 vs Proposed).

#### `POST /api/human-eval`
Submits a blind human evaluation rating.

**Request Body:**
```json
{
  "query_id": 1,
  "preferred_choice": "candidate_a",
  "scores": {
    "relevance": 5,
    "correctness": 4,
    "clarity": 5,
    "completeness": 4,
    "preference_match": 4
  },
  "notes": "Candidate A had superior code formatting."
}
```

#### `GET /api/export`
Exports research data in JSON or CSV format.

- Query parameter: `format=json` (default) or `format=csv`
