import pytest
from app.services.scoring import ScoringEngine
from app.schemas.pydantic_models import (
    NormalizedResponse,
    EvaluationResult,
    UserPreferenceSchema
)

def test_min_max_normalization():
    vals = [10.0, 20.0, 30.0]
    norm = ScoringEngine.normalize_min_max(vals)
    assert norm == [0.0, 0.5, 1.0]

    # Edge case: all same values
    same = [5.0, 5.0, 5.0]
    assert ScoringEngine.normalize_min_max(same) == [0.0, 0.0, 0.0]

def test_composite_scoring_quality_first():
    cand1 = NormalizedResponse(
        response_id=1,
        model="model-a",
        provider="prov-a",
        response_text="good answer",
        cost=0.001,
        total_tokens=500,
        latency_ms=1000
    )
    cand2 = NormalizedResponse(
        response_id=2,
        model="model-b",
        provider="prov-b",
        response_text="okay answer",
        cost=0.005,
        total_tokens=1500,
        latency_ms=2500
    )
    ev1 = EvaluationResult(
        response_id=1,
        model="model-a",
        evaluator_model="eval-x",
        relevance=9.0,
        correctness=9.0,
        completeness=9.0,
        clarity=9.0,
        consistency=9.0,
        preference_match=9.0,
        overall_score=9.0,
        reasoning="great"
    )
    ev2 = EvaluationResult(
        response_id=2,
        model="model-b",
        evaluator_model="eval-x",
        relevance=8.0,
        correctness=8.0,
        completeness=8.0,
        clarity=8.0,
        consistency=8.0,
        preference_match=8.0,
        overall_score=8.0,
        reasoning="good"
    )
    pref = UserPreferenceSchema(scoring_mode="quality-first")
    scores = ScoringEngine.calculate_composite_scores([cand1, cand2], [ev1, ev2], pref)
    assert len(scores) == 2
    assert scores[0]["overall_score"] == 9.0
    assert scores[1]["overall_score"] == 8.0
