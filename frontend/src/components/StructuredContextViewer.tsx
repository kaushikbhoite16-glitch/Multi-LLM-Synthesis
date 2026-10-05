import React, { useState } from 'react';
import { Copy, Check, FileCode, Info } from 'lucide-react';

interface StructuredContextViewerProps {
  context: string;
}

export const StructuredContextViewer: React.FC<StructuredContextViewerProps> = ({ context }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(context);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <FileCode className="w-5 h-5 text-sky-400" />
          <div>
            <h4 className="font-semibold text-white text-xs sm:text-sm">Structured Synthesis Context</h4>
            <p className="text-[11px] text-slate-400">Context payload supplied to the master synthesizer LLM</p>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs transition"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied Context</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-400" />
              <span>Copy Raw Context</span>
            </>
          )}
        </button>
      </div>

      <div className="flex items-start space-x-2 bg-sky-950/30 border border-sky-900/50 p-3 rounded-xl text-sky-300 text-xs leading-relaxed">
        <Info className="w-4 h-4 shrink-0 mt-0.5" />
        <p>
          <strong>Viva & Research Demonstration Note:</strong> This structured context is constructed dynamically from
          evaluated candidate outputs, agreement analysis, and contradiction resolution. Unlike simple RAG which retrieves documents,
          this RAG-like response synthesis architecture operates directly over evaluated model perspectives.
        </p>
      </div>

      <div className="relative">
        <pre className="bg-slate-950 p-5 rounded-xl border border-slate-800/90 font-mono text-[11px] text-slate-300 leading-relaxed overflow-x-auto max-h-[600px] overflow-y-auto whitespace-pre-wrap select-all">
          {context}
        </pre>
      </div>
    </div>
  );
};
