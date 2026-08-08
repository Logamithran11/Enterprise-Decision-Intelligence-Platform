from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.ml.churn_prediction import ChurnPredictionPaths, ChurnPredictionService


def test_churn_prediction_service_runs_and_persists(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    trained_models_dir = tmp_path / "trained_models"
    reports_dir = tmp_path / "reports"
    exports_dir = tmp_path / "exports"

    # Create mock customer features dataset
    df = pd.DataFrame({
        "customer_id": [f"CUS-{i:05d}" for i in range(12)],
        "annual_revenue": [100000.0] * 12,
        "total_revenue": [50000.0] * 12,
        "average_order_value": [5000.0] * 12,
        "customer_activity_score": [50.0] * 12,
        "churn_flag": [0, 1] * 6
    })
    df["annual_revenue_standard_scaled"] = 0.0
    df["total_revenue_standard_scaled"] = 0.0
    df["average_order_value_standard_scaled"] = 0.0
    df["customer_activity_score_standard_scaled"] = 0.0
    df.to_csv(features_dir / "customer_features.csv", index=False)

    paths = ChurnPredictionPaths(
        processed_dir=tmp_path,
        features_dir=features_dir,
        trained_models_dir=trained_models_dir,
        reports_dir=reports_dir,
        exports_dir=exports_dir
    )

    service = ChurnPredictionService(paths)
    comparison, artifact, preds = service.train_and_register(n_trials=2)

    assert not comparison.empty
    assert (reports_dir / "churn_model_comparison.csv").exists()
    assert (exports_dir / "customer_churn_predictions.csv").exists()
    assert (trained_models_dir / "model_registry.json").exists()
    assert artifact.accuracy >= 0.0
    assert len(preds) == 12
