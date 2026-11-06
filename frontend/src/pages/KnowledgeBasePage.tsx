import React, { useState, useEffect } from 'react';
import {
  Database,
  Upload,
  Search,
  Trash2,
  FileText,
  BookOpen,
  Globe,
  Sparkles,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Layers,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { apiService } from '../services/api';
import { RagDocument, RagStats, EvidenceChunk } from '../types';

export const KnowledgeBasePage: React.FC = () => {
  const [stats, setStats] = useState<RagStats | null>(null);
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [targetCollection, setTargetCollection] = useState<'general' | 'academic'>('general');
  const [isUploading, setIsUploading] = useState(false);

  // Academic Search State
  const [academicQuery, setAcademicQuery] = useState('');
  const [selectedProviders, setSelectedProviders] = useState<string[]>(['arxiv', 'openalex', 'crossref', 'semantic_scholar']);
  const [isSearchingAcademic, setIsSearchingAcademic] = useState(false);

  // Retrieval Tester State
  const [testQuery, setTestQuery] = useState('what is for loop');
  const [testSources, setTestSources] = useState<string[]>(['general', 'academic', 'dynamic_web']);
  const [retrievedEvidence, setRetrievedEvidence] = useState<EvidenceChunk[]>([]);
  const [isTestingRetrieval, setIsTestingRetrieval] = useState(false);

  // Search filter for table
  const [tableFilter, setTableFilter] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statsData, docsData] = await Promise.all([
        apiService.getRagStats(),
        apiService.getRagDocuments()
      ]);
      setStats(statsData);
      setDocuments(docsData.documents || []);
    } catch (e) {
      console.error('Failed to load RAG data:', e);
      setMessage({ text: 'Notice: Using local offline knowledge base state.', type: 'info' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setMessage({ text: 'Please select a PDF or TXT document to upload.', type: 'error' });
      return;
    }

    setIsUploading(true);
    setMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (uploadTitle) formData.append('title', uploadTitle);
      formData.append('collection', targetCollection);

      const res = await apiService.uploadRagDocument(formData);
      setMessage({ text: res.message || 'Document indexed successfully.', type: 'success' });
      setSelectedFile(null);
      setUploadTitle('');
      loadData();
    } catch (err: any) {
      setMessage({
        text: err.response?.data?.detail || 'Failed to upload document.',
        type: 'error'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleAcademicSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!academicQuery.trim()) return;

    setIsSearchingAcademic(true);
    setMessage(null);
    try {
      const res = await apiService.searchAcademicPapers(academicQuery, selectedProviders, 2);
      setMessage({
        text: `Indexed ${res.total_papers_ingested || 0} papers across academic providers.`,
        type: 'success'
      });
      loadData();
    } catch (err: any) {
      setMessage({
        text: err.response?.data?.detail || 'Academic query search encountered an issue.',
        type: 'error'
      });
    } finally {
      setIsSearchingAcademic(false);
    }
  };

  const handleDeleteDocument = async (id: string) => {
    if (!window.confirm('Delete this document and all its indexed chunks from ChromaDB?')) return;
    try {
      await apiService.deleteRagDocument(id);
      setMessage({ text: `Document ${id} purged successfully from vector store.`, type: 'success' });
      loadData();
    } catch (err: any) {
      setMessage({ text: 'Failed to delete document.', type: 'error' });
    }
  };

  const handleTestRetrieval = async () => {
    if (!testQuery.trim()) return;
    setIsTestingRetrieval(true);
    try {
      const res = await apiService.testRagRetrieval(testQuery, testSources, 5);
      setRetrievedEvidence(res.evidence || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTestingRetrieval(false);
    }
  };

  const filteredDocs = documents.filter(d =>
    d.title.toLowerCase().includes(tableFilter.toLowerCase()) ||
    d.source_type.toLowerCase().includes(tableFilter.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <span className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Database className="w-6 h-6" />
            </span>
            <h1 className="text-2xl font-bold text-white tracking-tight">Hybrid RAG Knowledge Base</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Persistent ChromaDB + PostgreSQL
            </span>
          </div>
          <p className="text-slate-400 text-sm">
            Manage multi-source evidence collections, ingest academic research papers, and audit dense + BM25 retrieval fusion.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-xl text-slate-300 hover:text-white transition-all text-sm font-medium"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-sky-400' : ''}`} />
          <span>Refresh Store</span>
        </button>
      </div>

      {/* Notifications */}
      {message && (
        <div
          className={`p-4 rounded-xl border flex items-center space-x-3 text-sm ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : message.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-sky-500/10 border-sky-500/30 text-sky-300'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5 shrink-0 text-emerald-400" />
          ) : (
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
          )}
          <span className="flex-1 font-medium">{message.text}</span>
          <button onClick={() => setMessage(null)} className="text-xs opacity-70 hover:opacity-100">
            Dismiss
          </button>
        </div>
      )}

      {/* Vector Store Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>General Knowledge</span>
            <FileText className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-1">
            {stats?.collections?.general_knowledge ?? 0}
            <span className="text-xs font-normal text-slate-400 ml-1.5">chunks</span>
          </div>
          <p className="text-xs text-slate-500">Permanent educational & technical documentation</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Academic Papers</span>
            <BookOpen className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-1">
            {stats?.collections?.academic_knowledge ?? 0}
            <span className="text-xs font-normal text-slate-400 ml-1.5">chunks</span>
          </div>
          <p className="text-xs text-slate-500">arXiv, OpenAlex, Crossref & Semantic Scholar</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Dynamic Web Cache</span>
            <Globe className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-1">
            {stats?.collections?.dynamic_web_cache ?? 0}
            <span className="text-xs font-normal text-slate-400 ml-1.5">chunks</span>
          </div>
          <p className="text-xs text-slate-500">TTL auto-expires after {stats?.dynamic_web_expiration_hours ?? 24} hours</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Embedding & Reranker</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xs font-bold text-slate-200 mb-1 truncate">
            {stats?.embedding_model ?? 'all-MiniLM-L6-v2'}
          </div>
          <p className="text-xs text-emerald-400 flex items-center space-x-1 mt-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Cross-Encoder ms-marco Active</span>
          </p>
        </div>
      </div>

      {/* Ingestion Panels Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Ingestion (PDF / TXT / HTML) */}
        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <span className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
                <Upload className="w-5 h-5" />
              </span>
              <div>
                <h3 className="font-semibold text-white">Upload Documents (PDF / TXT / HTML)</h3>
                <p className="text-xs text-slate-400">Extracts text via PyMuPDF / BeautifulSoup with SHA-256 deduplication</p>
              </div>
            </div>

            <form onSubmit={handleFileUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Document Title (Optional)</label>
                <input
                  type="text"
                  value={uploadTitle}
                  onChange={e => setUploadTitle(e.target.value)}
                  placeholder="e.g. Distributed Consensus in Raft"
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Target Collection</label>
                  <select
                    value={targetCollection}
                    onChange={e => setTargetCollection(e.target.value as any)}
                    className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="general">General Knowledge</option>
                    <option value="academic">Academic Papers</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">File Attachment</label>
                  <input
                    type="file"
                    accept=".pdf,.txt,.html,.md"
                    onChange={e => setSelectedFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isUploading || !selectedFile}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-sky-500/20 disabled:opacity-50 transition-all flex items-center justify-center space-x-2"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Chunking & Indexing...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Ingest & Index Document</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Academic Paper Search & Ingest */}
        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <span className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
                <BookOpen className="w-5 h-5" />
              </span>
              <div>
                <h3 className="font-semibold text-white">Academic Research Ingestion</h3>
                <p className="text-xs text-slate-400">Fetches & indexes papers from arXiv, OpenAlex, Crossref & Semantic Scholar</p>
              </div>
            </div>

            <form onSubmit={handleAcademicSearch} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Research Topic / Paper Query</label>
                <div className="relative">
                  <input
                    type="text"
                    value={academicQuery}
                    onChange={e => setAcademicQuery(e.target.value)}
                    placeholder="e.g. Retrieval Augmented Generation, Self-RAG, LLM Evaluation"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                  />
                  <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-2">Academic Providers</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: 'arxiv', label: 'arXiv' },
                    { id: 'openalex', label: 'OpenAlex' },
                    { id: 'crossref', label: 'Crossref' },
                    { id: 'semantic_scholar', label: 'Semantic Scholar' }
                  ].map(prov => (
                    <label
                      key={prov.id}
                      className={`flex items-center space-x-2 p-2 rounded-lg border text-xs cursor-pointer transition-colors ${
                        selectedProviders.includes(prov.id)
                          ? 'bg-purple-500/10 border-purple-500/40 text-purple-300'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedProviders.includes(prov.id)}
                        onChange={e => {
                          if (e.target.checked) {
                            setSelectedProviders([...selectedProviders, prov.id]);
                          } else {
                            setSelectedProviders(selectedProviders.filter(p => p !== prov.id));
                          }
                        }}
                        className="rounded border-slate-700 text-purple-600 focus:ring-0"
                      />
                      <span>{prov.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={isSearchingAcademic || !academicQuery.trim()}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-purple-500/20 disabled:opacity-50 transition-all flex items-center justify-center space-x-2"
              >
                {isSearchingAcademic ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Querying Providers & Embedding...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>Search & Ingest Research Papers</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Hybrid Retrieval & Cross-Encoder Tester */}
      <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </span>
            <div>
              <h3 className="font-semibold text-white">Live Retrieval & Cross-Encoder Inspector</h3>
              <p className="text-xs text-slate-400">Audit dense vector + BM25 keyword + RRF + Cross-Encoder reranking</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={testQuery}
            onChange={e => setTestQuery(e.target.value)}
            placeholder="Type query to test retrieval (e.g. what is for loop, explain virtual memory)"
            className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
          <button
            onClick={handleTestRetrieval}
            disabled={isTestingRetrieval}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold transition-all flex items-center justify-center space-x-2"
          >
            {isTestingRetrieval ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            <span>Run Hybrid Search</span>
          </button>
        </div>

        {retrievedEvidence.length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Retrieved Evidence Chunks ({retrievedEvidence.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {retrievedEvidence.map((ev, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="px-2 py-0.5 rounded font-mono font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                      {ev.citation_id}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold">
                      Score: {ev.relevance_score}
                    </span>
                  </div>
                  <h5 className="font-medium text-sm text-white truncate">{ev.title}</h5>
                  <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{ev.text}</p>
                  <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500 border-t border-slate-900">
                    <span className="capitalize">{ev.source_type}</span>
                    {ev.url && (
                      <a href={ev.url} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-1 text-sky-400 hover:underline">
                        <span>Source Link</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Indexed Documents Table */}
      <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-white">Indexed Documents & Relational Metadata</h3>
            <p className="text-xs text-slate-400">PostgreSQL metadata synchronized with ChromaDB embeddings</p>
          </div>
          <div className="relative w-full sm:w-64">
            <input
              type="text"
              value={tableFilter}
              onChange={e => setTableFilter(e.target.value)}
              placeholder="Filter indexed documents..."
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Document Title</th>
                <th className="px-4 py-3">Source Type</th>
                <th className="px-4 py-3">Chunks</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
              {filteredDocs.length > 0 ? (
                filteredDocs.map(doc => (
                  <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{doc.title}</div>
                      <div className="text-[11px] text-slate-500 font-mono">{doc.id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                          doc.source_type === 'academic'
                            ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                            : doc.source_type === 'web' || doc.source_type === 'dynamic_web'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                        }`}
                      >
                        {doc.source_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-300">{doc.chunk_count} chunks</td>
                    <td className="px-4 py-3">
                      <span className="flex items-center space-x-1 text-emerald-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        <span>{doc.status}</span>
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                        title="Delete Document & ChromaDB Chunks"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    No documents matching criteria. Ingest documents or search academic papers above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
