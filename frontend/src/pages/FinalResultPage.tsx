import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PipelineRunResponse } from '../types';
import { ComparisonTable } from '../components/ComparisonTable';
import { ConflictViewer } from '../components/ConflictViewer';
import { StructuredContextViewer } from '../components/StructuredContextViewer';
import {
  Sparkles,
  Award,
  Layers,
  FileCode,
  AlertTriangle,
  Scale,
  Coins,
  Clock,
  Copy,
  Check,
  RotateCcw,
  CheckCircle2,
  TrendingUp,
  Cpu,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface FinalResultPageProps {
  result: PipelineRunResponse;
  onNewQuery: () => void;
}

export const FinalResultPage: React.FC<FinalResultPageProps> = ({ result, onNewQuery }) => {
  const [activeTab, setActiveTab] = useState<'answer' | 'candidates' | 'evaluations' | 'conflicts' | 'context' | 'resources'>('answer');
  const [copiedAnswer, setCopiedAnswer] = useState(false);
  const [copiedCandidateId, setCopiedCandidateId] = useState<number | null>(null);

  const handleCopyAnswer = () => {
    navigator.clipboard.writeText(result.synthesis.final_response);
    setCopiedAnswer(true);
    setTimeout(() => setCopiedAnswer(false), 2000);
  };

  const handleCopyCandidate = (id: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCandidateId(id);
    setTimeout(() => setCopiedCandidateId(null), 2000);
  };

  const finalScore = result.final_evaluation.overall_score;
  const bestCandScore = result.final_evaluation.best_candidate_score;
  const improvementPct = result.final_evaluation.improvement_pct;

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-200">
      {/* Top Banner with Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-sky-950 text-sky-400 border border-sky-800 font-semibold">
              Query #{result.query_id}
            </span>
            <span
              className={`text-[11px] font-mono uppercase px-2.5 py-0.5 rounded-full border ${
                result.execution_mode === 'simulation' || result.is_mock
                  ? 'bg-purple-500/10 text-purple-300 border-purple-500/20'
                  : result.execution_mode === 'partial'
                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              }`}
            >
              {result.execution_mode === 'simulation' || result.is_mock
                ? 'SIMULATION MODE'
                : result.execution_mode === 'partial'
                ? 'PARTIAL LIVE / FALLBACK'
                : 'LIVE API (GENUINE)'}
            </span>
            <span className="text-xs text-slate-400 font-mono hidden md:inline">
              Domain: {result.analysis.domain} | Difficulty: {result.analysis.difficulty}
            </span>
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-white mt-1">
            "{result.query_text}"
          </h2>
        </div>

        <button
          onClick={onNewQuery}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition shrink-0"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>New Exploration</span>
        </button>
      </div>

      {/* Optional Diagnostic / Telemetry Notice Banner */}
      {result.api_notice && (
        <div className="bg-amber-950/30 border border-amber-600/30 text-amber-200 text-xs px-4 py-3 rounded-2xl flex items-start space-x-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-amber-300">Execution Telemetry: </span>
            {result.api_notice}
          </div>
        </div>
      )}

      {/* KPI Cards Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-2xl">
          <div className="flex items-center space-x-1 text-slate-400 text-xs mb-1">
            <Award className="w-3.5 h-3.5 text-sky-400" />
            <span>Master Score</span>
          </div>
          <div className="text-lg font-bold font-mono text-sky-400">
            {finalScore.toFixed(2)}/10
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-2xl">
          <div className="flex items-center space-x-1 text-slate-400 text-xs mb-1">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>Improvement</span>
          </div>
          <div className="text-lg font-bold font-mono text-emerald-400">
            +{improvementPct.toFixed(1)}%
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-2xl">
          <div className="flex items-center space-x-1 text-slate-400 text-xs mb-1">
            <Award className="w-3.5 h-3.5 text-indigo-400" />
            <span>Best Model</span>
          </div>
          <div className="text-lg font-bold font-mono text-indigo-400">
            {bestCandScore.toFixed(2)}/10
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-2xl">
          <div className="flex items-center space-x-1 text-slate-400 text-xs mb-1">
            <Coins className="w-3.5 h-3.5 text-amber-400" />
            <span>Total Cost</span>
          </div>
          <div className="text-lg font-bold font-mono text-amber-400">
            {result.execution_mode === 'simulation' || result.is_mock
              ? '$0.000000 (Simulated)'
              : `$${result.total_pipeline_cost.toFixed(6)}`}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-2xl">
          <div className="flex items-center space-x-1 text-slate-400 text-xs mb-1">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span>Tokens</span>
          </div>
          <div className="text-lg font-bold font-mono text-purple-400">
            {result.total_pipeline_tokens.toLocaleString()}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-2xl">
          <div className="flex items-center space-x-1 text-slate-400 text-xs mb-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Latency</span>
          </div>
          <div className="text-lg font-bold font-mono text-slate-300">
            {(result.total_pipeline_latency_ms / 1000).toFixed(2)}s
          </div>
        </div>
      </div>

      {/* Tabs Row */}
      <div className="flex items-center space-x-1 border-b border-slate-800 pb-2 overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveTab('answer')}
          className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
            activeTab === 'answer'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span>Synthesized Answer</span>
        </button>

        <button
          onClick={() => setActiveTab('candidates')}
          className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
            activeTab === 'candidates'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Scale className="w-3.5 h-3.5" />
          <span>Candidate Responses ({result.candidate_responses.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('evaluations')}
          className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
            activeTab === 'evaluations'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Award className="w-3.5 h-3.5" />
          <span>Multi-Criteria Scores</span>
        </button>

        <button
          onClick={() => setActiveTab('conflicts')}
          className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
            activeTab === 'conflicts'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Contradictions & Disagreements</span>
        </button>

        <button
          onClick={() => setActiveTab('context')}
          className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
            activeTab === 'context'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>Structured Context</span>
        </button>
      </div>

      {/* Tab 1: Prominent Final Synthesized Answer */}
      {activeTab === 'answer' && (
        <div className="space-y-6">
          <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 sm:p-8 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Adaptive Synthesized Response</h3>
                  <p className="text-xs text-slate-400">
                    Engineered by master synthesizer <span className="font-mono text-sky-400">{result.synthesis.synthesis_model}</span>
                  </p>
                </div>
              </div>

              <button
                onClick={handleCopyAnswer}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
              >
                {copiedAnswer ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Answer</span>
                  </>
                )}
              </button>
            </div>

            {/* Answer Text Rendered as Rich Styled Markdown */}
            <div className="text-slate-200 text-sm leading-relaxed font-sans">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ node, ...props }) => <h1 className="text-xl font-bold text-white mt-6 mb-3 border-b border-slate-800 pb-2" {...props} />,
                  h2: ({ node, ...props }) => <h2 className="text-lg font-bold text-sky-400 mt-5 mb-2.5" {...props} />,
                  h3: ({ node, ...props }) => <h3 className="text-base font-semibold text-indigo-300 mt-4 mb-2" {...props} />,
                  h4: ({ node, ...props }) => <h4 className="text-sm font-semibold text-slate-200 mt-3 mb-1.5" {...props} />,
                  p: ({ node, ...props }) => <p className="mb-3.5 leading-relaxed text-slate-300" {...props} />,
                  strong: ({ node, ...props }) => <strong className="font-semibold text-white" {...props} />,
                  em: ({ node, ...props }) => <em className="italic text-slate-300" {...props} />,
                  ul: ({ node, ...props }) => <ul className="list-disc list-outside pl-5 mb-3.5 space-y-1 text-slate-300" {...props} />,
                  ol: ({ node, ...props }) => <ol className="list-decimal list-outside pl-5 mb-3.5 space-y-1 text-slate-300" {...props} />,
                  li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                  blockquote: ({ node, ...props }) => (
                    <blockquote className="border-l-4 border-sky-500 pl-4 py-1.5 my-3 bg-slate-800/40 rounded-r text-slate-300 italic" {...props} />
                  ),
                  code: ({ node, inline, className, children, ...props }: any) => {
                    if (inline) {
                      return (
                        <code className="px-1.5 py-0.5 rounded bg-slate-800 text-sky-300 font-mono text-xs border border-slate-700/60" {...props}>
                          {children}
                        </code>
                      );
                    }
                    return (
                      <div className="my-4 rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                        <div className="bg-slate-900/90 px-4 py-1.5 text-[11px] font-mono text-slate-400 border-b border-slate-800 flex justify-between items-center">
                          <span>Code Example</span>
                        </div>
                        <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
                          <code {...props}>{children}</code>
                        </pre>
                      </div>
                    );
                  },
                  table: ({ node, ...props }) => (
                    <div className="my-4 overflow-x-auto rounded-xl border border-slate-800">
                      <table className="min-w-full divide-y divide-slate-800 text-xs" {...props} />
                    </div>
                  ),
                  thead: ({ node, ...props }) => <thead className="bg-slate-800/60 text-slate-200 font-semibold" {...props} />,
                  th: ({ node, ...props }) => <th className="px-3.5 py-2 text-left font-semibold text-slate-200" {...props} />,
                  td: ({ node, ...props }) => <td className="px-3.5 py-2 border-t border-slate-800/60 text-slate-300" {...props} />,
                  hr: ({ node, ...props }) => <hr className="border-slate-800 my-6" {...props} />,
                }}
              >
                {result.synthesis.final_response}
              </ReactMarkdown>
            </div>

            {/* Validation Reasoning Footer */}
            {result.final_evaluation && (
              <div className="mt-8 pt-5 border-t border-slate-800/80 bg-slate-950/40 -mx-6 -mb-6 p-6 rounded-b-3xl">
                <div className="flex items-center space-x-2 text-xs font-semibold text-sky-400 mb-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Validation & Semantic Scoring Notes</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {result.final_evaluation.reasoning}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Individual Model Responses */}
      {activeTab === 'candidates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.candidate_responses.map((cand) => (
            <div
              key={cand.response_id}
              className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-3">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-sky-400" />
                    <span className="font-semibold text-xs text-white">{cand.model}</span>
                    <span className="text-[10px] text-slate-400 font-mono">({cand.provider})</span>
                    {cand.is_fallback || cand.execution_mode === 'mock_fallback' ? (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                        SIMULATED
                      </span>
                    ) : cand.execution_mode === 'live' ? (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        LIVE
                      </span>
                    ) : null}
                  </div>
                  <button
                    onClick={() => handleCopyCandidate(cand.response_id, cand.response_text)}
                    className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                    title="Copy Model Response"
                  >
                    {copiedCandidateId === cand.response_id ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
                <div className="text-xs text-slate-300 leading-relaxed max-h-80 overflow-y-auto no-scrollbar space-y-2">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({ node, ...props }) => <h1 className="text-sm font-bold text-white mt-2 mb-1" {...props} />,
                      h2: ({ node, ...props }) => <h2 className="text-xs font-bold text-sky-400 mt-2 mb-1" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-xs font-semibold text-indigo-300 mt-1.5 mb-1" {...props} />,
                      p: ({ node, ...props }) => <p className="mb-2 leading-relaxed text-slate-300" {...props} />,
                      strong: ({ node, ...props }) => <strong className="font-semibold text-white" {...props} />,
                      em: ({ node, ...props }) => <em className="italic text-slate-300" {...props} />,
                      ul: ({ node, ...props }) => <ul className="list-disc list-outside pl-4 mb-2 space-y-0.5 text-slate-300" {...props} />,
                      ol: ({ node, ...props }) => <ol className="list-decimal list-outside pl-4 mb-2 space-y-0.5 text-slate-300" {...props} />,
                      li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                      code: ({ node, inline, className, children, ...props }: any) => {
                        if (inline) {
                          return (
                            <code className="px-1 py-0.5 rounded bg-slate-800 text-sky-300 font-mono text-[11px]" {...props}>
                              {children}
                            </code>
                          );
                        }
                        return (
                          <pre className="p-2.5 my-2 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-300 overflow-x-auto">
                            <code {...props}>{children}</code>
                          </pre>
                        );
                      },
                      table: ({ node, ...props }) => (
                        <div className="my-2 overflow-x-auto rounded-lg border border-slate-800">
                          <table className="min-w-full divide-y divide-slate-800 text-[11px]" {...props} />
                        </div>
                      ),
                      th: ({ node, ...props }) => <th className="px-2 py-1 text-left font-semibold text-slate-200" {...props} />,
                      td: ({ node, ...props }) => <td className="px-2 py-1 border-t border-slate-800/60 text-slate-300" {...props} />,
                    }}
                  >
                    {cand.response_text}
                  </ReactMarkdown>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Tokens: {cand.total_tokens}</span>
                <span>Latency: {(cand.latency_ms / 1000).toFixed(2)}s</span>
                <span>Cost: ${cand.cost.toFixed(5)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Multi-Criteria Evaluations */}
      {activeTab === 'evaluations' && (
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5">
          <ComparisonTable ranking={result.ranking} evaluations={result.evaluations} />
        </div>
      )}

      {/* Tab 4: Contradictions & Conflicts */}
      {activeTab === 'conflicts' && (
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5">
          <ConflictViewer conflicts={result.conflicts} />
        </div>
      )}

      {/* Tab 5: Structured Context */}
      {activeTab === 'context' && (
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5">
          <StructuredContextViewer context={result.structured_context} />
        </div>
      )}
    </div>
  );
};
