import asyncio
import json
from app.services.pipeline import PipelineOrchestrator
from app.schemas.pydantic_models import PipelineRunRequest, UserPreferenceSchema

TEST_QUERIES = [
    {
        "id": 1,
        "query": "What is a for loop in C++?",
        "expected_topic_terms": ["loop", "iteration", "c++", "for"],
        "forbidden_terms": ["virtual memory", "page fault", "mmu", "tlb"]
    },
    {
        "id": 2,
        "query": "Explain virtual memory and paging in OS",
        "expected_topic_terms": ["virtual memory", "page", "mmu"],
        "forbidden_terms": []
    },
    {
        "id": 3,
        "query": "What is a linked list and how does it work?",
        "expected_topic_terms": ["linked list", "node", "pointer"],
        "forbidden_terms": ["virtual memory", "for loop"]
    },
    {
        "id": 4,
        "query": "Difference between stack and queue",
        "expected_topic_terms": ["stack", "queue", "lifo", "fifo"],
        "forbidden_terms": ["virtual memory"]
    },
    {
        "id": 5,
        "query": "Explain binary search algorithm with time complexity",
        "expected_topic_terms": ["binary search", "log", "complexity"],
        "forbidden_terms": ["virtual memory", "stack vs queue"]
    }
]

async def run_verification():
    orchestrator = PipelineOrchestrator(db=None)
    print("=" * 80)
    print("RUNNING VERIFICATION ON 5 TEST QUERIES")
    print("=" * 80)

    all_passed = True

    for item in TEST_QUERIES:
        query = item["query"]
        print(f"\n[TEST #{item['id']}] Query: '{query}'")
        
        req = PipelineRunRequest(
            query=query,
            models=["google/gemini-2.5-flash", "openai/gpt-4o-mini", "meta-llama/llama-3.1-8b-instruct"],
            preferences=UserPreferenceSchema(scoring_mode="balanced"),
            execution_mode="live" # test how live handles expired key or simulation fallback
        )

        res = await orchestrator.execute_pipeline(req)

        print(f"  Execution Mode: {res.execution_mode} (is_mock={res.is_mock})")
        print(f"  API Notice: {res.api_notice}")
        print(f"  Total Cost: ${res.total_pipeline_cost:.6f}")
        print(f"  Candidates Generated: {len(res.candidate_responses)}")
        print(f"  Synthesis Length: {len(res.synthesis.final_response)} chars")
        print(f"  Synthesis Preview: {res.synthesis.final_response[:120]}...")

        # 1. Check expected topic terms in synthesis
        synth_lower = res.synthesis.final_response.lower()
        found_expected = [term for term in item["expected_topic_terms"] if term in synth_lower]
        if not found_expected:
            print(f"  FAILED: Missing expected terms {item['expected_topic_terms']}")
            all_passed = False
        else:
            print(f"  PASSED: Found topic keywords: {found_expected}")

        # 2. Check forbidden terms in synthesis
        found_forbidden = [term for term in item["forbidden_terms"] if term in synth_lower]
        if found_forbidden:
            print(f"  FAILED: Found forbidden off-topic terms: {found_forbidden}")
            all_passed = False
        else:
            print(f"  PASSED: Zero off-topic pollution.")

        # 3. Check candidate relevancy
        for cand in res.candidate_responses:
            cand_lower = cand.response_text.lower()
            c_forbidden = [term for term in item["forbidden_terms"] if term in cand_lower]
            if c_forbidden:
                print(f"  FAILED: Candidate {cand.model} contains off-topic terms: {c_forbidden}")
                all_passed = False

        # 4. Check cost correctness
        if res.execution_mode == "simulation" and res.total_pipeline_cost != 0.0:
            print(f"  FAILED: Simulated cost is non-zero: {res.total_pipeline_cost}")
            all_passed = False
        else:
            print(f"  PASSED: Accurate cost accounting ($0.00 for simulation).")

    print("\n" + "=" * 80)
    if all_passed:
        print("ALL 5 VERIFICATION SUITES PASSED FLAWLESSLY!")
    else:
        print("SOME VERIFICATION CHECKS FAILED.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_verification())
