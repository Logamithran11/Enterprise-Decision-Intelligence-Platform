import React, { useEffect, useState } from 'react';
import { Users, Heart, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import type { CustomerMetric } from '../types';

export const CustomerDashboard: React.FC = () => {
  const [customers, setCustomers] = useState<CustomerMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadData() {
      try {
        const cus = await api.analytics.getCustomers();
        setCustomers(cus);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch customer metrics');
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
        <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Loading Customer KPIs...</p>
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

  // Calculate segment distributions
  const segments = customers.reduce((acc: Record<string, number>, c) => {
    acc[c.segment] = (acc[c.segment] || 0) + 1;
    return acc;
  }, {});

  const chartData = Object.entries(segments).map(([name, value]) => ({ name, value }));
  const avgEngagement = customers.length ? customers.reduce((acc, c) => acc + c.engagement_score, 0) / customers.length : 0;
  const avgHealth = customers.length ? customers.reduce((acc, c) => acc + c.customer_health_score, 0) / customers.length : 0;

  const kpis = [
    {
      title: 'Total Accounts Logged',
      value: customers.length.toLocaleString(),
      icon: Users,
      colorClass: 'from-blue-500/10 to-indigo-500/10 text-blue-600 dark:text-blue-400',
      change: '100% active profiles'
    },
    {
      title: 'Average Engagement Score',
      value: `${avgEngagement.toFixed(1)} / 100`,
      icon: Activity,
      colorClass: 'from-indigo-500/10 to-purple-500/10 text-indigo-600 dark:text-indigo-400',
      change: 'High interaction rate'
    },
    {
      title: 'Average Account Health',
      value: `${avgHealth.toFixed(1)} / 100`,
      icon: Heart,
      colorClass: 'from-emerald-500/10 to-teal-500/10 text-emerald-600 dark:text-emerald-400',
      change: 'Stable retention indicator'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Customer summary cards */}
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Segment distributions chart */}
        <div className="glass-panel p-5 rounded-2xl lg:col-span-2 hover-scale-premium">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Customer Segment Distribution</h4>
              <p className="text-[10px] text-slate-400 mt-0.5">Demographics representation using machine learning segments</p>
            </div>
            <div className="flex items-center space-x-2 text-[10px] font-bold uppercase tracking-wider text-blue-500">
              <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
              <span>Segments</span>
            </div>
          </div>

          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-slate-200 dark:stroke-slate-800/60" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 10, fontWeight: 600 }} 
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                  className="fill-slate-400"
                />
                <YAxis 
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
                />
                <Bar dataKey="value" fill="#2563EB" radius={[6, 6, 0, 0]} maxBarSize={45} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Customer Accounts table preview */}
        <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between hover-scale-premium relative overflow-hidden">
          <div>
            <div className="pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
              <h4 className="text-sm font-bold text-slate-850 dark:text-white">Customer Accounts Preview</h4>
              <p className="text-[10px] text-slate-400 mt-0.5">Quick lookup of the most active enterprise accounts</p>
            </div>
            <div className="space-y-4">
              {customers.slice(0, 5).map((cust, idx) => (
                <div key={idx} className="flex justify-between items-center text-xs pb-3 border-b border-slate-100 dark:border-slate-850 last:border-b-0 last:pb-0">
                  <div>
                    <p className="font-bold text-slate-800 dark:text-slate-200 font-display">{cust.customer_id}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">{cust.industry} • {cust.region}</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex px-2 py-0.5 rounded-lg text-[9px] font-bold border ${
                      cust.customer_health_score >= 70 
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-450 border-emerald-200/50' 
                        : cust.customer_health_score >= 40 
                          ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-450 border-amber-200/50' 
                          : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-450 border-rose-200/50'
                    }`}>
                      Health: {cust.customer_health_score}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
