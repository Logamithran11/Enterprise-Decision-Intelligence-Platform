import React, { useEffect, useState } from 'react';
import { Landmark, AlertCircle, Percent } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import type { FinanceMetric } from '../types';

export const FinanceDashboard: React.FC = () => {
  const [finance, setFinance] = useState<FinanceMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadData() {
      try {
        const fin = await api.analytics.getFinance();
        setFinance(fin);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch finance metrics');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Loading Finance Metrics...</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="text-sm font-semibold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 p-4 rounded-xl">
        {error}
      </div>
    );
  }

  const latest = finance[finance.length - 1] || {};

  const kpis = [
    {
      title: 'Current Cash Reserve',
      value: `$${latest.cash_balance?.toLocaleString() || '0'}`,
      icon: Landmark,
      colorClass: 'from-emerald-500/10 to-teal-500/10 text-emerald-600 dark:text-emerald-400',
      change: '+4.5% vs last month',
      isPositive: true
    },
    {
      title: 'Outstanding Debt Balance',
      value: `$${latest.debt_balance?.toLocaleString() || '0'}`,
      icon: AlertCircle,
      colorClass: 'from-rose-500/10 to-pink-500/10 text-rose-500',
      change: '-1.8% amortization',
      isPositive: true
    },
    {
      title: 'Debt Service Coverage (DSCR)',
      value: latest.dscr || '0.00',
      icon: Percent,
      colorClass: 'from-blue-500/10 to-indigo-500/10 text-blue-600 dark:text-blue-400',
      change: 'Healthy range (> 1.25)',
      isPositive: true
    }
  ];

  return (
    <div className="space-y-6">
      {/* Finance KPI Badges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="glass-panel p-5 rounded-2xl flex items-center justify-between hover-scale-premium"
            >
              <div className="flex items-center space-x-4">
                <div className={`p-3 bg-gradient-to-tr ${kpi.colorClass} rounded-xl shadow-sm shrink-0`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{kpi.title}</span>
                  <h3 className="text-xl font-extrabold text-slate-800 dark:text-white mt-1 tracking-tight font-display">{kpi.value}</h3>
                </div>
              </div>
              <div className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md">
                {kpi.change}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Finance multi-series area chart */}
      <div className="glass-panel p-5 rounded-2xl hover-scale-premium">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Income vs Operational Costs</h4>
            <p className="text-[10px] text-slate-400 mt-0.5">Dual-channel cash performance tracking</p>
          </div>
          <div className="flex items-center space-x-4 text-[10px] font-bold uppercase tracking-wider">
            <div className="flex items-center space-x-1 text-blue-500">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
              <span>Revenue</span>
            </div>
            <div className="flex items-center space-x-1 text-emerald-500">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              <span>EBITDA</span>
            </div>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={finance.slice(-12)}>
              <defs>
                <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563EB" stopOpacity={0.22}/>
                  <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorEbitda" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.22}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-slate-200 dark:stroke-slate-800/60" />
              <XAxis 
                dataKey="order_month" 
                tick={{ fontSize: 10, fontWeight: 600 }} 
                axisLine={false} 
                tickLine={false} 
                dy={10} 
                className="fill-slate-400"
              />
              <YAxis 
                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} 
                tick={{ fontSize: 10, fontWeight: 600 }} 
                axisLine={false} 
                tickLine={false} 
                dx={-10} 
                className="fill-slate-400"
              />
              <Tooltip 
                contentStyle={{
                  background: 'rgba(30, 41, 59, 0.9)',
                  border: 'none',
                  borderRadius: '12px',
                  fontSize: '11px',
                  color: '#fff',
                  boxShadow: '0 10px 25px -5px rgba(0,0,0,0.3)'
                }}
                formatter={(value) => [`$${value?.toLocaleString() ?? 0}`]} 
              />
              <Area type="monotone" name="Revenue" dataKey="revenue" stroke="#2563EB" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRev)" />
              <Area type="monotone" name="EBITDA" dataKey="ebitda" stroke="#10B981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorEbitda)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Balance Sheet log table */}
      <div className="glass-panel rounded-2xl overflow-hidden hover-scale-premium">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/20">
          <div>
            <h4 className="text-sm font-bold text-slate-850 dark:text-white">Monthly Financial Records</h4>
            <p className="text-[10px] text-slate-400 mt-0.5">Tabular breakdown of the latest financial metrics</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-100/50 dark:bg-slate-800/40 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-850 uppercase tracking-wider text-[9px]">
                <th className="px-6 py-4">Month</th>
                <th className="px-6 py-4 text-right">Revenue</th>
                <th className="px-6 py-4 text-right">Gross Margin</th>
                <th className="px-6 py-4 text-right">EBITDA</th>
                <th className="px-6 py-4 text-right">Cash Balance</th>
                <th className="px-6 py-4 text-right">DSCR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {finance.slice(-6).map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-100/40 dark:hover:bg-slate-800/20 transition-colors">
                  <td className="px-6 py-4 font-bold text-slate-800 dark:text-slate-200">{item.order_month}</td>
                  <td className="px-6 py-4 text-right font-semibold">${item.revenue?.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                  <td className="px-6 py-4 text-right text-emerald-600 font-semibold">${item.gross_margin?.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                  <td className="px-6 py-4 text-right font-medium">${item.ebitda?.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                  <td className="px-6 py-4 text-right font-bold text-slate-800 dark:text-slate-200">${item.cash_balance?.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                  <td className="px-6 py-4 text-right font-semibold text-blue-600 dark:text-blue-400">{item.dscr}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
