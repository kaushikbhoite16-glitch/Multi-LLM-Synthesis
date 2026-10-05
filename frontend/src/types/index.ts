export interface UserPreferences {
  relevance_weight: number;
  correctness_weight: number;
  completeness_weight: number;
  clarity_weight: number;
  consistency_weight: number;
  preference_match_weight: number;
  conciseness_weight: number;
  technical_depth_weight: number;
  creativity_weight: number;

  cost_weight: number;
  token_weight: number;
  latency_weight: number;

  max_cost: number;
  max_tokens: number;
  max_latency_ms: number;

  scoring_mode: 'quality-first' | 'balanced' | 'cost-aware' | 'user-customized';
}

export interface QueryAnalysis {
  query_type: string;
  domain: string;
  difficulty: string;
  expected_style: string;
  recommended_criteria: string[];
  recommended_weights?: Record<string, number>;
}

export interface NormalizedResponse {
  response_id: number;
  model: string;
  provider: string;
  response_text: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost: number;
  latency_ms: number;
  status: string;
  generation_id?: string;
  error_message?: string;
}

export interface EvaluationResult {
  response_id: number;
  model: string;
  evaluator_model: string;
  relevance: number;
  correctness: number;
  completeness: number;
  clarity: number;
  consistency: number;
  preference_match: number;
  conciseness: number;
  technical_depth: number;
  overall_score: number;
  reasoning: string;
  criteria_breakdown?: Record<string, number>;
}

export interface RankedResponse {
  rank: number;
  response_id: number;
  model: string;
  provider: string;
  response_text: string;
  overall_score: number;
  quality_score: number;
  resource_penalty: number;
  cost: number;
  tokens: number;
  latency_ms: number;
  criteria_scores: Record<string, number>;
  reasoning: string;
}

export interface ConflictItem {
  claim_a: string;
  model_a: string;
  claim_b: string;
  model_b: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
}

export interface ConflictAnalysis {
  topic: string;
  shared_information: string[];
  unique_information: Record<string, string[]>;
  contradictions: ConflictItem[];
  potential_uncertainty: string[];
  consensus_level: string;
}

export interface SynthesisResult {
  query_id: number;
  synthesis_model: string;
  context: string;
  final_response: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost: number;
  latency_ms: number;
  status: string;
}

export interface FinalEvaluationResult {
  evaluator_model: string;
  relevance: number;
  correctness: number;
  completeness: number;
  clarity: number;
  consistency: number;
  preference_match: number;
  conciseness: number;
  technical_depth: number;
  overall_score: number;
  reasoning: string;
  best_candidate_model: string;
  best_candidate_score: number;
  improvement_pct: number;
}

export interface PipelineRunResponse {
  query_id: number;
  query_text: string;
  analysis: QueryAnalysis;
  candidate_responses: NormalizedResponse[];
  evaluations: EvaluationResult[];
  ranking: RankedResponse[];
  conflicts: ConflictAnalysis;
  structured_context: string;
  synthesis: SynthesisResult;
  final_evaluation: FinalEvaluationResult;
  total_pipeline_tokens: number;
  total_pipeline_cost: number;
  total_pipeline_latency_ms: number;
  is_mock: boolean;
}

export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  role: 'candidate' | 'evaluator' | 'synthesizer';
  enabled: boolean;
  max_tokens: number;
  temperature: number;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
}

export interface AnalyticsData {
  kpis: {
    total_queries: number;
    total_model_calls: number;
    total_tokens: number;
    total_cost: number;
    average_latency_ms: number;
    average_candidate_quality: number;
    average_synthesized_quality: number;
    synthesis_improvement_pct: number;
  };
  per_model: Array<{
    model: string;
    provider: string;
    calls: number;
    avg_quality: number;
    avg_tokens: number;
    avg_cost: number;
    avg_latency_ms: number;
  }>;
  quality_vs_cost: Array<{
    name: string;
    provider: string;
    cost: number;
    quality: number;
    tokens: number;
    latency: number;
    is_pareto?: boolean;
  }>;
  is_mock: boolean;
}
