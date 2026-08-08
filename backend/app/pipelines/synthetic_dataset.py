from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class SyntheticDatasetConfig:
    seed: int = 42
    num_customers: int = 8_000
    num_products: int = 900
    num_suppliers: int = 160
    num_employees: int = 420
    num_marketing_campaigns: int = 2_400
    num_orders: int = 120_000
    num_inventory_snapshots_per_product: int = 36
    num_warehouses: int = 4
    start_date: str = "2023-01-01"
    end_date: str = "2026-08-04"
    output_subdirectories: tuple[str, ...] = ("datasets",)


CUSTOMER_SEGMENTS = ["Enterprise", "Mid-Market", "SMB"]
INDUSTRIES = [
    "Retail",
    "Manufacturing",
    "Healthcare",
    "Finance",
    "Telecom",
    "Technology",
    "Energy",
    "Logistics",
    "Education",
    "Government",
]
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
CHANNELS = ["Direct", "Partner", "Online", "Field Sales", "Account Management"]
PRODUCT_CATEGORIES = {
    "Analytics": ["Dashboards", "Reporting", "Data Modeling", "Forecasting"],
    "Automation": ["Workflow", "RPA", "Integration", "Scheduling"],
    "Security": ["IAM", "Threat Detection", "Compliance", "Risk Scoring"],
    "Operations": ["Inventory Control", "Procurement", "Maintenance", "Logistics"],
    "Finance": ["Budgeting", "Planning", "Expense Control", "Revenue Ops"],
}
SUPPLIER_TYPES = ["OEM", "Distributor", "Strategic Partner", "Regional Supplier"]
DEPARTMENTS = ["Executive", "Sales", "Finance", "Operations", "Marketing", "Customer Success", "Supply Chain", "IT"]
EMPLOYEE_LEVELS = ["Junior", "Mid", "Senior", "Lead", "Director", "VP"]
WAREHOUSES = ["WH-North", "WH-South", "WH-East", "WH-West", "WH-Central"]
MARKETING_CHANNELS = ["Search", "Social", "Email", "Events", "Partner", "Content"]


def _date_range(start_date: str, end_date: str) -> pd.DatetimeIndex:
    return pd.date_range(start=pd.Timestamp(start_date), end=pd.Timestamp(end_date), freq="D", tz="UTC")


def _safe_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _customer_id(index: int) -> str:
    return f"CUS-{index:06d}"


def _product_id(index: int) -> str:
    return f"PRD-{index:05d}"


def _supplier_id(index: int) -> str:
    return f"SUP-{index:05d}"


def _employee_id(index: int) -> str:
    return f"EMP-{index:05d}"


def _campaign_id(index: int) -> str:
    return f"MKT-{index:05d}"


def generate_customers(config: SyntheticDatasetConfig, rng: np.random.Generator) -> pd.DataFrame:
    customer_index = np.arange(1, config.num_customers + 1)
    segments = rng.choice(CUSTOMER_SEGMENTS, size=config.num_customers, p=[0.28, 0.42, 0.30])
    industries = rng.choice(INDUSTRIES, size=config.num_customers)
    regions = rng.choice(REGIONS, size=config.num_customers, p=[0.32, 0.22, 0.18, 0.16, 0.12])

    signup_dates = pd.to_datetime(config.start_date, utc=True) + pd.to_timedelta(
        rng.integers(0, 900, size=config.num_customers), unit="D"
    )
    employee_counts = rng.integers(25, 25_000, size=config.num_customers)
    annual_revenue = np.where(
        segments == "Enterprise",
        rng.integers(20_000_000, 1_000_000_000, size=config.num_customers),
        np.where(
            segments == "Mid-Market",
            rng.integers(2_500_000, 25_000_000, size=config.num_customers),
            rng.integers(250_000, 5_000_000, size=config.num_customers),
        ),
    )
    engagement_score = np.clip(
        rng.normal(loc=np.where(segments == "Enterprise", 72, np.where(segments == "Mid-Market", 58, 44)), scale=14),
        0,
        100,
    )
    customer_health_score = np.clip(
        0.45 * engagement_score + 0.35 * (annual_revenue / annual_revenue.max() * 100) + rng.normal(0, 8, config.num_customers),
        0,
        100,
    )
    churn_risk_score = np.clip(100 - customer_health_score + rng.normal(0, 7, config.num_customers), 0, 100)
    churn_flag = (churn_risk_score > 58).astype(int)

    return pd.DataFrame(
        {
            "customer_id": [_customer_id(i) for i in customer_index],
            "customer_name": [f"Customer {i:05d}" for i in customer_index],
            "segment": segments,
            "industry": industries,
            "region": regions,
            "country": [f"Country-{i % 24:02d}" for i in customer_index],
            "signup_date": signup_dates,
            "employee_count": employee_counts,
            "annual_revenue": annual_revenue,
            "engagement_score": engagement_score.round(2),
            "customer_health_score": customer_health_score.round(2),
            "churn_risk_score": churn_risk_score.round(2),
            "churn_flag": churn_flag,
        }
    )


