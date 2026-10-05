import axios from 'axios';
import {
  PipelineRunResponse,
  UserPreferences,
  ModelConfig,
  AnalyticsData,
  QueryAnalysis
} from '../types';

const API_BASE = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  async runPipeline(payload: {
    query: string;
    models?: string[];
    evaluator_model?: string;
    synthesis_model?: string;
    preferences?: UserPreferences;
    scoring_mode?: string;
  }): Promise<PipelineRunResponse> {
    const res = await apiClient.post<PipelineRunResponse>('/run', payload);
    return res.data;
  },

  async analyzeQuery(query: string): Promise<QueryAnalysis> {
    const res = await apiClient.post<QueryAnalysis>('/query', { query });
    return res.data;
  },

  async getModels(): Promise<ModelConfig[]> {
    const res = await apiClient.get<ModelConfig[]>('/models');
    return res.data;
  },

  async updateModel(model: ModelConfig): Promise<ModelConfig> {
    const res = await apiClient.post<ModelConfig>('/models', model);
    return res.data;
  },

  async getAnalytics(): Promise<AnalyticsData> {
    const res = await apiClient.get<AnalyticsData>('/analytics');
    return res.data;
  },

  async getExperiments(): Promise<any[]> {
    const res = await apiClient.get<any[]>('/experiments');
    return res.data;
  },

  async getExperimentDetails(id: number): Promise<any> {
    const res = await apiClient.get<any>(`/experiments/${id}`);
    return res.data;
  },

  async submitHumanEvaluation(payload: {
    query_id: number;
    candidate_a_id: number;
    candidate_b_id: number;
    preferred_choice: string;
    relevance_score: number;
    correctness_score: number;
    clarity_score: number;
    completeness_score: number;
    preference_match_score: number;
    notes?: string;
  }): Promise<any> {
    const res = await apiClient.post('/human-eval', payload);
    return res.data;
  },

  getExportUrl(format: 'json' | 'csv'): string {
    return `/api/export?format=${format}`;
  }
};
