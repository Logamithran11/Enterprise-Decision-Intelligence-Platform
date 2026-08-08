from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RoleChecker, TokenData

router = APIRouter()

project_root = Path(__file__).resolve().parents[5]
processed_dir = project_root / "processed"
features_dir = project_root / "features"
exports_dir = project_root / "exports"

all_roles = ["admin", "executive", "manager", "analyst"]


@router.get("/overview", summary="Unified executive overview KPI metrics")
def get_executive_overview(
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> dict[str, Any]:
    finance_path = processed_dir / "finance_monthly.csv"
    orders_path = processed_dir / "orders.csv"
    customers_path = processed_dir / "customers.csv"
    
    # Defaults in case pipeline hasn't finished yet
    summary = {
        "total_revenue": 0.0,
        "total_orders": 0,
        "active_customers": 0,
        "average_gross_margin_rate": 0.0,
        "revenue_forecast_next_month": 0.0
    }
    
    try:
        if finance_path.exists():
            fin_df = pd.read_csv(finance_path)
            summary["total_revenue"] = float(fin_df["revenue"].sum())
            summary["total_orders"] = int(fin_df["order_count"].sum())
            summary["average_gross_margin_rate"] = float((fin_df["gross_margin"].sum() / max(fin_df["revenue"].sum(), 1)))
            
        if customers_path.exists():
            cus_df = pd.read_csv(customers_path)
            summary["active_customers"] = int(len(cus_df))

        # Check for next month forecast if exists
        forecast_path = exports_dir / "revenue_forecast.csv"
        if forecast_path.exists():
            fore_df = pd.read_csv(forecast_path)
            summary["revenue_forecast_next_month"] = float(fore_df["predicted_next_month_revenue"].iloc[-1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compiling overview statistics: {e}")
        
    return summary


@router.get("/finance", summary="Monthly finance signals")
def get_finance_analytics(
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> list[dict[str, Any]]:
    finance_path = processed_dir / "finance_monthly.csv"
    if not finance_path.exists():
        return []
    try:
        df = pd.read_csv(finance_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operations", summary="Daily operational metrics per warehouse")
def get_operations_analytics(
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> list[dict[str, Any]]:
    ops_path = processed_dir / "operations_daily.csv"
    if not ops_path.exists():
        return []
    try:
        # Group or limit dataset size to keep uvicorn memory light
        df = pd.read_csv(ops_path)
        # return last 100 entries to prevent huge transfer payloads
        return df.tail(200).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers", summary="Behavioral customer metric distributions")
def get_customer_analytics(
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> list[dict[str, Any]]:
    feat_path = features_dir / "customer_features.csv"
    if not feat_path.exists():
        return []
    try:
        df = pd.read_csv(feat_path)
        cols = [
            "customer_id", "segment", "industry", "region", 
            "annual_revenue", "engagement_score", 
            "customer_health_score", "customer_activity_score"
        ]
        return df[[c for c in cols if c in df.columns]].head(500).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