def generate_suppliers(config: SyntheticDatasetConfig, rng: np.random.Generator) -> pd.DataFrame:
    supplier_index = np.arange(1, config.num_suppliers + 1)
    supplier_regions = rng.choice(REGIONS, size=config.num_suppliers)
    reliability_score = np.clip(rng.normal(86, 9, config.num_suppliers), 55, 99)
    lead_time_days = rng.integers(7, 46, size=config.num_suppliers)

    return pd.DataFrame(
        {
            "supplier_id": [_supplier_id(i) for i in supplier_index],
            "supplier_name": [f"Supplier {i:04d}" for i in supplier_index],
            "supplier_type": rng.choice(SUPPLIER_TYPES, size=config.num_suppliers),
            "region": supplier_regions,
            "country": [f"Supplier-Country-{i % 18:02d}" for i in supplier_index],
            "lead_time_days": lead_time_days,
            "reliability_score": reliability_score.round(2),
            "contract_value": rng.integers(150_000, 15_000_000, size=config.num_suppliers),
        }
    )


def generate_products(config: SyntheticDatasetConfig, rng: np.random.Generator, suppliers: pd.DataFrame) -> pd.DataFrame:
    product_index = np.arange(1, config.num_products + 1)
    category_names = list(PRODUCT_CATEGORIES)
    categories = rng.choice(category_names, size=config.num_products)
    subcategories = [rng.choice(PRODUCT_CATEGORIES[category]) for category in categories]
    supplier_choices = rng.choice(suppliers["supplier_id"], size=config.num_products)
    base_cost = rng.uniform(75, 18_000, size=config.num_products)
    margin_rate = rng.uniform(0.18, 0.62, size=config.num_products)
    list_price = base_cost * (1 + margin_rate)
    demand_score = np.clip(rng.normal(62, 17, config.num_products), 5, 99)

    return pd.DataFrame(
        {
            "product_id": [_product_id(i) for i in product_index],
            "product_name": [f"Product {i:04d}" for i in product_index],
            "category": categories,
            "subcategory": subcategories,
            "supplier_id": supplier_choices,
            "unit_cost": base_cost.round(2),
            "list_price": list_price.round(2),
            "margin_rate": margin_rate.round(3),
            "demand_score": demand_score.round(2),
            "lifecycle_stage": rng.choice(["Intro", "Growth", "Mature", "Decline"], size=config.num_products, p=[0.12, 0.38, 0.36, 0.14]),
            "is_active": rng.choice([0, 1], size=config.num_products, p=[0.08, 0.92]),
        }
    )


def generate_employees(config: SyntheticDatasetConfig, rng: np.random.Generator) -> pd.DataFrame:
    employee_index = np.arange(1, config.num_employees + 1)
    departments = rng.choice(DEPARTMENTS, size=config.num_employees)
    seniority = rng.choice(EMPLOYEE_LEVELS, size=config.num_employees, p=[0.18, 0.32, 0.24, 0.15, 0.08, 0.03])
    performance_score = np.clip(rng.normal(78, 11, config.num_employees), 30, 99)
    managers = [
        None if idx <= 15 else f"EMP-{rng.integers(1, min(16, idx)):05d}"
        for idx in employee_index
    ]

    return pd.DataFrame(
        {
            "employee_id": [_employee_id(i) for i in employee_index],
            "employee_name": [f"Employee {i:04d}" for i in employee_index],
            "department": departments,
            "level": seniority,
            "region": rng.choice(REGIONS, size=config.num_employees),
            "hire_date": pd.to_datetime(config.start_date, utc=True) + pd.to_timedelta(rng.integers(0, 1000, size=config.num_employees), unit="D"),
            "salary": rng.integers(48_000, 320_000, size=config.num_employees),
            "performance_score": performance_score.round(2),
            "manager_id": managers,
            "is_active": rng.choice([0, 1], size=config.num_employees, p=[0.05, 0.95]),
        }
    )


