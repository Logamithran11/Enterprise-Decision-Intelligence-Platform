import React, { useState } from 'react';
import { ShieldAlert, ShieldCheck, Activity, Settings } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../services/api';

export const RiskCenter: React.FC = () => {
  const [riskType, setRiskType] = useState('customer');
  const [scoreInputs, setScoreInputs] = useState<Record<string, number>>({
    "dscr": 1.25,
    "cash_balance": 500000.0,
    "debt_balance": 600000.0,
    "stockout_risk": 0.45,
    "inventory_utilization": 0.60,
    "churn_risk_score": 45.0,
    "recency_days": 45
  });
  
  const [assessedRisk, setAssessedRisk] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field: string, val: string) => {
    setScoreInputs(prev => ({
      ...prev,
      [field]: Number(val)
    }));
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await api.prediction.predictRisk([scoreInputs], riskType);
      const assessment = result.assessments?.[0] ?? null;
      setAssessedRisk(assessment);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate risk scoring');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (cat: string) => {
    switch (cat?.toLowerCase()) {
      case 'high': return 'text-rose-700 bg-rose-50 dark:bg-rose-950/40 dark:text-rose-450 border-rose-200 dark:border-rose-900/40';
      case 'medium': return 'text-amber-700 bg-amber-50 dark:bg-amber-950/40 dark:text-amber-450 border-amber-200/50 dark:border-amber-900/40';
      default: return 'text-emerald-700 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-450 border-emerald-200/50 dark:border-emerald-900/40';
    }
  };

  // SVG Gauge details
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const scoreOffset = assessedRisk ? circumference - (assessedRisk.risk_score / 100) * circumference : circumference;

  return (
    <div className="space-y-6">
      {error && (
        <div className="text-sm font-semibold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/25 border border-red-200 dark:border-red-900/50 p-4 rounded-xl">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Risk Type Selection & Inputs */}
        <div className="glass-panel p-5 rounded-2xl hover-scale-premium flex flex-col justify-between">
          <div className="space-y-5">
            <div className="pb-3 border-b border-slate-100 dark:border-slate-800">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center space-x-2">
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Risk Profiler Settings</span>
              </h4>
              <p className="text-[10px] text-slate-400 mt-0.5 font-medium">Select evaluation matrix parameters</p>
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Evaluation Domain</label>
              <select
                value={riskType}
                onChange={(e) => setRiskType(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold focus:outline-none focus:border-blue-500 transition-colors capitalize text-slate-850 dark:text-slate-200"
              >
                <option value="customer">Customer Attrition Risk</option>
                <option value="financial">Financial Solvency Risk</option>
                <option value="operational">Operational Stockout Risk</option>
              </select>
            </div>

            <div className="space-y-3.5 pt-1">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Simulation Inputs</h4>
              
              {riskType === 'customer' && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500">Churn Risk Score (0-100)</label>
                    <input
                      type="number"
                      value={scoreInputs.churn_risk_score}
                      onChange={(e) => handleInputChange('churn_risk_score', e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500">Days Since Last Order</label>
                    <input
                      type="number"
                      value={scoreInputs.recency_days}
                      onChange={(e) => handleInputChange('recency_days', e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    />
                  </div>
                </div>
              )}

              {riskType === 'financial' && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500">DSCR (Coverage Ratio)</label>
                    <input
                      type="number"
                      step="0.05"
                      value={scoreInputs.dscr}
                      onChange={(e) => handleInputChange('dscr', e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500">Cash Reserves ($)</label>
                    <input
                      type="number"
                      value={scoreInputs.cash_balance}
                      onChange={(e) => handleInputChange('cash_balance', e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500">Debt Reserves ($)</label>
                    <input
                      type="number"
                      value={scoreInputs.debt_balance}
                      onChange={(e) => handleInputChange('debt_balance', e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    />
                  </div>
                </div>
              )}

              {riskType === 'operational' && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500">Stockout Risk Probability (0-1)</label>
                    <input
                      type="number"
                      step="0.05"
                      value={scoreInputs.stockout_risk}
                      onChange={(e) => handleInputChange('stockout_risk', e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-500">Inventory Utilization Ratio (0-1)</label>
                    <input
                      type="number"
                      step="0.05"
                      value={scoreInputs.inventory_utilization}
                      onChange={(e) => handleInputChange('inventory_utilization', e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleEvaluate}
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold p-3.5 rounded-xl text-xs transition-all shadow-md shadow-blue-500/10 active:scale-[0.98] cursor-pointer mt-6"
          >
            <Activity className="w-3.5 h-3.5 fill-white shrink-0 animate-pulse" />
            <span>{loading ? 'Analyzing Vector...' : 'Evaluate Risk Score'}</span>
          </button>
        </div>

        {/* Prediction Outputs */}
        <div className="glass-panel p-5 rounded-2xl lg:col-span-2 hover-scale-premium flex flex-col justify-between">
          <div>
            <div className="pb-3 border-b border-slate-100 dark:border-slate-800 mb-6">
              <h4 className="text-sm font-bold text-slate-850 dark:text-white">Assessed Risk Metrics</h4>
              <p className="text-[10px] text-slate-400 mt-0.5">Predictive scoring output analysis</p>
            </div>
            
            <AnimatePresence mode="wait">
              {assessedRisk ? (
                <motion.div 
                  key="result"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center"
                >
                  {/* Gauge representation */}
                  <div className="flex flex-col items-center justify-center p-4 bg-slate-50/50 dark:bg-slate-900/20 border border-slate-200/40 dark:border-slate-850 rounded-2xl">
                    <div className="relative w-36 h-36 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle 
                          cx="72" cy="72" r={radius} 
                          className="stroke-slate-200 dark:stroke-slate-800 fill-none" 
                          strokeWidth="8"
                        />
                        <motion.circle 
                          cx="72" cy="72" r={radius} 
                          className="stroke-blue-600 dark:stroke-blue-500 fill-none" 
                          strokeWidth="8"
                          strokeDasharray={circumference}
                          initial={{ strokeDashoffset: circumference }}
                          animate={{ strokeDashoffset: scoreOffset }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute flex flex-col items-center justify-center">
                        <span className="text-3xl font-extrabold tracking-tight font-display text-slate-850 dark:text-white">{assessedRisk.risk_score}</span>
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Score</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-5">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block leading-none">Risk Category Classification</span>
                      <p className={`mt-2 font-bold text-xs inline-flex px-3 py-1 rounded-lg border ${getRiskColor(assessedRisk.risk_category)}`}>
                        {assessedRisk.risk_category} Risk Alert
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block leading-none">Assessment Confidence Level</span>
                      <div className="flex items-center space-x-3 mt-2">
                        <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <motion.div 
                            className="h-full bg-blue-600 dark:bg-blue-500 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${assessedRisk.risk_confidence * 100}%` }}
                            transition={{ duration: 0.8, delay: 0.2 }}
                          />
                        </div>
                        <span className="font-extrabold text-xs text-blue-600 dark:text-blue-400">
                          {(assessedRisk.risk_confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div 
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-20 text-slate-450 flex flex-col items-center justify-center space-y-3"
                >
                  <div className="p-4 bg-slate-100 dark:bg-slate-900 rounded-2xl">
                    <ShieldAlert className="w-8 h-8 text-slate-400" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-700 dark:text-slate-300">Evaluate Risk Profile</p>
                    <p className="text-[10px] text-slate-400 mt-1">Configure inputs and trigger mathematical evaluations above.</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800 pt-5 mt-6 flex items-start space-x-3 text-xs text-slate-400">
            <ShieldCheck className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 animate-pulse" />
            <p className="text-[10px] font-medium leading-normal">
              Evaluated outcomes are registered dynamically with downstream prescriptive engines. Recommended action parameters are derived instantly.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
};
