import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { QuestionHistoryItem, PipelineRunResponse } from '../types';
import {
  History,
  Search,
  Calendar,
  Sparkles,
  ChevronRight,
  Trash2,
  Pencil,
  RotateCcw,
  AlertCircle,
  Coins,
  Cpu,
  Layers,
  Check,
  X,
  Plus
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
  const [historyItems, setHistoryItems] = useState<QuestionHistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Rename state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Delete state
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Inspector state
  const [fetchingDetailId, setFetchingDetailId] = useState<number | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async (search?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.getHistory(search);
      setHistoryItems(data);
    } catch (err: any) {
      if (err?.response?.status === 401) {
        setError('Please sign in to view your saved question history.');
      } else {
        setError(err?.response?.data?.detail || err.message || 'Failed to load question history.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadHistory(searchTerm);
  };

  const handleOpenDetail = async (id: number) => {
    setFetchingDetailId(id);
    try {
      const fullResult = await apiService.getHistoryDetail(id);
      onSelectQuestion(fullResult);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to open saved question details.');
    } finally {
      setFetchingDetailId(null);
    }
  };

  const handleStartRename = (e: React.MouseEvent, item: QuestionHistoryItem) => {
    e.stopPropagation();
    setEditingId(item.id);
    setEditTitle(item.title || item.query_text);
  };

  const handleSaveRename = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!editTitle.trim()) return;
    try {
      await apiService.renameQuestion(id, editTitle.trim());
      setHistoryItems((prev) =>
        prev.map((item) => (item.id === id ? { ...item, title: editTitle.trim() } : item))
      );
      setEditingId(null);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to rename question.');
    }
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this question and its saved evaluation runs?')) {
      return;
    }
    setDeletingId(id);
    try {
      await apiService.deleteQuestion(id);
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to delete question.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center space-x-2">
            <History className="w-6 h-6 text-sky-400" />
            <span>Question History</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Access previous research queries, synthesized conclusions, and model scoring results.
          </p>
        </div>

        <button
          onClick={onNavigateToQuery}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold text-xs shadow-md shadow-sky-500/20 transition-all shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Question</span>
        </button>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearchSubmit} className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search saved questions by prompt text or title..."
          className="w-full bg-slate-900 border border-slate-800 rounded-2xl py-2.5 pl-10 pr-24 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
        />
        <button
          type="submit"
          className="absolute right-2 top-2 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors"
        >
          Search
        </button>
      </form>

      {/* Error / Auth Required */}
      {error && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
          <p className="text-xs text-slate-300">{error}</p>
          <button
            onClick={onOpenAuth}
            className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white rounded-xl text-xs font-semibold transition"
          >
            Sign In to Account
          </button>
        </div>
      )}

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-2xl bg-slate-900/60 border border-slate-800/60 animate-pulse" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && historyItems.length === 0 && (
        <div className="text-center py-16 px-4 rounded-3xl bg-slate-900/40 border border-slate-800/60 space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-500 flex items-center justify-center mx-auto">
            <History className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-300">No Questions Saved Yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Your analyzed questions, multi-model outputs, and synthesis runs will be saved here automatically.
          </p>
          <button
            onClick={onNavigateToQuery}
            className="mt-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition"
          >
            Run Your First Query
          </button>
        </div>
      )}

      {/* History Items List */}
      {!isLoading && !error && historyItems.length > 0 && (
        <div className="space-y-3">
          {historyItems.map((item) => (
            <div
              key={item.id}
              onClick={() => handleOpenDetail(item.id)}
              className="p-5 rounded-2xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-all group relative"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                      #{item.id}
                    </span>
                    <span
                      className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${
                        item.execution_mode === 'simulation'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      }`}
                    >
                      {item.execution_mode.toUpperCase()}
                    </span>
                    {item.domain && (
                      <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
                        {item.domain}
                      </span>
                    )}
                  </div>

                  {/* Title or Inline Edit */}
                  {editingId === item.id ? (
                    <div className="flex items-center space-x-2 my-1" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="bg-slate-950 border border-sky-500 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none flex-1"
                        autoFocus
                      />
                      <button
                        onClick={(e) => handleSaveRename(e, item.id)}
                        className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={handleCancelRename}
                        className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <h3 className="text-sm font-semibold text-slate-100 group-hover:text-sky-300 transition-colors truncate">
                      {item.title || item.query_text}
                    </h3>
                  )}

                  {item.synthesized_preview && (
                    <p className="text-xs text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                      {item.synthesized_preview}
                    </p>
                  )}

                  {/* Metadata Chips */}
                  <div className="flex items-center space-x-4 mt-3 text-[11px] font-mono text-slate-400">
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3 h-3" />
                      <span>{item.created_at.split(' ')[0]}</span>
                    </span>
                    <span>Tokens: {item.total_tokens.toLocaleString()}</span>
                    <span>
                      Cost: {item.execution_mode === 'simulation' ? '$0.00' : `$${item.total_cost.toFixed(5)}`}
                    </span>
                    {item.synthesized_score && (
                      <span className="text-sky-400 font-semibold">
                        Score: {item.synthesized_score.toFixed(1)}/10
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions Row */}
                <div className="flex items-center space-x-1 shrink-0">
                  <button
                    onClick={(e) => handleStartRename(e, item)}
                    className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                    title="Rename Question"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, item.id)}
                    disabled={deletingId === item.id}
                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                    title="Delete Question"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <div className="p-1.5 text-slate-500 group-hover:text-sky-400 group-hover:translate-x-0.5 transition-all">
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
