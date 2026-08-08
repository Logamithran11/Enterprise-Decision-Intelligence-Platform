from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class CleaningPaths:
    raw_dir: Path
    processed_dir: Path
    features_dir: Path
    reports_dir: Path

    def ensure(self) -> None:
        for path in (self.raw_dir, self.processed_dir, self.features_dir, self.reports_dir):
            path.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class CleaningSummary:
    table_name: str
    input_rows: int
    output_rows: int
    null_count_before: int
    null_count_after: int
    duplicate_rows_removed: int


class EnterpriseDataCleaner:
    """Clean and standardize synthetic enterprise source tables."""

    def __init__(self, paths: CleaningPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def _load_table(self, table_name: str) -> pd.DataFrame:
        file_path = self.paths.raw_dir / f"{table_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing raw table: {file_path}")
        return pd.read_csv(file_path)

    @staticmethod
    def _standardize_columns(frame: pd.DataFrame) -> pd.DataFrame:
        cleaned = frame.copy()
        cleaned.columns = (
            cleaned.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_", regex=False)
            .str.replace("-", "_", regex=False)
        )
        return cleaned

    @staticmethod
    def _coerce_dates(frame: pd.DataFrame, date_columns: Iterable[str]) -> pd.DataFrame:
        cleaned = frame.copy()
        for column in date_columns:
            if column in cleaned.columns:
                cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce", utc=True)
        return cleaned

    @staticmethod
    def _fill_object_columns(frame: pd.DataFrame) -> pd.DataFrame:
        cleaned = frame.copy()
        object_columns = cleaned.select_dtypes(include=["object", "string"]).columns
        for column in object_columns:
            cleaned[column] = cleaned[column].fillna("Unknown").astype(str).str.strip()
        return cleaned

    @staticmethod
    def _clip_numeric_ranges(frame: pd.DataFrame) -> pd.DataFrame:
        cleaned = frame.copy()
        for column in cleaned.select_dtypes(include=["number"]).columns:
            if column.endswith("_score"):
                cleaned[column] = cleaned[column].clip(0, 100)
            elif column.endswith("_rate"):
                cleaned[column] = cleaned[column].clip(0, 1)
            elif column.endswith("_days"):
                cleaned[column] = cleaned[column].clip(lower=0)
            elif column in {"unit_cost", "list_price", "order_amount", "budget", "revenue", "gross_margin", "opex", "ebitda", "cash_balance", "debt_balance", "inventory_value", "annual_revenue", "salary", "contract_value"}:
                cleaned[column] = cleaned[column].clip(lower=0)
        return cleaned

    @staticmethod
    def _remove_duplicates(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        deduped = frame.drop_duplicates().reset_index(drop=True)
        removed = len(frame) - len(deduped)
        return deduped, removed

    @staticmethod
    def _forward_fill_time_series(frame: pd.DataFrame, sort_column: str) -> pd.DataFrame:
        cleaned = frame.copy()
        if sort_column in cleaned.columns:
            cleaned = cleaned.sort_values(sort_column).reset_index(drop=True)
        return cleaned

    def clean_table(self, table_name: str) -> tuple[pd.DataFrame, CleaningSummary]:
        raw = self._load_table(table_name)
        input_rows = len(raw)
        null_count_before = int(raw.isna().sum().sum())

        cleaned = self._standardize_columns(raw)
        cleaned = self._coerce_dates(
            cleaned,
            date_columns=[
                "signup_date",
                "start_date",
                "end_date",
                "order_date",
                "hire_date",
                "snapshot_date",
                "operating_date",
            ],
        )
        cleaned = self._fill_object_columns(cleaned)
        cleaned = self._clip_numeric_ranges(cleaned)
        cleaned, duplicate_rows_removed = self._remove_duplicates(cleaned)

        if table_name in {"orders", "finance_monthly", "operations_daily", "inventory_snapshots"}:
            sort_column = {
                "orders": "order_date",
                "finance_monthly": "order_month",
                "operations_daily": "operating_date",
                "inventory_snapshots": "snapshot_date",
            }[table_name]
            cleaned = self._forward_fill_time_series(cleaned, sort_column)

        output_rows = len(cleaned)
        null_count_after = int(cleaned.isna().sum().sum())

        summary = CleaningSummary(
            table_name=table_name,
            input_rows=input_rows,
            output_rows=output_rows,
            null_count_before=null_count_before,
            null_count_after=null_count_after,
            duplicate_rows_removed=duplicate_rows_removed,
        )
        return cleaned, summary

    def clean_all(self, tables: Iterable[str]) -> dict[str, pd.DataFrame]:
        cleaned_tables: dict[str, pd.DataFrame] = {}
        summaries: list[CleaningSummary] = []

        for table_name in tables:
            cleaned_frame, summary = self.clean_table(table_name)
            cleaned_tables[table_name] = cleaned_frame
            summaries.append(summary)
            cleaned_frame.to_csv(self.paths.processed_dir / f"{table_name}.csv", index=False)

        summary_frame = pd.DataFrame([asdict(summary) for summary in summaries])
        summary_frame.to_csv(self.paths.reports_dir / "data_cleaning_summary.csv", index=False)
        return cleaned_tables

    def build_customer_feature_table(self, orders: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
        latest_order_date = pd.to_datetime(orders["order_date"], utc=True).max()
        order_frame = orders.copy()
        order_frame["order_date"] = pd.to_datetime(order_frame["order_date"], utc=True)

        customer_orders = order_frame.groupby("customer_id").agg(
            total_orders=("order_id", "count"),
            total_revenue=("order_amount", "sum"),
            average_order_value=("order_amount", "mean"),
            average_discount_rate=("discount_rate", "mean"),
            average_shipping_days=("shipping_days", "mean"),
            last_order_date=("order_date", "max"),
            completed_orders=("order_status", lambda values: int((values == "Completed").sum())),
            cancelled_orders=("order_status", lambda values: int((values == "Cancelled").sum())),
        )
        customer_orders["recency_days"] = (latest_order_date - pd.to_datetime(customer_orders["last_order_date"], utc=True)).dt.days
        customer_orders["completion_rate"] = customer_orders["completed_orders"] / customer_orders["total_orders"].clip(lower=1)
        customer_orders["cancellation_rate"] = customer_orders["cancelled_orders"] / customer_orders["total_orders"].clip(lower=1)

        feature_table = customers.merge(customer_orders, on="customer_id", how="left")
        feature_table["total_orders"] = feature_table["total_orders"].fillna(0).astype(int)
        feature_table["total_revenue"] = feature_table["total_revenue"].fillna(0.0)
        feature_table["average_order_value"] = feature_table["average_order_value"].fillna(0.0)
        feature_table["average_discount_rate"] = feature_table["average_discount_rate"].fillna(0.0)
        feature_table["average_shipping_days"] = feature_table["average_shipping_days"].fillna(0.0)
        feature_table["recency_days"] = feature_table["recency_days"].fillna(999).astype(int)
        feature_table["completion_rate"] = feature_table["completion_rate"].fillna(0.0)
        feature_table["cancellation_rate"] = feature_table["cancellation_rate"].fillna(0.0)

        feature_table["customer_value_score"] = (
            0.35 * feature_table["engagement_score"]
            + 0.35 * np.log1p(feature_table["total_revenue"])
            + 0.20 * feature_table["completion_rate"] * 100
            - 0.10 * feature_table["cancellation_rate"] * 100
        ).round(2)
        feature_table["churn_target"] = ((feature_table["recency_days"] > 180) | (feature_table["cancellation_rate"] > 0.12)).astype(int)

        feature_table.to_csv(self.paths.features_dir / "customer_features.csv", index=False)
        return feature_table


def load_cleaned_tables(processed_dir: Path, table_names: Iterable[str]) -> dict[str, pd.DataFrame]:
    cleaned_tables: dict[str, pd.DataFrame] = {}
    for table_name in table_names:
        file_path = processed_dir / f"{table_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing cleaned table: {file_path}")
        cleaned_tables[table_name] = pd.read_csv(file_path)
    return cleaned_tables
