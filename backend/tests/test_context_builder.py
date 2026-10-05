import pytest
from app.services.context_builder import ContextBuilder
from app.schemas.pydantic_models import (
    RankedResponse,
    ConflictAnalysisResult,
    UserPreferenceSchema
)

def test_context_builder_structure():
    ranked = [
        RankedResponse(
            rank=1,
            response_id=1,
            model="google/gemini-2.0-flash-001",
            provider="Google",
            response_text="Virtual memory decouples logical and physical address space.",
            overall_score=9.1,
            quality_score=9.1,
            cost=0.0003,
            tokens=450,
            latency_ms=620,
            criteria_scores={"relevance": 9.2, "correctness": 9.0},
            reasoning="Concise and accurate."
        )
    ]
    conflicts = ConflictAnalysisResult(
        topic="Virtual Memory",
        shared_information=["All models emphasize MMU and paging."],
        unique_information={},
        contradictions=[],
        potential_uncertainty=[]
    )
    pref = UserPreferenceSchema(scoring_mode="quality-first")

    context = ContextBuilder.build_structured_context(
        query="Explain virtual memory.",
        ranked_candidates=ranked,
        conflicts=conflicts,
        preferences=pref
    )

    assert "USER QUERY" in context
    assert "USER PREFERENCES" in context
    assert "CANDIDATE RESPONSE #1" in context
    assert "AGREEMENT ANALYSIS" in context
    assert "CONFLICT AND CONTRADICTION ANALYSIS" in context
    assert "SYNTHESIS INSTRUCTIONS" in context
