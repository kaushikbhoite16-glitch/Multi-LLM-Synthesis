from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
import datetime

class UserPreferenceSchema(BaseModel):
    # Quality Weights (0.0 to 1.0 or percentage)
    relevance_weight: float = Field(0.25, ge=0.0, le=1.0)
    correctness_weight: float = Field(0.25, ge=0.0, le=1.0)
    completeness_weight: float = Field(0.15, ge=0.0, le=1.0)
    clarity_weight: float = Field(0.15, ge=0.0, le=1.0)
    consistency_weight: float = Field(0.05, ge=0.0, le=1.0)
    preference_match_weight: float = Field(0.10, ge=0.0, le=1.0)
    conciseness_weight: float = Field(0.05, ge=0.0, le=1.0)
    technical_depth_weight: float = Field(0.0, ge=0.0, le=1.0)
    creativity_weight: float = Field(0.0, ge=0.0, le=1.0)
    
    # Resource Penalty Weights (0.0 to 1.0)
    cost_weight: float = Field(0.0, ge=0.0, le=1.0)
    token_weight: float = Field(0.0, ge=0.0, le=1.0)
    latency_weight: float = Field(0.0, ge=0.0, le=1.0)
    
    # Resource Constraints
    max_cost: float = Field(0.10, ge=0.0)
    max_tokens: int = Field(4000, ge=100)
    max_latency_ms: int = Field(15000, ge=500)
    
    # Scoring Mode: quality-first, balanced, cost-aware, user-customized
    scoring_mode: str = Field("quality-first")

    def normalized_quality_weights(self) -> Dict[str, float]:
        weights = {
            "relevance": self.relevance_weight,
            "correctness": self.correctness_weight,
            "completeness": self.completeness_weight,
            "clarity": self.clarity_weight,
            "consistency": self.consistency_weight,
            "preference_match": self.preference_match_weight,
            "conciseness": self.conciseness_weight,
            "technical_depth": self.technical_depth_weight,
            "creativity": self.creativity_weight
        }
        total = sum(weights.values())
        if total <= 0:
            return {k: 1.0 / len(weights) for k in weights}
        return {k: round(v / total, 4) for k, v in weights.items()}


class QueryAnalysisResult(BaseModel):
    query_type: str = "educational"  # educational, coding, reasoning, creative, analytical, factual
    domain: str = "computer_science"
    difficulty: str = "beginner"     # beginner, intermediate, advanced
    expected_style: str = "explanatory"
    recommended_criteria: List[str] = [
        "relevance", "correctness", "completeness", "clarity", "consistency", "preference_match"
    ]
    recommended_weights: Optional[Dict[str, float]] = None


class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    role: str = "candidate"  # candidate, evaluator, synthesizer
    enabled: bool = True
    max_tokens: int = 1500
    temperature: float = 0.7
    cost_per_1k_input: float = 0.0005
    cost_per_1k_output: float = 0.0015


class NormalizedResponse(BaseModel):
    response_id: int
    model: str
    provider: str
    response_text: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    status: str = "success"  # success, error, timeout
    generation_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[str] = None


class EvaluationResult(BaseModel):
    response_id: int
    model: str
    evaluator_model: str
    relevance: float = Field(..., ge=0.0, le=10.0)
    correctness: float = Field(..., ge=0.0, le=10.0)
    completeness: float = Field(..., ge=0.0, le=10.0)
    clarity: float = Field(..., ge=0.0, le=10.0)
    consistency: float = Field(..., ge=0.0, le=10.0)
    preference_match: float = Field(..., ge=0.0, le=10.0)
    conciseness: float = Field(8.0, ge=0.0, le=10.0)
    technical_depth: float = Field(8.0, ge=0.0, le=10.0)
    overall_score: float = Field(..., ge=0.0, le=10.0)
    reasoning: str
    criteria_breakdown: Optional[Dict[str, float]] = None


class RankedResponse(BaseModel):
    rank: int
    response_id: int
    model: str
    provider: str
    response_text: str
    overall_score: float
    quality_score: float
    resource_penalty: float = 0.0
    cost: float
    tokens: int
    latency_ms: int
    criteria_scores: Dict[str, float]
    reasoning: str


class ConflictItem(BaseModel):
    claim_a: str
    model_a: str
    claim_b: str
    model_b: str
    description: str
    severity: str = "medium"  # low, medium, high


class ConflictAnalysisResult(BaseModel):
    topic: str
    shared_information: List[str] = []
    unique_information: Dict[str, List[str]] = {}
    contradictions: List[ConflictItem] = []
    potential_uncertainty: List[str] = []
    consensus_level: str = "medium"


class SynthesisResult(BaseModel):
    query_id: int
    synthesis_model: str
    context: str
    final_response: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    status: str = "success"


class FinalEvaluationResult(BaseModel):
    evaluator_model: str
    relevance: float
    correctness: float
    completeness: float
    clarity: float
    consistency: float
    preference_match: float
    conciseness: float
    technical_depth: float
    overall_score: float
    reasoning: str
    best_candidate_model: str
    best_candidate_score: float
    improvement_pct: float


class PipelineRunRequest(BaseModel):
    query: str
    models: Optional[List[str]] = None
    evaluator_model: Optional[str] = None
    synthesis_model: Optional[str] = None
    preferences: Optional[UserPreferenceSchema] = None
    scoring_mode: Optional[str] = "quality-first"


class PipelineRunResponse(BaseModel):
    query_id: int
    query_text: str
    analysis: QueryAnalysisResult
    candidate_responses: List[NormalizedResponse]
    evaluations: List[EvaluationResult]
    ranking: List[RankedResponse]
    conflicts: ConflictAnalysisResult
    structured_context: str
    synthesis: SynthesisResult
    final_evaluation: FinalEvaluationResult
    total_pipeline_tokens: int
    total_pipeline_cost: float
    total_pipeline_latency_ms: int
    is_mock: bool = False


class HumanEvaluationRequest(BaseModel):
    query_id: int
    candidate_a_id: int
    candidate_b_id: int
    preferred_choice: str  # 'A', 'B', 'equal'
    relevance_score: int = Field(5, ge=1, le=5)
    correctness_score: int = Field(5, ge=1, le=5)
    clarity_score: int = Field(5, ge=1, le=5)
    completeness_score: int = Field(5, ge=1, le=5)
    preference_match_score: int = Field(5, ge=1, le=5)
    notes: Optional[str] = None


class ExperimentCreateRequest(BaseModel):
    name: str
    description: str
    configuration: Dict[str, Any]
