import React from 'react';
import { ModelConfig } from '../types';
import { Cpu, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

interface ModelSelectorProps {
  availableModels: ModelConfig[];
  selectedModels: string[];
  onToggleModel: (modelId: string) => void;
  evaluatorModel: string;
  setEvaluatorModel: (modelId: string) => void;
  synthesisModel: string;
  setSynthesisModel: (modelId: string) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  availableModels,
  selectedModels,
  onToggleModel,
  evaluatorModel,
  setEvaluatorModel,
  synthesisModel,
  setSynthesisModel,
}) => {
  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-white text-sm tracking-wide">Candidate Model Pool Selection</h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {selectedModels.length} models active for generation
        </span>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {availableModels.map((model) => {
          const isSelected = selectedModels.includes(model.id);
          return (
            <div
              key={model.id}
              onClick={() => onToggleModel(model.id)}
              className={`p-3.5 rounded-xl border cursor-pointer transition relative flex flex-col justify-between ${
                isSelected
                  ? 'bg-sky-500/10 border-sky-500/40 shadow-sm'
                  : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-bold text-white block">{model.name}</span>
                  <span className="text-[11px] text-slate-400 font-mono">{model.provider}</span>
                </div>
                <div className={`w-4 h-4 rounded flex items-center justify-center border ${
                  isSelected ? 'bg-sky-500 border-sky-400 text-white' : 'border-slate-700 bg-slate-900'
                }`}>
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <span>In: ${model.cost_per_1k_input * 1000}/M</span>
                <span>Out: ${model.cost_per_1k_output * 1000}/M</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Evaluator and Synthesis Model Dropdowns */}
      <div className="border-t border-slate-800 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-950/40 p-3 rounded-xl border border-slate-800">
          <label className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300 mb-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Semantic Evaluator Model</span>
          </label>
          <select
            value={evaluatorModel}
            onChange={(e) => setEvaluatorModel(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
          >
            {availableModels.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.provider})
              </option>
            ))}
          </select>
          <p className="text-[10px] text-slate-400 mt-1">Performs impartial multi-criteria scoring and contradiction analysis.</p>
        </div>

        <div className="bg-slate-950/40 p-3 rounded-xl border border-slate-800">
          <label className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300 mb-1.5">
            <Zap className="w-4 h-4 text-amber-400" />
            <span>Master Synthesis Model</span>
          </label>
          <select
            value={synthesisModel}
            onChange={(e) => setSynthesisModel(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
          >
            {availableModels.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.provider})
              </option>
            ))}
          </select>
          <p className="text-[10px] text-slate-400 mt-1">Ingests structured evaluated context and resolves conflicts into master answer.</p>
        </div>
      </div>
    </div>
  );
};
