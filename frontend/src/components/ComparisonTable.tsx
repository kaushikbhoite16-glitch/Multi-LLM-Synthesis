import React, { useState } from 'react';
import { RankedResponse, EvaluationResult } from '../types';
import { Award, ChevronRight, X, ExternalLink, BarChart2 } from 'lucide-react';

interface ComparisonTableProps {
  ranking: RankedResponse[];
  evaluations: EvaluationResult[];
  synthesisScore?: number;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ ranking, evaluations }) => {
  const [selectedResponse, setSelectedResponse] = useState<RankedResponse | null>(null);

  const evalMap = new Map(evaluations.map(e => [e.response_id, e]));

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/70 text-slate-400 font-mono">
              <th className="py-3 px-4">RANK</th>
              <th className="py-3 px-4">MODEL / PROVIDER</th>
              <th className="py-3 px-4 text-center">OVERALL SCORE</th>
              <th className="py-3 px-4 text-center">RELEVANCE</th>
              <th className="py-3 px-4 text-center">CORRECTNESS</th>
              <th className="py-3 px-4 text-center">CLARITY</th>
              <th className="py-3 px-4 text-right">TOKENS</th>
              <th className="py-3 px-4 text-right">API COST</th>
              <th className="py-3 px-4 text-right">LATENCY</th>
              <th className="py-3 px-4 text-center">INSPECT</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {ranking.map((row) => {
              const ev = evalMap.get(row.response_id);
              const isFirst = row.rank === 1;

              return (
                <tr
                  key={row.response_id}
                  onClick={() => setSelectedResponse(row)}
                  className={`hover:bg-slate-800/40 cursor-pointer transition ${
                    isFirst ? 'bg-sky-500/5' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-mono font-bold">
                    <div className="flex items-center space-x-1.5">
                      {isFirst && <Award className="w-4 h-4 text-amber-400" />}
                      <span className={isFirst ? 'text-amber-400' : 'text-slate-400'}>
                        #{row.rank}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-semibold text-slate-200 block">{row.model}</span>
                    <span className="text-[11px] text-slate-400 font-mono">{row.provider}</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="inline-block px-2.5 py-1 rounded-full font-bold font-mono text-xs bg-sky-950 text-sky-300 border border-sky-800">
                      {row.overall_score.toFixed(2)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-mono text-slate-300">
                    {row.criteria_scores['relevance']?.toFixed(1) || '-'}
                  </td>
                  <td className="py-3 px-4 text-center font-mono text-slate-300">
                    {row.criteria_scores['correctness']?.toFixed(1) || '-'}
                  </td>
                  <td className="py-3 px-4 text-center font-mono text-slate-300">
                    {row.criteria_scores['clarity']?.toFixed(1) || '-'}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">
                    {row.tokens.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-emerald-400 font-medium">
                    ${row.cost.toFixed(5)}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-slate-400">
                    {row.latency_ms} ms
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button className="text-sky-400 hover:text-sky-300 p-1">
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Detail Inspection Modal */}
      {selectedResponse && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                    Rank #{selectedResponse.rank}
                  </span>
                  <h3 className="font-semibold text-white text-sm">{selectedResponse.model}</h3>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">Provider: {selectedResponse.provider}</p>
              </div>
              <button
                onClick={() => setSelectedResponse(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-5 text-xs">
              {/* Score & Resource Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Composite Score</span>
                  <span className="text-base font-bold text-sky-400 font-mono">
                    {selectedResponse.overall_score.toFixed(2)}/10
                  </span>
                </div>
                <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Total Tokens</span>
                  <span className="text-base font-bold text-slate-200 font-mono">
                    {selectedResponse.tokens}
                  </span>
                </div>
                <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">API Cost</span>
                  <span className="text-base font-bold text-emerald-400 font-mono">
                    ${selectedResponse.cost.toFixed(5)}
                  </span>
                </div>
                <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Latency</span>
                  <span className="text-base font-bold text-slate-300 font-mono">
                    {selectedResponse.latency_ms} ms
                  </span>
                </div>
              </div>

              {/* Multi-Criteria Breakdown */}
              <div>
                <h4 className="font-semibold text-slate-200 mb-2 flex items-center space-x-1.5">
                  <BarChart2 className="w-4 h-4 text-sky-400" />
                  <span>Semantic Criteria Scores</span>
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.entries(selectedResponse.criteria_scores).map(([k, v]) => (
                    <div key={k} className="bg-slate-950/40 p-2 rounded-lg border border-slate-800/80 flex justify-between items-center font-mono">
                      <span className="capitalize text-slate-400 text-[11px]">{k.replace('_', ' ')}</span>
                      <span className="font-bold text-slate-200">{v.toFixed(1)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Evaluator Reasoning */}
              <div className="bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
                <span className="font-semibold text-slate-300 block mb-1">Evaluator Reasoning:</span>
                <p className="text-slate-400 leading-relaxed">{selectedResponse.reasoning}</p>
              </div>

              {/* Full Output */}
              <div>
                <span className="font-semibold text-slate-300 block mb-1.5">Full Model Response:</span>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] leading-relaxed whitespace-pre-wrap text-slate-300 max-h-72 overflow-y-auto">
                  {selectedResponse.response_text}
                </div>
              </div>
            </div>

            <div className="p-3 border-t border-slate-800 bg-slate-950/60 flex justify-end">
              <button
                onClick={() => setSelectedResponse(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
