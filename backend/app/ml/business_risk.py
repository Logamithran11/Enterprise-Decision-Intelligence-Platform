from __future__ import annotations

import json
from dataclasses import asdict, dataclass
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.ml.model_registry import ModelRegistry
from app.ml.predict import ModelPredictor

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class BusinessRiskPaths:
    features_dir: Path
    trained_models_dir: Path
    reports_dir: Path
    exports_dir: Path

    def ensure(self) -> None:
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.trained_models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class RiskOutput:
    risk_score: float
    risk_category: str
    risk_confidence: float


class BusinessRiskService:
    """Assess and forecast financial, operational, and customer risk levels."""

    def __init__(self, paths: BusinessRiskPaths) -> None:
        self.paths = paths
        self.paths.ensure()
        self.registry = ModelRegistry(self.paths.trained_models_dir)
        self.predictor = ModelPredictor(self.registry)

    def load_features(self, name: str) -> pd.DataFrame:
        path = self.paths.features_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing feature table: {path}")
        return pd.read_csv(path)

    # 1. Financial Risk Modeling
    def train_financial_risk_model(self) -> dict[str, Any]:
        df = self.load_features("finance_features")
        
        # Define Financial Risk Targets (0=Low, 1=Medium, 2=High)
        # Check if dscr and debt metrics exist
        dscr = df["dscr"] if "dscr" in df.columns else pd.Series(2.0, index=df.index)
        cash = df["cash_balance"] if "cash_balance" in df.columns else pd.Series(1e6, index=df.index)
        debt = df["debt_balance"] if "debt_balance" in df.columns else pd.Series(1e5, index=df.index)
        
        targets = []
        for idx in df.index:
            if dscr.iloc[idx] < 1.15 or cash.iloc[idx] < 0.15 * max(debt.iloc[idx], 1):
                targets.append(2)  # High
            elif dscr.iloc[idx] < 1.5 or cash.iloc[idx] < 0.40 * max(debt.iloc[idx], 1):
                targets.append(1)  # Medium
            else:
                targets.append(0)  # Low
                
        df["financial_risk_label"] = targets
        
        # Prep features
        drop_cols = ["order_month", "financial_risk_label"]
        X = df.drop(columns=[c for c in drop_cols if c in df.columns])
        X = X.select_dtypes(include=["number"]).fillna(0)
        y = df["financial_risk_label"]
        
        clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
        clf.fit(X, y)
        
        registered = self.registry.register_model(
            name="financial_risk_model",
            model=clf,
            metrics={"accuracy": float(clf.score(X, y))},
            feature_names=list(X.columns),
            model_type="random_forest_classification",
            description="Classifier model predicting financial risk categories (Low/Medium/High)."
        )
        return {"model_name": registered.name, "accuracy": registered.metrics["accuracy"]}

    # 2. Operational Risk Modeling
    def train_operational_risk_model(self) -> dict[str, Any]:
        df = self.load_features("inventory_features")
        
        # Target based on stockout risk or utilization
        stockout = df["stockout_risk"] if "stockout_risk" in df.columns else pd.Series(0.1, index=df.index)
        utilization = df["inventory_utilization"] if "inventory_utilization" in df.columns else pd.Series(0.2, index=df.index)
        
        targets = []
        for idx in df.index:
            if stockout.iloc[idx] > 0.65 or utilization.iloc[idx] > 0.8:
                targets.append(2)
            elif stockout.iloc[idx] > 0.35 or utilization.iloc[idx] > 0.5:
                targets.append(1)
            else:
                targets.append(0)
                
        df["operational_risk_label"] = targets
        
        drop_cols = ["snapshot_date", "product_id", "warehouse_id", "operational_risk_label"]
        X = df.drop(columns=[c for c in drop_cols if c in df.columns])
        X = X.select_dtypes(include=["number"]).fillna(0)
        y = df["operational_risk_label"]
        
        clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
        clf.fit(X, y)
        
        registered = self.registry.register_model(
            name="operational_risk_model",
            model=clf,
            metrics={"accuracy": float(clf.score(X, y))},
            feature_names=list(X.columns),
            model_type="random_forest_classification",
            description="Classifier model predicting operational stockout and warehousing risk."
        )
        return {"model_name": registered.name, "accuracy": registered.metrics["accuracy"]}

    # 3. Customer Risk Modeling
    def train_customer_risk_model(self) -> dict[str, Any]:
        df = self.load_features("customer_features")
        
        # Target based on churn risk score or tenure / recency
        churn_risk = df["churn_risk_score"] if "churn_risk_score" in df.columns else pd.Series(20.0, index=df.index)
        recency = df["recency_days"] if "recency_days" in df.columns else pd.Series(30.0, index=df.index)
        
        targets = []
        for idx in df.index:
            if churn_risk.iloc[idx] > 70 or recency.iloc[idx] > 180:
                targets.append(2)
            elif churn_risk.iloc[idx] > 40 or recency.iloc[idx] > 90:
                targets.append(1)
            else:
                targets.append(0)
                
        df["customer_risk_label"] = targets
        
        drop_cols = [
            "customer_id", "customer_name", "signup_date", "last_order_date",
            "first_order_date", "recent_last_order", "customer_risk_label"
        ]
        X = df.drop(columns=[c for c in drop_cols if c in df.columns])
        X = X.select_dtypes(include=["number"]).fillna(0)
        y = df["customer_risk_label"]
        
        clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
        clf.fit(X, y)
        
        registered = self.registry.register_model(
            name="customer_risk_model",
            model=clf,
            metrics={"accuracy": float(clf.score(X, y))},
            feature_names=list(X.columns),
            model_type="random_forest_classification",
            description="Classifier model predicting customer attrition and relationship risk."
        )
        return {"model_name": registered.name, "accuracy": registered.metrics["accuracy"]}

    def train_all(self) -> dict[str, float]:
        fin_res = self.train_financial_risk_model()
        ops_res = self.train_operational_risk_model()
        cus_res = self.train_customer_risk_model()
        
        results = {
            "financial_accuracy": fin_res["accuracy"],
            "operational_accuracy": ops_res["accuracy"],
            "customer_accuracy": cus_res["accuracy"]
        }
        (self.paths.reports_dir / "business_risk_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        return results

    def predict_risk(self, model_name: str, features: pd.DataFrame) -> list[RiskOutput]:
        model = self.registry.load_trained_model(model_name)
        model_entry = self.registry.get_model(model_name)
        
        X = features.reindex(columns=model_entry.feature_names, fill_value=0)
        probabilities = model.predict_proba(X)
        
        outputs = []
        for prob in probabilities:
            # Map probabilities to a continuous score [0, 100]
            # prob is [p_low, p_medium, p_high]
            score = float(prob[1] * 50.0 + prob[2] * 100.0)
            
            # Category threshold mapping
            if score >= 70.0:
                cat = "High"
            elif score >= 35.0:
                cat = "Medium"
            else:
                cat = "Low"
                
            confidence = float(np.max(prob))
            outputs.append(RiskOutput(risk_score=round(score, 2), risk_category=cat, risk_confidence=round(confidence, 4)))
            
        return outputs

    def generate_enterprise_risk_report(self) -> pd.DataFrame:
        # Load and score all entities
        customer_df = self.load_features("customer_features")
        customer_risks = self.predict_risk("customer_risk_model", customer_df)
        
        risk_scores = [r.risk_score for r in customer_risks]
        risk_cats = [r.risk_category for r in customer_risks]
        risk_conf = [r.risk_confidence for r in customer_risks]
        
        report_df = pd.DataFrame({
            "customer_id": customer_df["customer_id"],
            "segment": customer_df["segment"] if "segment" in customer_df.columns else "Unknown",
            "region": customer_df["region"] if "region" in customer_df.columns else "Unknown",
            "risk_score": risk_scores,
            "risk_category": risk_cats,
            "confidence": risk_conf
        })
        
        report_df.to_csv(self.paths.exports_dir / "customer_risk_predictions.csv", index=False)
        return report_df
