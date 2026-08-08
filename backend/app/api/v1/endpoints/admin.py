from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RoleChecker, TokenData
from app.ml.drift_monitor import DriftMonitor
from app.ml.model_registry import ModelRegistry

router = APIRouter()

project_root = Path(__file__).resolve().parents[5]
features_dir = project_root / "features"
reports_dir = project_root / "reports"
trained_models_dir = project_root / "trained_models"

admin_roles = ["admin"]
management_roles = ["admin", "executive", "manager"]


@router.get("/models", summary="List all registered models and versions")
def list_registered_models(
    claims: TokenData = Depends(RoleChecker(management_roles))
) -> list[dict[str, Any]]:
    try:
        registry = ModelRegistry(trained_models_dir)
        models = registry.list_models()
        return [
            {
                "name": m.name,
                "model_path": m.model_path,
                "metrics": m.metrics,
                "feature_names": m.feature_names,
                "trained_at": m.trained_at,
                "model_type": m.model_type,
                "description": m.description
            } for m in models
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-drift", summary="Evaluate data drift for an incoming batch")
def evaluate_drift(
    payload: list[dict[str, Any]],
    dataset_name: str = "customer_features",
    claims: TokenData = Depends(RoleChecker(management_roles))
) -> dict[str, Any]:
    try:
        monitor = DriftMonitor(features_dir=features_dir, reports_dir=reports_dir)
        df = pd.DataFrame(payload)
        return monitor.check_drift(dataset_name, df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/drift-logs", summary="Fetch summary logs of historical drift checks")
def get_drift_logs(
    claims: TokenData = Depends(RoleChecker(management_roles))
) -> list[dict[str, Any]]:
    log_path = reports_dir / "drift_log.csv"
    if not log_path.exists():
        return []
    try:
        df = pd.read_csv(log_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
