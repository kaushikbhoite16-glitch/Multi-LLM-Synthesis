import React from 'react';
import { UserPreferences } from '../types';
import { Sliders, RotateCcw, Sparkles, DollarSign, Clock, Hash } from 'lucide-react';

interface PreferenceControlsProps {
  preferences: UserPreferences;
  onChange: (updated: UserPreferences) => void;
}

export const PreferenceControls: React.FC<PreferenceControlsProps> = ({ preferences, onChange }) => {
  const criteria = [
    { key: 'relevance_weight', label: 'Relevance', desc: 'Directly addresses prompt' },
    { key: 'correctness_weight', label: 'Correctness', desc: 'Technical & factual accuracy' },
    { key: 'completeness_weight', label: 'Completeness', desc: 'Sufficient coverage of nuances' },
    { key: 'clarity_weight', label: 'Clarity', desc: 'Structure, readability, flow' },
    { key: 'consistency_weight', label: 'Consistency', desc: 'Absence of self-contradiction' },
    { key: 'preference_match_weight', label: 'Preference Match', desc: 'Tone and style alignment' },
    { key: 'conciseness_weight', label: 'Conciseness', desc: 'Avoids fluff & bloat' },
    { key: 'technical_depth_weight', label: 'Technical Depth', desc: 'Rigorous architectural depth' },
  ];

  const presets: Record<string, Partial<UserPreferences>> = {
    'Balanced': {
      relevance_weight: 0.25,
      correctness_weight: 0.25,
      completeness_weight: 0.15,
      clarity_weight: 0.15,
      consistency_weight: 0.05,
      preference_match_weight: 0.10,
      conciseness_weight: 0.05,
      technical_depth_weight: 0.0,
      scoring_mode: 'balanced'
    },
    'Coding & Architecture': {
      relevance_weight: 0.20,
      correctness_weight: 0.35,
      completeness_weight: 0.15,
      clarity_weight: 0.15,
      consistency_weight: 0.05,
      preference_match_weight: 0.05,
      conciseness_weight: 0.0,
      technical_depth_weight: 0.05,
      scoring_mode: 'quality-first'
    },
    'Educational & Beginner': {
      relevance_weight: 0.20,
      correctness_weight: 0.25,
      completeness_weight: 0.15,
      clarity_weight: 0.30,
      consistency_weight: 0.05,
      preference_match_weight: 0.05,
      conciseness_weight: 0.0,
      technical_depth_weight: 0.0,
      scoring_mode: 'quality-first'
    },
    'Cost-Sensitive': {
      relevance_weight: 0.25,
      correctness_weight: 0.25,
      completeness_weight: 0.15,
      clarity_weight: 0.15,
      consistency_weight: 0.05,
      preference_match_weight: 0.10,
      conciseness_weight: 0.05,
      technical_depth_weight: 0.0,
      cost_weight: 0.20,
      latency_weight: 0.05,
      token_weight: 0.05,
      scoring_mode: 'cost-aware'
    }
  };

  const handleSliderChange = (key: keyof UserPreferences, value: number) => {
    onChange({
      ...preferences,
      [key]: value,
    });
  };

  const normalizeWeights = () => {
    const keys = criteria.map(c => c.key as keyof UserPreferences);
    const sum = keys.reduce((acc, k) => acc + (preferences[k] as number), 0);
    if (sum === 0) return;

    const normalized = { ...preferences };
    keys.forEach(k => {
      (normalized[k] as number) = Number(((preferences[k] as number) / sum).toFixed(3));
    });
    onChange(normalized);
  };

  const applyPreset = (presetName: string) => {
    onChange({
      ...preferences,
      ...presets[presetName]
    });
  };

  // Calculate current sum of quality weights
  const currentTotal = criteria.reduce(
    (acc, c) => acc + (preferences[c.key as keyof UserPreferences] as number),
    0
  );
  const totalPct = Math.round(currentTotal * 100);

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-sky-400" />
          <h3 className="font-semibold text-white text-sm tracking-wide">Multi-Criteria Evaluation Preferences</h3>
          <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${
            totalPct === 100 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
          }`}>
            Total Weight: {totalPct}%
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={normalizeWeights}
            className="flex items-center space-x-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            <RotateCcw className="w-3 h-3 text-sky-400" />
            <span>Normalize Weights (100%)</span>
          </button>
        </div>
      </div>

      {/* Preset Pills */}
      <div>
        <label className="text-xs text-slate-400 block mb-2 font-medium">Domain Presets:</label>
        <div className="flex flex-wrap gap-2">
          {Object.keys(presets).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-sky-950/60 hover:text-sky-300 hover:border-sky-700 border border-slate-700 text-slate-300 transition flex items-center space-x-1.5"
            >
              <Sparkles className="w-3 h-3 text-sky-400" />
              <span>{p}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Quality Weights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {criteria.map((c) => {
          const val = preferences[c.key as keyof UserPreferences] as number;
          const pct = Math.round(val * 100);
          return (
            <div key={c.key} className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
              <div className="flex justify-between items-center mb-1">
                <div>
                  <span className="text-xs font-semibold text-slate-200">{c.label}</span>
                  <p className="text-[11px] text-slate-400">{c.desc}</p>
                </div>
                <span className="text-xs font-mono font-medium text-sky-400 bg-sky-950/50 px-2 py-0.5 rounded border border-sky-900/60">
                  {pct}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={val}
                onChange={(e) => handleSliderChange(c.key as keyof UserPreferences, parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500 mt-2"
              />
            </div>
          );
        })}
      </div>

      {/* Scoring Mode & Objective Constraints */}
      <div className="border-t border-slate-800 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-semibold text-slate-300 block mb-2">Scoring Mode & Trade-offs</label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { id: 'quality-first', label: 'Quality First', desc: 'Zero cost penalty' },
              { id: 'balanced', label: 'Balanced', desc: 'Quality + minor resource check' },
              { id: 'cost-aware', label: 'Cost-Aware', desc: 'Penalizes high API expense' },
              { id: 'user-customized', label: 'Customized', desc: 'User-specified penalties' },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => onChange({ ...preferences, scoring_mode: m.id as any })}
                className={`p-2.5 rounded-xl border text-left text-xs transition ${
                  preferences.scoring_mode === m.id
                    ? 'bg-sky-500/10 border-sky-500/50 text-white font-medium'
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="font-semibold text-slate-200">{m.label}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-300 block mb-2">Resource Bounds</label>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs bg-slate-950/40 p-2 rounded-lg border border-slate-800">
              <span className="flex items-center space-x-1.5 text-slate-400">
                <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                <span>Max Cost / Query</span>
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="2.00"
                value={preferences.max_cost}
                onChange={(e) => onChange({ ...preferences, max_cost: parseFloat(e.target.value) || 0.1 })}
                className="w-20 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-right font-mono text-xs text-white"
              />
            </div>

            <div className="flex items-center justify-between text-xs bg-slate-950/40 p-2 rounded-lg border border-slate-800">
              <span className="flex items-center space-x-1.5 text-slate-400">
                <Hash className="w-3.5 h-3.5 text-indigo-400" />
                <span>Target Max Output Tokens</span>
              </span>
              <input
                type="number"
                step="200"
                min="200"
                max="8000"
                value={preferences.max_tokens}
                onChange={(e) => onChange({ ...preferences, max_tokens: parseInt(e.target.value, 10) || 2000 })}
                className="w-24 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-right font-mono text-xs text-white"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
