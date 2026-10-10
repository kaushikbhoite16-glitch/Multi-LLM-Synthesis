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
import { Play, Loader2, Sparkles, HelpCircle, FileText, CheckCircle2 } from 'lucide-react';

interface QueryPageProps {
  availableModels: ModelConfig[];
  onExecutionComplete: (result: PipelineRunResponse) => void;
}

export const QueryPage: React.FC<QueryPageProps> = ({
  availableModels,
  onExecutionComplete,
}) => {
  const [query, setQuery] = useState('Explain virtual memory in operating systems, paging mechanisms, and page fault handling.');
  const [selectedModels, setSelectedModels] = useState<string[]>([
    'google/gemini-2.5-flash',
    'openai/gpt-4o-mini',
    'meta-llama/llama-3.1-8b-instruct'
  ]);
  const [evaluatorModel, setEvaluatorModel] = useState<string>('openai/gpt-4o-mini');
  const [synthesisModel, setSynthesisModel] = useState<string>('openai/gpt-4o-mini');
  
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

  const samplePrompts = [
    {
      title: 'Operating Systems',
      prompt: 'Explain virtual memory in operating systems, paging mechanisms, and page fault handling.'
    },
    {
      title: 'Algorithms & Coding',
      prompt: 'Implement an LRU Cache in Python using a doubly linked list with O(1) operations, and explain thread-safety.'
    },
    {
      title: 'Mathematics & Proof',
      prompt: 'Explain Bayes Theorem and derive posterior probability given prior and likelihood with a clinical testing example.'
    },
    {
      title: 'Distributed Systems',
      prompt: 'Explain the Raft consensus algorithm and how leader election and log replication prevent split-brain.'
    }
  ];

  const handleToggleModel = (id: string) => {
    if (selectedModels.includes(id)) {
      if (selectedModels.length > 1) {
        setSelectedModels(selectedModels.filter(m => m !== id));
      }
    } else {
      setSelectedModels([...selectedModels, id]);
    }
  };

  const handleExecute = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);

    // Progressive step simulation for feedback while backend pipeline runs
    setSteps(initialSteps.map((s, idx) => ({ ...s, status: idx === 0 ? 'running' : 'idle' })));

    try {
      // Step simulation timers
      const timer1 = setTimeout(() => {
        setSteps(prev => prev.map((s, i) => i === 0 ? { ...s, status: 'completed' } : i === 1 ? { ...s, status: 'running' } : s));
      }, 300);

      const timer2 = setTimeout(() => {
        setSteps(prev => prev.map((s, i) => i <= 1 ? { ...s, status: 'completed' } : i === 2 ? { ...s, status: 'running' } : s));
      }, 700);

      const timer3 = setTimeout(() => {
        setSteps(prev => prev.map((s, i) => i <= 3 ? { ...s, status: 'completed' } : i === 4 ? { ...s, status: 'running' } : s));
      }, 1200);

      const res = await apiService.runPipeline({
        query,
        models: selectedModels,
        evaluator_model: evaluatorModel,
        synthesis_model: synthesisModel,
        preferences,
        scoring_mode: preferences.scoring_mode
      });

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);

      setSteps(initialSteps.map(s => ({ ...s, status: 'completed' })));
      onExecutionComplete(res);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || err.message || 'Pipeline execution failed.');
      setSteps(prev => prev.map(s => s.status === 'running' ? { ...s, status: 'error' } : s));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-200">
      {/* Page Header */}
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
          Query & Research Experiment Runner
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Configure multi-model parameters, set weighted criteria, and synthesize adaptive responses.
        </p>
      </div>

      {/* Main Query Input Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <FileText className="w-4 h-4 text-sky-400" />
            <span>Research Prompt / User Inquiry</span>
          </label>
          <span className="text-[11px] font-mono text-slate-400">{query.length} characters</span>
        </div>

        <textarea
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a prompt to evaluate across models and synthesize (e.g. Explain virtual memory in operating systems)..."
          className="w-full bg-slate-950 border border-slate-700/80 rounded-2xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition leading-relaxed resize-none font-sans"
        />

        {/* Preset Sample Prompts */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] text-slate-400 font-medium">Quick Benchmarks:</span>
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuery(p.prompt)}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/80 transition"
            >
              {p.title}
            </button>
          ))}
        </div>
      </div>

      {/* Model Selection Panel */}
      <ModelSelector
        availableModels={availableModels}
        selectedModels={selectedModels}
        onToggleModel={handleToggleModel}
        evaluatorModel={evaluatorModel}
        setEvaluatorModel={setEvaluatorModel}
        synthesisModel={synthesisModel}
        setSynthesisModel={setSynthesisModel}
      />

      {/* Preferences Controls */}
      <PreferenceControls
        preferences={preferences}
        onChange={setPreferences}
      />

      {/* Live Pipeline Stepper */}
      {isLoading && (
        <PipelineStepper steps={steps} />
      )}

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
          <strong>Execution Error:</strong> {error}
        </div>
      )}

      {/* Execute Button */}
      <div className="flex items-center justify-between pt-2">
        <div className="text-xs text-slate-400 flex items-center space-x-1.5 font-mono">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Full pipeline tracking: query classification, multi-criteria scoring, context synthesis, validation</span>
        </div>

        <button
          type="button"
          disabled={isLoading || !query.trim()}
          onClick={handleExecute}
          className="flex items-center space-x-2 px-8 py-3.5 rounded-2xl bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-slate-950 font-bold text-sm shadow-xl shadow-sky-500/25 transition cursor-pointer"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Orchestrating Pipeline...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Execute Multi-LLM Pipeline</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
