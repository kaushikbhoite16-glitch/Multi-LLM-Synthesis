import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';
import {
  X,
  Mail,
  Lock,
  User as UserIcon,
  LogIn,
  UserPlus,
  KeyRound,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'signup' | 'forgot' | 'admin';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  initialMode = 'login',
}) => {
  const { login, signUp, googleLogin } = useAuth();
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot' | 'reset' | 'admin'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Sync mode if initialMode changes
  React.useEffect(() => {
    setMode(initialMode);
    setError(null);
    setSuccess(null);
  }, [initialMode, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      if (mode === 'login' || mode === 'admin') {
        await login(email, password);
        onClose();
      } else if (mode === 'signup') {
        await signUp(email, password, fullName);
        onClose();
      } else if (mode === 'forgot') {
        const res = await apiService.forgotPassword(email);
        setSuccess(res.message);
        if (res.reset_token) {
          setResetToken(res.reset_token);
          setMode('reset');
        }
      } else if (mode === 'reset') {
        const res = await apiService.resetPassword(resetToken, newPassword);
        setSuccess(res.message);
        setTimeout(() => setMode('login'), 1500);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Operation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    setError(null);
    if (!email || !email.trim() || !email.includes('@')) {
      setError('Please enter your Google account email address above before continuing with Google.');
      return;
    }
    setIsLoading(true);
    try {
      await googleLogin(undefined, email.trim(), fullName || undefined);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Google authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const isAdminMode = mode === 'admin';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-150">
      <div
        className={`bg-slate-900 border rounded-3xl max-w-md w-full p-6 shadow-2xl relative transition-all ${
          isAdminMode ? 'border-amber-500/40 shadow-amber-500/10' : 'border-slate-800'
        }`}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center mb-6">
          <div
            className={`w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3 border ${
              isAdminMode
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-sky-500/10 border-sky-500/20 text-sky-400'
            }`}
          >
            {isAdminMode ? (
              <ShieldCheck className="w-6 h-6" />
            ) : mode === 'signup' ? (
              <UserPlus className="w-6 h-6" />
            ) : mode === 'forgot' || mode === 'reset' ? (
              <KeyRound className="w-6 h-6" />
            ) : (
              <LogIn className="w-6 h-6" />
            )}
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            {isAdminMode && 'Administrator Access'}
            {mode === 'login' && 'Welcome Back'}
            {mode === 'signup' && 'Create Your Account'}
            {mode === 'forgot' && 'Reset Password'}
            {mode === 'reset' && 'Set New Password'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            {isAdminMode && 'Authenticate with your administrator credentials to access system management.'}
            {mode === 'login' && 'Sign in to access your questions, benchmark history, and custom syntheses.'}
            {mode === 'signup' && 'Join the Multi-LLM research experimentation and synthesis platform.'}
            {mode === 'forgot' && 'Enter your registered email to receive a password recovery token.'}
            {mode === 'reset' && 'Enter the reset token and your new secure password.'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-300 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Vance"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-9 pr-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
                />
              </div>
            </div>
          )}

          {mode !== 'reset' && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                {isAdminMode ? 'Administrator Email' : 'Email Address'}
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={isAdminMode ? 'admin@multilllm.ai' : 'name@organization.com'}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-9 pr-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
                />
              </div>
            </div>
          )}

          {(mode === 'login' || mode === 'signup' || isAdminMode) && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-medium text-slate-300">Password</label>
                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => {
                      setMode('forgot');
                      setError(null);
                      setSuccess(null);
                    }}
                    className="text-[11px] text-sky-400 hover:text-sky-300"
                  >
                    Forgot Password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-9 pr-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
                />
              </div>
            </div>
          )}

          {mode === 'reset' && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Recovery Token</label>
                <input
                  type="text"
                  required
                  value={resetToken}
                  onChange={(e) => setResetToken(e.target.value)}
                  placeholder="Paste token received"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 px-3 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">New Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="New password (min 6 characters)"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-9 pr-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
                  />
                </div>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-2.5 px-4 rounded-xl text-xs font-semibold shadow-md transition-all duration-150 disabled:opacity-50 mt-2 ${
              isAdminMode
                ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
                : 'bg-sky-500 hover:bg-sky-400 text-white shadow-sky-500/25'
            }`}
          >
            {isLoading
              ? 'Verifying...'
              : isAdminMode
              ? 'Sign In as Administrator'
              : mode === 'login'
              ? 'Sign In'
              : mode === 'signup'
              ? 'Create Account'
              : mode === 'forgot'
              ? 'Send Reset Token'
              : 'Update Password'}
          </button>
        </form>

        {(mode === 'login' || mode === 'signup') && (
          <>
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-800"></div>
              </div>
              <div className="relative flex justify-center text-[10px] uppercase font-mono tracking-wider">
                <span className="bg-slate-900 px-2 text-slate-400">Or continue with</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGoogleAuth}
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>
          </>
        )}

        {/* Bottom Switch Links */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-col items-center gap-2 text-xs text-slate-400">
          {isAdminMode ? (
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError(null);
                setSuccess(null);
              }}
              className="text-sky-400 hover:text-sky-300 font-semibold"
            >
              &larr; Return to Regular User Login
            </button>
          ) : mode === 'login' ? (
            <>
              <p>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setMode('signup');
                    setError(null);
                    setSuccess(null);
                  }}
                  className="text-sky-400 hover:text-sky-300 font-semibold"
                >
                  Sign Up
                </button>
              </p>
              <button
                type="button"
                onClick={() => {
                  setMode('admin');
                  setError(null);
                  setSuccess(null);
                }}
                className="text-[11px] text-slate-400 hover:text-amber-400 flex items-center space-x-1"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Administrator Login</span>
              </button>
            </>
          ) : (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setError(null);
                  setSuccess(null);
                }}
                className="text-sky-400 hover:text-sky-300 font-semibold"
              >
                Sign In
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
