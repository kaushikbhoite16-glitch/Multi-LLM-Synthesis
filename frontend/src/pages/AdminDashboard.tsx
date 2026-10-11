import React, { useState, useEffect } from 'react';
import {
  Shield,
  Users,
  MessageSquare,
  Zap,
  Activity,
  DollarSign,
  TrendingUp,
  Search,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Server,
  Database,
  Lock,
  Calendar,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { apiService } from '../services/api';
import { AdminStats, AdminUserItem } from '../types';

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'status'>('overview');
  const [userSearch, setUserSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggleLoading, setToggleLoading] = useState<number | null>(null);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsData, usersData] = await Promise.all([
        apiService.getAdminStats(),
        apiService.getAdminUsers()
      ]);
      setStats(statsData);
      setUsers(usersData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load administrator data.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    if (!window.confirm(`Are you sure you want to ${currentStatus ? 'deactivate' : 'activate'} this account?`)) {
      return;
    }
    setToggleLoading(userId);
    try {
      const res = await apiService.toggleUserStatus(userId, !currentStatus);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: res.is_active } : u))
      );
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update user status.');
    } finally {
      setToggleLoading(null);
    }
  };

  const filteredUsers = users.filter((u) => {
    if (!userSearch.trim()) return true;
    const term = userSearch.toLowerCase();
    return (
      (u.email || '').toLowerCase().includes(term) ||
      (u.full_name || '').toLowerCase().includes(term) ||
      (u.role || '').toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-amber-500/10 via-slate-900 to-indigo-950/40 border border-amber-500/20">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-amber-500/20 text-amber-300">
              <Shield className="w-5 h-5" />
            </span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
              Privileged Control Center
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Administrator Dashboard</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time platform activity metrics, user governance, API costs, and system telemetry.
          </p>
        </div>

        <button
          onClick={loadAdminData}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors shrink-0 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadAdminData} className="underline text-red-200">
            Retry
          </button>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex space-x-1 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors ${
            activeTab === 'overview'
              ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          Activity & Metrics Overview
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors ${
            activeTab === 'users'
              ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          User Accounts ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('status')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors ${
            activeTab === 'status'
              ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          System Health Telemetry
        </button>
      </div>

      {/* Tab Content: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary KPI Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Registered Users</span>
                <Users className="w-4 h-4 text-sky-400" />
              </div>
              <p className="text-2xl font-bold text-white font-mono">
                {stats?.total_users ?? 0}
              </p>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Across all active roles
              </span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Total Questions Run</span>
                <MessageSquare className="w-4 h-4 text-indigo-400" />
              </div>
              <p className="text-2xl font-bold text-white font-mono">
                {stats?.total_queries ?? 0}
              </p>
              <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-1">
                <span className="text-emerald-400 font-mono">{stats?.live_queries ?? 0} live</span>
                <span>•</span>
                <span className="text-amber-400 font-mono">{stats?.simulation_queries ?? 0} sim</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Genuine API Cost</span>
                <DollarSign className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-white font-mono">
                ${(stats?.total_cost ?? 0).toFixed(6)}
              </p>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Excludes simulated calls ($0.00)
              </span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Total Tokens Consumed</span>
                <Zap className="w-4 h-4 text-purple-400" />
              </div>
              <p className="text-2xl font-bold text-white font-mono">
                {(stats?.total_tokens ?? 0).toLocaleString()}
              </p>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Aggregated model generation
              </span>
            </div>
          </div>

          {/* Mode Breakdown Card */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-amber-400" />
              <span>Execution Mode Distribution</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-500/20">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-emerald-400">Live API Invocations</span>
                  <span className="text-xs font-mono font-bold text-white">{stats?.live_queries ?? 0}</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Genuine API calls to OpenRouter gateway. Incurs genuine token cost and latency.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-amber-500/20">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-amber-400">Simulation Invocations</span>
                  <span className="text-xs font-mono font-bold text-white">{stats?.simulation_queries ?? 0}</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Synthetic test runs without consuming external API credits. Zero financial expense.
                </p>
              </div>
            </div>
          </div>

          {/* Recent Platform Activity */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
              <Activity className="w-4 h-4 text-sky-400" />
              <span>Recent Question Activity</span>
            </h3>
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              <div className="divide-y divide-slate-800/60">
                {stats.recent_activity.map((act) => (
                  <div key={act.id} className="py-2.5 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-3 min-w-0">
                      <span className="font-mono text-slate-400 shrink-0">#{act.id}</span>
                      <span className="text-slate-200 font-medium truncate">{act.title}</span>
                    </div>
                    <div className="flex items-center space-x-3 shrink-0">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                          act.execution_mode === 'simulation'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}
                      >
                        {act.execution_mode.toUpperCase()}
                      </span>
                      <span className="text-slate-400 font-mono text-[10px] hidden sm:inline">
                        {act.created_at.split('.')[0]}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 py-4 text-center">No recent activity recorded.</p>
            )}
          </div>
        </div>
      )}

      {/* Tab Content: USERS */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {/* User Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              placeholder="Search by email, name, or role..."
              className="w-full bg-slate-900/80 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
            />
          </div>

          {/* User Accounts Table */}
          <div className="rounded-2xl bg-slate-900/80 border border-slate-800/80 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase font-mono text-[10px]">
                  <tr>
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Queries Run</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Joined Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2.5">
                          <div className="w-7 h-7 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center font-bold text-[10px]">
                            {u.full_name ? u.full_name[0].toUpperCase() : u.email ? u.email[0].toUpperCase() : 'U'}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-100">{u.full_name || 'Anonymous'}</p>
                            <p className="text-[11px] text-slate-400 font-mono">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                            u.role === 'admin'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {u.role.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono">{u.query_count}</td>
                      <td className="py-3 px-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center space-x-1 text-emerald-400 text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Active</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 text-red-400 text-[11px]">
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Disabled</span>
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                        {u.created_at ? u.created_at.split(' ')[0] : '-'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {u.role !== 'admin' ? (
                          <button
                            onClick={() => handleToggleStatus(u.id, u.is_active)}
                            disabled={toggleLoading === u.id}
                            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                              u.is_active
                                ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                                : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                            }`}
                          >
                            {toggleLoading === u.id ? 'Updating...' : u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        ) : (
                          <span className="text-[10px] text-slate-500 italic">Protected</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content: STATUS */}
      {activeTab === 'status' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
              <div className="flex items-center space-x-2 text-emerald-400 mb-2">
                <Server className="w-5 h-5" />
                <h4 className="font-semibold text-sm">Backend Engine</h4>
              </div>
              <p className="text-xs text-slate-400">FastAPI Async Core v1.0.0</p>
              <div className="mt-3 flex items-center space-x-1.5 text-xs text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>Operational & Healthy</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
              <div className="flex items-center space-x-2 text-sky-400 mb-2">
                <Database className="w-5 h-5" />
                <h4 className="font-semibold text-sm">Database Engine</h4>
              </div>
              <p className="text-xs text-slate-400">SQLite + aiosqlite Async Session</p>
              <div className="mt-3 flex items-center space-x-1.5 text-xs text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>Connected & Migrated</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80">
              <div className="flex items-center space-x-2 text-purple-400 mb-2">
                <Lock className="w-5 h-5" />
                <h4 className="font-semibold text-sm">Security & RBAC</h4>
              </div>
              <p className="text-xs text-slate-400">PBKDF2-HMAC-SHA256 & JWT Bearer</p>
              <div className="mt-3 flex items-center space-x-1.5 text-xs text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>Role Enforcement Active</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
