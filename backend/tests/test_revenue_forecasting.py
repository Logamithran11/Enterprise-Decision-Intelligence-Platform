from __future__ import annotations

from pathlib import Path

from app.features.feature_engineering import EnterpriseFeatureEngineer, FeatureEngineeringPaths
from app.ml.revenue_forecasting import RevenueForecastingPaths, RevenueForecastingService
from app.pipelines.data_cleaning import CleaningPaths, EnterpriseDataCleaner
from app.pipelines.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_enterprise_dataset


TABLES = [
    "customers",
    "products",
    "suppliers",
    "employees",
    "marketing_campaigns",
    "orders",
    "inventory_snapshots",
    "finance_monthly",
    "operations_daily",
    "customer_kpis",
]


def _prepare_pipeline(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    features_dir = tmp_path / "features"
    reports_dir = tmp_path / "reports"
    trained_models_dir = tmp_path / "trained_models"
    exports_dir = tmp_path / "exports"

    generate_synthetic_enterprise_dataset(
        raw_dir,
        SyntheticDatasetConfig(
            seed=103,
            num_customers=200,
            num_products=90,
            num_suppliers=28,
            num_employees=36,
            num_marketing_campaigns=40,
            num_orders=1_800,
            num_inventory_snapshots_per_product=4,
            num_warehouses=3,
        ),
    )

    cleaner = EnterpriseDataCleaner(
        CleaningPaths(
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            features_dir=features_dir,
            reports_dir=reports_dir,
        )
    )
    cleaner.clean_all(TABLES)

    engineer = EnterpriseFeatureEngineer(
        FeatureEngineeringPaths(
            processed_dir=processed_dir,
            features_dir=features_dir,
            reports_dir=reports_dir,
        )
    )
    engineer.build_feature_package()
    return processed_dir, trained_models_dir, reports_dir, exports_dir, features_dir


def test_revenue_forecasting_pipeline_trains_and_saves_artifacts(tmp_path: Path) -> None:
    processed_dir, trained_models_dir, reports_dir, exports_dir, _ = _prepare_pipeline(tmp_path)

    service = RevenueForecastingService(
        RevenueForecastingPaths(
            processed_dir=processed_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir,
        )
    )
    comparison_frame, artifact, forecast_frame = service.train_and_register(n_trials=4)

    assert not comparison_frame.empty
    assert (reports_dir / "revenue_model_comparison.csv").exists()
    assert (reports_dir / "revenue_forecast_summary.json").exists()
    assert (exports_dir / "revenue_forecast.csv").exists()
    assert (exports_dir / "revenue_forecast_plot.png").exists()
    assert (trained_models_dir / "model_registry.json").exists()
    assert artifact.mae >= 0.0
    assert forecast_frame["predicted_next_month_revenue"].iloc[0] > 0
    assert comparison_frame.iloc[0]["model_name"] in {"random_forest", "gradient_boosting", "xgboost", "xgboost_optimized"}
