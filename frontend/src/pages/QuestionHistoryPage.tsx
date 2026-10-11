import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { QuestionHistoryItem, PipelineRunResponse } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  History,
  Search,
  Trash2,
  Edit2,
  ExternalLink,
  Loader2,
  Calendar,
  Zap,
  Coins,
  Cpu,
  Check,
  X,
  AlertTriangle,
  FileQuestion,
  Lock
} from 'lucide-react';

interface QuestionHistoryPageProps {
  onSelectQuestion: (result: PipelineRunResponse) => void;
  onNavigateToQuery: () => void;
  onOpenAuth: () => void;
}

export const QuestionHistoryPage: React.FC<QuestionHistoryPageProps> = ({
  onSelectQuestion,
  onNavigateToQuery,
  onOpenAuth
}) => {
  const { user } = useAuth();
  const [items, setItems] = useState<QuestionHistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingDetailId, setLoadingDetailId] = useState<number | null>(null);

  // Rename state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Delete confirmation modal state
  const [deletingItem, setDeletingItem] = useState<QuestionHistoryItem | null>(null);

  useEffect(() => {
    if (user) {
      loadHistory();
    }
  }, [user]);

  const loadHistory = async (search?: string) => {
    setIsLoading(true);
    try {
      const data = await apiService.getHistory(search);
      setItems(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadHistory(searchTerm);
  };

  const handleStartRename = (item: QuestionHistoryItem) => {
    setEditingId(item.id);
    setEditTitle(item.title || item.query_text);
  };

  const handleSaveRename = async (id: number) => {
    if (!editTitle.trim()) return;
    try {
      await apiService.renameQuestion(id, editTitle.trim());
      setItems(prev => prev.map(item => item.id === id ? { ...item, title: editTitle.trim() } : item));
      setEditingId(null);
    } catch (err) {
      console.error('Failed to rename question:', err);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingItem) return;
    try {
      await apiService.deleteQuestion(deletingItem.id);
      setItems(prev => prev.filter(item => item.id !== deletingItem.id));
      setDeletingItem(null);
    } catch (err) {
      console.error('Failed to delete question:', err);
    }
  };

  const handleInspect = async (id: number) => {
    setLoadingDetailId(id);
    try {
      const detail = await apiService.getHistoryDetail(id);
      onSelectQuestion(detail);
    } catch (err) {
      console.error('Failed to retrieve history detail:', err);
    } finally {
      setLoadingDetailId(null);
    }
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center">
        <div className="w-16 h-16 bg-slate-900 border border-slate-800 text-sky-400 rounded-3xl flex items-center justify-center mx-auto mb-4 shadow-xl">
          <Lock className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Question History is Protected</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto mt-2 mb-6">
          Sign in or create an account to securely save questions, inspect synthesized outputs, track tokens, and maintain research history.
        </p>
        <button
          onClick={onOpenAuth}
          className="py-2.5 px-6 bg-sky-500 hover:bg-sky-400 text-white rounded-xl text-xs font-semibold shadow-md shadow-sky-500/25 transition-all"
        >
          Sign In / Create Account
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-200">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <History className="w-6 h-6 text-sky-400" />
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Research Question History
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Browse previous synthesized inquiries, inspect full evaluations without re-calling APIs, and manage saved queries.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search history..."
              className="bg-slate-900 border border-slate-800 rounded-xl py-2 pl-9 pr-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-48 sm:w-64"
            />
          </div>
          <button
            type="submit"
            className="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-xl transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* History Items List */}
      {isLoading ? (
        <div className="text-center py-16">
          <Loader2 className="w-8 h-8 text-sky-400 animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-400">Loading your inquiry history...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/50 border border-slate-800 rounded-3xl p-8">
          <FileQuestion className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-200">No Questions Saved Yet</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-5">
            Run a multi-LLM synthesis query in Live API or Simulation mode to automatically preserve your research runs.
          </p>
          <button
            onClick={onNavigateToQuery}
            className="py-2 px-4 bg-sky-500 hover:bg-sky-400 text-white rounded-xl text-xs font-medium transition-all"
          >
            Start a New Query
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-lg transition-all duration-150 flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-2 flex-1 min-w-0">
                {/* Title and Execution Mode */}
                <div className="flex items-center space-x-2.5">
                  {editingId === item.id ? (
                    <div className="flex items-center space-x-2 flex-1 max-w-md">
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="bg-slate-950 border border-sky-500 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none flex-1"
                        autoFocus
                      />
                      <button
                        onClick={() => handleSaveRename(item.id)}
                        className="p-1 text-emerald-400 hover:bg-emerald-500/10 rounded"
                        title="Save"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="p-1 text-slate-400 hover:bg-slate-800 rounded"
                        title="Cancel"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2 group">
                      <h4 className="text-sm font-bold text-white tracking-tight truncate max-w-md">
                        {item.title || item.query_text}
                      </h4>
                      <button
                        onClick={() => handleStartRename(item)}
                        className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-sky-400 transition-opacity p-0.5"
                        title="Rename Question"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Mode Badge */}
                  <span
                    className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${
                      item.execution_mode === 'simulation'
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    }`}
                  >
                    {item.execution_mode === 'simulation' ? 'SIMULATION' : 'LIVE API'}
                  </span>
                </div>

                {/* Query Text Snippet */}
                <p className="text-xs text-slate-300 line-clamp-2">
                  {item.query_text}
                </p>

                {/* Synthesis preview */}
                {item.synthesized_preview && (
                  <p className="text-[11px] text-slate-400 italic line-clamp-1 bg-slate-950/40 px-2 py-1 rounded border border-slate-800/60">
                    &ldquo;{item.synthesized_preview}&rdquo;
                  </p>
                )}

                {/* Meta Attributes */}
                <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400 pt-1">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                  </span>
                  <span>&bull;</span>
                  <span className="flex items-center space-x-1">
                    <Cpu className="w-3 h-3 text-indigo-400" />
                    <span>{item.candidate_count} models</span>
                  </span>
                  <span>&bull;</span>
                  <span className="flex items-center space-x-1">
                    <Zap className="w-3 h-3 text-sky-400" />
                    <span>{item.total_tokens.toLocaleString()} tokens</span>
                  </span>
                  <span>&bull;</span>
                  <span className="flex items-center space-x-1 text-emerald-400">
                    <Coins className="w-3 h-3" />
                    <span>
                      {item.execution_mode === 'simulation' ? '$0.00 (Sim)' : `$${item.total_cost.toFixed(6)}`}
                    </span>
                  </span>
                  {item.synthesized_score !== null && item.synthesized_score !== undefined && (
                    <>
                      <span>&bull;</span>
                      <span className="text-amber-400 font-semibold">
                        Score: {item.synthesized_score.toFixed(1)}/10
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2 shrink-0 self-end md:self-center">
                <button
                  onClick={() => handleInspect(item.id)}
                  disabled={loadingDetailId === item.id}
                  className="py-1.5 px-3 bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 text-sky-300 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors disabled:opacity-50"
                >
                  {loadingDetailId === item.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <ExternalLink className="w-3.5 h-3.5" />
                  )}
                  <span>View Saved Result</span>
                </button>

                <button
                  onClick={() => setDeletingItem(item)}
                  className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors"
                  title="Delete Question"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-sm w-full p-6 shadow-2xl space-y-4">
            <div className="w-12 h-12 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl flex items-center justify-center mx-auto">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="text-center">
              <h3 className="text-base font-bold text-white">Delete Question History?</h3>
              <p className="text-xs text-slate-400 mt-1">
                Are you sure you want to delete <span className="text-slate-200 font-medium">&ldquo;{deletingItem.title || deletingItem.query_text}&rdquo;</span>? This will permanently remove its candidate runs and synthesized response.
              </p>
            </div>
            <div className="flex items-center space-x-2 pt-2">
              <button
                onClick={() => setDeletingItem(null)}
                className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="flex-1 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-rose-600/20 transition-all"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
