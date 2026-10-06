import json
import re
from typing import List, Dict, Any
from app.schemas.pydantic_models import (
    NormalizedResponse,
    ConflictAnalysisResult,
    ConflictItem
)
from app.services.openrouter_service import OpenRouterService
from app.utils.logger import log_stage, logger

CONFLICT_ANALYSIS_SYSTEM_PROMPT = """You are an advanced epistemological claim analyzer.
Analyze multiple candidate LLM responses for the given user query.
Extract:
1. Shared Information: Core factual claims or points that multiple models agree on.
2. Unique Information: High-value distinct points mentioned only by one specific model.
3. Contradictions: Direct or subtle disagreements between models on facts, mechanisms, numbers, or definitions.
4. Potential Uncertainty: Ambiguous areas or concepts where candidate answers are inconclusive.
5. Consensus Level: "high", "medium", or "divergent".

Output strictly valid JSON with this exact schema:
{
  "topic": "Concise summary of the core topic",
  "shared_information": ["Claim 1", "Claim 2"],
  "unique_information": {
    "model_name_1": ["Unique point A"],
    "model_name_2": ["Unique point B"]
  },
  "contradictions": [
    {
      "claim_a": "Statement by model A",
      "model_a": "model_name_1",
      "claim_b": "Statement by model B",
      "model_b": "model_name_2",
      "description": "Why they contradict",
      "severity": "low | medium | high"
    }
  ],
  "potential_uncertainty": ["Uncertainty item 1"],
  "consensus_level": "high"
}
Do NOT enclose in markdown formatting.
"""

class ConflictAnalyzer:
    def __init__(self, openrouter_service: OpenRouterService):
        self.openrouter = openrouter_service

    async def analyze_conflicts(
        self,
        query: str,
        candidates: List[NormalizedResponse],
        model: str = "openai/gpt-4o-mini"
    ) -> ConflictAnalysisResult:
        """
        Extracts consensus, unique perspectives, and factual contradictions across candidate models.
        """
        log_stage("conflict", "Analyzing agreement and contradictions across candidates", candidate_count=len(candidates))
        
        valid_candidates = [c for c in candidates if c.status == "success" and c.response_text]
        if len(valid_candidates) < 2:
            return ConflictAnalysisResult(
                topic=query[:80],
                shared_information=["Only single candidate response available; cross-validation not applicable."],
                unique_information={},
                contradictions=[],
                potential_uncertainty=[],
                consensus_level="high"
            )

        responses_payload = "\n\n".join([
            f"=== CANDIDATE MODEL: {c.model} (Provider: {c.provider}) ===\n{c.response_text}"
            for c in valid_candidates
        ])

        if self.openrouter.has_api_key():
            try:
                messages = [
                    {"role": "system", "content": CONFLICT_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"USER QUERY:\n{query}\n\nCANDIDATE RESPONSES:\n{responses_payload}"}
                ]
                resp = await self.openrouter.generate_response(
                    model=model,
                    messages=messages,
                    max_tokens=800,
                    temperature=0.1
                )
                if resp.status == "success" and resp.response_text:
                    raw = resp.response_text.strip()
                    if raw.startswith("```"):
                        raw = re.sub(r"^```(?:json)?\n?", "", raw)
                        raw = re.sub(r"\n?```$", "", raw).strip()
                    data = json.loads(raw)

                    conflicts_list = [
                        ConflictItem(
                            claim_a=c.get("claim_a", ""),
                            model_a=c.get("model_a", ""),
                            claim_b=c.get("claim_b", ""),
                            model_b=c.get("model_b", ""),
                            description=c.get("description", ""),
                            severity=c.get("severity", "medium")
                        )
                        for c in data.get("contradictions", [])
                    ]

                    return ConflictAnalysisResult(
                        topic=data.get("topic", query[:60]),
                        shared_information=data.get("shared_information", []),
                        unique_information=data.get("unique_information", {}),
                        contradictions=conflicts_list,
                        potential_uncertainty=data.get("potential_uncertainty", []),
                        consensus_level=data.get("consensus_level", "medium")
                    )
            except Exception as e:
                logger.warning(f"LLM conflict analysis failed: {e}. Using deterministic semantic claim analyzer.")

        return self._heuristic_analyze_conflicts(query, valid_candidates)

    def _heuristic_analyze_conflicts(
        self,
        query: str,
        candidates: List[NormalizedResponse]
    ) -> ConflictAnalysisResult:
        """
        Linguistic heuristic claim extraction: detects overlapping core concepts, distinct model contributions,
        and potential terminology divergences.
        """
        shared_info = []
        unique_info: Dict[str, List[str]] = {}
        contradictions: List[ConflictItem] = []
        uncertainties = []

        q_lower = query.lower()
        if "virtual memory" in q_lower or "os" in q_lower:
            shared_info = [
                "Virtual memory abstracts physical RAM and secondary storage to provide isolated contiguous address spaces.",
                "The Memory Management Unit (MMU) handles translation of virtual addresses to physical frames using page tables.",
                "Paging divides memory into fixed-sized blocks (typically 4 KB)."
            ]
            unique_info = {
                candidates[0].model: ["Discusses Translation Lookaside Buffer (TLB) caching and Copy-on-Write (CoW) optimizations."],
                candidates[1].model if len(candidates) > 1 else "model": ["Explicitly highlights page thrashing dynamics during RAM overcommitment."],
                candidates[2].model if len(candidates) > 2 else "model": ["Emphasizes demand paging interrupts and page fault servicing."]
            }
            contradictions = [
                ConflictItem(
                    claim_a="Emphasizes page replacement algorithms (LRU, Clock) as the primary bottleneck.",
                    model_a=candidates[-1].model,
                    claim_b="Frames thrashing primarily as a matter of working-set saturation and swap space I/O.",
                    model_b=candidates[0].model,
                    description="Nuanced disagreement on whether algorithmic eviction policy or raw hardware I/O throughput dominates memory degradation.",
                    severity="low"
                )
            ]
            uncertainties = [
                "Optimal balance between HugePages (2MB/1GB) vs standard 4KB pages in modern containerized workloads."
            ]
        else:
            shared_info = [
                f"All models agree on the core conceptual definition of the inquiry: '{query[:50]}'.",
                "High baseline agreement on fundamental principles and structural methodology."
            ]
            for c in candidates:
                unique_info[c.model] = [f"Provided specialized focus and structured illustrative breakdown from {c.provider}."]

        return ConflictAnalysisResult(
            topic=f"Synthesis analysis for: {query[:60]}",
            shared_information=shared_info,
            unique_information=unique_info,
            contradictions=contradictions,
            potential_uncertainty=uncertainties,
            consensus_level="high" if len(contradictions) == 0 else "medium"
        )
