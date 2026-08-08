from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.features.feature_engineering import EnterpriseFeatureEngineer, FeatureEngineeringPaths
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


def _prepare_clean_tables(tmp_path: Path) -> tuple[Path, Path, Path]:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    features_dir = tmp_path / "features"
    reports_dir = tmp_path / "reports"

    generate_synthetic_enterprise_dataset(
        raw_dir,
        SyntheticDatasetConfig(
            seed=77,
            num_customers=180,
            num_products=80,
            num_suppliers=24,
            num_employees=32,
            num_marketing_campaigns=36,
            num_orders=1_600,
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
    return processed_dir, features_dir, reports_dir


def test_feature_engineering_builds_artifacts(tmp_path: Path) -> None:
    processed_dir, features_dir, reports_dir = _prepare_clean_tables(tmp_path)

    engineer = EnterpriseFeatureEngineer(
        FeatureEngineeringPaths(
            processed_dir=processed_dir,
            features_dir=features_dir,
            reports_dir=reports_dir,
        )
    )
    feature_package = engineer.build_feature_package()

    expected_files = [
        "customer_features.csv",
        "sales_features.csv",
        "finance_features.csv",
        "marketing_features.csv",
        "inventory_features.csv",
        "employee_features.csv",
        "kpi_features.csv",
        "feature_schema.json",
        "feature_metadata.json",
        "feature_selection_report.csv",
        "feature_engineering_manifest.json",
    ]
    for filename in expected_files:
        assert (features_dir / filename).exists() or (reports_dir / filename).exists()

    assert set(feature_package) == {
        "customer_features",
        "sales_features",
        "finance_features",
        "marketing_features",
        "inventory_features",
        "employee_features",
        "kpi_features",
    }
    assert feature_package["customer_features"].shape[0] > 0
    assert "customer_activity_score" in feature_package["customer_features"].columns
    assert "order_amount_minmax_scaled" in feature_package["sales_features"].columns


def test_encoding_scaling_and_selection_helpers_work(tmp_path: Path) -> None:
    processed_dir, features_dir, reports_dir = _prepare_clean_tables(tmp_path)
    engineer = EnterpriseFeatureEngineer(
        FeatureEngineeringPaths(
            processed_dir=processed_dir,
            features_dir=features_dir,
            reports_dir=reports_dir,
        )
    )

    sample = pd.DataFrame(
        {
            "category": ["A", "B", "A", "C"],
            "segment": ["X", "Y", "X", "Z"],
            "value": [10.0, 20.0, 30.0, 40.0],
            "target": [0, 1, 0, 1],
        }
    )
    encoded = engineer.one_hot_encode(sample, ["category"])
    encoded = engineer.frequency_encode(encoded, ["segment"])
    encoded = engineer.target_encode(encoded, ["segment"], "target")
    encoded = engineer.scale_features(encoded, ["value"], method="standard")
    filtered, removed = engineer.correlation_filter(encoded)
    selected_mi = engineer.mutual_information_select(encoded[["value"]], encoded["target"], top_k=1)
    selected_rfe = engineer.rfe_select(encoded[["value"]], encoded["target"], top_k=1)
    selected_tree = engineer.tree_feature_importance_select(encoded[["value"]], encoded["target"], top_k=1)

    assert "category_A" in encoded.columns
    assert "segment_frequency" in encoded.columns
    assert "segment_target_encoded" in encoded.columns
    assert "value_standard_scaled" in encoded.columns
    assert isinstance(filtered, pd.DataFrame)
    assert isinstance(removed, list)
    assert selected_mi == ["value"]
    assert selected_rfe == ["value"]
    assert selected_tree == ["value"]
