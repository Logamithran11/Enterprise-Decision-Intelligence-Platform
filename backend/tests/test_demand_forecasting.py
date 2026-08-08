from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.ml.demand_forecasting import DemandForecastingPaths, DemandForecastingService


def test_demand_forecasting_pipeline(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    trained_models_dir = tmp_path / "trained_models"
    reports_dir = tmp_path / "reports"
    exports_dir = tmp_path / "exports"

    # Create mock orders.csv
    orders_df = pd.DataFrame({
        "order_id": [f"ORD-{i}" for i in range(12)],
        "product_id": ["PRD-01", "PRD-02"] * 6,
        "campaign_id": ["MKT-01"] * 12,
        "order_date": pd.date_range("2024-01-01", periods=12, freq="30D"),  # Generates spread across multiple months
        "quantity": [2, 5] * 6,
        "order_amount": [20.0, 50.0] * 6,
        "gross_margin": [8.0, 20.0] * 6,
        "category": ["Analytics", "Automation"] * 6
    })
    orders_df.to_csv(processed_dir / "orders.csv", index=False)

    # Create mock products.csv
    products_df = pd.DataFrame({
        "product_id": ["PRD-01", "PRD-02"],
        "product_name": ["Prod 1", "Prod 2"],
        "category": ["Analytics", "Automation"],
        "subcategory": ["Dashboards", "Workflow"],
        "supplier_id": ["SUP-01", "SUP-02"],
        "unit_cost": [10.0, 20.0],
        "list_price": [20.0, 40.0],
        "margin_rate": [0.5, 0.5],
        "demand_score": [60.0, 70.0],
        "lifecycle_stage": ["Mature", "Growth"],
        "is_active": [1, 1]
    })
    products_df.to_csv(processed_dir / "products.csv", index=False)

    # Create mock suppliers.csv
    suppliers_df = pd.DataFrame({
        "supplier_id": ["SUP-01", "SUP-02"],
        "supplier_name": ["Supplier 1", "Supplier 2"],
        "supplier_type": ["OEM", "Distributor"],
        "region": ["North America", "Europe"],
        "country": ["USA", "Germany"],
        "lead_time_days": [14, 21],
        "reliability_score": [90.0, 95.0],
        "contract_value": [500000, 1000000]
    })
    suppliers_df.to_csv(processed_dir / "suppliers.csv", index=False)

    paths = DemandForecastingPaths(
        processed_dir=processed_dir,
        trained_models_dir=trained_models_dir,
        reports_dir=reports_dir,
        exports_dir=exports_dir
    )

    service = DemandForecastingService(paths)
    comparison, artifact, output = service.train_and_register()

    assert not comparison.empty
    assert (exports_dir / "product_demand_forecasts.csv").exists()
    assert (exports_dir / "category_seasonality.csv").exists()
    assert (exports_dir / "inventory_requirements.csv").exists()
    assert artifact.mae >= 0.0