def generate_marketing_campaigns(config: SyntheticDatasetConfig, rng: np.random.Generator) -> pd.DataFrame:
    campaign_index = np.arange(1, config.num_marketing_campaigns + 1)
    start_anchor = pd.to_datetime(config.start_date, utc=True)
    campaign_starts = start_anchor + pd.to_timedelta(rng.integers(0, 1150, size=config.num_marketing_campaigns), unit="D")
    campaign_lengths = rng.integers(14, 92, size=config.num_marketing_campaigns)
    campaign_ends = campaign_starts + pd.to_timedelta(campaign_lengths, unit="D")
    budgets = rng.integers(18_000, 920_000, size=config.num_marketing_campaigns)
    target_segments = rng.choice(CUSTOMER_SEGMENTS, size=config.num_marketing_campaigns, p=[0.34, 0.41, 0.25])
    channels = rng.choice(MARKETING_CHANNELS, size=config.num_marketing_campaigns)
    conversion_rate = np.clip(rng.normal(0.042, 0.016, config.num_marketing_campaigns), 0.004, 0.13)

    leads_generated = np.maximum((budgets / rng.uniform(35, 125, size=config.num_marketing_campaigns)).astype(int), 15)
    attributed_revenue = (budgets * rng.uniform(3.2, 8.8, size=config.num_marketing_campaigns)).round(2)

    return pd.DataFrame(
        {
            "campaign_id": [_campaign_id(i) for i in campaign_index],
            "campaign_name": [f"Campaign {i:04d}" for i in campaign_index],
            "channel": channels,
            "target_segment": target_segments,
            "start_date": campaign_starts,
            "end_date": campaign_ends,
            "budget": budgets,
            "leads_generated": leads_generated,
            "conversion_rate": conversion_rate.round(4),
            "attributed_revenue": attributed_revenue,
        }
    )


def _order_propensity(customers: pd.DataFrame) -> np.ndarray:
    segment_weight = customers["segment"].map({"Enterprise": 2.2, "Mid-Market": 1.2, "SMB": 0.7}).to_numpy()
    health_component = np.clip(customers["customer_health_score"].to_numpy() / 100, 0.25, 1.0)
    revenue_component = np.clip(np.log1p(customers["annual_revenue"].to_numpy()) / 25, 0.35, 1.35)
    propensity = segment_weight * health_component * revenue_component
    return propensity / propensity.sum()


