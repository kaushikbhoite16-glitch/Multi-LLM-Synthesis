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
        model="openai/gpt-4o-mini",
        provider="OpenAI",
        response_text="Virtual memory allows an operating system to execute processes by mapping virtual addresses to physical RAM using page tables.",
        status="success"
    )
    cand2 = NormalizedResponse(
        response_id=2,
        model="meta-llama/llama-3.1-8b-instruct",
        provider="Meta",
        response_text="Virtual memory allows an operating system to execute processes using page tables and address translation.",
        status="success"
    )

    conflicts = await analyzer.analyze_conflicts("Explain virtual memory.", [cand1, cand2])
    assert len(conflicts.shared_information) > 0 or len(conflicts.unique_information) > 0
    assert conflicts.consensus_level in ("high", "medium", "divergent")
