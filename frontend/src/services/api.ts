import axios from 'axios';
import {
  PipelineRunResponse,
  UserPreferences,
  ModelConfig,
  AnalyticsData,
  QueryAnalysis,
  User,
  AuthResponse,
  QuestionHistoryItem
} from '../types';

const API_BASE = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token from localStorage if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiService = {
  // Authentication
  async signUp(payload: { email: string; password: string; full_name?: string }): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>('/auth/signup', payload);
    if (res.data.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
    }
    return res.data;
  },

  async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>('/auth/login', payload);
    if (res.data.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
    }
    return res.data;
  },

  async googleLogin(payload: { email: string; full_name?: string; google_id?: string; credential?: string }): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>('/auth/google', payload);
    if (res.data.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
    }
    return res.data;
  },

  async forgotPassword(email: string): Promise<{ message: string; reset_token?: string }> {
    const res = await apiClient.post('/auth/forgot-password', { email });
    return res.data;
  },

  async resetPassword(token: string, new_password: string): Promise<{ message: string }> {
    const res = await apiClient.post('/auth/reset-password', { token, new_password });
    return res.data;
  },

  async getMe(): Promise<User> {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  logout(): void {
    localStorage.removeItem('access_token');
  },

  // Question History
  async getHistory(search?: string): Promise<QuestionHistoryItem[]> {
    const params = search ? { search } : {};
    const res = await apiClient.get<QuestionHistoryItem[]>('/history', { params });
    return res.data;
  },

  async getHistoryDetail(queryId: number): Promise<PipelineRunResponse> {
    const res = await apiClient.get<PipelineRunResponse>(`/history/${queryId}`);
    return res.data;
  },

  async renameQuestion(queryId: number, title: string): Promise<{ status: string; id: number; title: string }> {
    const res = await apiClient.put(`/history/${queryId}/rename`, { title });
    return res.data;
  },

  async deleteQuestion(queryId: number): Promise<{ status: string; message: string }> {
    const res = await apiClient.delete(`/history/${queryId}`);
    return res.data;
  },

  // Core Pipeline Execution
  async runPipeline(payload: {
    query: string;
    models?: string[];
    evaluator_model?: string;
    synthesis_model?: string;
    preferences?: UserPreferences;
    scoring_mode?: string;
    execution_mode?: 'live' | 'simulation';
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
