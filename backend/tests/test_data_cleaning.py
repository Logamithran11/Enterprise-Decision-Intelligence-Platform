from __future__ import annotations

from pathlib import Path

from app.pipelines.data_cleaning import CleaningPaths, EnterpriseDataCleaner, load_cleaned_tables
from app.pipelines.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_enterprise_dataset


def test_cleaning_pipeline_writes_processed_tables_and_features(tmp_path: Path) -> None:
    raw_dir = tmp_path / "datasets"
    processed_dir = tmp_path / "processed"
    features_dir = tmp_path / "features"
    reports_dir = tmp_path / "reports"

    generate_synthetic_enterprise_dataset(
        raw_dir,
        SyntheticDatasetConfig(
            seed=21,
            num_customers=140,
            num_products=55,
            num_suppliers=16,
            num_employees=24,
            num_marketing_campaigns=30,
            num_orders=1_200,
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
    cleaned_tables = cleaner.clean_all(
        [
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
    )

    assert (processed_dir / "customers.csv").exists()
    assert (reports_dir / "data_cleaning_summary.csv").exists()
    assert set(cleaned_tables) == {
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
    }

    loaded_tables = load_cleaned_tables(processed_dir, ["customers", "orders"])
    feature_table = cleaner.build_customer_feature_table(
        orders=loaded_tables["orders"],
        customers=loaded_tables["customers"],
    )

    assert (features_dir / "customer_features.csv").exists()
    assert "customer_value_score" in feature_table.columns
    assert "churn_target" in feature_table.columns
    assert feature_table["customer_id"].is_unique
