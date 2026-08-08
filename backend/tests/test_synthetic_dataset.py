from __future__ import annotations

from pathlib import Path

from app.pipelines.synthetic_dataset import (
    SyntheticDatasetConfig,
    generate_synthetic_enterprise_dataset,
)


def test_synthetic_dataset_generator_writes_expected_tables(tmp_path: Path) -> None:
    config = SyntheticDatasetConfig(
        seed=7,
        num_customers=120,
        num_products=40,
        num_suppliers=12,
        num_employees=18,
        num_marketing_campaigns=24,
        num_orders=1_000,
        num_inventory_snapshots_per_product=6,
        num_warehouses=3,
    )

    datasets = generate_synthetic_enterprise_dataset(tmp_path, config)

    assert set(datasets) == {
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
    assert len(datasets["orders"]) == 1_000
    assert len(datasets["customers"]) == 120
    assert len(datasets["inventory_snapshots"]) > 0
    assert (tmp_path / "dataset_manifest.json").exists()
    assert (tmp_path / "orders.csv").exists()


def test_customer_kpis_contains_model_features(tmp_path: Path) -> None:
    config = SyntheticDatasetConfig(
        seed=11,
        num_customers=80,
        num_products=25,
        num_suppliers=8,
        num_employees=10,
        num_marketing_campaigns=18,
        num_orders=500,
        num_inventory_snapshots_per_product=4,
        num_warehouses=2,
    )

    datasets = generate_synthetic_enterprise_dataset(tmp_path, config)
    customer_kpis = datasets["customer_kpis"]

    expected_columns = {
        "customer_id",
        "segment",
        "industry",
        "total_orders",
        "total_revenue",
        "recent_order_count",
        "days_since_last_order",
        "order_velocity",
        "revenue_90d_target",
    }

    assert expected_columns.issubset(customer_kpis.columns)
    assert customer_kpis["revenue_90d_target"].notna().all()
