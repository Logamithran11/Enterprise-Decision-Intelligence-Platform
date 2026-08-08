import React, { useEffect, useState } from 'react';
import { Sparkles, RefreshCw, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import type { BusinessRecommendation } from '../types';

export const RecommendationCenter: React.FC = () => {
  const [recommendations, setRecommendations] = useState<BusinessRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      const data = await api.recommendations.get();
      setRecommendations(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch business recommendations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await api.recommendations.regenerate();
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to regenerate recommendations');
    } finally {
      setRegenerating(false);
    }
  };

  const getPriorityColor = (prio: string) => {
    switch (prio?.toLowerCase()) {
      case 'critical': return 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-450 border-rose-200 dark:border-rose-900/40';
      case 'high': return 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-450 border-amber-200/50 dark:border-amber-900/40';
      default: return 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-450 border-blue-200/50 dark:border-blue-900/40';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Loading Recommendations Desk...</p>
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

  return (
    <div className="space-y-6">
      {/* Controls row */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-100/50 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-800/80 p-4 rounded-2xl">
        <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400 font-medium">
          <div className="p-2 bg-blue-50 dark:bg-blue-950 rounded-xl border border-blue-200/50 dark:border-blue-900/50 shrink-0">
            <Sparkles className="w-4 h-4 text-blue-500 animate-pulse" />
          </div>
          <p className="leading-relaxed">
            Recommendations compiled from latest forecasting estimates, regional operational delays, and financial solvency constraints.
          </p>
        </div>
        
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/70 text-white font-bold text-xs px-4 py-2.5 rounded-xl transition-all shadow-md shadow-blue-500/10 active:scale-[0.98] cursor-pointer whitespace-nowrap"
        >
          <RefreshCw className={`w-3.5 h-3.5 shrink-0 ${regenerating ? 'animate-spin' : ''}`} />
          <span>{regenerating ? 'Re-calculating Insights...' : 'Re-run Engine'}</span>
        </button>
      </div>

      {/* Recommendations Cards Layout */}
      <div className="space-y-5">
        {recommendations.map((rec, idx) => (
          <motion.div 
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="glass-panel p-5 rounded-2xl space-y-4 hover-scale-premium relative overflow-hidden"
          >
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
              <div className="space-y-1">
                <span className={`inline-flex px-2.5 py-1 rounded-lg text-[9px] font-bold border capitalize ${getPriorityColor(rec.priority)}`}>
                  {rec.priority} Priority Alert
                </span>
                <h3 className="text-[10px] font-bold mt-3 text-slate-400 dark:text-slate-500 uppercase tracking-wider block">Core business insight</h3>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-relaxed font-display">{rec.business_insight}</p>
              </div>
              <div className="shrink-0">
                <span className="text-[9px] text-slate-400 dark:text-slate-500 block uppercase font-bold text-left sm:text-right">Confidence</span>
                <span className="text-xs font-extrabold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 border border-blue-200/50 dark:border-blue-900/40 px-2.5 py-1.5 rounded-lg inline-block mt-1.5 shadow-sm">
                  {(rec.confidence * 100).toFixed(0)}% Match
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 border-t border-slate-100 dark:border-slate-800/80 pt-4 text-xs font-semibold">
              <div className="space-y-1">
                <h4 className="text-[9px] text-slate-400 dark:text-slate-500 uppercase tracking-wider">Root Cause Analysis</h4>
                <p className="text-slate-650 dark:text-slate-350 leading-relaxed font-medium mt-1.5">{rec.root_cause}</p>
              </div>
              <div className="space-y-1">
                <h4 className="text-[9px] text-blue-500 uppercase tracking-wider">Prescriptive Action</h4>
                <p className="text-slate-850 dark:text-white leading-relaxed mt-1.5 font-bold">{rec.recommendation}</p>
              </div>
            </div>

            {/* ROI Metrics Row */}
            <div className="border-t border-slate-100 dark:border-slate-800/80 pt-4 flex flex-wrap gap-4 text-xs font-bold">
              <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-450 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-250/30 dark:border-emerald-900/30 px-3 py-1.5 rounded-lg shadow-sm">
                <TrendingUp className="w-4 h-4 shrink-0" />
                <span>Estimated ROI: {rec.estimated_roi}%</span>
              </div>
              <div className="flex items-center space-x-2 text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-250/30 dark:border-indigo-900/30 px-3 py-1.5 rounded-lg shadow-sm">
                <Clock className="w-4 h-4 shrink-0" />
                <span>Benefit Horizon: {rec.estimated_time_to_benefit}</span>
              </div>
              <div className="flex items-center space-x-2 text-slate-500 dark:text-slate-400 bg-slate-100/50 dark:bg-slate-850/40 border border-slate-200/50 dark:border-slate-800 px-3 py-1.5 rounded-lg">
                <AlertCircle className="w-4 h-4 shrink-0 text-slate-400" />
                <span>Impact: {rec.expected_impact}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
