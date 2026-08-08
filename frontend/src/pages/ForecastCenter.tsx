import React, { useEffect, useState } from 'react';
import { Play, Info, BarChart, Settings as SettingsIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../services/api';
import type { ModelMetadata } from '../types';

export const ForecastCenter: React.FC = () => {
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [selectedModel, setSelectedModel] = useState('revenue_forecast_model');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Local Predict Inputs
  const [featureInputs, setFeatureInputs] = useState<Record<string, number>>({});
  const [predictedValue, setPredictedValue] = useState<number | null>(null);
  const [shapExplanations, setShapExplanations] = useState<any[]>([]);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    async function loadModels() {
      try {
        const data = await api.admin.getModels();
        setModels(data);
        // Pre-fill features inputs
        const current = data.find(m => m.name === selectedModel);
        if (current) {
          const initial: Record<string, number> = {};
          current.feature_names.slice(0, 8).forEach(f => {
            initial[f] = 0.5; // defaults
          });
          setFeatureInputs(initial);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load model registry metadata');
      } finally {
        setLoading(false);
      }
    }
    loadModels();
  }, [selectedModel]);

  const handleInputChange = (feat: string, val: string) => {
    setFeatureInputs(prev => ({
      ...prev,
      [feat]: Number(val)
    }));
  };

  const handlePredict = async () => {
    setPredicting(true);
    setError('');
    try {
      let result;
      if (selectedModel === 'revenue_forecast_model') {
        result = await api.prediction.predictRevenue([featureInputs]);
      } else if (selectedModel === 'demand_forecast_model') {
        result = await api.prediction.predictDemand([featureInputs]);
      } else {
        result = await api.prediction.predictChurn([featureInputs]);
      }
      
      const pred = result.predictions?.[0] ?? null;
      setPredictedValue(pred);

      const shapResult = await api.explainability.getLocal(featureInputs, selectedModel);
      setShapExplanations(shapResult.features || []);
    } catch (err: any) {
      setError(err.message || 'Error running forecast inference');
    } finally {
      setPredicting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Loading Model Registry...</p>
      </div>
    );
  }

  const currentModel = models.find(m => m.name === selectedModel);

  return (
    <div className="space-y-6">
      {error && (
        <div className="text-sm font-semibold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/25 border border-red-200 dark:border-red-900/50 p-4 rounded-xl flex items-center space-x-2">
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Model Selection and Details */}
        <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between hover-scale-premium">
          <div className="space-y-5">
            <div className="pb-3 border-b border-slate-100 dark:border-slate-800">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center space-x-2">
                <SettingsIcon className="w-4 h-4 text-slate-400" />
                <span>Model Selection</span>
              </h4>
              <p className="text-[10px] text-slate-400 mt-0.5">Toggle targeted registered estimators</p>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Target Model</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold focus:outline-none focus:border-blue-500 transition-colors capitalize text-slate-800 dark:text-slate-200"
              >
                {models.map(m => (
                  <option key={m.name} value={m.name}>{m.name.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>

            {currentModel && (
              <div className="space-y-4 pt-2 text-xs">
                <div className="flex justify-between items-center py-2 border-b border-slate-100/50 dark:border-slate-900/40">
                  <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px]">Model Type</span>
                  <span className="font-bold text-slate-700 dark:text-slate-350 capitalize bg-slate-100 dark:bg-slate-850 px-2 py-0.5 rounded-md">
                    {currentModel.model_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-100/50 dark:border-slate-900/40">
                  <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px]">Registered At</span>
                  <span className="font-semibold text-slate-600 dark:text-slate-400">
                    {new Date(currentModel.trained_at).toLocaleDateString()}
                  </span>
                </div>
                
                <div className="space-y-2">
                  <span className="font-bold text-slate-400 uppercase tracking-wider text-[9px] block">Performance Metrics</span>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(currentModel.metrics).map(([k, v]) => (
                      <div key={k} className="bg-slate-50 dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 p-2.5 rounded-xl text-center">
                        <span className="text-[9px] text-slate-400 uppercase font-bold block">{k}</span>
                        <p className="font-extrabold text-sm text-blue-600 dark:text-blue-400 mt-0.5">{v.toFixed(4)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Prediction Form & Feature Inputs */}
        <div className="glass-panel p-5 rounded-2xl lg:col-span-2 hover-scale-premium flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3 mb-5">
              <div>
                <h4 className="text-sm font-bold text-slate-850 dark:text-white">Forecast Input Vector Simulation</h4>
                <p className="text-[10px] text-slate-400 mt-0.5">Customize specific inference boundaries</p>
              </div>
              {currentModel && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-900/60">
                  {currentModel.feature_names.length} Dimensions
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {Object.keys(featureInputs).map(feat => (
                <div key={feat} className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider truncate block" title={feat}>{feat}</label>
                  <input
                    type="number"
                    value={featureInputs[feat]}
                    onChange={(e) => handleInputChange(feat, e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs focus:outline-none focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 transition-all font-semibold"
                  />
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={predicting}
            className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold p-3.5 rounded-xl text-xs transition-all shadow-md shadow-blue-500/10 active:scale-[0.98] cursor-pointer mt-6"
          >
            <Play className="w-3.5 h-3.5 fill-white shrink-0" />
            <span>{predicting ? 'Executing Model Inference...' : 'Run Simulation Forecast'}</span>
          </button>
        </div>
      </div>

      {/* Prediction Output & Explainability */}
      <AnimatePresence>
        {predictedValue !== null && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 15 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-6"
          >
            {/* Prediction Metric Card */}
            <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between hover-scale-premium relative overflow-hidden">
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/10 dark:bg-blue-500/5 rounded-full blur-2xl pointer-events-none" />
              
              <div>
                <div className="pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Model Output Inferences</span>
                </div>
                <div className="mt-4">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block leading-none">Simulation prediction</span>
                  <h3 className="text-3xl font-extrabold text-blue-600 dark:text-blue-450 mt-3 font-display tracking-tight">
                    {typeof predictedValue === 'number' && predictedValue > 1 ? `$${predictedValue.toLocaleString(undefined, {maximumFractionDigits: 2})}` : predictedValue}
                  </h3>
                </div>
              </div>

              <div className="border-t border-slate-100 dark:border-slate-800 pt-4 mt-6 flex space-x-2.5 text-xs text-slate-400">
                <Info className="w-4.5 h-4.5 text-slate-400 shrink-0" />
                <p className="text-[10px] leading-normal font-medium">Predictive probabilities calculated dynamically. Output validated for covariance drift.</p>
              </div>
            </div>

            {/* Local SHAP water falls preview */}
            <div className="glass-panel p-5 rounded-2xl lg:col-span-2 hover-scale-premium">
              <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100 dark:border-slate-800 mb-5">
                <BarChart className="w-4.5 h-4.5 text-slate-400" />
                <div>
                  <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Local Feature Impact (SHAP Values)</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">Individual variable attribution towards model output</p>
                </div>
              </div>
              
              <div className="space-y-3.5 max-h-64 overflow-y-auto pr-1">
                {shapExplanations.map((shapItem, idx) => {
                  const isPositive = shapItem.shap_value >= 0;
                  // Compute a simple percentage-based width limit for positive/negative visual indicators
                  const barWidth = Math.min(Math.abs(shapItem.shap_value) * 150, 100);
                  
                  return (
                    <div key={idx} className="space-y-1 text-xs">
                      <div className="flex justify-between items-center font-medium">
                        <span className="text-slate-700 dark:text-slate-300 truncate max-w-xs">{shapItem.feature}</span>
                        <div className="flex items-center space-x-3">
                          <span className="text-[10px] text-slate-400 font-semibold">({shapItem.actual_value.toFixed(2)})</span>
                          <span className={`font-bold text-[10px] ${
                            isPositive ? 'text-rose-500' : 'text-emerald-500'
                          }`}>
                            {isPositive ? '+' : ''}{shapItem.shap_value.toFixed(4)}
                          </span>
                        </div>
                      </div>
                      
                      {/* Premium Custom visual progress bars for positive/negative SHAP values */}
                      <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden relative">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${
                            isPositive ? 'bg-rose-500' : 'bg-emerald-500'
                          }`}
                          style={{ 
                            width: `${barWidth}%`,
                            marginLeft: isPositive ? '50%' : 'auto',
                            marginRight: !isPositive ? '50%' : 'auto'
                          }}
                        />
                        {/* Center marker */}
                        <div className="absolute left-1/2 top-0 w-0.5 h-full bg-slate-300 dark:bg-slate-600" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
