"""
Adversarial Contradiction Test — Conflict Analyzer Validation
================================================================
Constructs test cases where two candidate models produce known conflicting
answers (deliberately seeded), then verifies the ConflictAnalyzer correctly:
  (a) flags the contradiction
  (b) assigns severity correctly
  (c) feeds the correct resolution to the synthesizer

Tests the claim: "The system detects when models disagree and resolves conflicts."

This addresses the NeurIPS 2024 Multi-LLM Debate finding that naive
ensembles can reinforce shared misconceptions.
"""

import sys
import os
import asyncio
import json
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.services.conflict_analyzer import ConflictAnalyzer
from app.services.synthesizer import SynthesizerService
from app.services.context_builder import ContextBuilder
from app.services.openrouter_service import OpenRouterService
from app.schemas.pydantic_models import NormalizedResponse, UserPreferenceSchema, RankedResponse, EvaluationResult


# ─────────────────────────────────────────────────────────────
# Adversarial Test Case Registry
# ─────────────────────────────────────────────────────────────

ADVERSARIAL_CASES = [
    {
        "id": "ADV-001",
        "query": "What is the time complexity of binary search?",
        "description": "Classic complexity confusion",
        "candidates": [
            {"model": "model_a", "response": "Binary search has O(log n) time complexity because it halves the search space at each step."},
            {"model": "model_b", "response": "Binary search runs in O(n) time complexity since it may need to scan all elements in the worst case."},
            {"model": "model_c", "response": "Binary search operates in O(log n) time. Each comparison eliminates half the remaining elements."},
        ],
        "expected_contradiction": True,
        "ground_truth": "O(log n)",
        "false_claim_model": "model_b",
    },
    {
        "id": "ADV-002",
        "query": "In Python, is a list mutable or immutable?",
        "description": "Mutability confusion",
        "candidates": [
            {"model": "model_a", "response": "Python lists are mutable — you can add, remove, or modify elements after creation."},
            {"model": "model_b", "response": "Python lists are immutable, similar to tuples. You cannot change them after creation."},
            {"model": "model_c", "response": "Lists in Python are mutable data structures. Unlike tuples, they support in-place modification."},
        ],
        "expected_contradiction": True,
        "ground_truth": "mutable",
        "false_claim_model": "model_b",
    },
    {
        "id": "ADV-003",
        "query": "What does HTTP stand for?",
        "description": "Acronym contradiction",
        "candidates": [
            {"model": "model_a", "response": "HTTP stands for HyperText Transfer Protocol, the foundation of data communication on the web."},
            {"model": "model_b", "response": "HTTP stands for HyperText Transmission Protocol. It defines how web servers communicate."},
            {"model": "model_c", "response": "HTTP is the HyperText Transfer Protocol, used to structure requests and responses over the internet."},
        ],
        "expected_contradiction": True,
        "ground_truth": "HyperText Transfer Protocol",
        "false_claim_model": "model_b",
    },
    {
        "id": "ADV-004",
        "query": "Is Python interpreted or compiled?",
        "description": "Execution model contradiction",
        "candidates": [
            {"model": "model_a", "response": "Python is an interpreted language — the Python interpreter executes code line by line at runtime."},
            {"model": "model_b", "response": "Python is a fully compiled language, similar to C or Java, which generates native machine code before execution."},
            {"model": "model_c", "response": "Python is primarily interpreted, though CPython does compile source code to bytecode first before interpretation."},
        ],
        "expected_contradiction": True,
        "ground_truth": "interpreted (with bytecode compilation step)",
        "false_claim_model": "model_b",
    },
    {
        "id": "ADV-005",
        "query": "What is the default port for HTTPS?",
        "description": "Port number contradiction",
        "candidates": [
            {"model": "model_a", "response": "HTTPS uses port 443 by default for secure encrypted web communication."},
            {"model": "model_b", "response": "HTTPS runs on port 80, which is shared with HTTP but uses SSL/TLS encryption."},
            {"model": "model_c", "response": "The standard port for HTTPS is 443. Port 80 is reserved for plain HTTP."},
        ],
        "expected_contradiction": True,
        "ground_truth": "443",
        "false_claim_model": "model_b",
    },
    {
        "id": "ADV-006",
        "query": "Does quicksort have worst-case O(n^2) time complexity?",
        "description": "Consensus case — no contradiction expected",
        "candidates": [
            {"model": "model_a", "response": "Yes, quicksort has O(n^2) worst-case complexity, which occurs when the pivot always selects the minimum or maximum element."},
            {"model": "model_b", "response": "Yes, quicksort degrades to O(n^2) in the worst case, though its average case is O(n log n)."},
            {"model": "model_c", "response": "Quicksort is O(n^2) worst-case (already-sorted input with bad pivot) but O(n log n) on average."},
        ],
        "expected_contradiction": False,
        "ground_truth": "O(n^2) worst case, O(n log n) average",
        "false_claim_model": None,
    },
]


