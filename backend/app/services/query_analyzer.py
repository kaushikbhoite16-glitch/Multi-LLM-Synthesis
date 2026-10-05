import json
import re
from typing import Dict, Any, List
from app.schemas.pydantic_models import QueryAnalysisResult
from app.services.openrouter_service import OpenRouterService
from app.utils.logger import log_stage, logger

QUERY_ANALYSIS_SYSTEM_PROMPT = """You are an expert natural language query analyzer for an advanced multi-LLM evaluation system.
Analyze the user's query and output a strict JSON object with these exact keys:
{
  "query_type": "educational | coding | reasoning | creative | analytical | factual",
  "domain": "computer_science | mathematics | science | humanities | medicine | general_knowledge",
  "difficulty": "beginner | intermediate | advanced",
  "expected_style": "explanatory | code_centric | step_by_step | concise | creative | formal",
  "recommended_criteria": ["relevance", "correctness", "completeness", "clarity", "consistency", "preference_match"],
  "recommended_weights": {
    "relevance": 0.25,
    "correctness": 0.30,
    "completeness": 0.15,
    "clarity": 0.15,
    "consistency": 0.05,
    "preference_match": 0.10
  }
}
Output ONLY valid JSON.
"""

class QueryAnalyzer:
    def __init__(self, openrouter_service: OpenRouterService):
        self.openrouter = openrouter_service

    async def analyze(self, query: str, model: str = "google/gemini-2.0-flash-001") -> QueryAnalysisResult:
        """
        Analyzes the incoming query using LLM structured extraction, with deterministic heuristic fallback.
        """
        log_stage("query", "Analyzing query characteristics", query=query[:60])
        
        if self.openrouter.has_api_key():
            try:
                messages = [
                    {"role": "system", "content": QUERY_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Query: {query}"}
                ]
                resp = await self.openrouter.generate_response(
                    model=model,
                    messages=messages,
                    max_tokens=400,
                    temperature=0.1
                )
                if resp.status == "success" and resp.response_text:
                    # Clean markdown code blocks if any
                    clean_text = resp.response_text.strip()
                    if clean_text.startswith("```"):
                        clean_text = re.sub(r"^```(?:json)?\n?", "", clean_text)
                        clean_text = re.sub(r"\n?```$", "", clean_text).strip()
                    parsed = json.loads(clean_text)
                    return QueryAnalysisResult(**parsed)
            except Exception as e:
                logger.warning(f"LLM query analysis failed or invalid JSON: {e}. Falling back to rule-based analyzer.")

        return self._heuristic_analyze(query)

    def _heuristic_analyze(self, query: str) -> QueryAnalysisResult:
        q = query.lower()
        
        # Determine query type and domain
        if any(w in q for w in ["code", "function", "program", "python", "c++", "java", "sql", "bug", "algorithm", "pointer", "class"]):
            q_type = "coding"
            domain = "computer_science"
            style = "code_centric"
            criteria = ["correctness", "completeness", "clarity", "relevance", "technical_depth"]
            weights = {"correctness": 0.35, "completeness": 0.20, "relevance": 0.20, "clarity": 0.15, "consistency": 0.05, "preference_match": 0.05}
        elif any(w in q for w in ["calculate", "solve", "math", "equation", "proof", "integral", "derivative", "probability"]):
            q_type = "reasoning"
            domain = "mathematics"
            style = "step_by_step"
            criteria = ["correctness", "consistency", "clarity", "completeness", "relevance"]
            weights = {"correctness": 0.40, "consistency": 0.20, "completeness": 0.15, "clarity": 0.15, "relevance": 0.10}
        elif any(w in q for w in ["story", "poem", "essay", "creative", "metaphor", "write a"]):
            q_type = "creative"
            domain = "humanities"
            style = "creative"
            criteria = ["clarity", "creativity", "relevance", "preference_match"]
            weights = {"clarity": 0.25, "creativity": 0.35, "preference_match": 0.20, "relevance": 0.20}
        elif any(w in q for w in ["explain", "what is", "how does", "beginner", "introduction", "teach me"]):
            q_type = "educational"
            domain = "computer_science" if any(w in q for w in ["memory", "process", "network", "cache", "thread"]) else "general_knowledge"
            style = "explanatory"
            criteria = ["clarity", "correctness", "relevance", "completeness", "preference_match"]
            weights = {"clarity": 0.30, "correctness": 0.25, "relevance": 0.20, "completeness": 0.15, "preference_match": 0.10}
        else:
            q_type = "analytical"
            domain = "general_knowledge"
            style = "formal"
            criteria = ["relevance", "correctness", "completeness", "clarity", "consistency"]
            weights = {"relevance": 0.25, "correctness": 0.25, "completeness": 0.20, "clarity": 0.20, "consistency": 0.10}

        # Determine difficulty
        if any(w in q for w in ["beginner", "simple", "basics", "for dummies", "elementary", "high school"]):
            difficulty = "beginner"
        elif any(w in q for w in ["advanced", "deep dive", "kernel", "optimization", "complex", "internals", "distributed"]):
            difficulty = "advanced"
        else:
            difficulty = "intermediate"

        return QueryAnalysisResult(
            query_type=q_type,
            domain=domain,
            difficulty=difficulty,
            expected_style=style,
            recommended_criteria=criteria,
            recommended_weights=weights
        )
