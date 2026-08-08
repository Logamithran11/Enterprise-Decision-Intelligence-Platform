from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import shap

from app.ml.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

class ExplainabilityService:
    """Implement explainable AI diagnostics utilizing SHAP (SHapley Additive exPlanations)."""

    def __init__(self, trained_models_dir: Path, exports_dir: Path) -> None:
        self.registry = ModelRegistry(trained_models_dir)
        self.exports_dir = exports_dir
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def explain_global(self, model_name: str, X: pd.DataFrame) -> dict[str, Any]:
        """Generate global SHAP explanations and save summary plot."""
        model = self.registry.load_trained_model(model_name)
        model_entry = self.registry.get_model(model_name)
        
        # Ensure correct features are used
        X_feat = X.reindex(columns=model_entry.feature_names, fill_value=0)
        
        # Determine appropriate SHAP Explainer
        explainer = shap.TreeExplainer(model)
        shap_values = explainer(X_feat)
        
        # Save summary plot
        figure, ax = plt.subplots(figsize=(10, 6))
        shap.summary_plot(shap_values.values, X_feat, show=False)
        plt.title(f"SHAP Global Explanation - {model_name}")
        figure.tight_layout()
        figure.savefig(self.exports_dir / f"{model_name}_shap_summary.png", dpi=180, bbox_inches="tight")
        plt.close(figure)
        
        # Calculate feature importances from SHAP absolute values
        # shap_values.values can be 3D for multi-class classification
        if len(shap_values.values.shape) == 3:
            # Multi-class: average absolute shap values over classes and samples
            mean_abs_shap = np.abs(shap_values.values).mean(axis=(0, 2))
        else:
            mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
            
        feature_importance = pd.DataFrame({
            "feature": model_entry.feature_names,
            "shap_importance": [float(v) for v in mean_abs_shap]
        }).sort_values("shap_importance", ascending=False).reset_index(drop=True)
        
        return {
            "model_name": model_name,
            "global_importance": feature_importance.to_dict(orient="records")
        }

    def explain_local(self, model_name: str, instance: pd.DataFrame) -> dict[str, Any]:
        """Generate local SHAP explanations (waterfall / force plot data) for a single instance."""
        model = self.registry.load_trained_model(model_name)
        model_entry = self.registry.get_model(model_name)
        
        X_inst = instance.reindex(columns=model_entry.feature_names, fill_value=0)
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer(X_inst)
        
        # For multi-class (e.g. churn or risk classification with multiple classes),
        # take the positive/highest class shap values.
        # Churn binary classification might have shap_values of shape (1, features, 2) or (1, features).
        val_shape = shap_values.values.shape
        
        # Extract base value and shap values for the first sample
        if len(val_shape) == 3:  # (samples, features, classes)
            # Binary classification or Multi-class classification
            # Typically binary classification tree explainer outputs shape (samples, features, 2) in new SHAP APIs.
            # We want class 1 (e.g., Churn or High Risk)
            class_idx = 1 if val_shape[2] == 2 else 0
            base_val = float(shap_values.base_values[0][class_idx])
            s_vals = shap_values.values[0, :, class_idx]
        elif len(val_shape) == 2:  # (samples, features)
            base_val = float(shap_values.base_values[0])
            s_vals = shap_values.values[0]
        else:
            base_val = float(shap_values.base_values)
            s_vals = shap_values.values
            
        local_df = pd.DataFrame({
            "feature": model_entry.feature_names,
            "actual_value": [float(v) for v in X_inst.iloc[0].values],
            "shap_value": [float(v) for v in s_vals]
        }).sort_values(by="shap_value", key=abs, ascending=False).reset_index(drop=True)
        
        # Save local waterfall plot
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            # Extract a mock single Explanation object for plotting
            if len(val_shape) == 3:
                exp = shap.Explanation(
                    values=shap_values.values[0, :, class_idx],
                    base_values=shap_values.base_values[0][class_idx],
                    data=X_inst.iloc[0].values,
                    feature_names=model_entry.feature_names
                )
            else:
                exp = shap.Explanation(
                    values=shap_values.values[0],
                    base_values=shap_values.base_values[0],
                    data=X_inst.iloc[0].values,
                    feature_names=model_entry.feature_names
                )
            shap.plots.waterfall(exp, max_display=10, show=False)
            plt.title(f"SHAP Local Explanation - {model_name}")
            fig.tight_layout()
            fig.savefig(self.exports_dir / f"{model_name}_shap_local_waterfall.png", dpi=180, bbox_inches="tight")
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Failed to generate local waterfall plot: {e}")
            
        return {
            "model_name": model_name,
            "base_value": base_val,
            "features": local_df.to_dict(orient="records")
        }
