from __future__ import annotations

import json
from dataclasses import asdict, dataclass
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc
from xgboost import XGBClassifier

from app.ml.evaluate import evaluate_classification, ClassificationEvaluation
from app.ml.model_registry import ModelRegistry
from app.ml.predict import ModelPredictor

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class ChurnPredictionPaths:
    processed_dir: Path
    features_dir: Path
    trained_models_dir: Path
    reports_dir: Path
    exports_dir: Path

    def ensure(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.trained_models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class ChurnArtifact:
    model_name: str
    path: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    description: str


class ChurnPredictionService:
    """Train, evaluate, and persist customer churn prediction models."""

    def __init__(self, paths: ChurnPredictionPaths) -> None:
        self.paths = paths
        self.paths.ensure()
        self.registry = ModelRegistry(self.paths.trained_models_dir)
        self.predictor = ModelPredictor(self.registry)

    def load_dataset(self) -> pd.DataFrame:
        features_path = self.paths.features_dir / "customer_features.csv"
        if not features_path.exists():
            raise FileNotFoundError(f"Missing customer features dataset: {features_path}")
        return pd.read_csv(features_path)

    def prepare_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str]]:
        # Target column is churn_flag
        if "churn_flag" not in df.columns:
            raise KeyError("Target column 'churn_flag' not found in customer features.")
        
        y = df["churn_flag"].astype(int)
        
        # Select features: drop identifiers, dates, target and customer_id
        cols_to_drop = [
            "customer_id", "customer_name", "signup_date", "last_order_date",
            "first_order_date", "recent_last_order", "churn_flag", "churn_target"
        ]
        X = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
        
        # Only use numeric columns for training
        numeric_cols = [col for col in X.columns if pd.api.types.is_numeric_dtype(X[col])]
        X = X[numeric_cols].fillna(0)
        
        return X, y, list(X.columns)

    def _cross_validate(self, estimator: Any, X: pd.DataFrame, y: pd.Series) -> ClassificationEvaluation:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        accuracies, precisions, recalls, f1s, roc_aucs = [], [], [], [], []
        
        for train_idx, test_idx in skf.split(X, y):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Clone and fit
            model = joblib.load(joblib.dump(estimator, "tmp.joblib")[0]) if hasattr(estimator, "fit") else estimator
            # Handle scale_pos_weight for XGBoost dynamically per fold if needed
            if isinstance(model, XGBClassifier):
                neg_count = len(y_train) - sum(y_train)
                pos_count = sum(y_train)
                model.scale_pos_weight = neg_count / max(pos_count, 1)
                
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds
            
            evals = evaluate_classification(y_test, preds, proba)
            accuracies.append(evals.accuracy)
            precisions.append(evals.precision)
            recalls.append(evals.recall)
            f1s.append(evals.f1)
            roc_aucs.append(evals.roc_auc)
            
        return ClassificationEvaluation(
            accuracy=float(np.mean(accuracies)),
            precision=float(np.mean(precisions)),
            recall=float(np.mean(recalls)),
            f1=float(np.mean(f1s)),
            roc_auc=float(np.mean(roc_aucs))
        )

    def optimize_xgboost(self, X: pd.DataFrame, y: pd.Series, n_trials: int = 10) -> dict[str, Any]:
        def objective(trial: optuna.Trial) -> float:
            neg_count = len(y) - sum(y)
            pos_count = sum(y)
            scale_pos = neg_count / max(pos_count, 1)
            
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 7),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "subsample": trial.suggest_float("subsample", 0.7, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
                "scale_pos_weight": scale_pos,
                "random_state": 42,
                "eval_metric": "logloss",
                "use_label_encoder": False
            }
            clf = XGBClassifier(**params)
            evals = self._cross_validate(clf, X, y)
            # Track trial experiments in tracking logs
            self._log_experiment("xgboost_trial", params, evals)
            return evals.f1

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        return study.best_params

    def _log_experiment(self, model_name: str, params: dict[str, Any], metrics: ClassificationEvaluation) -> None:
        log_path = self.paths.reports_dir / "experiment_tracking.csv"
        new_row = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "model_name": model_name,
            "parameters": json.dumps(params),
            "accuracy": metrics.accuracy,
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1": metrics.f1,
            "roc_auc": metrics.roc_auc
        }
        df_row = pd.DataFrame([new_row])
        if log_path.exists():
            try:
                existing = pd.read_csv(log_path)
                updated = pd.concat([existing, df_row], ignore_index=True)
                updated.to_csv(log_path, index=False)
            except Exception as e:
                logger.warning(f"Error updating experiment tracking: {e}")
                df_row.to_csv(log_path, index=False)
        else:
            df_row.to_csv(log_path, index=False)

    def train_and_register(self, n_trials: int = 10) -> tuple[pd.DataFrame, ChurnArtifact, pd.DataFrame]:
        df = self.load_dataset()
        X, y, feature_cols = self.prepare_data(df)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        neg_count = len(y_train) - sum(y_train)
        pos_count = sum(y_train)
        scale_pos = neg_count / max(pos_count, 1)

        candidate_models = {
            "random_forest": RandomForestClassifier(n_estimators=150, random_state=42, class_weight="balanced"),
            "xgboost": XGBClassifier(n_estimators=150, scale_pos_weight=scale_pos, eval_metric="logloss", random_state=42, use_label_encoder=False)
        }

        # Optimize XGBoost
        best_xgb_params = self.optimize_xgboost(X_train, y_train, n_trials=n_trials)
        candidate_models["xgboost_optimized"] = XGBClassifier(**best_xgb_params, eval_metric="logloss", random_state=42, use_label_encoder=False)

        model_evals = {}
        fitted_models = {}
        comparison_rows = []

        for name, clf in candidate_models.items():
            evals = self._cross_validate(clf, X_train, y_train)
            model_evals[name] = evals
            self._log_experiment(name, clf.get_params() if hasattr(clf, "get_params") else {}, evals)
            
            # Fit on full train split
            clf.fit(X_train, y_train)
            fitted_models[name] = clf
            
            comparison_rows.append({
                "model_name": name,
                "accuracy": evals.accuracy,
                "precision": evals.precision,
                "recall": evals.recall,
                "f1": evals.f1,
                "roc_auc": evals.roc_auc
            })

        comparison_frame = pd.DataFrame(comparison_rows).sort_values("f1", ascending=False).reset_index(drop=True)
        comparison_path = self.paths.reports_dir / "churn_model_comparison.csv"
        comparison_frame.to_csv(comparison_path, index=False)

        best_model_name = comparison_frame.iloc[0]["model_name"]
        best_model = fitted_models[best_model_name]
        best_evals = model_evals[best_model_name]

        # Evaluate on holdout test set
        test_preds = best_model.predict(X_test)
        test_proba = best_model.predict_proba(X_test)[:, 1] if hasattr(best_model, "predict_proba") else test_preds
        test_metrics = evaluate_classification(y_test, test_preds, test_proba)

        # Register best model
        registered_model = self.registry.register_model(
            name="churn_prediction_model",
            model=best_model,
            metrics={
                "accuracy": test_metrics.accuracy,
                "precision": test_metrics.precision,
                "recall": test_metrics.recall,
                "f1": test_metrics.f1,
                "roc_auc": test_metrics.roc_auc
            },
            feature_names=feature_cols,
            model_type=best_model_name,
            description="Classification model trained to predict customer churn probability."
        )

        artifact = ChurnArtifact(
            model_name=registered_model.name,
            path=registered_model.model_path,
            accuracy=test_metrics.accuracy,
            precision=test_metrics.precision,
            recall=test_metrics.recall,
            f1=test_metrics.f1,
            roc_auc=test_metrics.roc_auc,
            description=registered_model.description
        )

        # Output predictions file
        all_preds = best_model.predict(X)
        all_proba = best_model.predict_proba(X)[:, 1] if hasattr(best_model, "predict_proba") else all_preds
        predictions_df = pd.DataFrame({
            "customer_id": df["customer_id"],
            "actual_churn": y,
            "predicted_churn": all_preds,
            "churn_probability": all_proba
        })
        predictions_df.to_csv(self.paths.exports_dir / "customer_churn_predictions.csv", index=False)

        # Generate evaluation visuals
        self._generate_plots(best_model, X_test, y_test, best_model_name)

        return comparison_frame, artifact, predictions_df

    def _generate_plots(self, model: Any, X_test: pd.DataFrame, y_test: pd.Series, model_name: str) -> None:
        # ROC Curve
        test_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)
        fpr, tpr, _ = roc_curve(y_test, test_proba)
        roc_auc = auc(fpr, tpr)

        figure, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        ax1.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (area = {roc_auc:.2f})")
        ax1.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
        ax1.set_xlim([0.0, 1.0])
        ax1.set_ylim([0.0, 1.05])
        ax1.set_xlabel("False Positive Rate")
        ax1.set_ylabel("True Positive Rate")
        ax1.set_title(f"Receiver Operating Characteristic - {model_name}")
        ax1.legend(loc="lower right")

        # Confusion Matrix
        test_preds = model.predict(X_test)
        cm = confusion_matrix(y_test, test_preds)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Non-Churn", "Churn"])
        disp.plot(ax=ax2, cmap=plt.cm.Blues, values_format="d")
        ax2.set_title("Confusion Matrix")

        figure.tight_layout()
        figure.savefig(self.paths.exports_dir / "churn_evaluation_plots.png", dpi=180, bbox_inches="tight")
        plt.close(figure)

        # Feature Importance Plot
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1]
            top_k = min(15, len(importances))
            
            fig_fi, ax_fi = plt.subplots(figsize=(10, 6))
            ax_fi.barh(range(top_k), importances[indices[:top_k]][::-1], align="center")
            ax_fi.set_yticks(range(top_k))
            ax_fi.set_yticklabels([X_test.columns[i] for i in indices[:top_k]][::-1])
            ax_fi.set_xlabel("Relative Importance")
            ax_fi.set_title(f"Top 15 Feature Importances ({model_name})")
            fig_fi.tight_layout()
            fig_fi.savefig(self.paths.exports_dir / "churn_feature_importance.png", dpi=180, bbox_inches="tight")
            plt.close(fig_fi)
