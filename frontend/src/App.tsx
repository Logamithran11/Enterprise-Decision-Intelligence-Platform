import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import type { User } from './types';
import { DashboardLayout } from './layouts/DashboardLayout';
import { ExecutiveDashboard } from './pages/ExecutiveDashboard';
import { SalesDashboard } from './pages/SalesDashboard';
import { FinanceDashboard } from './pages/FinanceDashboard';
import { OperationsDashboard } from './pages/OperationsDashboard';
import { CustomerDashboard } from './pages/CustomerDashboard';
import { ForecastCenter } from './pages/ForecastCenter';
import { RiskCenter } from './pages/RiskCenter';
import { RecommendationCenter } from './pages/RecommendationCenter';
import { ShieldCheck } from 'lucide-react';

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState('executive');
  const [darkMode, setDarkMode] = useState<boolean>(localStorage.getItem('dark_mode') === 'true');

  // Login Form credentials state
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);

  // Sync dark theme class with document body
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark');
      localStorage.setItem('dark_mode', 'true');
    } else {
      document.body.classList.remove('dark');
      localStorage.setItem('dark_mode', 'false');
    }
  }, [darkMode]);

  // Load user profile if token exists
  useEffect(() => {
    if (token) {
      api.auth.me()
        .then(u => setUser(u))
        .catch(() => handleLogout());
    }
  }, [token]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoggingIn(true);
    try {
      const data = await api.auth.login(usernameInput, passwordInput);
      localStorage.setItem('access_token', data.access_token);
      setToken(data.access_token);
    } catch (err: any) {
      setLoginError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const renderActiveDashboard = () => {
    switch (activeTab) {
      case 'executive':
        return <ExecutiveDashboard />;
      case 'sales':
        return <SalesDashboard />;
      case 'finance':
        return <FinanceDashboard />;
      case 'operations':
        return <OperationsDashboard />;
      case 'customer':
        return <CustomerDashboard />;
      case 'forecast':
        return <ForecastCenter />;
      case 'risk':
        return <RiskCenter />;
      case 'recommendation':
        return <RecommendationCenter />;
      default:
        return <ExecutiveDashboard />;
    }
  };

  // If not authenticated, render Login Page
  if (!token) {
    return (
      <div className={`min-h-screen flex items-center justify-center transition-colors duration-300 p-4 ${
        darkMode ? 'bg-[#0F172A]' : 'bg-[#F8FAFC]'
      }`}>
        {/* Decorative subtle background gradients */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 dark:bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/10 dark:bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="w-full max-w-md p-8 md:p-10 rounded-2xl glass-panel relative z-10 hover-scale-premium">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white font-bold text-xl shadow-lg shadow-blue-500/20 mb-4 font-display">
              A
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white font-display">
              Decision Intelligence Desk
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 font-medium">
              Please sign in to access enterprise forecast modules
            </p>
          </div>

          {loginError && (
            <div className="mb-6 text-xs font-semibold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 p-3.5 rounded-xl flex items-center space-x-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600 dark:bg-red-400 animate-ping shrink-0" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Username</label>
              <input
                type="text"
                required
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                placeholder="e.g. admin"
                className="w-full bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-sm focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-medium text-slate-800 dark:text-slate-200 shadow-inner"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Password</label>
              <input
                type="password"
                required
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-sm focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-medium text-slate-800 dark:text-slate-200 shadow-inner"
              />
            </div>
            
            <button
              type="submit"
              disabled={loggingIn}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold p-3.5 rounded-xl text-sm transition-all shadow-md shadow-blue-500/10 hover:shadow-blue-500/20 active:scale-[0.98] cursor-pointer mt-2"
            >
              {loggingIn ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          {/* Quick info credentials helper for development/testing */}
          <div className="mt-8 border-t border-slate-200/60 dark:border-slate-800/80 pt-5 text-[10px] text-slate-400 dark:text-slate-500 flex items-start space-x-3 font-medium">
            <ShieldCheck className="w-4 h-4 text-blue-500 shrink-0" />
            <p className="leading-normal">
              Ensure backend server is running on port 8000 and user registration endpoints are seeded.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // If authenticated, render Dashboard Layout with current subpage
  return (
    <DashboardLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      darkMode={darkMode}
      setDarkMode={setDarkMode}
      user={user}
      onLogout={handleLogout}
    >
      {renderActiveDashboard()}
    </DashboardLayout>
  );
}
