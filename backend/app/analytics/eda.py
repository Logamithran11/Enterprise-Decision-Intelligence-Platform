from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", context="talk")


@dataclass(frozen=True, slots=True)
class EDAPaths:
    processed_dir: Path
    reports_dir: Path
    exports_dir: Path

    def ensure(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class EDAResult:
    name: str
    path: str
    rows: int
    columns: int
    description: str


class EnterpriseEDA:
    """Generate exploratory analytics and publish reusable outputs."""

    def __init__(self, paths: EDAPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def _load_table(self, table_name: str) -> pd.DataFrame:
        file_path = self.paths.processed_dir / f"{table_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing processed table: {file_path}")
        frame = pd.read_csv(file_path)
        date_columns = [
            column
            for column in frame.columns
            if column.endswith("date") or column.endswith("_date") or column.endswith("_at")
        ]
        for column in date_columns:
            try:
                frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
            except Exception:
                continue
        return frame

    @staticmethod
    def _save_figure(figure: plt.Figure, path: Path) -> None:
        figure.tight_layout()
        figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(figure)

    @staticmethod
    def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
        denominator = denominator.replace(0, np.nan)
        return numerator / denominator

    def summary_statistics(self, frame: pd.DataFrame) -> pd.DataFrame:
        numeric_summary = frame.describe(include="all").transpose().reset_index().rename(columns={"index": "column"})
        numeric_summary.to_csv(self.paths.exports_dir / "eda_summary_statistics.csv", index=False)
        return numeric_summary

    def missing_value_analysis(self, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        for table_name, frame in tables.items():
            for column_name in frame.columns:
                null_count = int(frame[column_name].isna().sum())
                records.append(
                    {
                        "table_name": table_name,
                        "column_name": column_name,
                        "missing_count": null_count,
                        "missing_pct": round(null_count / max(len(frame), 1) * 100, 4),
                    }
                )
        missing_frame = pd.DataFrame(records).sort_values(["missing_pct", "missing_count"], ascending=False)
        missing_frame.to_csv(self.paths.exports_dir / "eda_missing_values.csv", index=False)
        return missing_frame

    def correlation_analysis(self, frame: pd.DataFrame) -> pd.DataFrame:
        numeric_frame = frame.select_dtypes(include=["number"])
        if numeric_frame.empty:
            correlation_frame = pd.DataFrame()
        else:
            correlation_frame = numeric_frame.corr(numeric_only=True)
        correlation_frame.to_csv(self.paths.exports_dir / "eda_correlation_matrix.csv")
        if not correlation_frame.empty:
            figure, ax = plt.subplots(figsize=(14, 10))
            sns.heatmap(correlation_frame, cmap="coolwarm", center=0, ax=ax, linewidths=0.2)
            ax.set_title("Enterprise Metric Correlation Heatmap")
            self._save_figure(figure, self.paths.exports_dir / "eda_correlation_heatmap.png")
        return correlation_frame

    def revenue_analysis(self, orders: pd.DataFrame) -> dict[str, pd.DataFrame]:
        order_frame = orders.copy()
        order_frame["order_date"] = pd.to_datetime(order_frame["order_date"], utc=True, errors="coerce")
        order_frame["order_month"] = order_frame["order_date"].dt.strftime("%Y-%m")
        monthly_revenue = order_frame.groupby("order_month", as_index=False).agg(
            revenue=("order_amount", "sum"),
            order_count=("order_id", "count"),
            gross_margin=("gross_margin", "sum"),
        )
        monthly_revenue["average_order_value"] = self._safe_divide(monthly_revenue["revenue"], monthly_revenue["order_count"]).fillna(0.0)
        monthly_revenue.to_csv(self.paths.exports_dir / "eda_monthly_revenue.csv", index=False)

        figure, ax = plt.subplots(figsize=(14, 6))
        sns.lineplot(data=monthly_revenue, x="order_month", y="revenue", marker="o", ax=ax)
        ax.set_title("Monthly Revenue Trend")
        ax.set_xlabel("Month")
        ax.set_ylabel("Revenue")
        ax.tick_params(axis="x", rotation=45)
        self._save_figure(figure, self.paths.exports_dir / "eda_monthly_revenue_trend.png")

        return {"monthly_revenue": monthly_revenue}

    def product_analysis(self, orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
        product_summary = orders.groupby("product_id", as_index=False).agg(
            total_orders=("order_id", "count"),
            total_revenue=("order_amount", "sum"),
            average_discount_rate=("discount_rate", "mean"),
            total_margin=("gross_margin", "sum"),
        )
        product_summary = product_summary.merge(products[["product_id", "product_name", "category", "subcategory"]], on="product_id", how="left")
        product_summary["margin_rate_realized"] = self._safe_divide(product_summary["total_margin"], product_summary["total_revenue"]).fillna(0.0)
        product_summary = product_summary.sort_values("total_revenue", ascending=False)
        product_summary.to_csv(self.paths.exports_dir / "eda_product_summary.csv", index=False)

        top_products = product_summary.head(15)
        figure, ax = plt.subplots(figsize=(14, 8))
        sns.barplot(data=top_products, y="product_name", x="total_revenue", hue="category", dodge=False, ax=ax)
        ax.set_title("Top Products by Revenue")
        ax.set_xlabel("Revenue")
        ax.set_ylabel("Product")
        ax.legend(loc="lower right", frameon=True)
        self._save_figure(figure, self.paths.exports_dir / "eda_top_products.png")
        return product_summary

    def regional_analysis(self, customers: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
        regional_orders = orders.merge(customers[["customer_id", "region", "segment"]], on="customer_id", how="left")
        regional_summary = regional_orders.groupby(["region", "segment"], as_index=False).agg(
            revenue=("order_amount", "sum"),
            orders=("order_id", "count"),
            customers=("customer_id", "nunique"),
        )
        regional_summary["revenue_per_customer"] = self._safe_divide(regional_summary["revenue"], regional_summary["customers"]).fillna(0.0)
        regional_summary.to_csv(self.paths.exports_dir / "eda_regional_summary.csv", index=False)

        figure, ax = plt.subplots(figsize=(14, 6))
        sns.barplot(data=regional_summary.sort_values("revenue", ascending=False), x="region", y="revenue", hue="segment", ax=ax)
        ax.set_title("Revenue by Region and Segment")
        ax.set_xlabel("Region")
        ax.set_ylabel("Revenue")
        ax.tick_params(axis="x", rotation=20)
        self._save_figure(figure, self.paths.exports_dir / "eda_regional_revenue.png")
        return regional_summary

    def seasonal_trend_analysis(self, orders: pd.DataFrame) -> pd.DataFrame:
        seasonal_frame = orders.copy()
        seasonal_frame["order_date"] = pd.to_datetime(seasonal_frame["order_date"], utc=True, errors="coerce")
        seasonal_frame["month"] = seasonal_frame["order_date"].dt.month_name()
        seasonal_frame["quarter"] = seasonal_frame["order_date"].dt.year.astype(str) + "-Q" + seasonal_frame["order_date"].dt.quarter.astype(str)
        seasonal_summary = seasonal_frame.groupby(["quarter", "month"], as_index=False).agg(
            revenue=("order_amount", "sum"),
            orders=("order_id", "count"),
        )
        seasonal_summary.to_csv(self.paths.exports_dir / "eda_seasonal_summary.csv", index=False)
        return seasonal_summary

    def customer_segmentation_insights(self, customer_kpis: pd.DataFrame) -> pd.DataFrame:
        segmentation = customer_kpis.groupby("segment", as_index=False).agg(
            customers=("customer_id", "count"),
            revenue=("recent_revenue", "sum"),
            average_revenue=("recent_revenue", "mean"),
            average_order_velocity=("order_velocity", "mean"),
            average_revenue_target=("revenue_90d_target", "mean"),
            churn_rate=("churn_flag", "mean"),
            average_days_since_last_order=("days_since_last_order", "mean"),
        )
        segmentation["churn_rate"] = segmentation["churn_rate"].fillna(0.0)
        segmentation.to_csv(self.paths.exports_dir / "eda_customer_segmentation.csv", index=False)
        return segmentation

    def business_kpi_summary(self, finance: pd.DataFrame, operations: pd.DataFrame, customer_kpis: pd.DataFrame) -> pd.DataFrame:
        customer_value_proxy = (
            0.45 * customer_kpis["recent_revenue"].fillna(0.0)
            + 0.35 * customer_kpis["revenue_90d_target"].fillna(0.0)
            + 0.20 * customer_kpis["order_velocity"].fillna(0.0) * 100_000
        )
        kpi_summary = pd.DataFrame(
            {
                "kpi": [
                    "avg_monthly_revenue",
                    "avg_gross_margin",
                    "avg_ebitda",
                    "avg_on_time_delivery_rate",
                    "avg_fulfillment_rate",
                    "customer_churn_rate",
                    "avg_customer_value_proxy",
                ],
                "value": [
                    float(finance["revenue"].mean()),
                    float(finance["gross_margin"].mean()),
                    float(finance["ebitda"].mean()),
                    float(operations["on_time_delivery_rate"].mean()),
                    float(operations["fulfillment_rate"].mean()),
                    float(customer_kpis["churn_flag"].mean()),
                    float(customer_value_proxy.mean()),
                ],
            }
        )
        kpi_summary.to_csv(self.paths.exports_dir / "eda_business_kpi_summary.csv", index=False)
        return kpi_summary

    def _build_analysis_frame(
        self,
        customers: pd.DataFrame,
        products: pd.DataFrame,
        orders: pd.DataFrame,
        customer_kpis: pd.DataFrame,
    ) -> pd.DataFrame:
        analysis_frame = orders.merge(
            customers[["customer_id", "annual_revenue", "engagement_score", "customer_health_score", "churn_risk_score", "churn_flag", "segment", "region"]],
            on="customer_id",
            how="left",
            suffixes=("", "_customer"),
        ).merge(
            products[["product_id", "unit_cost", "list_price", "margin_rate", "demand_score", "category"]],
            on="product_id",
            how="left",
            suffixes=("", "_product"),
        ).merge(
            customer_kpis[["customer_id", "total_orders", "total_revenue", "recent_order_count", "recent_revenue", "recent_avg_discount", "recent_avg_shipping_days", "days_since_last_order", "order_velocity", "revenue_90d_target"]],
            on="customer_id",
            how="left",
            suffixes=("", "_kpi"),
        )
        return analysis_frame

    def build_eda_package(self) -> dict[str, Any]:
        tables = {
            "customers": self._load_table("customers"),
            "products": self._load_table("products"),
            "suppliers": self._load_table("suppliers"),
            "employees": self._load_table("employees"),
            "marketing_campaigns": self._load_table("marketing_campaigns"),
            "orders": self._load_table("orders"),
            "inventory_snapshots": self._load_table("inventory_snapshots"),
            "finance_monthly": self._load_table("finance_monthly"),
            "operations_daily": self._load_table("operations_daily"),
            "customer_kpis": self._load_table("customer_kpis"),
        }

        summary_statistics = self.summary_statistics(tables["orders"])
        missing_values = self.missing_value_analysis(tables)
        analysis_frame = self._build_analysis_frame(
            customers=tables["customers"],
            products=tables["products"],
            orders=tables["orders"],
            customer_kpis=tables["customer_kpis"],
        )
        correlation = self.correlation_analysis(analysis_frame)
        revenue = self.revenue_analysis(tables["orders"])
        products = self.product_analysis(tables["orders"], tables["products"])
        regions = self.regional_analysis(tables["customers"], tables["orders"])
        seasonal = self.seasonal_trend_analysis(tables["orders"])
        segmentation = self.customer_segmentation_insights(tables["customer_kpis"])
        kpi_summary = self.business_kpi_summary(tables["finance_monthly"], tables["operations_daily"], tables["customer_kpis"])

        package = {
            "summary_statistics": summary_statistics,
            "missing_values": missing_values,
            "correlation": correlation,
            "revenue": revenue,
            "products": products,
            "regions": regions,
            "seasonal": seasonal,
            "segmentation": segmentation,
            "kpi_summary": kpi_summary,
        }

        report_manifest = {
            "artifacts": [
                {"name": key, "rows": int(value.shape[0]) if isinstance(value, pd.DataFrame) else 0, "columns": int(value.shape[1]) if isinstance(value, pd.DataFrame) else 0}
                for key, value in package.items()
            ]
        }
        (self.paths.reports_dir / "eda_manifest.json").write_text(json.dumps(report_manifest, indent=2), encoding="utf-8")
        return package
