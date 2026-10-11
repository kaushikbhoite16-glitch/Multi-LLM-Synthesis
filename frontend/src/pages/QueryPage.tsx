import React, { useState } from 'react';
import {
  UserPreferences,
  ModelConfig,
  PipelineRunResponse
} from '../types';
import { PreferenceControls } from '../components/PreferenceControls';
import { ModelSelector } from '../components/ModelSelector';
import { PipelineStepper, StepItem } from '../components/PipelineStepper';
import { apiService } from '../services/api';
import {
  Sparkles,
  ArrowUp,
  Loader2,
  Sliders,
  ChevronDown,
  ChevronUp,
  Cpu,
  Zap,
  Globe,
  Layers,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

interface QueryPageProps {
  availableModels: ModelConfig[];
  onExecutionComplete: (result: PipelineRunResponse) => void;
}

export const QueryPage: React.FC<QueryPageProps> = ({
  availableModels,
  onExecutionComplete,
}) => {
  const [query, setQuery] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([
    'google/gemini-2.5-flash',
    'openai/gpt-4o-mini',
    'meta-llama/llama-3.1-8b-instruct'
  ]);
  const [evaluatorModel, setEvaluatorModel] = useState<string>('openai/gpt-4o-mini');
  const [synthesisModel, setSynthesisModel] = useState<string>('openai/gpt-4o-mini');
  const [executionMode, setExecutionMode] = useState<'live' | 'simulation'>('simulation');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [preferences, setPreferences] = useState<UserPreferences>({
    relevance_weight: 0.25,
    correctness_weight: 0.25,
    completeness_weight: 0.15,
    clarity_weight: 0.15,
    consistency_weight: 0.05,
    preference_match_weight: 0.10,
    conciseness_weight: 0.05,
    technical_depth_weight: 0.0,
    creativity_weight: 0.0,
    cost_weight: 0.0,
    token_weight: 0.0,
    latency_weight: 0.0,
    max_cost: 0.10,
    max_tokens: 2500,
    max_latency_ms: 15000,
    scoring_mode: 'balanced'
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialSteps: StepItem[] = [
    { id: 'query_analysis', name: '1. Query Analysis', status: 'idle' },
    { id: 'generation', name: '2. Multi-LLM Calls', status: 'idle' },
    { id: 'evaluation', name: '3. Semantic Eval', status: 'idle' },
    { id: 'ranking', name: '4. Scoring & Ranking', status: 'idle' },
    { id: 'conflicts', name: '5. Conflict Analysis', status: 'idle' },
    { id: 'synthesis', name: '6. Master Synthesis', status: 'idle' },
    { id: 'final_eval', name: '7. Final Validation', status: 'idle' },
  ];

  const [steps, setSteps] = useState<StepItem[]>(initialSteps);

  const examplePrompts = [
    {
      title: 'Operating Systems & Architecture',
      prompt: 'Explain virtual memory in operating systems, paging mechanisms, and page fault handling with a clear step-by-step example.'
    },
    {
      title: 'Concurrent Algorithms & Data Structures',
      prompt: 'Implement an LRU Cache in Python using a doubly linked list with O(1) operations, and explain thread-safety mechanisms.'
    },
    {
      title: 'Probability & Scientific Inference',
      prompt: 'Explain Bayes Theorem and derive posterior probability given prior and likelihood with a clinical diagnostic test example.'
    },
    {
      title: 'Distributed Consensus & CAP Theorem',
      prompt: 'Compare Raft and Paxos consensus algorithms: core phases, leader election, and split-brain resolution.'
    }
  ];

  const updateStepStatus = (id: string, status: 'idle' | 'running' | 'completed' | 'error') => {
    setSteps((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status } : s))
    );
  };

  const handleRunPipeline = async () => {
    if (!query.trim() || query.trim().length < 3) {
      setError('Please enter a query of at least 3 characters.');
      return;
    }

    if (selectedModels.length === 0) {
      setError('Please select at least one candidate model.');
      return;
    }

    setError(null);
    setIsLoading(true);
    setSteps(initialSteps.map((s) => ({ ...s, status: 'idle' })));

    try {
      updateStepStatus('query_analysis', 'running');
      await new Promise((r) => setTimeout(r, 400));
      updateStepStatus('query_analysis', 'completed');
      updateStepStatus('generation', 'running');

      const result = await apiService.runPipeline({
        query: query.trim(),
        models: selectedModels,
        evaluator_model: evaluatorModel,
        synthesis_model: synthesisModel,
        preferences: preferences,
        execution_mode: executionMode
      });

      setSteps((prev) => prev.map((s) => ({ ...s, status: 'completed' })));
      onExecutionComplete(result);
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || err.message || 'Pipeline execution failed.';
      setError(errMsg);
      setSteps((prev) =>
        prev.map((s) => (s.status === 'running' ? { ...s, status: 'error' } : s))
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleRunPipeline();
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4 sm:py-8 animate-in fade-in duration-200">
      {/* ChatGPT / Claude Style Welcome Header */}
      <div className="text-center space-y-3">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-xl shadow-sky-500/20">
          <Sparkles className="w-7 h-7 text-white" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          What would you like to synthesize today?
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
          Query multiple frontier AI models simultaneously, evaluate criteria, detect contradictions, and synthesize an optimal answer.
        </p>

        {/* Mode Selector Pill */}
        <div className="inline-flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
          <button
            onClick={() => setExecutionMode('simulation')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              executionMode === 'simulation'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Simulation (Mock)
          </button>
          <button
            onClick={() => setExecutionMode('live')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              executionMode === 'live'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Live API (Real Gateway)
          </button>
        </div>
      </div>

      {/* Prominent Question Input Box (ChatGPT/Claude Inspired) */}
      <div className="relative rounded-3xl bg-slate-900/90 border border-slate-800 shadow-2xl focus-within:border-sky-500/60 focus-within:ring-2 focus-within:ring-sky-500/20 transition-all p-4">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a complex question, challenge multiple LLMs, or request code synthesis... (Press Enter to run, Shift+Enter for new line)"
          rows={3}
          disabled={isLoading}
          className="w-full bg-transparent text-slate-100 placeholder-slate-500 resize-none text-sm focus:outline-none min-h-[90px] max-h-[300px]"
        />

        <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
          <div className="flex items-center space-x-2 text-slate-400">
            <span className="font-mono text-[11px] hidden sm:inline">
              Selected Models: {selectedModels.length}
            </span>
            <span className="hidden sm:inline">•</span>
            <span className="text-[11px] font-mono">
              Mode: <strong className={executionMode === 'live' ? 'text-emerald-400' : 'text-amber-400'}>{executionMode.toUpperCase()}</strong>
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span className="text-[11px] hidden sm:inline">Configure</span>
              {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            <button
              onClick={handleRunPipeline}
              disabled={isLoading || !query.trim()}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-xs shadow-md shadow-sky-500/25 transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <span>Run Analysis</span>
                  <ArrowUp className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-center space-x-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Stepper Pipeline Progress (Visible When Running) */}
      {isLoading && (
        <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 space-y-4 animate-in fade-in">
          <div className="flex items-center space-x-2 text-sky-400 text-xs font-semibold">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Multi-Agent Research Pipeline In Progress...</span>
          </div>
          <PipelineStepper steps={steps} />
        </div>
      )}

      {/* Clickable Example Prompts (Claude / ChatGPT 2x2 Grid) */}
      {!isLoading && (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
            Explore Example Benchmarks
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {examplePrompts.map((p, idx) => (
              <div
                key={idx}
                onClick={() => setQuery(p.prompt)}
                className="p-4 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-all group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-slate-200 group-hover:text-sky-300 transition-colors">
                    {p.title}
                  </span>
                  <ArrowUp className="w-3.5 h-3.5 text-slate-500 group-hover:text-sky-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all rotate-45" />
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                  {p.prompt}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collapsible Advanced Options Section */}
      {showAdvanced && (
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-6 animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-sky-400" />
              <span>Multi-LLM Synthesis Configuration</span>
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">Custom Param Tuning</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ModelSelector
              availableModels={availableModels}
              selectedModels={selectedModels}
              onToggleModel={(modelId: string) => {
                setSelectedModels((prev) =>
                  prev.includes(modelId) ? prev.filter((m) => m !== modelId) : [...prev, modelId]
                );
              }}
              evaluatorModel={evaluatorModel}
              setEvaluatorModel={setEvaluatorModel}
              synthesisModel={synthesisModel}
              setSynthesisModel={setSynthesisModel}
            />

            <PreferenceControls
              preferences={preferences}
              onChange={setPreferences}
            />
          </div>
        </div>
      )}
    </div>
  );
};
