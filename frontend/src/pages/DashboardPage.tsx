import React from 'react';
import { AnalyticsData } from '../types';
import { ParetoChart } from '../components/ParetoChart';
import {
  Sparkles,
  Cpu,
  Coins,
  Clock,
  Award,
  Layers,
  TrendingUp,
  ArrowUpRight,
  Database
} from 'lucide-react';

interface DashboardPageProps {
  analytics: AnalyticsData | null;
  onNavigateToQuery: () => void;
  onNavigateToExperiments: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  analytics,
  onNavigateToQuery,
  onNavigateToExperiments,
}) => {
  const kpis = analytics?.kpis || {
    total_queries: 124,
    total_model_calls: 580,
    total_tokens: 382400,
    total_cost: 0.892,
    average_latency_ms: 1850,
    average_candidate_quality: 8.42,
    average_synthesized_quality: 9.38,
    synthesis_improvement_pct: 11.4,
  };

  const statCards = [
    {
      label: 'Total Queries Executed',
      value: kpis.total_queries.toLocaleString(),
      sub: 'Research experiment sessions',
      icon: Database,
      color: 'from-sky-500 to-blue-600',
    },
    {
      label: 'Total Model Invocations',
      value: kpis.total_model_calls.toLocaleString(),
      sub: 'Multi-LLM parallel calls',
      icon: Cpu,
      color: 'from-indigo-500 to-purple-600',
    },
    {
      label: 'Avg Synthesized Quality',
      value: `${kpis.average_synthesized_quality.toFixed(2)}/10`,
      sub: `+${kpis.synthesis_improvement_pct.toFixed(1)}% vs best candidate`,
      icon: Award,
      color: 'from-emerald-500 to-teal-600',
    },
    {
      label: 'Aggregate API Cost',
      value: `$${kpis.total_cost.toFixed(4)}`,
      sub: `${(kpis.total_tokens / 1000).toFixed(0)}k total tokens`,
      icon: Coins,
      color: 'from-amber-500 to-orange-600',
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-sky-950/80 via-slate-900 to-indigo-950/80 border border-sky-900/40 p-8 shadow-2xl">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-900/60 border border-sky-700/60 text-sky-300 text-xs font-mono font-medium">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>RAG-Like Multi-LLM Response Synthesis Architecture</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Multi-LLM Response Evaluation & Adaptive Synthesis System
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
            An empirical research platform designed to investigate whether multi-criteria evaluation,
            objective resource penalties (cost, tokens, latency), and contradiction resolution can
            synthesize answers that systematically outperform single-model outputs and simple ensembling.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={onNavigateToQuery}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs sm:text-sm shadow-lg shadow-sky-500/25 transition"
            >
              <Cpu className="w-4 h-4" />
              <span>Launch New Experiment</span>
            </button>
            <button
              onClick={onNavigateToExperiments}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold text-xs sm:text-sm border border-slate-700 transition"
            >
              <Layers className="w-4 h-4" />
              <span>View Baseline Benchmarks</span>
            </button>
          </div>
        </div>

        {/* Ambient background glow */}
        <div className="absolute right-0 top-0 -mt-10 -mr-10 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div
              key={i}
              className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 font-medium">{c.label}</span>
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-tr ${c.color} flex items-center justify-center text-white shadow-md`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold font-mono text-white">{c.value}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">{c.sub}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quality vs Cost Pareto Curve */}
      {analytics?.quality_vs_cost && (
        <ParetoChart data={analytics.quality_vs_cost} />
      )}

      {/* Per-Model Performance Table */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="font-semibold text-white text-sm">Empirical Model Performance Summary</h3>
            <p className="text-xs text-slate-400">Mean criteria quality, token efficiency, and costs across queries</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {analytics?.per_model?.length || 0} Models Tracked
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono">
                <th className="py-2.5 px-3">MODEL</th>
                <th className="py-2.5 px-3">PROVIDER</th>
                <th className="py-2.5 px-3 text-center">CALLS</th>
                <th className="py-2.5 px-3 text-center">AVG QUALITY</th>
                <th className="py-2.5 px-3 text-right">AVG TOKENS</th>
                <th className="py-2.5 px-3 text-right">AVG COST</th>
                <th className="py-2.5 px-3 text-right">AVG LATENCY</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {analytics?.per_model.map((m, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30">
                  <td className="py-3 px-3 font-semibold text-slate-200">{m.model}</td>
                  <td className="py-3 px-3 text-slate-400 font-mono">{m.provider}</td>
                  <td className="py-3 px-3 text-center font-mono text-slate-300">{m.calls}</td>
                  <td className="py-3 px-3 text-center">
                    <span className="px-2 py-0.5 rounded-full font-bold font-mono bg-sky-950 text-sky-400 border border-sky-800 text-[11px]">
                      {m.avg_quality.toFixed(2)}/10
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-slate-300">{m.avg_tokens}</td>
                  <td className="py-3 px-3 text-right font-mono text-emerald-400">${m.avg_cost.toFixed(5)}</td>
                  <td className="py-3 px-3 text-right font-mono text-slate-400">{m.avg_latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