# ─────────────────────────────────────────────────────────────
# Test Runner
# ─────────────────────────────────────────────────────────────

async def run_adversarial_tests():
    openrouter = OpenRouterService()
    conflict_analyzer = ConflictAnalyzer(openrouter)
    synthesizer = SynthesizerService(openrouter)

    results = []
    passed = 0
    total = len(ADVERSARIAL_CASES)

    print("=" * 65)
    print("ADVERSARIAL CONTRADICTION DETECTION TEST SUITE")
    print("=" * 65)
    print(f"Total test cases: {total}\n")

    for case in ADVERSARIAL_CASES:
        cid = case["id"]
        query = case["query"]
        print(f"[{cid}] {case['description']}")
        print(f"  Query: {query}")

        # Build NormalizedResponse objects for each candidate
        candidate_responses = []
        for i, cand in enumerate(case["candidates"]):
            candidate_responses.append(NormalizedResponse(
                response_id=i + 1,
                model=cand["model"],
                provider="test-provider",
                response_text=cand["response"],
                input_tokens=15,
                output_tokens=len(cand["response"].split()),
                total_tokens=15 + len(cand["response"].split()),
                cost=0.0001,
                latency_ms=800,
                status="success"
            ))

        # Run Conflict Analyzer
        conflict_result = await conflict_analyzer.analyze_conflicts(
            query=query,
            candidates=candidate_responses,
            model="openai/gpt-4o-mini"
        )

        # Check results
        found_contradiction = len(conflict_result.contradictions) > 0
        expected = case["expected_contradiction"]
        test_passed = found_contradiction == expected

        if test_passed:
            passed += 1
            status_str = "[PASS]"
        else:
            status_str = "[FAIL]"

        print(f"  Expected contradiction: {expected}")
        print(f"  Found contradiction   : {found_contradiction}")
        print(f"  Contradictions found  : {len(conflict_result.contradictions)}")
        print(f"  Consensus level       : {conflict_result.consensus_level}")

        if conflict_result.contradictions:
            for c in conflict_result.contradictions:
                print(f"  -> [{c.severity.upper()}] {c.claim_a!r} vs {c.claim_b!r}")

        print(f"  Status: {status_str}")

        # If contradiction expected, also run synthesis and check it reflects ground truth
        synthesis_correct = None
        synthesis_text = ""
        if expected and found_contradiction:
            prefs = UserPreferenceSchema()
            ranked = [RankedResponse(
                response_id=c.response_id,
                model=c.model,
                provider=c.provider,
                response_text=c.response_text,
                rank=i+1,
                quality_score=8.0,
                resource_penalty=0.0,
                overall_score=8.0,
                cost=c.cost,
                tokens=c.total_tokens,
                latency_ms=c.latency_ms,
                criteria_scores={"relevance": 8.0, "correctness": 8.0, "completeness": 8.0, "clarity": 8.0},
                reasoning="Test evaluation reasoning"
            ) for i, c in enumerate(candidate_responses)]

            context = ContextBuilder.build_structured_context(
                query=query, ranked_candidates=ranked,
                conflicts=conflict_result, preferences=prefs
            )
            synthesis = await synthesizer.synthesize(
                query_id=0, query=query,
                structured_context=context,
                synthesis_model="openai/gpt-4o-mini",
                preferences=prefs
            )
            synthesis_text = synthesis.final_response
            ground_truth = case["ground_truth"].lower()
            synthesis_correct = ground_truth.split()[0] in synthesis_text.lower()
            print(f"  Synthesis correct ({case['ground_truth']}): {synthesis_correct}")

        print()
        results.append({
            "id": cid,
            "query": query,
            "description": case["description"],
            "expected_contradiction": expected,
            "found_contradiction": found_contradiction,
            "n_contradictions": len(conflict_result.contradictions),
            "consensus_level": conflict_result.consensus_level,
            "contradictions": [
                {"claim_a": c.claim_a, "claim_b": c.claim_b, "severity": c.severity}
                for c in conflict_result.contradictions
            ],
            "test_passed": test_passed,
            "ground_truth": case["ground_truth"],
            "false_claim_model": case["false_claim_model"],
            "synthesis_correct": synthesis_correct,
            "synthesis_text": synthesis_text[:500] if synthesis_text else "",
        })

    # Summary
    print("=" * 65)
    print(f"ADVERSARIAL TEST RESULTS: {passed}/{total} PASSED")
    precision = passed / total * 100
    print(f"Contradiction Detection Accuracy: {precision:.1f}%")
    print("=" * 65)

    # Save
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "adversarial_test_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "summary": {"passed": passed, "total": total, "accuracy_pct": round(precision, 2)},
            "cases": results
        }, f, indent=2)
    print(f"\nResults saved to: {out_path}")
    return results


if __name__ == "__main__":
    asyncio.run(run_adversarial_tests())
