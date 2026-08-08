"""Feature engineering module for enterprise model preparation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import json

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.feature_selection import RFE, SelectKBest, mutual_info_classif, mutual_info_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, OrdinalEncoder, RobustScaler, StandardScaler

from app.pipelines.data_cleaning import load_cleaned_tables


@dataclass(frozen=True, slots=True)
class FeatureEngineeringPaths:
    processed_dir: Path
    features_dir: Path
    reports_dir: Path

    def ensure(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class FeatureArtifact:
    name: str
    path: str
    rows: int
    columns: int
    description: str


class EnterpriseFeatureEngineer:
    """Build model-ready enterprise feature datasets and metadata artifacts."""

    def __init__(self, paths: FeatureEngineeringPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    @staticmethod
    def _parse_dates(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        parsed = frame.copy()
        for column in columns:
            if column in parsed.columns:
                parsed[column] = pd.to_datetime(parsed[column], utc=True, errors="coerce", format="mixed")
        return parsed

    @staticmethod
    def add_date_features(frame: pd.DataFrame, date_column: str, prefix: str) -> pd.DataFrame:
        if date_column not in frame.columns:
            return frame.copy()
        enriched = frame.copy()
        enriched[date_column] = pd.to_datetime(enriched[date_column], utc=True, errors="coerce")
        enriched[f"{prefix}_year"] = enriched[date_column].dt.year.fillna(0).astype(int)
        enriched[f"{prefix}_month"] = enriched[date_column].dt.month.fillna(0).astype(int)
        enriched[f"{prefix}_quarter"] = enriched[date_column].dt.quarter.fillna(0).astype(int)
        enriched[f"{prefix}_dayofweek"] = enriched[date_column].dt.dayofweek.fillna(0).astype(int)
        enriched[f"{prefix}_day"] = enriched[date_column].dt.day.fillna(0).astype(int)
        enriched[f"{prefix}_is_month_start"] = enriched[date_column].dt.is_month_start.fillna(False).astype(int)
        enriched[f"{prefix}_is_month_end"] = enriched[date_column].dt.is_month_end.fillna(False).astype(int)
        return enriched

    @staticmethod
    def add_lag_features(
        frame: pd.DataFrame,
        group_column: str,
        sort_column: str,
        numeric_columns: Iterable[str],
        lags: Iterable[int] = (1, 2, 3),
    ) -> pd.DataFrame:
        lagged = frame.copy().sort_values([group_column, sort_column]).reset_index(drop=True)
        for numeric_column in numeric_columns:
            if numeric_column not in lagged.columns:
                continue
            for lag_value in lags:
                lagged[f"{numeric_column}_lag_{lag_value}"] = lagged.groupby(group_column)[numeric_column].shift(lag_value)
        return lagged

    @staticmethod
    def add_rolling_features(
        frame: pd.DataFrame,
        group_column: str,
        sort_column: str,
        numeric_columns: Iterable[str],
        windows: Iterable[int] = (3, 5),
    ) -> pd.DataFrame:
        rolled = frame.copy().sort_values([group_column, sort_column]).reset_index(drop=True)
        for numeric_column in numeric_columns:
            if numeric_column not in rolled.columns:
                continue
            grouped = rolled.groupby(group_column)[numeric_column]
            for window_size in windows:
                rolled[f"{numeric_column}_roll_mean_{window_size}"] = grouped.transform(
                    lambda series: series.shift(1).rolling(window_size, min_periods=1).mean()
                )
                rolled[f"{numeric_column}_roll_std_{window_size}"] = grouped.transform(
                    lambda series: series.shift(1).rolling(window_size, min_periods=1).std()
                )
        return rolled

    @staticmethod
    def one_hot_encode(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        source = frame.copy()
        available_columns = [column for column in columns if column in source.columns]
        if not available_columns:
            return source
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        encoded = encoder.fit_transform(source[available_columns].fillna("Unknown"))
        encoded_columns = encoder.get_feature_names_out(available_columns)
        encoded_frame = pd.DataFrame(encoded, columns=encoded_columns, index=source.index)
        source = source.drop(columns=available_columns)
        return pd.concat([source, encoded_frame], axis=1)

    @staticmethod
    def ordinal_encode(frame: pd.DataFrame, columns: Iterable[str], categories_map: dict[str, list[str]]) -> pd.DataFrame:
        source = frame.copy()
        available_columns = [column for column in columns if column in source.columns]
        if not available_columns:
            return source
        categories = [categories_map[column] for column in available_columns]
        encoder = OrdinalEncoder(categories=categories, handle_unknown="use_encoded_value", unknown_value=-1)
        encoded = encoder.fit_transform(source[available_columns].fillna("Unknown"))
        for index, column in enumerate(available_columns):
            source[f"{column}_ordinal"] = encoded[:, index]
        return source.drop(columns=available_columns)

    @staticmethod
    def frequency_encode(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        source = frame.copy()
        for column in columns:
            if column not in source.columns:
                continue
            frequencies = source[column].value_counts(dropna=False, normalize=True)
            source[f"{column}_frequency"] = source[column].map(frequencies).fillna(0.0)
        return source

    @staticmethod
    def target_encode(frame: pd.DataFrame, columns: Iterable[str], target_column: str, smoothing: float = 10.0) -> pd.DataFrame:
        source = frame.copy()
        if target_column not in source.columns:
            return source
        target_mean = source[target_column].mean()
        for column in columns:
            if column not in source.columns:
                continue
            grouped = source.groupby(column)[target_column].agg(["mean", "count"])
            encoded_values = (grouped["mean"] * grouped["count"] + target_mean * smoothing) / (grouped["count"] + smoothing)
            source[f"{column}_target_encoded"] = source[column].map(encoded_values).fillna(target_mean)
        return source

    @staticmethod
    def scale_features(frame: pd.DataFrame, columns: Iterable[str], method: str = "standard") -> pd.DataFrame:
        source = frame.copy()
        available_columns = [column for column in columns if column in source.columns and is_numeric_dtype(source[column])]
        if not available_columns:
            return source
        scaler_map = {
            "standard": StandardScaler(),
            "minmax": MinMaxScaler(),
            "robust": RobustScaler(),
        }
        if method not in scaler_map:
            raise ValueError(f"Unsupported scaling method: {method}")
        scaler = scaler_map[method]
        scaled = scaler.fit_transform(source[available_columns].fillna(0))
        scaled_columns = [f"{column}_{method}_scaled" for column in available_columns]
        scaled_frame = pd.DataFrame(scaled, columns=scaled_columns, index=source.index)
        return pd.concat([source, scaled_frame], axis=1)

    @staticmethod
    def correlation_filter(frame: pd.DataFrame, threshold: float = 0.9) -> tuple[pd.DataFrame, list[str]]:
        numeric_frame = frame.select_dtypes(include=["number"])
        if numeric_frame.empty:
            return frame.copy(), []
        correlation_matrix = numeric_frame.corr(numeric_only=True).abs()
        upper_triangle = correlation_matrix.where(np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper_triangle.columns if any(upper_triangle[column] > threshold)]
        filtered = frame.drop(columns=to_drop, errors="ignore")
        return filtered, to_drop

    @staticmethod
    def _is_classification_target(target: pd.Series) -> bool:
        if target.dtype.kind in {"b", "i", "u"}:
            return True
        if target.dtype.kind == "f" and target.nunique(dropna=True) <= 10:
            return True
        if target.dtype == "object" or str(target.dtype).startswith("category"):
            return True
        return False

    @classmethod
    def mutual_information_select(cls, features: pd.DataFrame, target: pd.Series, top_k: int = 15) -> list[str]:
        numeric_features = features.select_dtypes(include=["number"]).fillna(0)
        if numeric_features.empty:
            return []
        if cls._is_classification_target(target):
            selector = SelectKBest(score_func=mutual_info_classif, k=min(top_k, numeric_features.shape[1]))
        else:
            selector = SelectKBest(score_func=mutual_info_regression, k=min(top_k, numeric_features.shape[1]))
        selector.fit(numeric_features, target)
        return list(numeric_features.columns[selector.get_support()])

    @classmethod
    def rfe_select(cls, features: pd.DataFrame, target: pd.Series, top_k: int = 15) -> list[str]:
        numeric_features = features.select_dtypes(include=["number"]).fillna(0)
        if numeric_features.empty:
            return []
        if numeric_features.shape[1] < 2:
            return list(numeric_features.columns)
        estimator = RandomForestClassifier(n_estimators=150, random_state=42) if cls._is_classification_target(target) else RandomForestRegressor(n_estimators=150, random_state=42)
        selector = RFE(estimator=estimator, n_features_to_select=min(top_k, numeric_features.shape[1]))
        selector.fit(numeric_features, target)
        return list(numeric_features.columns[selector.get_support()])

    @classmethod
    def tree_feature_importance_select(cls, features: pd.DataFrame, target: pd.Series, top_k: int = 15) -> list[str]:
        numeric_features = features.select_dtypes(include=["number"]).fillna(0)
        if numeric_features.empty:
            return []
        estimator = RandomForestClassifier(n_estimators=250, random_state=42) if cls._is_classification_target(target) else RandomForestRegressor(n_estimators=250, random_state=42)
        estimator.fit(numeric_features, target)
        importances = pd.Series(estimator.feature_importances_, index=numeric_features.columns)
        return list(importances.sort_values(ascending=False).head(top_k).index)

    def _load_tables(self) -> dict[str, pd.DataFrame]:
        return load_cleaned_tables(
            self.paths.processed_dir,
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
            ],
        )

    def _save_feature_frame(self, frame: pd.DataFrame, name: str, description: str) -> FeatureArtifact:
        path = self.paths.features_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        return FeatureArtifact(name=name, path=str(path), rows=len(frame), columns=len(frame.columns), description=description)

    def build_customer_features(self, customers: pd.DataFrame, orders: pd.DataFrame, customer_kpis: pd.DataFrame) -> pd.DataFrame:
        orders_frame = self._parse_dates(orders, ["order_date"])
        orders_frame = self.add_date_features(orders_frame, "order_date", "order")
        orders_frame = self.add_lag_features(orders_frame, "customer_id", "order_date", ["order_amount", "discount_rate", "shipping_days"])
        orders_frame = self.add_rolling_features(orders_frame, "customer_id", "order_date", ["order_amount", "discount_rate", "shipping_days"])

        aggregated_orders = orders_frame.groupby("customer_id").agg(
            total_orders=("order_id", "count"),
            total_revenue=("order_amount", "sum"),
            average_order_value=("order_amount", "mean"),
            average_discount_rate=("discount_rate", "mean"),
            average_shipping_days=("shipping_days", "mean"),
            max_order_value=("order_amount", "max"),
            min_order_value=("order_amount", "min"),
            revenue_std=("order_amount", "std"),
            last_order_date=("order_date", "max"),
            first_order_date=("order_date", "min"),
            order_amount_lag_1=("order_amount_lag_1", "mean"),
            order_amount_roll_mean_3=("order_amount_roll_mean_3", "mean"),
            order_amount_roll_mean_5=("order_amount_roll_mean_5", "mean"),
        ).reset_index()
        aggregated_orders["revenue_per_order"] = aggregated_orders["total_revenue"] / aggregated_orders["total_orders"].replace(0, np.nan)
        aggregated_orders["customer_tenure_days"] = (
            pd.to_datetime(aggregated_orders["last_order_date"], utc=True) - pd.to_datetime(aggregated_orders["first_order_date"], utc=True)
        ).dt.days.fillna(0).astype(int)
        aggregated_orders["days_since_last_order"] = (
            pd.to_datetime(orders_frame["order_date"], utc=True).max() - pd.to_datetime(aggregated_orders["last_order_date"], utc=True)
        ).dt.days.fillna(0).astype(int)

        feature_frame = customers.merge(aggregated_orders, on="customer_id", how="left").merge(customer_kpis, on="customer_id", how="left", suffixes=("", "_kpi"))
        feature_frame = self._parse_dates(feature_frame, ["signup_date", "last_order_date", "first_order_date", "recent_last_order"])
        feature_frame = self.add_date_features(feature_frame, "signup_date", "signup")
        feature_frame = self.add_date_features(feature_frame, "last_order_date", "last_order")
        feature_frame["customer_lifetime_revenue_ratio"] = feature_frame["total_revenue"] / feature_frame["annual_revenue"].replace(0, np.nan)
        feature_frame["customer_activity_score"] = (
            0.4 * feature_frame["engagement_score"] + 0.35 * feature_frame["customer_health_score"] + 0.25 * (100 - feature_frame["churn_risk_score"])
        )
        feature_frame = self.frequency_encode(feature_frame, ["segment", "industry", "region"])
        feature_frame = self.one_hot_encode(feature_frame, ["segment", "industry", "region"])
        feature_frame = self.scale_features(feature_frame, ["annual_revenue", "total_revenue", "average_order_value", "customer_activity_score"], method="standard")
        feature_frame = self.scale_features(feature_frame, ["annual_revenue", "total_revenue", "average_order_value", "customer_activity_score"], method="robust")
        return feature_frame

    def build_sales_features(self, orders: pd.DataFrame, customers: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
        sales_frame = orders.merge(customers[["customer_id", "segment", "industry", "region", "annual_revenue"]], on="customer_id", how="left").merge(
            products[["product_id", "category", "subcategory", "unit_cost", "list_price", "margin_rate"]], on="product_id", how="left"
        )
        sales_frame = self._parse_dates(sales_frame, ["order_date"])
        sales_frame = self.add_date_features(sales_frame, "order_date", "order")
        sales_frame = self.frequency_encode(sales_frame, ["sales_channel", "order_status", "category", "segment"])
        sales_frame = self.target_encode(sales_frame, ["sales_channel", "category", "segment"], "order_amount")
        sales_frame = self.ordinal_encode(
            sales_frame,
            ["order_status"],
            {"order_status": ["Cancelled", "Returned", "Shipped", "Completed"]},
        )
        sales_frame = self.one_hot_encode(sales_frame, ["sales_channel", "category", "segment"])
        sales_frame = self.add_lag_features(sales_frame, "customer_id", "order_date", ["order_amount", "discount_rate"], lags=(1, 2))
        sales_frame = self.add_rolling_features(sales_frame, "customer_id", "order_date", ["order_amount", "discount_rate"], windows=(3, 7))
        sales_frame = self.scale_features(sales_frame, ["order_amount", "discount_rate", "unit_price", "annual_revenue", "margin_rate"], method="minmax")
        return sales_frame

    def build_finance_features(self, finance: pd.DataFrame) -> pd.DataFrame:
        finance_frame = self._parse_dates(finance, [])
        finance_frame["month_index"] = np.arange(len(finance_frame))
        finance_frame = self.add_lag_features(finance_frame, "order_month", "order_month", ["revenue", "gross_margin", "ebitda", "cash_balance"], lags=(1, 2))
        finance_frame = self.add_rolling_features(finance_frame, "order_month", "order_month", ["revenue", "gross_margin", "ebitda", "cash_balance"], windows=(2, 3))
        finance_frame = self.scale_features(finance_frame, ["revenue", "gross_margin", "ebitda", "cash_balance", "debt_balance"], method="robust")
        return finance_frame

    def build_marketing_features(self, marketing_campaigns: pd.DataFrame) -> pd.DataFrame:
        marketing_frame = marketing_campaigns.copy()
        marketing_frame = self._parse_dates(marketing_frame, ["start_date", "end_date"])
        marketing_frame = self.add_date_features(marketing_frame, "start_date", "campaign_start")
        marketing_frame["campaign_duration_days"] = (marketing_frame["end_date"] - marketing_frame["start_date"]).dt.days.fillna(0).astype(int)
        marketing_frame["cost_per_lead"] = marketing_frame["budget"] / marketing_frame["leads_generated"].replace(0, np.nan)
        marketing_frame["revenue_per_budget"] = marketing_frame["attributed_revenue"] / marketing_frame["budget"].replace(0, np.nan)
        marketing_frame = self.frequency_encode(marketing_frame, ["channel", "target_segment"])
        marketing_frame = self.target_encode(marketing_frame, ["channel", "target_segment"], "attributed_revenue")
        marketing_frame = self.one_hot_encode(marketing_frame, ["channel", "target_segment"])
        marketing_frame = self.scale_features(marketing_frame, ["budget", "leads_generated", "conversion_rate", "attributed_revenue", "cost_per_lead"], method="standard")
        return marketing_frame

    def build_inventory_features(self, inventory: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
        inventory_frame = inventory.merge(products[["product_id", "category", "subcategory", "unit_cost", "list_price", "margin_rate"]], on="product_id", how="left")
        inventory_frame = self._parse_dates(inventory_frame, ["snapshot_date"])
        inventory_frame = self.add_date_features(inventory_frame, "snapshot_date", "snapshot")
        inventory_frame = self.add_lag_features(inventory_frame, "product_id", "snapshot_date", ["on_hand_units", "reserved_units", "stockout_risk"], lags=(1, 2, 3))
        inventory_frame = self.add_rolling_features(inventory_frame, "product_id", "snapshot_date", ["on_hand_units", "reserved_units", "stockout_risk"], windows=(3, 6))
        inventory_frame["inventory_utilization"] = inventory_frame["reserved_units"] / inventory_frame["on_hand_units"].replace(0, np.nan)
        inventory_frame = self.frequency_encode(inventory_frame, ["warehouse_id", "category", "subcategory"])
        inventory_frame = self.one_hot_encode(inventory_frame, ["warehouse_id", "category", "subcategory"])
        inventory_frame = self.scale_features(inventory_frame, ["on_hand_units", "reserved_units", "reorder_point", "inventory_value", "stockout_risk"], method="minmax")
        return inventory_frame

    def build_employee_features(self, employees: pd.DataFrame) -> pd.DataFrame:
        employee_frame = self._parse_dates(employees, ["hire_date"])
        employee_frame = self.add_date_features(employee_frame, "hire_date", "hire")
        employee_frame["tenure_days"] = (pd.Timestamp.now(tz=timezone.utc) - employee_frame["hire_date"]).dt.days.fillna(0).astype(int)
        employee_frame["salary_performance_ratio"] = employee_frame["salary"] / employee_frame["performance_score"].replace(0, np.nan)
        employee_frame = self.frequency_encode(employee_frame, ["department", "level", "region"])
        employee_frame = self.one_hot_encode(employee_frame, ["department", "level", "region"])
        employee_frame = self.scale_features(employee_frame, ["salary", "performance_score", "tenure_days"], method="robust")
        return employee_frame

    def build_kpi_features(self, customer_kpis: pd.DataFrame, finance: pd.DataFrame, operations: pd.DataFrame) -> pd.DataFrame:
        kpi_frame = customer_kpis.copy()
        kpi_frame = self._parse_dates(kpi_frame, ["signup_date", "recent_last_order"])
        kpi_frame = self.add_date_features(kpi_frame, "signup_date", "signup")
        kpi_frame = self.add_date_features(kpi_frame, "recent_last_order", "recent_order")
        finance_kpi = finance[["order_month", "revenue", "gross_margin", "ebitda", "cash_balance"]].copy()
        finance_kpi["order_month"] = finance_kpi["order_month"].astype(str)
        kpi_frame["recent_revenue_ratio"] = kpi_frame["recent_revenue"] / kpi_frame["annual_revenue"].replace(0, np.nan)
        kpi_frame["customer_value_proxy"] = (
            0.4 * kpi_frame["recent_revenue"].fillna(0.0)
            + 0.35 * kpi_frame["revenue_90d_target"].fillna(0.0)
            + 0.25 * kpi_frame["order_velocity"].fillna(0.0) * 100_000
        )
        kpi_frame = self.frequency_encode(kpi_frame, ["segment", "industry", "region"])
        kpi_frame = self.scale_features(kpi_frame, ["total_orders", "total_revenue", "recent_revenue", "days_since_last_order", "customer_value_proxy"], method="standard")
        return kpi_frame

    def _save_schema(self, datasets: dict[str, pd.DataFrame]) -> None:
        schema = {
            name: [{"column": column, "dtype": str(dtype)} for column, dtype in frame.dtypes.items()]
            for name, frame in datasets.items()
        }
        (self.paths.features_dir / "feature_schema.json").write_text(json.dumps(schema, indent=2, default=str), encoding="utf-8")

    def _save_metadata(self, artifacts: list[FeatureArtifact], selection_report: pd.DataFrame) -> None:
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(artifacts),
            "artifacts": [asdict(artifact) for artifact in artifacts],
            "selection_rows": int(len(selection_report)),
            "selected_features": selection_report["feature_name"].tolist() if not selection_report.empty else [],
        }
        (self.paths.features_dir / "feature_metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    def _build_selection_report(self, feature_frame: pd.DataFrame, target: pd.Series, dataset_name: str) -> pd.DataFrame:
        numeric_frame = feature_frame.select_dtypes(include=["number"]).fillna(0)
        if numeric_frame.empty:
            return pd.DataFrame(columns=["dataset", "feature_name", "rank", "importance_method"])
        selected_mi = self.mutual_information_select(numeric_frame, target, top_k=min(10, numeric_frame.shape[1]))
        selected_rfe = self.rfe_select(numeric_frame, target, top_k=min(10, numeric_frame.shape[1]))
        selected_tree = self.tree_feature_importance_select(numeric_frame, target, top_k=min(10, numeric_frame.shape[1]))
        combined = list(dict.fromkeys(selected_mi + selected_rfe + selected_tree))
        return pd.DataFrame(
            {
                "dataset": dataset_name,
                "feature_name": combined,
                "rank": list(range(1, len(combined) + 1)),
                "importance_method": ["combined"] * len(combined),
            }
        )

    def build_feature_package(self) -> dict[str, pd.DataFrame]:
        tables = self._load_tables()
        customer_features = self.build_customer_features(tables["customers"], tables["orders"], tables["customer_kpis"])
        sales_features = self.build_sales_features(tables["orders"], tables["customers"], tables["products"])
        finance_features = self.build_finance_features(tables["finance_monthly"])
        marketing_features = self.build_marketing_features(tables["marketing_campaigns"])
        inventory_features = self.build_inventory_features(tables["inventory_snapshots"], tables["products"])
        employee_features = self.build_employee_features(tables["employees"])
        kpi_features = self.build_kpi_features(tables["customer_kpis"], tables["finance_monthly"], tables["operations_daily"])

        feature_datasets = {
            "customer_features": customer_features,
            "sales_features": sales_features,
            "finance_features": finance_features,
            "marketing_features": marketing_features,
            "inventory_features": inventory_features,
            "employee_features": employee_features,
            "kpi_features": kpi_features,
        }

        artifacts: list[FeatureArtifact] = []
        for name, frame in feature_datasets.items():
            artifact = self._save_feature_frame(frame, name, f"Model-ready {name.replace('_', ' ')}")
            artifacts.append(artifact)

        selection_report = self._build_selection_report(customer_features, customer_features["churn_flag"], "customer_features")
        selection_report.to_csv(self.paths.reports_dir / "feature_selection_report.csv", index=False)
        self._save_schema(feature_datasets)
        self._save_metadata(artifacts, selection_report)

        manifest = {
            "feature_datasets": [asdict(artifact) for artifact in artifacts],
            "selection_rows": int(len(selection_report)),
        }
        (self.paths.reports_dir / "feature_engineering_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return feature_datasets
