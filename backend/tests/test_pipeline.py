import pytest
from app.services.pipeline import PipelineOrchestrator
from app.schemas.pydantic_models import PipelineRunRequest, UserPreferenceSchema

@pytest.mark.asyncio
async def test_full_pipeline_orchestration():
    orchestrator = PipelineOrchestrator(db=None)
    req = PipelineRunRequest(
        query="Explain virtual memory in operating systems.",
        models=["google/gemini-2.5-flash", "openai/gpt-4o-mini", "meta-llama/llama-3.1-8b-instruct"],
        preferences=UserPreferenceSchema(scoring_mode="balanced")
    )

    res = await orchestrator.execute_pipeline(req)

    assert res.query_text == req.query
    assert len(res.candidate_responses) == 3
    assert len(res.evaluations) == 3
    assert len(res.ranking) == 3
    assert res.synthesis is not None
    assert len(res.synthesis.final_response) > 50
    assert res.final_evaluation is not None
    assert res.final_evaluation.overall_score >= 0.0
    assert res.total_pipeline_tokens > 0
    assert res.total_pipeline_cost >= 0.0