def generate_orders(
    config: SyntheticDatasetConfig,
    rng: np.random.Generator,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> pd.DataFrame:
    order_index = np.arange(1, config.num_orders + 1)
    customer_weights = _order_propensity(customers)
    customer_choices = rng.choice(customers["customer_id"], size=config.num_orders, p=customer_weights)
    customer_lookup = customers.set_index("customer_id")["signup_date"].to_dict()
    customer_segment_lookup = customers.set_index("customer_id")["segment"].to_dict()

    product_popularity = np.clip(products["demand_score"].to_numpy(), 1, None)
    product_weights = product_popularity / product_popularity.sum()
    product_choices = rng.choice(products["product_id"], size=config.num_orders, p=product_weights)
    product_lookup = products.set_index("product_id")["list_price"].to_dict()
    category_lookup = products.set_index("product_id")["category"].to_dict()

    order_dates = []
    order_amounts = []
    order_statuses = []
    discounts = np.clip(rng.normal(0.07, 0.05, config.num_orders), 0.0, 0.35)
    quantities = rng.integers(1, 18, size=config.num_orders)
    shipping_days = rng.integers(1, 21, size=config.num_orders)
    sales_channels = rng.choice(CHANNELS, size=config.num_orders, p=[0.34, 0.19, 0.16, 0.21, 0.10])
    attributed_campaigns = rng.choice(campaigns["campaign_id"], size=config.num_orders)

    for idx, customer_id in enumerate(customer_choices):
        signup_date = customer_lookup[customer_id]
        max_date = pd.Timestamp(config.end_date, tz="UTC")
        if signup_date > max_date:
            signup_date = max_date - pd.Timedelta(days=1)
        span_days = max((max_date - signup_date).days, 1)
        order_date = signup_date + pd.Timedelta(days=int(rng.integers(0, span_days + 1)))
        order_dates.append(order_date)

        unit_price = product_lookup[product_choices[idx]]
        amount = unit_price * quantities[idx] * (1 - discounts[idx])
        order_amounts.append(round(float(amount), 2))

        customer_segment = customer_segment_lookup[customer_id]
        if customer_segment == "Enterprise":
            status = rng.choice(["Completed", "Shipped", "Returned"], p=[0.80, 0.14, 0.06])
        elif customer_segment == "Mid-Market":
            status = rng.choice(["Completed", "Shipped", "Returned", "Cancelled"], p=[0.74, 0.15, 0.06, 0.05])
        else:
            status = rng.choice(["Completed", "Shipped", "Returned", "Cancelled"], p=[0.69, 0.14, 0.07, 0.10])
        order_statuses.append(status)

    orders = pd.DataFrame(
        {
            "order_id": [f"ORD-{i:07d}" for i in order_index],
            "customer_id": customer_choices,
            "product_id": product_choices,
            "campaign_id": attributed_campaigns,
            "order_date": pd.to_datetime(order_dates, utc=True),
            "sales_channel": sales_channels,
            "order_status": order_statuses,
            "quantity": quantities,
            "unit_price": [product_lookup[pid] for pid in product_choices],
            "discount_rate": discounts.round(4),
            "order_amount": order_amounts,
            "shipping_days": shipping_days,
            "category": [category_lookup[pid] for pid in product_choices],
        }
    )
    orders["gross_margin"] = (orders["order_amount"] * rng.uniform(0.22, 0.61, size=config.num_orders)).round(2)
    orders["order_month"] = orders["order_date"].dt.strftime("%Y-%m")
    return orders.sort_values("order_date").reset_index(drop=True)


def generate_inventory_snapshots(
    config: SyntheticDatasetConfig,
    rng: np.random.Generator,
    products: pd.DataFrame,
) -> pd.DataFrame:
    snapshot_dates = pd.date_range(config.start_date, config.end_date, freq="MS", tz="UTC")[-config.num_inventory_snapshots_per_product :]
    records: list[dict[str, Any]] = []

    for product_id, demand_score, base_cost in products[["product_id", "demand_score", "unit_cost"]].itertuples(index=False):
        for snapshot_date in snapshot_dates:
            for warehouse in rng.choice(WAREHOUSES, size=config.num_warehouses, replace=False):
                on_hand = int(max(rng.normal(420 + demand_score * 8, 110), 0))
                reserved = int(max(rng.normal(on_hand * 0.12, 10), 0))
                reorder_point = int(max(rng.normal(120 + demand_score * 2.4, 25), 20))
                stockout_risk = np.clip(rng.normal(0.18 + (1 - demand_score / 100) * 0.4, 0.08), 0.01, 0.98)
                records.append(
                    {
                        "snapshot_date": snapshot_date,
                        "warehouse_id": warehouse,
                        "product_id": product_id,
                        "on_hand_units": on_hand,
                        "reserved_units": min(reserved, on_hand),
                        "reorder_point": reorder_point,
                        "stockout_risk": round(float(stockout_risk), 4),
                        "inventory_value": round(float(on_hand * base_cost), 2),
                    }
                )

    return pd.DataFrame.from_records(records)


def generate_finance_snapshot(config: SyntheticDatasetConfig, rng: np.random.Generator, orders: pd.DataFrame) -> pd.DataFrame:
    monthly_revenue = orders.groupby("order_month")["order_amount"].sum().reset_index(name="revenue")
    monthly_margin = orders.groupby("order_month")["gross_margin"].sum().reset_index(name="gross_margin")
    monthly_orders = orders.groupby("order_month").size().reset_index(name="order_count")

    finance = monthly_revenue.merge(monthly_margin, on="order_month").merge(monthly_orders, on="order_month")
    finance["cogs"] = (finance["revenue"] - finance["gross_margin"]).round(2)
    finance["opex"] = (finance["revenue"] * rng.uniform(0.18, 0.34, size=len(finance))).round(2)
    finance["ebitda"] = (finance["gross_margin"] - finance["opex"]).round(2)
    finance["cash_balance"] = (2_000_000 + finance["ebitda"].cumsum() + rng.normal(0, 55_000, size=len(finance))).round(2)
    finance["debt_balance"] = (1_250_000 - np.linspace(0, 380_000, len(finance)) + rng.normal(0, 12_000, size=len(finance))).round(2)
    finance["dscr"] = np.clip(finance["ebitda"] / np.maximum(finance["opex"], 1), 0.5, 5.0).round(3)
    return finance


def generate_operations_snapshot(config: SyntheticDatasetConfig, rng: np.random.Generator) -> pd.DataFrame:
    dates = pd.date_range(config.start_date, config.end_date, freq="D", tz="UTC")
    records: list[dict[str, Any]] = []

    for warehouse in WAREHOUSES[: config.num_warehouses]:
        throughput_base = rng.uniform(820, 2_400)
        for current_date in dates:
            incidents = int(rng.poisson(0.35))
            on_time_rate = np.clip(rng.normal(0.94, 0.03) - incidents * 0.02, 0.72, 0.995)
            fulfillment_rate = np.clip(rng.normal(0.97, 0.015) - incidents * 0.01, 0.75, 0.999)
            throughput = int(max(rng.normal(throughput_base, 180), 0))
            labor_hours = round(float(throughput / rng.uniform(18, 28)), 2)
            records.append(
                {
                    "operating_date": current_date,
                    "warehouse_id": warehouse,
                    "throughput_units": throughput,
                    "on_time_delivery_rate": round(float(on_time_rate), 4),
                    "fulfillment_rate": round(float(fulfillment_rate), 4),
                    "incident_count": incidents,
                    "labor_hours": labor_hours,
                    "downtime_minutes": int(incidents * rng.integers(12, 90)),
                }
            )

    return pd.DataFrame.from_records(records)


def build_customer_kpi_dataset(customers: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    order_dates = pd.to_datetime(orders["order_date"], utc=True)
    cutoff_date = order_dates.max() - pd.Timedelta(days=180)
    recent_orders = orders[order_dates >= cutoff_date]

    recent_summary = recent_orders.groupby("customer_id").agg(
        recent_order_count=("order_id", "count"),
        recent_revenue=("order_amount", "sum"),
        recent_avg_discount=("discount_rate", "mean"),
        recent_avg_shipping_days=("shipping_days", "mean"),
        recent_last_order=("order_date", "max"),
    )
    all_summary = orders.groupby("customer_id").agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_amount", "sum"),
        total_margin=("gross_margin", "sum"),
    )
    model_df = customers.merge(all_summary, on="customer_id", how="left").merge(recent_summary, on="customer_id", how="left")
    model_df["days_since_last_order"] = (order_dates.max() - pd.to_datetime(model_df["recent_last_order"], utc=True)).dt.days
    model_df["days_since_last_order"] = model_df["days_since_last_order"].fillna(999).astype(int)
    model_df["recent_revenue"] = model_df["recent_revenue"].fillna(0.0)
    model_df["recent_order_count"] = model_df["recent_order_count"].fillna(0).astype(int)
    model_df["recent_avg_discount"] = model_df["recent_avg_discount"].fillna(0.0)
    model_df["recent_avg_shipping_days"] = model_df["recent_avg_shipping_days"].fillna(0.0)
    model_df["order_velocity"] = (model_df["total_orders"] / np.maximum(model_df["days_since_last_order"].replace(0, 1), 1)).round(4)
    model_df["revenue_90d_target"] = (model_df["recent_revenue"] * np.clip(np.random.default_rng(123).normal(1.08, 0.14, len(model_df)), 0.65, 1.45)).round(2)
    return model_df


def generate_synthetic_enterprise_dataset(
    output_dir: str | Path,
    config: SyntheticDatasetConfig | None = None,
) -> dict[str, pd.DataFrame]:
    config = config or SyntheticDatasetConfig()
    rng = np.random.default_rng(config.seed)
    output_path = _safe_directory(Path(output_dir))

    customers = generate_customers(config, rng)
    suppliers = generate_suppliers(config, rng)
    products = generate_products(config, rng, suppliers)
    employees = generate_employees(config, rng)
    campaigns = generate_marketing_campaigns(config, rng)
    orders = generate_orders(config, rng, customers, products, campaigns)
    inventory = generate_inventory_snapshots(config, rng, products)
    finance = generate_finance_snapshot(config, rng, orders)
    operations = generate_operations_snapshot(config, rng)
    customer_kpis = build_customer_kpi_dataset(customers, orders)

    datasets = {
        "customers": customers,
        "products": products,
        "suppliers": suppliers,
        "employees": employees,
        "marketing_campaigns": campaigns,
        "orders": orders,
        "inventory_snapshots": inventory,
        "finance_monthly": finance,
        "operations_daily": operations,
        "customer_kpis": customer_kpis,
    }

    for name, frame in datasets.items():
        frame.to_csv(output_path / f"{name}.csv", index=False)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": config.seed,
        "row_counts": {name: int(len(frame)) for name, frame in datasets.items()},
        "minimum_dataset_size": int(sum(len(frame) for frame in datasets.values())),
        "config": asdict(config),
    }
    (output_path / "dataset_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return datasets


if __name__ == "__main__":
    target_dir = Path(__file__).resolve().parents[3] / "datasets"
    generate_synthetic_enterprise_dataset(target_dir)
    print(f"Synthetic enterprise dataset generated in {target_dir}")
