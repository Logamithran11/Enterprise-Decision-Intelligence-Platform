from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.ml.customer_segmentation import CustomerSegmentationPaths, CustomerSegmentationService


def test_customer_segmentation_pipeline(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    trained_models_dir = tmp_path / "trained_models"
    reports_dir = tmp_path / "reports"
    exports_dir = tmp_path / "exports"

    # Create mock customer features
    df = pd.DataFrame({
        "customer_id": [f"CUS-{i:05d}" for i in range(12)],
        "annual_revenue": [100000.0, 500000.0] * 6,
        "total_revenue": [50000.0, 200000.0] * 6,
        "average_order_value": [5000.0, 15000.0] * 6,
        "customer_activity_score": [30.0, 80.0] * 6
    })
    df["annual_revenue_standard_scaled"] = (df["annual_revenue"] - df["annual_revenue"].mean()) / df["annual_revenue"].std()
    df["total_revenue_standard_scaled"] = (df["total_revenue"] - df["total_revenue"].mean()) / df["total_revenue"].std()
    df["average_order_value_standard_scaled"] = (df["average_order_value"] - df["average_order_value"].mean()) / df["average_order_value"].std()
    df["customer_activity_score_standard_scaled"] = (df["customer_activity_score"] - df["customer_activity_score"].mean()) / df["customer_activity_score"].std()
    df.to_csv(features_dir / "customer_features.csv", index=False)

    paths = CustomerSegmentationPaths(
        features_dir=features_dir,
        trained_models_dir=trained_models_dir,
        reports_dir=reports_dir,
        exports_dir=exports_dir
    )

    service = CustomerSegmentationService(paths)
    artifact, segments = service.train_and_register(n_clusters=2)

    assert (exports_dir / "customer_segments.csv").exists()
    assert (exports_dir / "customer_segments_pca_plot.png").exists()
    assert (reports_dir / "customer_persona_definitions.json").exists()
    assert artifact.silhouette >= -1.0
    assert "persona" in segments.columns
