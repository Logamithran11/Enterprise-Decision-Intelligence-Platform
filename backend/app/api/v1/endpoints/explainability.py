from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RoleChecker, TokenData
from app.ml.explainability import ExplainabilityService

router = APIRouter()

project_root = Path(__file__).resolve().parents[5]
trained_models_dir = project_root / "trained_models"
exports_dir = project_root / "exports"
features_dir = project_root / "features"

all_roles = ["admin", "executive", "manager", "analyst"]


@router.get("/global", summary="Get global SHAP explanation metrics")
def get_global_explanations(
    model_name: str = "churn_prediction_model",
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> dict[str, Any]:
    try:
        service = ExplainabilityService(trained_models_dir=trained_models_dir, exports_dir=exports_dir)
        
        # Load sample dataset to compute explanations
        dataset_mapping = {
            "churn_prediction_model": "customer_features",
            "customer_risk_model": "customer_features",
            "revenue_forecast_model": "finance_features",
            "demand_forecast_model": "inventory_features"
        }
        feat_name = dataset_mapping.get(model_name, "customer_features")
        feat_path = features_dir / f"{feat_name}.csv"
        if not feat_path.exists():
            raise FileNotFoundError(f"Features file {feat_name}.csv not found for explainability.")
            
        df = pd.read_csv(feat_path)
        # Select first 100 rows to speed up global SHAP computation
        sample_df = df.head(100)
        
        return service.explain_global(model_name, sample_df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/local", summary="Get local SHAP explanation values for a specific prediction")
def get_local_explanation(
    payload: dict[str, Any],
    model_name: str = "churn_prediction_model",
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> dict[str, Any]:
    try:
        service = ExplainabilityService(trained_models_dir=trained_models_dir, exports_dir=exports_dir)
        df_inst = pd.DataFrame([payload])
        return service.explain_local(model_name, df_inst)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
