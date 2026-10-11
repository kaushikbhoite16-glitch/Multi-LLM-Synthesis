import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { QueryPage } from './pages/QueryPage';
import { FinalResultPage } from './pages/FinalResultPage';
import { ResponseComparisonPage } from './pages/ResponseComparisonPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ExperimentPage } from './pages/ExperimentPage';
import { ModelConfigPage } from './pages/ModelConfigPage';
import { EvaluationConfigPage } from './pages/EvaluationConfigPage';
import { HumanEvalPage } from './pages/HumanEvalPage';
import { QuestionHistoryPage } from './pages/QuestionHistoryPage';
import { AdminDashboard } from './pages/AdminDashboard';
import { AuthModal } from './components/AuthModal';
import { AuthProvider, useAuth } from './context/AuthContext';
import { apiService } from './services/api';
import {
  ModelConfig,
  PipelineRunResponse,
  AnalyticsData
} from './types';
import { Menu } from 'lucide-react';

const MainApp: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('query');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [latestResult, setLatestResult] = useState<PipelineRunResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isMock, setIsMock] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'signup' | 'forgot' | 'admin'>('login');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const modelsData = await apiService.getModels();
      setModels(modelsData);

      const analyticsData = await apiService.getAnalytics();
      setAnalytics(analyticsData);
      setIsMock(analyticsData.is_mock);
    } catch (e) {
      console.warn('Initial backend fetch warning (using standard offline fallbacks):', e);
    }
  };

  const handleExecutionComplete = (result: PipelineRunResponse) => {
    setLatestResult(result);
    setIsMock(result.is_mock);
    setActiveTab('result');
    apiService.getAnalytics().then(setAnalytics).catch(() => {});
  };

  const handleSelectHistoryQuestion = (result: PipelineRunResponse) => {
    setLatestResult(result);
    setIsMock(result.is_mock);
    setActiveTab('result');
  };

  const handleOpenAuth = (mode: 'login' | 'signup' | 'forgot' | 'admin' = 'login') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const sidebarWidthClass = isCollapsed ? 'lg:pl-20' : 'lg:pl-64';

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Modern Fixed Left Sidebar */}
      <Sidebar
        activeTab={activeTab === 'result' ? 'query' : activeTab}
        setActiveTab={setActiveTab}
        isMock={isMock}
        onOpenAuth={handleOpenAuth}
        onNewAnalysis={() => setActiveTab('query')}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Container Area with dynamic sidebar offset */}
      <div className={`flex-1 flex flex-col transition-all duration-200 ${sidebarWidthClass}`}>
        {/* Mobile Header Top Bar */}
        <div className="lg:hidden flex items-center justify-between px-4 h-14 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md sticky top-0 z-20">
          <button
            onClick={() => setIsMobileOpen(true)}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="font-bold text-sm text-white">Multi-LLM Synthesis</span>
          <div className="w-6" />
        </div>

        {/* Content Workspace */}
        <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {activeTab === 'dashboard' && (
            <DashboardPage
              analytics={analytics}
              onNavigateToQuery={() => setActiveTab('query')}
              onNavigateToExperiments={() => setActiveTab('experiments')}
            />
          )}

          {activeTab === 'query' && (
            <QueryPage
              availableModels={models}
              onExecutionComplete={handleExecutionComplete}
            />
          )}

          {activeTab === 'history' && (
            <QuestionHistoryPage
              onSelectQuestion={handleSelectHistoryQuestion}
              onNavigateToQuery={() => setActiveTab('query')}
              onOpenAuth={() => handleOpenAuth('login')}
            />
          )}

          {activeTab === 'result' && latestResult && (
            <FinalResultPage
              result={latestResult}
              onNewQuery={() => setActiveTab('query')}
            />
          )}

          {activeTab === 'comparison' && (
            <ResponseComparisonPage
              result={latestResult}
              onNavigateToQuery={() => setActiveTab('query')}
            />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsPage analytics={analytics} />
          )}

          {activeTab === 'experiments' && (
            <ExperimentPage />
          )}

          {activeTab === 'models' && (
            <ModelConfigPage
              models={models}
              onModelsUpdated={loadInitialData}
            />
          )}

          {activeTab === 'evaluation' && (
            <EvaluationConfigPage />
          )}

          {activeTab === 'human-eval' && (
            <HumanEvalPage />
          )}

          {activeTab === 'admin' && (
            <AdminDashboard />
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-900 bg-slate-950/40 py-5 text-center text-xs text-slate-400">
          <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div>
              Multi-LLM Response Evaluation & Adaptive Answer Synthesis &bull; Research Architecture
            </div>
            <div className="flex items-center space-x-3 font-mono text-[11px] text-slate-400">
              <span>OpenRouter Gateway</span>
              <span>&bull;</span>
              <span>RBAC Secured</span>
              <span>&bull;</span>
              <span>Live & Sim Telemetry</span>
            </div>
          </div>
        </footer>
      </div>

      {/* Authentication Modal with Admin Login Support */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
};

export default App;
