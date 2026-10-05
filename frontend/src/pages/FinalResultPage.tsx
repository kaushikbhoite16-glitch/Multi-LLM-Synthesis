import React, { useState } from 'react';
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
  TrendingUp
} from 'lucide-react';

interface FinalResultPageProps {
  result: PipelineRunResponse;
  onNewQuery: () => void;
}

export const FinalResultPage: React.FC<FinalResultPageProps> = ({ result, onNewQuery }) => {
  const [activeTab, setActiveTab] = useState<'answer' | 'candidates' | 'evaluations' | 'conflicts' | 'context' | 'resources'>('answer');
  const [copied, setCopied] = useState(false);

  const handleCopyAnswer = () => {
    navigator.clipboard.writeText(result.synthesis.final_response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const finalScore = result.final_evaluation.overall_score;
  const bestCandScore = result.final_evaluation.best_candidate_score;
  const improvementPct = result.final_evaluation.improvement_pct;

  const candidateTokens = result.candidate_responses.reduce((sum, c) => sum + c.total_tokens, 0);

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-in fade-in duration-200">
      {/* Top Banner with Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-sky-950 text-sky-400 border border-sky-800 font-semibold">
              Query #{result.query_id}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Domain: {result.analysis.domain} | Difficulty: {result.analysis.difficulty}
            </span>
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-white mt-1">
            "{result.query_text}"
          </h2>
        </div>

        <button
          onClick={onNewQuery}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>New Experiment</span>
        </button>
      </div>

      {/* KPI Cards Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5">
          <span className="text-slate-400 text-[10px] uppercase font-mono block">Synthesized Score</span>
          <div className="flex items-baseline space-x-1 mt-1">
            <span className="text-xl font-bold font-mono text-sky-400">{finalScore.toFixed(2)}</span>
            <span className="text-xs text-slate-400 font-mono">/ 10</span>
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Automated Multi-Criteria</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5">
          <span className="text-slate-400 text-[10px] uppercase font-mono block">Improvement Delta</span>
          <div className="flex items-baseline space-x-1 mt-1">
            <span className={`text-xl font-bold font-mono ${improvementPct >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {improvementPct >= 0 ? `+${improvementPct.toFixed(1)}%` : `${improvementPct.toFixed(1)}%`}
            </span>
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">vs Best Candidate</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5">
          <span className="text-slate-400 text-[10px] uppercase font-mono block">Models Ensembled</span>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {result.candidate_responses.length}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Parallel Queries</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5">
          <span className="text-slate-400 text-[10px] uppercase font-mono block">Token Footprint</span>
          <div className="text-xl font-bold font-mono text-slate-200 mt-1">
            {result.total_pipeline_tokens.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">{candidateTokens} cand / {result.synthesis.total_tokens} synth</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5">
          <span className="text-slate-400 text-[10px] uppercase font-mono block">Pipeline Cost</span>
          <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
            ${result.total_pipeline_cost.toFixed(5)}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Actual OpenRouter Bill</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5">
          <span className="text-slate-400 text-[10px] uppercase font-mono block">Total Latency</span>
          <div className="text-xl font-bold font-mono text-slate-300 mt-1">
            {(result.total_pipeline_latency_ms / 1000).toFixed(2)}s
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">End-to-End Pipeline</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-2 overflow-x-auto pb-1 text-xs">
        {[
          { id: 'answer', label: 'Final Master Answer', icon: Sparkles },
          { id: 'candidates', label: `Candidate Responses (${result.candidate_responses.length})`, icon: Layers },
          { id: 'evaluations', label: 'Evaluation Matrix', icon: Scale },
          { id: 'conflicts', label: `Conflicts & Agreement (${result.conflicts.contradictions.length})`, icon: AlertTriangle },
          { id: 'context', label: 'Synthesis Context (Viva View)', icon: FileCode },
          { id: 'resources', label: 'Cost & Usage', icon: Coins },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-1.5 px-4 py-2.5 rounded-t-xl font-medium transition whitespace-nowrap ${
                isActive
                  ? 'bg-slate-800 text-sky-400 border-t-2 border-sky-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Final Master Answer */}
      {activeTab === 'answer' && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Adaptive Synthesized Response</h3>
                <p className="text-xs text-slate-400 font-mono">
                  Synthesizer: {result.synthesis.synthesis_model}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopyAnswer}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs border border-slate-700 transition"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400 font-medium">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Answer</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Formatted Synthesized Text */}
          <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
            {result.synthesis.final_response}
          </div>

          {/* Final Evaluation Reasoning Card */}
          <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-300">Automated Evaluation Protocol Assessment:</span>
              <span className="font-mono text-sky-400 font-bold">
                Final Score: {finalScore.toFixed(2)}/10 vs Best Candidate ({result.final_evaluation.best_candidate_model}): {bestCandScore.toFixed(2)}/10
              </span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              {result.final_evaluation.reasoning}
            </p>
          </div>
        </div>
      )}

      {/* Tab 2: Candidate Responses Cards */}
      {activeTab === 'candidates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.ranking.map((cand) => (
            <div
              key={cand.response_id}
              className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                  <div>
                    <div className="flex items-center space-x-1.5">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                        Rank #{cand.rank}
                      </span>
                      <h4 className="font-semibold text-white text-xs">{cand.model}</h4>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono">{cand.provider}</span>
                  </div>
                  <span className="text-sm font-bold font-mono text-sky-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                    {cand.overall_score.toFixed(2)}/10
                  </span>
                </div>

                <div className="mt-3 bg-slate-950 p-3.5 rounded-xl border border-slate-800/80 font-mono text-[11px] text-slate-300 max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {cand.response_text}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span>Tokens: {cand.tokens}</span>
                <span className="text-emerald-400">${cand.cost.toFixed(5)}</span>
                <span>{cand.latency_ms} ms</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Evaluation Matrix */}
      {activeTab === 'evaluations' && (
        <ComparisonTable
          ranking={result.ranking}
          evaluations={result.evaluations}
          synthesisScore={finalScore}
        />
      )}

      {/* Tab 4: Conflicts & Agreement */}
      {activeTab === 'conflicts' && (
        <ConflictViewer conflicts={result.conflicts} />
      )}

      {/* Tab 5: Structured Context for Synthesis */}
      {activeTab === 'context' && (
        <StructuredContextViewer context={result.structured_context} />
      )}

      {/* Tab 6: Resource Usage Breakdown */}
      {activeTab === 'resources' && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-5">
          <h3 className="font-semibold text-white text-sm">Objective Resource Metrics Breakdown</h3>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono">
                  <th className="py-2.5 px-3">STAGE / MODEL</th>
                  <th className="py-2.5 px-3">ROLE</th>
                  <th className="py-2.5 px-3 text-right">INPUT TOKENS</th>
                  <th className="py-2.5 px-3 text-right">OUTPUT TOKENS</th>
                  <th className="py-2.5 px-3 text-right">TOTAL TOKENS</th>
                  <th className="py-2.5 px-3 text-right">COST ($)</th>
                  <th className="py-2.5 px-3 text-right">LATENCY (MS)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {result.candidate_responses.map((c) => (
                  <tr key={c.response_id} className="hover:bg-slate-800/20">
                    <td className="py-2.5 px-3 font-semibold text-slate-200">{c.model}</td>
                    <td className="py-2.5 px-3 text-slate-400">Candidate</td>
                    <td className="py-2.5 px-3 text-right text-slate-300">{c.input_tokens}</td>
                    <td className="py-2.5 px-3 text-right text-slate-300">{c.output_tokens}</td>
                    <td className="py-2.5 px-3 text-right text-slate-200 font-bold">{c.total_tokens}</td>
                    <td className="py-2.5 px-3 text-right text-emerald-400">${c.cost.toFixed(5)}</td>
                    <td className="py-2.5 px-3 text-right text-slate-400">{c.latency_ms}</td>
                  </tr>
                ))}
                <tr className="bg-sky-950/20 font-semibold border-t-2 border-sky-800">
                  <td className="py-2.5 px-3 text-sky-300">{result.synthesis.synthesis_model}</td>
                  <td className="py-2.5 px-3 text-sky-400">Synthesizer</td>
                  <td className="py-2.5 px-3 text-right text-slate-300">{result.synthesis.input_tokens}</td>
                  <td className="py-2.5 px-3 text-right text-slate-300">{result.synthesis.output_tokens}</td>
                  <td className="py-2.5 px-3 text-right text-sky-300 font-bold">{result.synthesis.total_tokens}</td>
                  <td className="py-2.5 px-3 text-right text-emerald-400">${result.synthesis.cost.toFixed(5)}</td>
                  <td className="py-2.5 px-3 text-right text-slate-300">{result.synthesis.latency_ms}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
