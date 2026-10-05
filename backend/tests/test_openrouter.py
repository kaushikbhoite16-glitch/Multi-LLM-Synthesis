import pytest
from app.services.openrouter_service import OpenRouterService

@pytest.mark.asyncio
async def test_openrouter_cost_calculation():
    service = OpenRouterService()
    # 1000 input tokens, 1000 output tokens on Gemini 2.0 Flash ($0.10/M in, $0.40/M out)
    cost = service.calculate_cost("google/gemini-2.0-flash-001", 1000, 1000)
    assert cost == pytest.approx(0.0005, rel=1e-3)

@pytest.mark.asyncio
async def test_mock_response_generation():
    service = OpenRouterService()
    messages = [{"role": "user", "content": "Explain virtual memory in operating systems."}]
    res = await service.generate_response(
        model="google/gemini-2.0-flash-001",
        messages=messages,
        max_tokens=500,
        force_mock=True
    )
    assert res.status == "success"
    assert res.total_tokens > 0
    assert res.latency_ms > 0
    assert "virtual memory" in res.response_text.lower()
    assert res.cost > 0
