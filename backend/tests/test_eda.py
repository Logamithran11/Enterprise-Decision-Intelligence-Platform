from __future__ import annotations

from pathlib import Path

from app.analytics.eda import EDAPaths, EnterpriseEDA
from app.pipelines.data_cleaning import CleaningPaths, EnterpriseDataCleaner
from app.pipelines.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_enterprise_dataset


def test_eda_builds_reports_and_exports(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    features_dir = tmp_path / "features"
    reports_dir = tmp_path / "reports"
    exports_dir = tmp_path / "exports"

    generate_synthetic_enterprise_dataset(
        raw_dir,
        SyntheticDatasetConfig(
            seed=91,
            num_customers=120,
            num_products=60,
            num_suppliers=16,
            num_employees=24,
            num_marketing_campaigns=28,
            num_orders=1_000,
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
    cleaner.clean_all(
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

    eda = EnterpriseEDA(
        EDAPaths(
            processed_dir=processed_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir,
        )
    )
    package = eda.build_eda_package()

    assert (exports_dir / "eda_summary_statistics.csv").exists()
    assert (exports_dir / "eda_missing_values.csv").exists()
    assert (exports_dir / "eda_monthly_revenue.csv").exists()
    assert (exports_dir / "eda_customer_segmentation.csv").exists()
    assert (reports_dir / "eda_manifest.json").exists()
    assert "summary_statistics" in package
    assert "missing_values" in package
    assert "correlation" in package
    assert "kpi_summary" in package
    assert package["kpi_summary"].shape[0] >= 5
