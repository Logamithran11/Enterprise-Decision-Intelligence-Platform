import React, { useEffect, useState } from 'react';
import { ShoppingBag, TrendingUp, Truck, Calculator, ArrowUpRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import type { FinanceMetric } from '../types';

export const SalesDashboard: React.FC = () => {
  const [finance, setFinance] = useState<FinanceMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Interactive Margin Calculator
  const [quantity, setQuantity] = useState(5);
  const [price, setPrice] = useState(150.0);
  const [discount, setDiscount] = useState(10.0);
  const [marginRate, setMarginRate] = useState(45.0);
  const [calculatedMargin, setCalculatedMargin] = useState<number | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const fin = await api.analytics.getFinance();
        setFinance(fin);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch sales analytics');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleCalculate = () => {
    const grossAmount = quantity * price;
    const netAmount = grossAmount * (1 - discount / 100);
    const cost = netAmount * (1 - marginRate / 100);
    const margin = netAmount - cost;
    setCalculatedMargin(margin);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Loading Sales Hub...</p>
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

  // Calculate high-level summaries
  const totalQuantity = finance.reduce((acc, row) => acc + row.order_count, 0);
  const avgMonthlyRev = finance.length ? finance.reduce((acc, row) => acc + row.revenue, 0) / finance.length : 0;

  const kpis = [
    {
      title: 'Total Managed Orders',
      value: totalQuantity.toLocaleString(),
      icon: ShoppingBag,
      colorClass: 'from-indigo-500/10 to-blue-500/10 text-indigo-600 dark:text-indigo-400',
      change: '+14% MoM'
    },
    {
      title: 'Monthly Avg Velocity',
      value: `$${avgMonthlyRev.toLocaleString(undefined, {maximumFractionDigits: 0})}`,
      icon: TrendingUp,
      colorClass: 'from-blue-500/10 to-sky-500/10 text-blue-600 dark:text-blue-400',
      change: 'Steady growth'
    },
    {
      title: 'Avg Shipping Lead',
      value: '3.8 Days',
      icon: Truck,
      colorClass: 'from-emerald-500/10 to-teal-500/10 text-emerald-600 dark:text-emerald-400',
      change: 'Optimal performance'
    }
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
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
                  <Icon className="w-6 h-6" />
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
        {/* Sales Volume chart */}
        <div className="glass-panel p-5 rounded-2xl lg:col-span-2 hover-scale-premium">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Monthly Order Volumes</h4>
              <p className="text-[10px] text-slate-400 mt-0.5">Historical monthly customer transaction count</p>
            </div>
            <div className="flex items-center space-x-2 text-[10px] font-bold uppercase tracking-wider text-indigo-400">
              <span className="w-2 h-2 rounded-full bg-indigo-500 inline-block" />
              <span>Orders</span>
            </div>
          </div>

          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={finance.slice(-12)}>
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
                  formatter={(value) => [value?.toLocaleString() ?? 0, 'Orders']} 
                />
                <Bar dataKey="order_count" fill="#4F46E5" radius={[6, 6, 0, 0]} maxBarSize={45} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Interactive Margin Calculator */}
        <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between hover-scale-premium relative overflow-hidden">
          <div>
            <div className="flex items-center space-x-2 mb-5 pb-3 border-b border-slate-100 dark:border-slate-800">
              <Calculator className="w-4 h-4 text-slate-400" />
              <h4 className="text-sm font-bold text-slate-850 dark:text-white">Order Margin Simulation</h4>
            </div>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500">Order Quantity</label>
                <input 
                  type="number" 
                  value={quantity} 
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-semibold"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500">Unit Price ($)</label>
                <input 
                  type="number" 
                  value={price} 
                  onChange={(e) => setPrice(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-semibold"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500">Discount (%)</label>
                  <input 
                    type="number" 
                    value={discount} 
                    onChange={(e) => setDiscount(Number(e.target.value))}
                    className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-semibold"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500">Margin Rate (%)</label>
                  <input 
                    type="number" 
                    value={marginRate} 
                    onChange={(e) => setMarginRate(Number(e.target.value))}
                    className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-semibold"
                  />
                </div>
              </div>
              <button 
                onClick={handleCalculate}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold p-3 rounded-xl text-xs transition-all shadow-md shadow-indigo-500/10 active:scale-[0.98] cursor-pointer mt-2"
              >
                Simulate Profit Margin
              </button>
            </div>
          </div>

          {calculatedMargin !== null && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border-t border-slate-100 dark:border-slate-800 pt-4 mt-5 flex items-center justify-between"
            >
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block leading-none">Estimated Profit</span>
                <h3 className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1.5 font-display tracking-tight">
                  ${calculatedMargin.toFixed(2)}
                </h3>
              </div>
              <div className="flex items-center space-x-1 text-[10px] text-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/50 dark:border-emerald-900/40 rounded-lg px-2.5 py-1 font-bold">
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>ROI verified</span>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};
