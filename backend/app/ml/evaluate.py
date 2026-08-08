from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score, roc_auc_score


@dataclass(frozen=True, slots=True)
class RegressionEvaluation:
    mae: float
    rmse: float
    r2: float


@dataclass(frozen=True, slots=True)
class ClassificationEvaluation:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float


def evaluate_regression(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray) -> RegressionEvaluation:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    return RegressionEvaluation(mae=mae, rmse=rmse, r2=r2)


def evaluate_classification(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    y_pred_proba: pd.Series | np.ndarray | None = None,
) -> ClassificationEvaluation:
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, y_pred_proba if y_pred_proba is not None else y_pred))
    return ClassificationEvaluation(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
    )


def regression_evaluation_frame(results: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(results).sort_values(["mae", "rmse", "r2"], ascending=[True, True, False]).reset_index(drop=True)
