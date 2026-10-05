import React from 'react';
import { PipelineRunResponse } from '../types';
import { ComparisonTable } from '../components/ComparisonTable';
import { Scale, ArrowLeft } from 'lucide-react';

interface ResponseComparisonPageProps {
  result: PipelineRunResponse | null;
  onNavigateToQuery: () => void;
}

export const ResponseComparisonPage: React.FC<ResponseComparisonPageProps> = ({
  result,
  onNavigateToQuery,
}) => {
  if (!result) {
    return (
      <div className="text-center py-20 bg-slate-900/60 border border-slate-800 rounded-3xl p-8 max-w-xl mx-auto space-y-4">
        <Scale className="w-12 h-12 text-slate-500 mx-auto" />
        <h3 className="text-lg font-bold text-white">No Candidate Evaluation Loaded</h3>
        <p className="text-xs text-slate-400">
          Run a query experiment first to inspect and compare candidate responses side by side.
        </p>
        <button
          onClick={onNavigateToQuery}
          className="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition"
        >
          Go to Query Runner
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-in fade-in duration-200">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Candidate Response Evaluation Matrix</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Query: <span className="text-slate-200 font-semibold">"{result.query_text}"</span>
          </p>
        </div>

        <button
          onClick={onNavigateToQuery}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Query</span>
        </button>
      </div>

      <ComparisonTable
        ranking={result.ranking}
        evaluations={result.evaluations}
        synthesisScore={result.final_evaluation.overall_score}
      />
    </div>
  );
};
