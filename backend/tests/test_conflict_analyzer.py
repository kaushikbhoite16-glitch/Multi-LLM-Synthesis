import pytest
from app.services.conflict_analyzer import ConflictAnalyzer
from app.services.openrouter_service import OpenRouterService
from app.schemas.pydantic_models import NormalizedResponse

@pytest.mark.asyncio
async def test_conflict_analyzer_heuristic():
    openrouter = OpenRouterService()
    analyzer = ConflictAnalyzer(openrouter)
    
    cand1 = NormalizedResponse(
        response_id=1,
        model="anthropic/claude-3.5-sonnet",
        provider="Anthropic",
        response_text="Virtual memory uses paging with MMU and TLB.",
        status="success"
    )
    cand2 = NormalizedResponse(
        response_id=2,
        model="google/gemini-2.0-flash-001",
        provider="Google",
        response_text="Virtual memory allows swap space and page fault management.",
        status="success"
    )

    conflicts = await analyzer.analyze_conflicts("Explain virtual memory.", [cand1, cand2])
    assert len(conflicts.shared_information) > 0
    assert conflicts.consensus_level in ("high", "medium", "divergent")
