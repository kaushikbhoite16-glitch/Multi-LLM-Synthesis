import React from 'react';
import { AnalyticsData } from '../types';
import { ParetoChart } from '../components/ParetoChart';
import { apiService } from '../services/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import {
  Download,
  BarChart3,
  TrendingUp,
  FileSpreadsheet,
  FileJson,
  Layers,
  Award,
  Coins
} from 'lucide-react';

interface AnalyticsPageProps {
  analytics: AnalyticsData | null;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ analytics }) => {
  const perModelData = analytics?.per_model || [];

  const handleExport = (format: 'json' | 'csv') => {
    const url = apiService.getExportUrl(format);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-in fade-in duration-200">
      {/* Header and Export Tools */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Research Analytics & Statistical Distributions
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Empirical quality-cost trade-offs, Pareto frontier analysis, and reproducible dataset exports.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleExport('json')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
          >
            <FileJson className="w-3.5 h-3.5 text-sky-400" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Pareto Frontier Scatter Chart */}
      {analytics?.quality_vs_cost && (
        <ParetoChart data={analytics.quality_vs_cost} />
      )}

      {/* Model Quality & Cost Comparative Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Bar Chart */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Award className="w-4 h-4 text-sky-400" />
            <h4 className="font-semibold text-white text-xs sm:text-sm">Average Quality by Model (0-10)</h4>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={perModelData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="model" stroke="#64748b" fontSize={10} tickFormatter={(m) => m.split('/')[1] || m} />
                <YAxis domain={[7.0, 10.0]} stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '11px' }}
                />
                <Bar dataKey="avg_quality" fill="#38bdf8" radius={[6, 6, 0, 0]} name="Avg Quality" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost & Tokens Chart */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Coins className="w-4 h-4 text-emerald-400" />
            <h4 className="font-semibold text-white text-xs sm:text-sm">Average Latency (ms) by Model</h4>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={perModelData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="model" stroke="#64748b" fontSize={10} tickFormatter={(m) => m.split('/')[1] || m} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '11px' }}
                />
                <Bar dataKey="avg_latency_ms" fill="#a855f7" radius={[6, 6, 0, 0]} name="Latency (ms)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
