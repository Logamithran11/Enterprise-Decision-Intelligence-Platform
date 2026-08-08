import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, TrendingUp, DollarSign, Activity, 
  Users, BarChart2, ShieldAlert, HeartHandshake, LogOut, Sun, Moon,
  ChevronLeft, ChevronRight, Bell, Search, Calendar, ShieldCheck,
  User as UserIcon, HelpCircle, Menu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { User } from '../types';

interface DashboardLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  user: User | null;
  onLogout: () => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  activeTab,
  setActiveTab,
  darkMode,
  setDarkMode,
  user,
  onLogout
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState<string[]>([
    'Inference Drift shield validated successfully.',
    'System generated 3 new recommendations.',
    'Inventory replenishment triggers compiled.'
  ]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [currentDateString, setCurrentDateString] = useState('');

  useEffect(() => {
    const options: Intl.DateTimeFormatOptions = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
    setCurrentDateString(new Date().toLocaleDateString('en-US', options));
  }, []);

  const menuGroups = [
    {
      group: 'Core Insights',
      items: [
        { id: 'executive', name: 'Executive Overview', icon: LayoutDashboard },
        { id: 'sales', name: 'Sales Hub', icon: TrendingUp },
        { id: 'finance', name: 'Finance Metrics', icon: DollarSign },
      ]
    },
    {
      group: 'Operational Logs',
      items: [
        { id: 'operations', name: 'Operations Log', icon: Activity },
        { id: 'customer', name: 'Customer KPIs', icon: Users },
      ]
    },
    {
      group: 'Intelligence desk',
      items: [
        { id: 'forecast', name: 'Forecast Center', icon: BarChart2 },
        { id: 'risk', name: 'Risk Analytics', icon: ShieldAlert },
        { id: 'recommendation', name: 'Recommendation Desk', icon: HeartHandshake }
      ]
    }
  ];

  const getBreadcrumbs = () => {
    const tabNames: Record<string, string> = {
      executive: 'Executive Overview',
      sales: 'Sales Hub',
      finance: 'Finance Metrics',
      operations: 'Operations Log',
      customer: 'Customer KPIs',
      forecast: 'Forecast Center',
      risk: 'Risk Analytics',
      recommendation: 'Recommendation Desk'
    };
    return ['Platform', tabNames[activeTab] || activeTab];
  };

  return (
    <div className="min-h-screen flex transition-colors duration-300 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      
      {/* Sidebar Navigation */}
      <motion.aside 
        animate={{ width: collapsed ? 76 : 260 }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        className="border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between glass-panel fixed h-full z-20"
      >
        <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden py-5 px-3">
          {/* Brand header */}
          <div className={`flex items-center justify-between mb-8 px-2 ${collapsed ? 'justify-center' : ''}`}>
            {!collapsed && (
              <motion.div 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="flex flex-col"
              >
                <h1 className="text-lg font-extrabold bg-gradient-to-r from-blue-600 to-indigo-500 bg-clip-text text-transparent font-display tracking-tight leading-tight">
                  Agilisium MITU
                </h1>
                <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium tracking-wide uppercase mt-0.5">
                  Decision Intelligence
                </p>
              </motion.div>
            )}
            
            <button 
              onClick={() => setCollapsed(!collapsed)}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 transition-colors cursor-pointer"
            >
              {collapsed ? <ChevronRight className="w-4 h-4 text-slate-500" /> : <ChevronLeft className="w-4 h-4 text-slate-500" />}
            </button>
          </div>

          {/* Navigation Links Grouped */}
          <div className="space-y-6 flex-1">
            {menuGroups.map((group, groupIdx) => (
              <div key={groupIdx} className="space-y-1">
                {!collapsed && (
                  <motion.h3 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="px-3 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2"
                  >
                    {group.group}
                  </motion.h3>
                )}
                <div className="space-y-0.5">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setActiveTab(item.id)}
                        className={`w-full flex items-center rounded-lg text-sm transition-all py-2.5 px-3 relative font-medium group cursor-pointer ${
                          isActive 
                            ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20' 
                            : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400'
                        } ${collapsed ? 'justify-center' : 'space-x-3'}`}
                        title={collapsed ? item.name : undefined}
                      >
                        <Icon className={`w-4 h-4 shrink-0 transition-transform duration-200 group-hover:scale-110 ${isActive ? 'text-white' : 'text-slate-500 dark:text-slate-400'}`} />
                        {!collapsed && (
                          <motion.span
                            initial={{ opacity: 0, x: -5 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -5 }}
                          >
                            {item.name}
                          </motion.span>
                        )}
                        {/* Active line accent for unselected items on hover */}
                        {!isActive && !collapsed && (
                          <span className="absolute left-0 w-1 h-0 bg-blue-500 group-hover:h-1/2 transition-all duration-200 rounded-r-lg" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* User profile & controls at bottom */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 space-y-3">
          {user && (
            <div className={`flex items-center px-2 py-1.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/30 ${collapsed ? 'justify-center' : 'space-x-3'}`}>
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-sm shrink-0">
                {user.username.charAt(0).toUpperCase()}
              </div>
              {!collapsed && (
                <div className="overflow-hidden">
                  <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate leading-none">{user.username}</p>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1 capitalize leading-none font-medium">{user.role}</p>
                </div>
              )}
            </div>
          )}

          <div className={`flex items-center pt-2 ${collapsed ? 'flex-col space-y-2' : 'justify-between'}`}>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 cursor-pointer"
              title="Toggle Theme"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button
              onClick={onLogout}
              className={`flex items-center text-xs font-medium text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 p-2 rounded-lg transition-colors border border-transparent hover:border-red-200 dark:hover:border-red-950 cursor-pointer ${
                collapsed ? 'justify-center' : 'space-x-2'
              }`}
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
              {!collapsed && <span>Sign Out</span>}
            </button>
          </div>
        </div>
      </motion.aside>

      {/* Main Display Frame */}
      <div className="flex-1 flex flex-col min-w-0" style={{ paddingLeft: collapsed ? 76 : 260 }}>
        {/* Top Navbar */}
        <header className="h-16 border-b border-slate-200 dark:border-slate-800 glass-panel px-6 flex items-center justify-between sticky top-0 z-10">
          {/* Left: Breadcrumbs / Title */}
          <div className="flex items-center space-x-3">
            <Menu className="w-4 h-4 text-slate-400 md:hidden cursor-pointer" />
            <div className="hidden md:flex items-center space-x-2 text-xs font-medium text-slate-400 dark:text-slate-500">
              {getBreadcrumbs().map((b, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <span className="text-[10px] text-slate-300 dark:text-slate-700">/</span>}
                  <span className={i === getBreadcrumbs().length - 1 ? 'text-slate-700 dark:text-slate-300 font-semibold' : ''}>{b}</span>
                </React.Fragment>
              ))}
            </div>
            <h2 className="text-base font-bold tracking-tight text-slate-800 dark:text-slate-100 md:hidden capitalize">
              {activeTab.replace('_', ' ')}
            </h2>
          </div>

          {/* Right: Search, Actions, Date, Status */}
          <div className="flex items-center space-x-4">
            
            {/* Search Input */}
            <div className="relative hidden md:block">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                type="text" 
                placeholder="Search metrics, reports..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-56 bg-slate-100/80 dark:bg-slate-900/60 p-2 pl-9 rounded-lg border border-slate-200/80 dark:border-slate-800/80 text-xs focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-medium"
              />
            </div>

            {/* Date Display */}
            <div className="hidden lg:flex items-center space-x-1.5 text-xs text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 px-2.5 py-1.5 rounded-lg bg-white/50 dark:bg-slate-900/40">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-semibold">{currentDateString}</span>
            </div>

            {/* Live Backend Connection Status */}
            <div className="flex items-center space-x-1.5 text-xs border border-slate-200 dark:border-slate-800 px-2.5 py-1.5 rounded-lg bg-white/50 dark:bg-slate-900/40">
              <ShieldCheck className="w-3.5 h-3.5 text-green-500" />
              <span className="font-semibold text-slate-600 dark:text-slate-400 hidden sm:inline">API</span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            </div>

            {/* Notifications Dropdown */}
            <div className="relative">
              <button 
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 cursor-pointer relative"
              >
                <Bell className="w-4 h-4" />
                {notifications.length > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-blue-600 dark:bg-blue-400 rounded-full" />
                )}
              </button>

              <AnimatePresence>
                {showNotifications && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute right-0 mt-2 w-80 glass-panel rounded-xl overflow-hidden shadow-xl p-3 z-30"
                  >
                    <div className="flex justify-between items-center mb-2 pb-2 border-b border-slate-100 dark:border-slate-800">
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300">Notifications</span>
                      <button 
                        onClick={() => setNotifications([])} 
                        className="text-[10px] text-blue-500 hover:underline"
                      >
                        Clear All
                      </button>
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <p className="text-[11px] text-slate-400 text-center py-4">No new alerts</p>
                      ) : (
                        notifications.map((n, i) => (
                          <div key={i} className="text-[11px] text-slate-600 dark:text-slate-400 p-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-lg">
                            • {n}
                          </div>
                        ))
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Profile Dropdown icon */}
            <div className="relative">
              <button 
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 font-bold flex items-center justify-center border border-blue-200 dark:border-blue-800 cursor-pointer text-xs"
              >
                {user?.username.charAt(0).toUpperCase() || <UserIcon className="w-4 h-4" />}
              </button>

              <AnimatePresence>
                {showProfileMenu && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute right-0 mt-2 w-48 glass-panel rounded-xl shadow-xl p-1.5 z-30"
                  >
                    <div className="p-2 border-b border-slate-100 dark:border-slate-800 mb-1">
                      <p className="text-xs font-semibold">{user?.username}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{user?.email}</p>
                    </div>
                    <button className="w-full text-left px-2 py-1.5 rounded-lg text-xs hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center space-x-2">
                      <UserIcon className="w-3.5 h-3.5" />
                      <span>Account Settings</span>
                    </button>
                    <button className="w-full text-left px-2 py-1.5 rounded-lg text-xs hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center space-x-2">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Help & Support</span>
                    </button>
                    <button 
                      onClick={onLogout}
                      className="w-full text-left px-2 py-1.5 rounded-lg text-xs hover:bg-red-50 dark:hover:bg-red-950/20 text-red-500 flex items-center space-x-2 mt-1 border-t border-slate-100 dark:border-slate-800 pt-2"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

          </div>
        </header>

        {/* Content Body with slide-up page transitions */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};
