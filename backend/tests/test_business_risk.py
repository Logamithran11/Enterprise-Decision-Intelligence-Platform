from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.ml.business_risk import BusinessRiskPaths, BusinessRiskService


def test_business_risk_pipeline(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    trained_models_dir = tmp_path / "trained_models"
    reports_dir = tmp_path / "reports"
    exports_dir = tmp_path / "exports"

    # Create mock finance features
    fin_df = pd.DataFrame({
        "dscr": [1.5, 1.0, 2.0] * 2,
        "cash_balance": [100000, 10000, 200000] * 2,
        "debt_balance": [100000, 200000, 50000] * 2
    })
    fin_df.to_csv(features_dir / "finance_features.csv", index=False)

    # Create mock inventory features
    inv_df = pd.DataFrame({
        "stockout_risk": [0.1, 0.8, 0.4] * 2,
        "inventory_utilization": [0.2, 0.9, 0.4] * 2
    })
    inv_df.to_csv(features_dir / "inventory_features.csv", index=False)

    # Create mock customer features
    cus_df = pd.DataFrame({
        "customer_id": [f"CUS-{i}" for i in range(6)],
        "churn_risk_score": [20.0, 80.0, 50.0] * 2,
        "recency_days": [30, 200, 100] * 2
    })
    cus_df.to_csv(features_dir / "customer_features.csv", index=False)

    paths = BusinessRiskPaths(
        features_dir=features_dir,
        trained_models_dir=trained_models_dir,
        reports_dir=reports_dir,
        exports_dir=exports_dir
    )

    service = BusinessRiskService(paths)
    res = service.train_all()

    assert "financial_accuracy" in res
    assert "operational_accuracy" in res
    assert "customer_accuracy" in res

    report = service.generate_enterprise_risk_report()
    assert not report.empty
    assert (exports_dir / "customer_risk_predictions.csv").exists()
    assert "risk_score" in report.columns
