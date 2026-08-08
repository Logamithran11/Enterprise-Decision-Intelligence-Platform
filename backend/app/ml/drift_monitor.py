from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class DriftMonitor:
    """Monitor incoming inference data for schema violations and distribution drift."""

    def __init__(self, features_dir: Path, reports_dir: Path) -> None:
        self.features_dir = features_dir
        self.reports_dir = reports_dir
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.schema_path = self.features_dir / "feature_schema.json"
        self.metadata_path = self.features_dir / "feature_metadata.json"

    def _load_reference_stats(self, dataset_name: str) -> pd.DataFrame | None:
        ref_path = self.features_dir / f"{dataset_name}.csv"
        if ref_path.exists():
            try:
                return pd.read_csv(ref_path)
            except Exception as e:
                logger.warning(f"Error loading reference features: {e}")
        return None

    def check_drift(self, dataset_name: str, incoming_df: pd.DataFrame) -> dict[str, Any]:
        """Compare incoming inference data against reference training distributions."""
        report = {
            "dataset_name": dataset_name,
            "timestamp": pd.Timestamp.now().isoformat(),
            "schema_valid": True,
            "drift_detected": False,
            "missing_columns": [],
            "out_of_bound_columns": {},
            "unexpected_categories": {},
            "drift_metrics": {}
        }

        # 1. Schema Check
        if self.schema_path.exists():
            try:
                schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
                if dataset_name in schema:
                    expected_cols = {col_info["column"] for col_info in schema[dataset_name]}
                    incoming_cols = set(incoming_df.columns)
                    
                    missing = list(expected_cols - incoming_cols)
                    if missing:
                        report["schema_valid"] = False
                        report["missing_columns"] = missing
            except Exception as e:
                logger.warning(f"Error parsing schema check: {e}")

        # Load reference dataset for statistics
        ref_df = self._load_reference_stats(dataset_name)
        if ref_df is None:
            return report

        # 2. Values and Drift Check
        for col in incoming_df.columns:
            if col not in ref_df.columns:
                continue

            # Numeric columns
            if pd.api.types.is_numeric_dtype(ref_df[col]):
                ref_min = float(ref_df[col].min())
                ref_max = float(ref_df[col].max())
                
                incoming_min = float(incoming_df[col].min())
                incoming_max = float(incoming_df[col].max())
                
                # Check bounds
                if incoming_min < ref_min or incoming_max > ref_max:
                    report["out_of_bound_columns"][col] = {
                        "expected_range": [ref_min, ref_max],
                        "actual_range": [incoming_min, incoming_max]
                    }

                # Run Kolmogorov-Smirnov test for distribution drift
                try:
                    from scipy.stats import ks_2samp
                    ks_stat, p_value = ks_2samp(ref_df[col].dropna(), incoming_df[col].dropna())
                    p_value = float(p_value)
                    
                    # If p-value < 0.05, we reject the null hypothesis that distributions are same
                    drift = p_value < 0.05
                    report["drift_metrics"][col] = {
                        "method": "Kolmogorov-Smirnov",
                        "stat": float(ks_stat),
                        "p_value": p_value,
                        "drift_detected": drift
                    }
                    if drift:
                        report["drift_detected"] = True
                except ImportError:
                    # Fallback to mean/std comparisons
                    ref_mean, ref_std = ref_df[col].mean(), ref_df[col].std()
                    inc_mean, inc_std = incoming_df[col].mean(), incoming_df[col].std()
                    
                    mean_diff = abs(ref_mean - inc_mean)
                    # Drift if mean deviates by more than 2 std devs
                    drift = mean_diff > (2 * ref_std) if ref_std > 0 else False
                    report["drift_metrics"][col] = {
                        "method": "Mean-deviation",
                        "ref_mean": float(ref_mean),
                        "inc_mean": float(inc_mean),
                        "drift_detected": drift
                    }
                    if drift:
                        report["drift_detected"] = True

            # Categorical columns
            else:
                ref_cats = set(ref_df[col].dropna().unique())
                incoming_cats = set(incoming_df[col].dropna().unique())
                
                unexpected = list(incoming_cats - ref_cats)
                if unexpected:
                    report["unexpected_categories"][col] = unexpected
                    report["drift_detected"] = True

        # Save drift report
        report_file = self.reports_dir / f"{dataset_name}_drift_report.json"
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        
        # Append summary to global drift log
        log_path = self.reports_dir / "drift_log.csv"
        log_row = pd.DataFrame([{
            "timestamp": report["timestamp"],
            "dataset": dataset_name,
            "schema_valid": report["schema_valid"],
            "drift_detected": report["drift_detected"],
            "num_features_checked": len(report["drift_metrics"])
        }])
        if log_path.exists():
            try:
                pd.concat([pd.read_csv(log_path), log_row], ignore_index=True).to_csv(log_path, index=False)
            except Exception:
                log_row.to_csv(log_path, index=False)
        else:
            log_row.to_csv(log_path, index=False)

        return report
