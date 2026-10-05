import React, { useState } from 'react';
import { ModelConfig } from '../types';
import { apiService } from '../services/api';
import { Settings2, Plus, Check, ShieldCheck, Zap, Cpu } from 'lucide-react';

interface ModelConfigPageProps {
  models: ModelConfig[];
  onModelsUpdated: () => void;
}

export const ModelConfigPage: React.FC<ModelConfigPageProps> = ({ models, onModelsUpdated }) => {
  const [modelList, setModelList] = useState<ModelConfig[]>(models);
  const [newModel, setNewModel] = useState<Partial<ModelConfig>>({
    id: '',
    name: '',
    provider: 'OpenRouter',
    role: 'candidate',
    enabled: true,
    max_tokens: 1500,
    temperature: 0.7,
    cost_per_1k_input: 0.0002,
    cost_per_1k_output: 0.0008,
  });
  const [saving, setSaving] = useState(false);

  const handleToggle = async (m: ModelConfig) => {
    const updated = { ...m, enabled: !m.enabled };
    await apiService.updateModel(updated);
    setModelList(modelList.map(item => item.id === m.id ? updated : item));
    onModelsUpdated();
  };

  const handleRoleChange = async (m: ModelConfig, role: 'candidate' | 'evaluator' | 'synthesizer') => {
    const updated = { ...m, role };
    await apiService.updateModel(updated);
    setModelList(modelList.map(item => item.id === m.id ? updated : item));
    onModelsUpdated();
  };

  const handleAddModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newModel.id || !newModel.name) return;
    setSaving(true);
    try {
      await apiService.updateModel(newModel as ModelConfig);
      setModelList([...modelList, newModel as ModelConfig]);
      setNewModel({
        id: '',
        name: '',
        provider: 'OpenRouter',
        role: 'candidate',
        enabled: true,
        max_tokens: 1500,
        temperature: 0.7,
        cost_per_1k_input: 0.0002,
        cost_per_1k_output: 0.0008,
      });
      onModelsUpdated();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-in fade-in duration-200">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
          Model Pool & Architecture Configuration
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Configure available candidate models, roles, token budgets, and pricing parameters.
        </p>
      </div>

      {/* Models List */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="font-semibold text-white text-sm">Active Model Pool ({modelList.length})</h3>
        <div className="space-y-3">
          {modelList.map((m) => (
            <div
              key={m.id}
              className={`p-4 rounded-xl border flex flex-wrap items-center justify-between gap-4 transition ${
                m.enabled ? 'bg-slate-950/60 border-slate-800' : 'bg-slate-950/20 border-slate-900 opacity-50'
              }`}
            >
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-white text-sm">{m.name}</span>
                  <span className="text-[11px] font-mono text-slate-400">({m.id})</span>
                </div>
                <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1 font-mono">
                  <span>Provider: {m.provider}</span>
                  <span>•</span>
                  <span>Max Tokens: {m.max_tokens}</span>
                  <span>•</span>
                  <span>Pricing: ${m.cost_per_1k_input * 1000}/M in, ${m.cost_per_1k_output * 1000}/M out</span>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <select
                  value={m.role}
                  onChange={(e) => handleRoleChange(m, e.target.value as any)}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 font-mono"
                >
                  <option value="candidate">Candidate</option>
                  <option value="evaluator">Evaluator</option>
                  <option value="synthesizer">Synthesizer</option>
                </select>

                <button
                  type="button"
                  onClick={() => handleToggle(m)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold border transition ${
                    m.enabled
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  {m.enabled ? 'Active' : 'Disabled'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add New Model Form */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="font-semibold text-white text-sm flex items-center space-x-1.5">
          <Plus className="w-4 h-4 text-sky-400" />
          <span>Add Custom Model to Pool</span>
        </h3>

        <form onSubmit={handleAddModel} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="text-slate-400 block mb-1">OpenRouter Model ID</label>
            <input
              type="text"
              required
              placeholder="e.g. mistralai/mistral-large"
              value={newModel.id}
              onChange={(e) => setNewModel({ ...newModel, id: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
            />
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Display Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Mistral Large"
              value={newModel.name}
              onChange={(e) => setNewModel({ ...newModel, name: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Provider</label>
            <input
              type="text"
              placeholder="e.g. Mistral"
              value={newModel.provider}
              onChange={(e) => setNewModel({ ...newModel, provider: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
            />
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Default Role</label>
            <select
              value={newModel.role}
              onChange={(e) => setNewModel({ ...newModel, role: e.target.value as any })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
            >
              <option value="candidate">Candidate</option>
              <option value="evaluator">Evaluator</option>
              <option value="synthesizer">Synthesizer</option>
            </select>
          </div>

          <div className="sm:col-span-2 lg:col-span-4 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold transition flex items-center space-x-1.5"
            >
              <Plus className="w-4 h-4" />
              <span>Add Model to System Pool</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
