from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd
import optuna
from matplotlib import pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from app.ml.evaluate import regression_evaluation_frame
from app.ml.model_registry import ModelRegistry
from app.ml.predict import ModelPredictor
from app.ml.train import RegressionModelTrainer


@dataclass(frozen=True, slots=True)
class RevenueForecastingPaths:
    processed_dir: Path
    trained_models_dir: Path
    reports_dir: Path
    exports_dir: Path

    def ensure(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.trained_models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class ForecastArtifact:
    model_name: str
    path: str
    mae: float
    rmse: float
    r2: float
    description: str


class RevenueForecastingService:
    """Train, evaluate, and persist revenue forecasting models."""

    def __init__(self, paths: RevenueForecastingPaths) -> None:
        self.paths = paths
        self.paths.ensure()
        self.registry = ModelRegistry(self.paths.trained_models_dir)
        self.trainer = RegressionModelTrainer(n_splits=5, random_state=42)
        self.predictor = ModelPredictor(self.registry)

    def _load_finance_table(self) -> pd.DataFrame:
        finance_path = self.paths.processed_dir / "finance_monthly.csv"
        if not finance_path.exists():
            raise FileNotFoundError(f"Missing processed finance table: {finance_path}")
        finance = pd.read_csv(finance_path)
        finance["order_month"] = pd.to_datetime(finance["order_month"], format="mixed", errors="coerce")
        finance = finance.sort_values("order_month").reset_index(drop=True)
        return finance

    @staticmethod
    def _add_time_features(frame: pd.DataFrame) -> pd.DataFrame:
        enriched = frame.copy()
        enriched["month"] = enriched["order_month"].dt.month
        enriched["quarter"] = enriched["order_month"].dt.quarter
        enriched["year"] = enriched["order_month"].dt.year
        enriched["month_sin"] = np.sin(2 * np.pi * enriched["month"] / 12)
        enriched["month_cos"] = np.cos(2 * np.pi * enriched["month"] / 12)
        enriched["quarter_sin"] = np.sin(2 * np.pi * enriched["quarter"] / 4)
        enriched["quarter_cos"] = np.cos(2 * np.pi * enriched["quarter"] / 4)
        return enriched

    @staticmethod
    def _add_lag_and_rolling_features(frame: pd.DataFrame, value_columns: list[str], lags: tuple[int, ...] = (1, 2, 3, 6), windows: tuple[int, ...] = (3, 6)) -> pd.DataFrame:
        enriched = frame.copy().sort_values("order_month").reset_index(drop=True)
        for column in value_columns:
            if column not in enriched.columns:
                continue
            for lag in lags:
                enriched[f"{column}_lag_{lag}"] = enriched[column].shift(lag)
            for window in windows:
                enriched[f"{column}_roll_mean_{window}"] = enriched[column].shift(1).rolling(window, min_periods=1).mean()
                enriched[f"{column}_roll_std_{window}"] = enriched[column].shift(1).rolling(window, min_periods=1).std()
        return enriched

    def build_supervised_frame(self, finance: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
        frame = finance.copy()
        frame = self._add_time_features(frame)
        frame = self._add_lag_and_rolling_features(
            frame,
            ["revenue", "gross_margin", "order_count", "ebitda", "cash_balance", "debt_balance", "dscr"],
        )
        frame["revenue_growth_rate"] = frame["revenue"].pct_change().replace([np.inf, -np.inf], np.nan)
        frame["margin_rate"] = frame["gross_margin"] / frame["revenue"].replace(0, np.nan)
        frame["liquidity_ratio"] = frame["cash_balance"] / frame["debt_balance"].replace(0, np.nan)
        frame["target_revenue"] = frame["revenue"].shift(-horizon)
        frame = frame.dropna(subset=["target_revenue"]).reset_index(drop=True)
        return frame

    def _candidate_models(self) -> dict[str, Any]:
        return {
            "random_forest": RandomForestRegressor(n_estimators=250, random_state=42, max_depth=8, min_samples_leaf=2),
            "gradient_boosting": GradientBoostingRegressor(random_state=42, learning_rate=0.05, n_estimators=250, max_depth=3),
            "xgboost": XGBRegressor(
                random_state=42,
                n_estimators=300,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.9,
                colsample_bytree=0.9,
                objective="reg:squarederror",
            ),
        }

    def _feature_columns(self, frame: pd.DataFrame) -> list[str]:
        excluded = {"order_month", "target_revenue"}
        return [column for column in frame.columns if column not in excluded and pd.api.types.is_numeric_dtype(frame[column])]

    def optimize_xgboost(self, features: pd.DataFrame, target: pd.Series, n_trials: int = 12) -> dict[str, Any]:
        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 150, 450),
                "max_depth": trial.suggest_int("max_depth", 2, 6),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
                "subsample": trial.suggest_float("subsample", 0.7, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
                "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 6.0),
                "gamma": trial.suggest_float("gamma", 0.0, 1.0),
                "objective": "reg:squarederror",
                "random_state": 42,
            }
            estimator = XGBRegressor(**params)
            summary = self.trainer.summarize("xgboost_trial", estimator, features, target)
            return summary.mean_mae

        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        return {"best_params": study.best_params, "best_mae": float(study.best_value)}

    def train_and_register(self, n_trials: int = 12) -> tuple[pd.DataFrame, ForecastArtifact, pd.DataFrame]:
        finance = self._load_finance_table()
        supervised = self.build_supervised_frame(finance)
        feature_columns = self._feature_columns(supervised)
        features = supervised[feature_columns].fillna(0)
        target = supervised["target_revenue"]

        comparison_rows: list[dict[str, Any]] = []
        candidate_models = self._candidate_models()

        xgb_optimization = self.optimize_xgboost(features, target, n_trials=n_trials)
        candidate_models["xgboost_optimized"] = XGBRegressor(
            **xgb_optimization["best_params"],
            objective="reg:squarederror",
            random_state=42,
        )

        training_summaries = []
        for model_name, estimator in candidate_models.items():
            summary = self.trainer.summarize(model_name, estimator, features, target)
            training_summaries.append(summary)
            comparison_rows.append(
                {
                    "model_name": model_name,
                    "mae": summary.mean_mae,
                    "rmse": summary.mean_rmse,
                    "r2": summary.mean_r2,
                }
            )

        comparison_frame = regression_evaluation_frame(comparison_rows)
        comparison_path = self.paths.reports_dir / "revenue_model_comparison.csv"
        comparison_frame.to_csv(comparison_path, index=False)

        best_row = comparison_frame.iloc[0]
        best_summary = next(summary for summary in training_summaries if summary.model_name == best_row["model_name"])
        registered_model = self.registry.register_model(
            name="revenue_forecast_model",
            model=best_summary.fitted_estimator,
            metrics={"mae": float(best_row["mae"]), "rmse": float(best_row["rmse"]), "r2": float(best_row["r2"])},
            feature_names=feature_columns,
            model_type=best_summary.model_name,
            description="Revenue forecast model trained on monthly enterprise finance features.",
        )

        latest_features = features.iloc[[-1]]
        next_month_prediction = self.predictor.predict("revenue_forecast_model", latest_features).predictions[0]
        forecast_frame = pd.DataFrame(
            {
                "forecast_month": [str(finance.iloc[-1]["order_month"])],
                "predicted_next_month_revenue": [float(next_month_prediction)],
                "actual_current_month_revenue": [float(finance.iloc[-1]["revenue"])],
                "model_name": [registered_model.model_type],
            }
        )
        forecast_path = self.paths.exports_dir / "revenue_forecast.csv"
        forecast_frame.to_csv(forecast_path, index=False)

        artifact = ForecastArtifact(
            model_name=registered_model.name,
            path=registered_model.model_path,
            mae=float(best_row["mae"]),
            rmse=float(best_row["rmse"]),
            r2=float(best_row["r2"]),
            description=registered_model.description,
        )

        report_payload = {
            "best_model": asdict(artifact),
            "xgb_optimization": xgb_optimization,
            "feature_count": len(feature_columns),
            "row_count": int(len(supervised)),
        }
        (self.paths.reports_dir / "revenue_forecast_summary.json").write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

        figure, ax = plt.subplots(figsize=(12, 4))
        ax.plot(finance["order_month"].astype(str), finance["revenue"], marker="o", label="Actual Revenue")
        ax.axhline(float(next_month_prediction), color="tab:red", linestyle="--", label="Forecast Next Month")
        ax.set_title("Revenue Forecast Overview")
        ax.set_xlabel("Month")
        ax.set_ylabel("Revenue")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="best")
        figure.tight_layout()
        figure.savefig(self.paths.exports_dir / "revenue_forecast_plot.png", dpi=180, bbox_inches="tight")
        plt.close(figure)

        return comparison_frame, artifact, forecast_frame
