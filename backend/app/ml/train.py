from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import TimeSeriesSplit

from app.ml.evaluate import RegressionEvaluation, evaluate_regression


@dataclass(frozen=True, slots=True)
class TrainingFoldResult:
    fold: int
    mae: float
    rmse: float
    r2: float


@dataclass(frozen=True, slots=True)
class ModelTrainingSummary:
    model_name: str
    folds: list[TrainingFoldResult]
    mean_mae: float
    mean_rmse: float
    mean_r2: float
    fitted_estimator: Any


class RegressionModelTrainer:
    """Train and cross-validate regression models for enterprise forecasting."""

    def __init__(self, n_splits: int = 5, random_state: int = 42) -> None:
        self.n_splits = n_splits
        self.random_state = random_state

    def cross_validate(self, estimator: Any, features: pd.DataFrame, target: pd.Series) -> list[TrainingFoldResult]:
        tscv = TimeSeriesSplit(n_splits=min(self.n_splits, max(len(features) - 1, 2)))
        fold_results: list[TrainingFoldResult] = []
        for fold_index, (train_index, test_index) in enumerate(tscv.split(features), start=1):
            model = clone(estimator)
            X_train, X_test = features.iloc[train_index], features.iloc[test_index]
            y_train, y_test = target.iloc[train_index], target.iloc[test_index]
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            metrics = evaluate_regression(y_test, predictions)
            fold_results.append(
                TrainingFoldResult(
                    fold=fold_index,
                    mae=metrics.mae,
                    rmse=metrics.rmse,
                    r2=metrics.r2,
                )
            )
        return fold_results

    def fit(self, estimator: Any, features: pd.DataFrame, target: pd.Series) -> Any:
        model = clone(estimator)
        model.fit(features, target)
        return model

    def summarize(self, model_name: str, estimator: Any, features: pd.DataFrame, target: pd.Series) -> ModelTrainingSummary:
        folds = self.cross_validate(estimator, features, target)
        fitted_estimator = self.fit(estimator, features, target)
        mean_mae = float(np.mean([fold.mae for fold in folds]))
        mean_rmse = float(np.mean([fold.rmse for fold in folds]))
        mean_r2 = float(np.mean([fold.r2 for fold in folds]))
        return ModelTrainingSummary(
            model_name=model_name,
            folds=folds,
            mean_mae=mean_mae,
            mean_rmse=mean_rmse,
            mean_r2=mean_r2,
            fitted_estimator=fitted_estimator,
        )
