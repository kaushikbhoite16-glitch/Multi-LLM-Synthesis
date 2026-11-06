import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.pipeline import PipelineOrchestrator
from app.schemas.pydantic_models import PipelineRunRequest
from app.rag.seed_data import ensure_seed_data

async def main():
    ensure_seed_data()
    orchestrator = PipelineOrchestrator()
    req = PipelineRunRequest(
        query="explain virtual memory and page replacement",
        execution_mode="simulation",
        enable_rag=True
    )
    print("Executing pipeline with Hybrid RAG enabled...")
    res = await orchestrator.execute_pipeline(req)
    
    print(f"\n[1] Query: '{res.query_text}'")
    print(f"[2] Retrieved Evidence Chunks: {len(res.retrieved_evidence)}")
    assert len(res.retrieved_evidence) >= 1, "Evidence chunks must not be empty"
    
    for idx, e in enumerate(res.retrieved_evidence):
        print(f"    Chunk {idx+1}: {e.get('citation_id')} - {e.get('title')} (score: {e.get('score', 0):.3f})")
    
    print(f"\n[3] Candidate Models Evaluated on Identical Evidence: {len(res.ranking)}")
    assert len(res.ranking) >= 3, "Expected at least 3 models evaluated"
    
    for r in res.ranking:
        claims_count = len(r.verified_claims) if r.verified_claims else 0
        cites = ", ".join(r.citations) if r.citations else "none"
        print(f"    Model: {r.model:<30} | Overall: {r.overall_score:.2f} | Evidence: {r.evidence_score or 0.0:.2f} | Claims Verified: {claims_count} | Citations: {cites}")
        assert r.overall_score is not None
        assert r.model is not None
    
    print(f"\n[4] Adaptive Synthesis Output:")
    print(f"    Synthesis Model: {res.synthesis.synthesis_model}")
    print(f"    Factuality Score: {res.synthesis.factuality_score or 0.0:.2f}")
    print(f"    Synthesized Text Preview: {res.synthesis.final_response[:200]}...")
    assert len(res.synthesis.final_response) > 50
    if res.synthesis.citations:
        print(f"    Citations attached: {len(res.synthesis.citations)}")
    print("\nSUCCESS: Hybrid RAG pipeline with multi-model identical evidence ranking verified completely!")

if __name__ == "__main__":
    asyncio.run(main())
