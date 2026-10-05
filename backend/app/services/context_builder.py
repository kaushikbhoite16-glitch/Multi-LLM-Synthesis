from typing import List, Optional
from app.schemas.pydantic_models import (
    RankedResponse,
    ConflictAnalysisResult,
    UserPreferenceSchema
)

class ContextBuilder:
    @staticmethod
    def build_structured_context(
        query: str,
        ranked_candidates: List[RankedResponse],
        conflicts: ConflictAnalysisResult,
        preferences: Optional[UserPreferenceSchema] = None
    ) -> str:
        """
        Builds a comprehensive, research-grade structured context for the synthesis LLM.
        Explicitly isolates query, user preferences, candidate evaluations, resource metrics,
        shared claims, and resolved contradictions.
        """
        divider = "=" * 60
        sections: List[str] = []

        # 1. User Query Section
        sections.append(f"{divider}\nUSER QUERY\n{divider}\n{query.strip()}\n")

        # 2. User Preferences Section
        pref_text = "Standard Balanced Settings (Relevance: 25%, Correctness: 25%, Completeness: 15%, Clarity: 15%, Consistency: 5%, Match: 10%, Conciseness: 5%)"
        if preferences:
            weights = preferences.normalized_quality_weights()
            pref_lines = [f"- {k.replace('_', ' ').capitalize()}: {int(v * 100)}%" for k, v in weights.items() if v > 0]
            pref_text = f"Scoring Mode: {preferences.scoring_mode}\n" + "\n".join(pref_lines)
            if preferences.max_tokens:
                pref_text += f"\n- Target Max Output Tokens: {preferences.max_tokens}"
        sections.append(f"{divider}\nUSER PREFERENCES & CONSTRAINTS\n{divider}\n{pref_text}\n")

        # 3. Candidate Responses with Multi-Criteria & Resource Metrics
        for idx, cand in enumerate(ranked_candidates):
            scores_str = ", ".join([f"{k}: {v}" for k, v in cand.criteria_scores.items()])
            cand_sec = (
                f"{divider}\n"
                f"CANDIDATE RESPONSE #{idx + 1} (Rank #{cand.rank} | Overall Score: {cand.overall_score}/10)\n"
                f"{divider}\n"
                f"Model: {cand.model} (Provider: {cand.provider})\n\n"
                f"Evaluation Scores:\n{scores_str}\n"
                f"Evaluator Reasoning: {cand.reasoning}\n\n"
                f"Objective Resource Usage:\n"
                f"- Total Tokens: {cand.tokens}\n"
                f"- API Cost: ${cand.cost:.6f}\n"
                f"- Generation Latency: {cand.latency_ms} ms\n\n"
                f"Response Text:\n{cand.response_text}\n"
            )
            sections.append(cand_sec)

        # 4. Agreement Analysis Section
        shared_str = "\n".join([f"• {item}" for item in conflicts.shared_information]) if conflicts.shared_information else "No broad consensus points identified."
        sections.append(f"{divider}\nAGREEMENT ANALYSIS (CONSENSUS)\n{divider}\n{shared_str}\n")

        # 5. Conflict & Contradiction Analysis Section
        contradiction_lines = []
        for c in conflicts.contradictions:
            contradiction_lines.append(
                f"• [{c.severity.upper()} SEVERITY] Divergence between {c.model_a} and {c.model_b}:\n"
                f"  - Claim A: \"{c.claim_a}\"\n"
                f"  - Claim B: \"{c.claim_b}\"\n"
                f"  - Issue: {c.description}"
            )
        conflicts_str = "\n".join(contradiction_lines) if contradiction_lines else "No direct factual contradictions detected across candidate outputs."
        
        uncertainties_str = ""
        if conflicts.potential_uncertainty:
            uncertainties_str = "\nPotential Uncertainties:\n" + "\n".join([f"• {u}" for u in conflicts.potential_uncertainty])
            
        sections.append(f"{divider}\nCONFLICT AND CONTRADICTION ANALYSIS\n{divider}\n{conflicts_str}{uncertainties_str}\n")

        # 6. Synthesis Instructions
        instructions = (
            f"{divider}\nSYNTHESIS INSTRUCTIONS\n{divider}\n"
            "You are the Final Synthesizer in a RAG-like Multi-LLM Response Synthesis Architecture.\n"
            "Your task is to synthesize ONE master response tailored to the user's specific query and preferences.\n"
            "Rules:\n"
            "1. Combine accurate, verified, and useful information from across all candidate responses.\n"
            "2. Prioritize user style and depth requirements (e.g. beginner friendly or deep technical, concise or thorough).\n"
            "3. Do NOT blindly pick the highest-ranked candidate or blindly follow majority vote.\n"
            "4. Carefully resolve all flagged contradictions and dismiss unsupported or dubious claims.\n"
            "5. Eliminate duplicated phrases, redundant fluff, and filler.\n"
            "6. Provide a cohesive, elegant, comprehensive, and well-structured answer.\n"
            "7. CRITICAL: Do NOT mention internal system details, evaluation scores, ranking, candidate model names, or OpenRouter in your final output unless explicitly asked in the query."
        )
        sections.append(instructions)

        return "\n".join(sections)
