import React from 'react';
import { ConflictAnalysis } from '../types';
import { CheckCircle, AlertTriangle, HelpCircle, Layers, Split } from 'lucide-react';

interface ConflictViewerProps {
  conflicts: ConflictAnalysis;
}

export const ConflictViewer: React.FC<ConflictViewerProps> = ({ conflicts }) => {
  return (
    <div className="space-y-6">
      {/* Consensus Summary Banner */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <Split className="w-5 h-5 text-indigo-400" />
          <div>
            <h4 className="font-semibold text-white text-xs sm:text-sm">Consensus & Conflict Analysis</h4>
            <p className="text-[11px] text-slate-400">Cross-validation of claims across candidate responses</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-mono">Consensus Level:</span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-bold uppercase ${
            conflicts.consensus_level === 'high'
              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
              : conflicts.consensus_level === 'medium'
              ? 'bg-amber-950 text-amber-300 border border-amber-800'
              : 'bg-rose-950 text-rose-300 border border-rose-800'
          }`}>
            {conflicts.consensus_level}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Shared Claims (Consensus) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <h5 className="font-semibold text-white text-xs uppercase tracking-wider">
              Shared Information ({conflicts.shared_information.length})
            </h5>
          </div>
          <ul className="space-y-2.5">
            {conflicts.shared_information.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-xs text-slate-300 bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Contradictions & Disagreements */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h5 className="font-semibold text-white text-xs uppercase tracking-wider">
              Detected Contradictions ({conflicts.contradictions.length})
            </h5>
          </div>

          {conflicts.contradictions.length === 0 ? (
            <div className="p-6 text-center text-slate-400 text-xs bg-slate-950/30 rounded-xl border border-slate-800/60">
              No factual contradictions or direct conflicts detected among candidate outputs.
            </div>
          ) : (
            <div className="space-y-3">
              {conflicts.contradictions.map((c, idx) => (
                <div key={idx} className="bg-slate-950/50 p-3.5 rounded-xl border border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">Discrepancy #{idx + 1}</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                      c.severity === 'high' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'
                    }`}>
                      {c.severity} Severity
                    </span>
                  </div>
                  <p className="text-slate-400 leading-relaxed">{c.description}</p>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                    <div className="bg-slate-900/90 p-2 rounded border border-slate-800 text-slate-300">
                      <span className="text-[10px] text-sky-400 block font-semibold">{c.model_a}:</span>
                      "{c.claim_a}"
                    </div>
                    <div className="bg-slate-900/90 p-2 rounded border border-slate-800 text-slate-300">
                      <span className="text-[10px] text-indigo-400 block font-semibold">{c.model_b}:</span>
                      "{c.claim_b}"
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Unique Model Contributions */}
      {Object.keys(conflicts.unique_information).length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Layers className="w-4 h-4 text-sky-400" />
            <h5 className="font-semibold text-white text-xs uppercase tracking-wider">
              Distinct Perspectives & Unique Information
            </h5>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(conflicts.unique_information).map(([model, items]) => (
              <div key={model} className="bg-slate-950/40 p-3 rounded-xl border border-slate-800 space-y-1.5 text-xs">
                <span className="font-mono font-semibold text-sky-400 text-[11px] block truncate">{model}</span>
                {items.map((it, i) => (
                  <p key={i} className="text-slate-400 text-[11px] leading-relaxed">
                    • {it}
                  </p>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
