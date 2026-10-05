import React from 'react';
import { Sliders, Scale, Info, ShieldCheck, FileCheck } from 'lucide-react';

export const EvaluationConfigPage: React.FC = () => {
  const criteriaList = [
    {
      name: 'Relevance',
      range: '0.0 - 10.0',
      defaultWeight: '25%',
      desc: "Evaluates whether the candidate response addresses the user's specific prompt directly and comprehensively without straying into unrelated domains."
    },
    {
      name: 'Correctness',
      range: '0.0 - 10.0',
      defaultWeight: '25%',
      desc: 'Checks all technical claims, code logic, mathematical derivations, and historical facts for empirical and theoretical validity.'
    },
    {
      name: 'Completeness',
      range: '0.0 - 10.0',
      defaultWeight: '15%',
      desc: 'Assesses whether the response explores implied edge cases, structural components, and essential depth rather than superficial summaries.'
    },
    {
      name: 'Clarity & Structure',
      range: '0.0 - 10.0',
      defaultWeight: '15%',
      desc: 'Evaluates logical sequencing, heading hierarchy, formatting readability, and overall communicative flow.'
    },
    {
      name: 'Internal Consistency',
      range: '0.0 - 10.0',
      defaultWeight: '5%',
      desc: 'Ensures the candidate output is harmonious and does not contradict its own definitions, claims, or data within the same text.'
    },
    {
      name: 'Preference Match',
      range: '0.0 - 10.0',
      defaultWeight: '10%',
      desc: "Measures alignment with explicit user style preferences such as formality, technical depth, beginner-friendliness, or conciseness."
    },
    {
      name: 'Conciseness',
      range: '0.0 - 10.0',
      defaultWeight: '5%',
      desc: 'Measures signal-to-noise ratio and penalizes excessive filler, repetitive terminology, and gratuitous verbosity.'
    },
    {
      name: 'Technical Depth',
      range: '0.0 - 10.0',
      defaultWeight: 'Dynamic',
      desc: 'Verifies appropriate architectural, algorithmic, or mechanical rigor when evaluating complex engineering queries.'
    }
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-in fade-in duration-200">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
          Evaluation Framework & Scoring Specifications
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Detailed mathematical formulations and criteria definitions governing response evaluation.
        </p>
      </div>

      {/* Formula Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <h3 className="font-semibold text-white text-sm flex items-center space-x-2">
          <Scale className="w-4 h-4 text-sky-400" />
          <span>Multi-Criteria Composite Scoring Model</span>
        </h3>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-sky-300 space-y-2">
          <p className="text-slate-300">
            <strong>Quality Score:</strong> Q = &sum; (w<sub>i</sub> &times; C<sub>i</sub>) &nbsp;&nbsp;where &sum; w<sub>i</sub> = 1.0
          </p>
          <p className="text-slate-300">
            <strong>Resource Penalty:</strong> P = (w<sub>cost</sub> &times; Cost<sub>norm</sub> + w<sub>tok</sub> &times; Tok<sub>norm</sub> + w<sub>lat</sub> &times; Lat<sub>norm</sub>) &times; 10
          </p>
          <p className="text-emerald-400 font-bold">
            <strong>Composite Score:</strong> S = clamp(0.0, 10.0, (Q &times; &alpha;) - P + (1 - &alpha;) &times; 5.0)
          </p>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          Resource metrics are strictly min-max normalized across candidates within each query batch to prevent scale distortion:
          <span className="font-mono text-slate-300"> X<sub>norm</sub> = (X - min) / (max - min)</span>.
        </p>
      </div>

      {/* Criteria Breakdown Grid */}
      <div className="space-y-4">
        <h3 className="font-semibold text-white text-sm">Semantic Evaluation Dimensions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {criteriaList.map((c, i) => (
            <div key={i} className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">{c.name}</span>
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                  {c.defaultWeight}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{c.desc}</p>
              <div className="text-[11px] font-mono text-slate-400 pt-1">
                Scale: {c.range}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
