import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { QueryPage } from './pages/QueryPage';
import { FinalResultPage } from './pages/FinalResultPage';
import { ResponseComparisonPage } from './pages/ResponseComparisonPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ExperimentPage } from './pages/ExperimentPage';
import { ModelConfigPage } from './pages/ModelConfigPage';
import { EvaluationConfigPage } from './pages/EvaluationConfigPage';
import { HumanEvalPage } from './pages/HumanEvalPage';
import { apiService } from './services/api';
import {
  ModelConfig,
  PipelineRunResponse,
  AnalyticsData
} from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [latestResult, setLatestResult] = useState<PipelineRunResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isMock, setIsMock] = useState(true);

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
    // Refresh analytics after run
    apiService.getAnalytics().then(setAnalytics).catch(() => {});
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Top Academic Navigation Bar */}
      <Navbar
        activeTab={activeTab === 'result' ? 'query' : activeTab}
        setActiveTab={setActiveTab}
        isMock={isMock}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
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
      </main>

      {/* Academic Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            Multi-LLM Response Evaluation & Adaptive Answer Synthesis Platform &bull; Academic Research Prototype
          </div>
          <div className="flex items-center space-x-4 font-mono text-[11px] text-slate-400">
            <span>RAG-Like Response Synthesis</span>
            <span>&bull;</span>
            <span>OpenRouter Gateway</span>
            <span>&bull;</span>
            <span>SQLite/PostgreSQL</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
