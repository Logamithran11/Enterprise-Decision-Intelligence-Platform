from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.pipelines.data_cleaning import CleaningPaths, EnterpriseDataCleaner
from app.pipelines.data_validation import EnterpriseDataValidator, ValidationPaths
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


def _prepare_processed_tables(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    features_dir = tmp_path / "features"
    reports_dir = tmp_path / "reports"

    generate_synthetic_enterprise_dataset(
        raw_dir,
        SyntheticDatasetConfig(
            seed=31,
            num_customers=160,
            num_products=70,
            num_suppliers=20,
            num_employees=28,
            num_marketing_campaigns=36,
            num_orders=1_500,
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
    return raw_dir, processed_dir, features_dir, reports_dir


def test_validator_produces_quality_report(tmp_path: Path) -> None:
    _, processed_dir, _, reports_dir = _prepare_processed_tables(tmp_path)
    validator = EnterpriseDataValidator(ValidationPaths(processed_dir=processed_dir, reports_dir=reports_dir))
    validator.EXPECTED_MIN_ROWS = {table_name: 1 for table_name in TABLES}

    report = validator.validate_all()

    assert (reports_dir / "data_validation_report.csv").exists()
    assert (reports_dir / "data_validation_summary.json").exists()
    assert report["passed"].all()
    assert validator.quality_score(report) == 100.0


def test_validator_detects_foreign_key_and_duplicate_violations(tmp_path: Path) -> None:
    _, processed_dir, _, reports_dir = _prepare_processed_tables(tmp_path)
    orders_path = processed_dir / "orders.csv"
    orders_frame = pd.read_csv(orders_path)

    duplicate_row = orders_frame.iloc[[0]].copy()
    duplicate_row["order_id"] = orders_frame.iloc[1]["order_id"]
    duplicate_row["customer_id"] = "CUS-999999"
    corrupted_orders = pd.concat([orders_frame, duplicate_row], ignore_index=True)
    corrupted_orders.to_csv(orders_path, index=False)

    validator = EnterpriseDataValidator(ValidationPaths(processed_dir=processed_dir, reports_dir=reports_dir))
    validator.EXPECTED_MIN_ROWS = {table_name: 1 for table_name in TABLES}

    report = validator.validate_all()

    failing_checks = report[report["status"] == "fail"]
    assert not failing_checks.empty
    assert any(failing_checks["check_name"].str.contains("primary_key_uniqueness"))
    assert any(failing_checks["check_name"].str.contains("foreign_key_customer_id_to_customers"))
