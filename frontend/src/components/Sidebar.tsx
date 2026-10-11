import React from 'react';
import {
  MessageSquarePlus,
  History,
  LayoutDashboard,
  Scale,
  TrendingUp,
  FlaskConical,
  Cpu,
  SlidersHorizontal,
  UserCheck,
  ShieldCheck,
  LogOut,
  LogIn,
  ChevronLeft,
  ChevronRight,
  Layers,
  Sparkles
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isMock: boolean;
  onOpenAuth: (mode?: 'login' | 'signup' | 'forgot' | 'admin') => void;
  onNewAnalysis: () => void;
  isCollapsed: boolean;
  setIsCollapsed: (v: boolean) => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (v: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isMock,
  onOpenAuth,
  onNewAnalysis,
  isCollapsed,
  setIsCollapsed,
  isMobileOpen,
  setIsMobileOpen
}) => {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === 'admin';

  const navItems = [
    { id: 'query', label: 'New Exploration', icon: MessageSquarePlus, badge: 'AI' },
    { id: 'history', label: 'Question History', icon: History },
    { id: 'dashboard', label: 'System Overview', icon: LayoutDashboard },
    { id: 'comparison', label: 'Model Benchmarking', icon: Scale },
    { id: 'analytics', label: 'Analytics & Pareto', icon: TrendingUp },
    { id: 'experiments', label: 'Hypothesis Suite', icon: FlaskConical },
    { id: 'models', label: 'Model Catalog', icon: Cpu },
    { id: 'evaluation', label: 'Evaluation Weights', icon: SlidersHorizontal },
    { id: 'human-eval', label: 'Human Evaluation', icon: UserCheck },
  ];

  const handleSelectTab = (tabId: string) => {
    setActiveTab(tabId);
    setIsMobileOpen(false);
  };

  return (
    <aside
      className={`fixed left-0 top-0 h-full bg-slate-950/95 backdrop-blur-xl border-r border-slate-800/80 z-40 transition-all duration-200 flex flex-col justify-between ${
        isCollapsed ? 'w-20' : 'w-64'
      } ${isMobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full lg:translate-x-0'}`}
    >
      {/* Top Header & Branding */}
      <div className="p-4 border-b border-slate-800/70">
        <div className="flex items-center justify-between">
          <div
            onClick={() => handleSelectTab('query')}
            className="flex items-center space-x-3 cursor-pointer group overflow-hidden"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform shrink-0">
              <Layers className="w-5 h-5 text-white" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-bold text-sm text-slate-100 tracking-tight leading-none group-hover:text-sky-300 transition-colors truncate">
                  Multi-LLM Synthesis
                </span>
                <span className="text-[10px] text-slate-400 font-medium tracking-wide mt-1 truncate">
                  Adaptive AI Architecture
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800/80 transition-colors"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Live / Simulation Mode Indicator */}
        {!isCollapsed ? (
          <div className="mt-4 flex items-center justify-between px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
            <span className="text-[11px] text-slate-400 font-medium">Pipeline Gateway</span>
            {isMock ? (
              <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                <span>SIMULATION</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>LIVE API</span>
              </span>
            )}
          </div>
        ) : (
          <div className="mt-3 flex justify-center">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isMock ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'
              }`}
              title={isMock ? 'Mode: Simulation' : 'Mode: Live API'}
            />
          </div>
        )}

        {/* Prominent "New Prompt / Analysis" Action */}
        <button
          onClick={() => {
            onNewAnalysis();
            setIsMobileOpen(false);
          }}
          className={`mt-3 w-full flex items-center justify-center space-x-2 py-2.5 px-3 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-medium text-xs shadow-md shadow-sky-500/20 transition-all ${
            isCollapsed ? 'px-0' : ''
          }`}
          title="New Prompt Exploration"
        >
          <Sparkles className="w-4 h-4 shrink-0" />
          {!isCollapsed && <span>New Analysis</span>}
        </button>
      </div>

      {/* Primary Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1 no-scrollbar">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleSelectTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-sky-500/15 text-sky-300 border border-sky-500/25 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              } ${isCollapsed ? 'justify-center px-0' : ''}`}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
              {!isCollapsed && <span className="truncate">{item.label}</span>}
              {!isCollapsed && item.badge && !isActive && (
                <span className="ml-auto text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        {/* Dedicated Administrator Section (Shown for Authenticated Admins) */}
        {isAdmin && (
          <div className="pt-3 mt-3 border-t border-slate-800/80">
            {!isCollapsed && (
              <span className="px-3 text-[10px] font-semibold uppercase tracking-wider text-amber-400/80 font-mono">
                Privileged System
              </span>
            )}
            <button
              onClick={() => handleSelectTab('admin')}
              className={`mt-1 w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                activeTab === 'admin'
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-amber-400/80 hover:text-amber-300 hover:bg-amber-500/10'
              } ${isCollapsed ? 'justify-center px-0' : ''}`}
              title="Administrator Dashboard"
            >
              <ShieldCheck className="w-4 h-4 shrink-0 text-amber-400" />
              {!isCollapsed && <span>Admin Dashboard</span>}
            </button>
          </div>
        )}
      </div>

      {/* Bottom Profile / Account Area */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/40">
        {user ? (
          <div className={`flex items-center space-x-2 ${isCollapsed ? 'justify-center' : ''}`}>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 text-white border border-indigo-400/30 flex items-center justify-center font-bold text-xs shrink-0 shadow-sm">
              {user.full_name ? user.full_name[0].toUpperCase() : user.email ? user.email[0].toUpperCase() : 'U'}
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-1.5">
                  <p className="text-xs font-medium text-slate-200 truncate">
                    {user.full_name || user.email?.split('@')[0]}
                  </p>
                  {isAdmin && (
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-mono font-semibold">
                      ADMIN
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
              </div>
            )}
            {!isCollapsed && (
              <button
                onClick={logout}
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-900 rounded-lg transition-colors"
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-1.5">
            <button
              onClick={() => onOpenAuth('login')}
              className={`w-full flex items-center space-x-2 py-2 px-3 rounded-xl bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 text-sky-300 font-semibold text-xs transition-colors ${
                isCollapsed ? 'justify-center px-0' : 'justify-center'
              }`}
            >
              <LogIn className="w-4 h-4 shrink-0" />
              {!isCollapsed && <span>Sign In</span>}
            </button>
            {!isCollapsed && (
              <button
                onClick={() => onOpenAuth('admin')}
                className="w-full flex items-center justify-center space-x-1.5 py-1 text-[11px] text-slate-500 hover:text-amber-400 transition-colors"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Administrator Login</span>
              </button>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
