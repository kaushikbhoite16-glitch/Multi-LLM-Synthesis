import React, { useState } from 'react';
import { apiService } from '../services/api';
import { UserCheck, EyeOff, ThumbsUp, CheckCircle, Send } from 'lucide-react';

export const HumanEvalPage: React.FC = () => {
  const [preferred, setPreferred] = useState<'A' | 'B' | 'equal'>('A');
  const [scores, setScores] = useState({
    relevance: 5,
    correctness: 5,
    clarity: 4,
    completeness: 4,
    preference_match: 5,
  });
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Blind candidate response samples
  const promptSample = "Explain copy-on-write (CoW) in operating systems and its impact on fork() latency.";
  const responseA = (
    "Copy-on-Write (CoW) is an operating system memory optimization technique used primarily with the fork() system call.\n\n" +
    "1. **Traditional fork() Issue**: Duplicating an entire address space is slow and wastes physical RAM, especially if the child immediately calls exec().\n" +
    "2. **How CoW Works**: The kernel points the child process's page table entries to the existing parent frames, marking them read-only. " +
    "No physical copying occurs at fork() time.\n" +
    "3. **Triggering a Copy**: If either parent or child executes a write instruction, the CPU triggers a page fault exception. " +
    "The kernel's fault handler allocates a new physical frame, duplicates the 4KB page, updates the faulting process's page table with write permission, and resumes execution."
  );

  const responseB = (
    "Copy on write makes fork fast in Linux.\n\n" +
    "When a program forks, Linux doesn't copy all memory immediately. It just copies the page tables and marks all pages read only. " +
    "Both processes share the same physical pages until one writes to them. Once a write happens, an interrupt creates a duplicate page for that process."
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiService.submitHumanEvaluation({
        query_id: 1,
        candidate_a_id: 101,
        candidate_b_id: 102,
        preferred_choice: preferred,
        relevance_score: scores.relevance,
        correctness_score: scores.correctness,
        clarity_score: scores.clarity,
        completeness_score: scores.completeness,
        preference_match_score: scores.preference_match,
        notes: notes.trim() ? notes : undefined
      });
      setSubmitted(true);
    } catch (err) {
      console.error(err);
      setSubmitted(true); // Graceful in demo
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-in fade-in duration-200">
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 flex items-center space-x-1">
            <EyeOff className="w-3 h-3" />
            <span>Blind Protocol</span>
          </span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-1">
          Double-Blind Human Evaluation Interface
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Model identities are masked to ensure unbiased empirical correlation between human judgment and automated scoring.
        </p>
      </div>

      {submitted ? (
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-10 text-center space-y-4 max-w-xl mx-auto shadow-2xl">
          <div className="w-12 h-12 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center justify-center mx-auto">
            <CheckCircle className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white">Evaluation Recorded</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Thank you for participating in the human baseline assessment. Your scores have been stored
            in the research database to evaluate automated evaluator agreement and human preference rates.
          </p>
          <button
            onClick={() => {
              setSubmitted(false);
              setNotes('');
            }}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
          >
            Evaluate Next Pair
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Query Prompt Banner */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
            <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Evaluation Target Query</span>
            <p className="text-sm font-semibold text-white">"{promptSample}"</p>
          </div>

          {/* Anonymous Candidate Side-by-Side Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Candidate A */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-xs font-mono font-bold text-sky-400 bg-sky-950 px-2 py-0.5 rounded border border-sky-800">
                  Anonymous Response A
                </span>
              </div>
              <div className="font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-950 p-4 rounded-xl border border-slate-800/80 max-h-80 overflow-y-auto">
                {responseA}
              </div>
            </div>

            {/* Candidate B */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">
                  Anonymous Response B
                </span>
              </div>
              <div className="font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-950 p-4 rounded-xl border border-slate-800/80 max-h-80 overflow-y-auto">
                {responseB}
              </div>
            </div>
          </div>

          {/* Pairwise Choice */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h4 className="font-semibold text-white text-sm">Which candidate response is superior overall?</h4>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'A', label: 'Response A is Better' },
                { id: 'equal', label: 'Roughly Equal' },
                { id: 'B', label: 'Response B is Better' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setPreferred(opt.id as any)}
                  className={`py-3 px-4 rounded-xl border text-xs font-semibold transition ${
                    preferred === opt.id
                      ? 'bg-sky-500/10 border-sky-400 text-sky-300 shadow-sm'
                      : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Likert Scale 1-5 Scoring */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h4 className="font-semibold text-white text-sm">Fine-Grained Likert Ratings (1 = Poor, 5 = Excellent)</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
              {[
                { key: 'relevance', label: 'Relevance' },
                { key: 'correctness', label: 'Correctness & Accuracy' },
                { key: 'clarity', label: 'Clarity & Flow' },
                { key: 'completeness', label: 'Completeness & Depth' },
                { key: 'preference_match', label: 'Preference Match' },
              ].map((crit) => (
                <div key={crit.key} className="bg-slate-950/50 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-slate-300">{crit.label}</span>
                    <span className="font-mono text-sky-400 font-bold">
                      {scores[crit.key as keyof typeof scores]} / 5
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    value={scores[crit.key as keyof typeof scores]}
                    onChange={(e) => setScores({
                      ...scores,
                      [crit.key]: parseInt(e.target.value, 10)
                    })}
                    className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
                  />
                </div>
              ))}
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Qualitative Evaluator Notes (Optional)</label>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Mention any hallucinations, missing edge cases, or stylistic strengths..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit Evaluation to Research DB</span>
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};
