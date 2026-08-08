from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd

from app.ml.model_registry import ModelRegistry

class ModelEvaluationService:
    """Consolidate training results and generate a model evaluation leaderboard."""

    def __init__(self, trained_models_dir: Path, reports_dir: Path) -> None:
        self.registry = ModelRegistry(trained_models_dir)
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_leaderboard(self) -> dict[str, Any]:
        models = self.registry.list_models()
        
        regression_entries = []
        classification_entries = []
        
        for model in models:
            metrics = model.metrics
            entry = {
                "name": model.name,
                "algorithm": model.model_type,
                "trained_at": model.trained_at,
                "description": model.description,
                **metrics
            }
            # Heuristic to separate regression from classification
            if "mae" in metrics or "rmse" in metrics or "r2" in metrics:
                regression_entries.append(entry)
            else:
                classification_entries.append(entry)
                
        reg_df = pd.DataFrame(regression_entries)
        clf_df = pd.DataFrame(classification_entries)
        
        # Sort regressors by MAE, classifiers by F1
        if not reg_df.empty:
            reg_df = reg_df.sort_values("mae", ascending=True).reset_index(drop=True)
        if not clf_df.empty:
            clf_df = clf_df.sort_values("f1", ascending=False).reset_index(drop=True)
            
        leaderboard_data = {
            "regression_leaderboard": reg_df.to_dict(orient="records") if not reg_df.empty else [],
            "classification_leaderboard": clf_df.to_dict(orient="records") if not clf_df.empty else []
        }
        
        # Write to JSON report
        json_path = self.reports_dir / "model_leaderboard.json"
        json_path.write_text(json.dumps(leaderboard_data, indent=2), encoding="utf-8")
        
        # Write to Markdown report
        md_content = self._format_markdown_leaderboard(reg_df, clf_df)
        md_path = self.reports_dir / "model_leaderboard.md"
        md_path.write_text(md_content, encoding="utf-8")
        
        return leaderboard_data

    def _format_markdown_leaderboard(self, reg_df: pd.DataFrame, clf_df: pd.DataFrame) -> str:
        md = "# Model Evaluation Leaderboard\n\n"
        
        md += "## Classification Models Leaderboard (Sorted by F1-Score)\n\n"
        if clf_df.empty:
            md += "*No classification models registered yet.*\n\n"
        else:
            cols = ["name", "algorithm", "accuracy", "precision", "recall", "f1", "roc_auc"]
            headers = ["Model Name", "Algorithm", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
            md += " | ".join(headers) + "\n"
            md += " | ".join(["---"] * len(headers)) + "\n"
            for _, row in clf_df.iterrows():
                row_vals = []
                for col in cols:
                    val = row.get(col, "-")
                    if isinstance(val, float):
                        row_vals.append(f"{val:.4f}")
                    else:
                        row_vals.append(str(val))
                md += " | ".join(row_vals) + "\n"
            md += "\n"
            
        md += "## Regression Models Leaderboard (Sorted by MAE)\n\n"
        if reg_df.empty:
            md += "*No regression models registered yet.*\n\n"
        else:
            cols = ["name", "algorithm", "mae", "rmse", "r2"]
            headers = ["Model Name", "Algorithm", "MAE", "RMSE", "R²"]
            md += " | ".join(headers) + "\n"
            md += " | ".join(["---"] * len(headers)) + "\n"
            for _, row in reg_df.iterrows():
                row_vals = []
                for col in cols:
                    val = row.get(col, "-")
                    if isinstance(val, float):
                        row_vals.append(f"{val:.4f}")
                    else:
                        row_vals.append(str(val))
                md += " | ".join(row_vals) + "\n"
            md += "\n"
            
        return md
