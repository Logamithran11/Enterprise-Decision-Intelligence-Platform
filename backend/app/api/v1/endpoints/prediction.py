from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RoleChecker, TokenData, get_current_user_claims
from app.ml.revenue_forecasting import RevenueForecastingPaths, RevenueForecastingService
from app.ml.churn_prediction import ChurnPredictionPaths, ChurnPredictionService
from app.ml.business_risk import BusinessRiskPaths, BusinessRiskService
from app.ml.demand_forecasting import DemandForecastingPaths, DemandForecastingService

router = APIRouter()

# Resolve paths relative to prediction.py
project_root = Path(__file__).resolve().parents[5]
processed_dir = project_root / "processed"
features_dir = project_root / "features"
trained_models_dir = project_root / "trained_models"
reports_dir = project_root / "reports"
exports_dir = project_root / "exports"

# Allowed roles: admins, executives, managers, and analysts (view-only)
all_roles = ["admin", "executive", "manager", "analyst"]
write_roles = ["admin", "executive", "manager"]


@router.post("/revenue", summary="Forecast revenue for next period")
def predict_revenue(
    payload: list[dict[str, Any]],
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> dict[str, Any]:
    try:
        paths = RevenueForecastingPaths(
            processed_dir=processed_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
        service = RevenueForecastingService(paths)
        
        df = pd.DataFrame(payload)
        # Select features based on registry feature names
        model_entry = service.registry.get_model("revenue_forecast_model")
        X = df.reindex(columns=model_entry.feature_names, fill_value=0)
        
        output = service.predictor.predict("revenue_forecast_model", X)
        return {
            "model_name": output.model_name,
            "predictions": [float(val) for val in output.predictions]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/churn", summary="Predict customer churn probability")
def predict_churn(
    payload: list[dict[str, Any]],
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> dict[str, Any]:
    try:
        paths = ChurnPredictionPaths(
            processed_dir=processed_dir,
            features_dir=features_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
        service = ChurnPredictionService(paths)
        
        df = pd.DataFrame(payload)
        model_entry = service.registry.get_model("churn_prediction_model")
        X = df.reindex(columns=model_entry.feature_names, fill_value=0)
        
        model = service.registry.load_trained_model("churn_prediction_model")
        preds = model.predict(X)
        proba = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else preds
        
        return {
            "model_name": "churn_prediction_model",
            "predictions": [int(val) for val in preds],
            "probabilities": [float(val) for val in proba]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/risk", summary="Assess business risk levels")
def predict_risk(
    payload: list[dict[str, Any]],
    risk_type: str = "customer",  # customer, financial, operational
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> dict[str, Any]:
    try:
        paths = BusinessRiskPaths(
            features_dir=features_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
        service = BusinessRiskService(paths)
        
        df = pd.DataFrame(payload)
        model_name = f"{risk_type}_risk_model"
        
        outputs = service.predict_risk(model_name, df)
        return {
            "model_name": model_name,
            "assessments": [
                {
                    "risk_score": r.risk_score,
                    "risk_category": r.risk_category,
                    "risk_confidence": r.risk_confidence
                } for r in outputs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/demand", summary="Forecast monthly product unit demand")
def predict_demand(
    payload: list[dict[str, Any]],
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> dict[str, Any]:
    try:
        paths = DemandForecastingPaths(
            processed_dir=processed_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
        service = DemandForecastingService(paths)
        
        df = pd.DataFrame(payload)
        model_entry = service.registry.get_model("demand_forecast_model")
        X = df.reindex(columns=model_entry.feature_names, fill_value=0)
        
        model = service.registry.load_trained_model("demand_forecast_model")
        preds = model.predict(X)
        
        return {
            "model_name": "demand_forecast_model",
            "predictions": [float(val) for val in preds]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
