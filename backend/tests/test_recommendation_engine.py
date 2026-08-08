from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.ml.recommendation_engine import BusinessRecommendationService


def test_recommendation_engine(tmp_path: Path) -> None:
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    reports_dir = tmp_path / "reports"

    # Create mock customer churn predictions
    churn_df = pd.DataFrame({
        "customer_id": ["CUS-00104"],
        "churn_probability": [0.72]
    })
    churn_df.to_csv(exports_dir / "customer_churn_predictions.csv", index=False)

    # Create mock inventory requirements
    inv_df = pd.DataFrame({
        "product_id": ["PRD-00042"],
        "category": ["Security"],
        "stockout_risk": [0.85],
        "reorder_point": [100.0]
    })
    inv_df.to_csv(exports_dir / "inventory_requirements.csv", index=False)

    # Create mock revenue forecast
    rev_df = pd.DataFrame({
        "actual_current_month_revenue": [1000000.0],
        "predicted_next_month_revenue": [900000.0]
    })
    rev_df.to_csv(exports_dir / "revenue_forecast.csv", index=False)

    service = BusinessRecommendationService(exports_dir=exports_dir, reports_dir=reports_dir)
    recs = service.generate_recommendations()

    assert len(recs) >= 3
    assert (exports_dir / "business_recommendations.json").exists()
    assert (exports_dir / "business_recommendations.csv").exists()
    assert recs[0].confidence > 0.0
    assert recs[0].estimated_roi > 0.0
