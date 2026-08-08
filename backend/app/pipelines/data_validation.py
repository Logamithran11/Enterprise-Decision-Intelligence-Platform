from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
import json

import pandas as pd


@dataclass(frozen=True, slots=True)
class ValidationPaths:
    processed_dir: Path
    reports_dir: Path

    def ensure(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    table_name: str
    check_name: str
    status: str
    passed: bool
    failed_records: int
    message: str


class EnterpriseDataValidator:
    """Validate processed enterprise tables and persist quality reports."""

    REQUIRED_TABLES = (
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
    )

    PRIMARY_KEYS = {
        "customers": "customer_id",
        "products": "product_id",
        "suppliers": "supplier_id",
        "employees": "employee_id",
        "marketing_campaigns": "campaign_id",
        "orders": "order_id",
    }

    REQUIRED_COLUMNS = {
        "customers": {
            "customer_id",
            "customer_name",
            "segment",
            "industry",
            "region",
            "country",
            "signup_date",
            "employee_count",
            "annual_revenue",
            "engagement_score",
            "customer_health_score",
            "churn_risk_score",
            "churn_flag",
        },
        "products": {
            "product_id",
            "product_name",
            "category",
            "subcategory",
            "supplier_id",
            "unit_cost",
            "list_price",
            "margin_rate",
            "demand_score",
            "lifecycle_stage",
            "is_active",
        },
        "suppliers": {
            "supplier_id",
            "supplier_name",
            "supplier_type",
            "region",
            "country",
            "lead_time_days",
            "reliability_score",
            "contract_value",
        },
        "employees": {
            "employee_id",
            "employee_name",
            "department",
            "level",
            "region",
            "hire_date",
            "salary",
            "performance_score",
            "manager_id",
            "is_active",
        },
        "marketing_campaigns": {
            "campaign_id",
            "campaign_name",
            "channel",
            "target_segment",
            "start_date",
            "end_date",
            "budget",
            "leads_generated",
            "conversion_rate",
            "attributed_revenue",
        },
        "orders": {
            "order_id",
            "customer_id",
            "product_id",
            "campaign_id",
            "order_date",
            "sales_channel",
            "order_status",
            "quantity",
            "unit_price",
            "discount_rate",
            "order_amount",
            "shipping_days",
            "category",
            "gross_margin",
            "order_month",
        },
        "inventory_snapshots": {
            "snapshot_date",
            "warehouse_id",
            "product_id",
            "on_hand_units",
            "reserved_units",
            "reorder_point",
            "stockout_risk",
            "inventory_value",
        },
        "finance_monthly": {
            "order_month",
            "revenue",
            "gross_margin",
            "order_count",
            "cogs",
            "opex",
            "ebitda",
            "cash_balance",
            "debt_balance",
            "dscr",
        },
        "operations_daily": {
            "operating_date",
            "warehouse_id",
            "throughput_units",
            "on_time_delivery_rate",
            "fulfillment_rate",
            "incident_count",
            "labor_hours",
            "downtime_minutes",
        },
        "customer_kpis": {
            "customer_id",
            "segment",
            "industry",
            "region",
            "country",
            "signup_date",
            "employee_count",
            "annual_revenue",
            "engagement_score",
            "customer_health_score",
            "churn_risk_score",
            "churn_flag",
            "total_orders",
            "total_revenue",
            "recent_order_count",
            "recent_revenue",
            "recent_avg_discount",
            "recent_avg_shipping_days",
            "recent_last_order",
            "days_since_last_order",
            "order_velocity",
            "revenue_90d_target",
        },
    }

    FOREIGN_KEYS = (
        ("products", "supplier_id", "suppliers", "supplier_id"),
        ("orders", "customer_id", "customers", "customer_id"),
        ("orders", "product_id", "products", "product_id"),
        ("orders", "campaign_id", "marketing_campaigns", "campaign_id"),
        ("inventory_snapshots", "product_id", "products", "product_id"),
        ("customer_kpis", "customer_id", "customers", "customer_id"),
    )

    NUMERIC_RANGES = {
        "customers": {
            "engagement_score": (0, 100),
            "customer_health_score": (0, 100),
            "churn_risk_score": (0, 100),
            "churn_flag": (0, 1),
        },
        "products": {
            "unit_cost": (0, None),
            "list_price": (0, None),
            "margin_rate": (0, 1),
            "demand_score": (0, 100),
        },
        "suppliers": {
            "lead_time_days": (0, None),
            "reliability_score": (0, 100),
            "contract_value": (0, None),
        },
        "employees": {
            "salary": (0, None),
            "performance_score": (0, 100),
            "is_active": (0, 1),
        },
        "marketing_campaigns": {
            "budget": (0, None),
            "leads_generated": (0, None),
            "conversion_rate": (0, 1),
            "attributed_revenue": (0, None),
        },
        "orders": {
            "quantity": (1, None),
            "unit_price": (0, None),
            "discount_rate": (0, 1),
            "order_amount": (0, None),
            "shipping_days": (0, None),
            "gross_margin": (0, None),
        },
        "inventory_snapshots": {
            "on_hand_units": (0, None),
            "reserved_units": (0, None),
            "reorder_point": (0, None),
            "stockout_risk": (0, 1),
            "inventory_value": (0, None),
        },
        "finance_monthly": {
            "revenue": (0, None),
            "gross_margin": (None, None),
            "cogs": (0, None),
            "opex": (0, None),
            "ebitda": (None, None),
            "cash_balance": (0, None),
            "debt_balance": (0, None),
            "dscr": (0, None),
        },
        "operations_daily": {
            "throughput_units": (0, None),
            "on_time_delivery_rate": (0, 1),
            "fulfillment_rate": (0, 1),
            "incident_count": (0, None),
            "labor_hours": (0, None),
            "downtime_minutes": (0, None),
        },
        "customer_kpis": {
            "total_orders": (0, None),
            "total_revenue": (0, None),
            "recent_order_count": (0, None),
            "days_since_last_order": (0, None),
            "order_velocity": (0, None),
            "revenue_90d_target": (0, None),
            "churn_flag": (0, 1),
        },
    }

    EXPECTED_MIN_ROWS = {
        "customers": 10_000,
        "products": 1_000,
        "suppliers": 100,
        "employees": 500,
        "marketing_campaigns": 1_000,
        "orders": 100_000,
        "inventory_snapshots": 100_000,
        "finance_monthly": 12,
        "operations_daily": 365,
        "customer_kpis": 10_000,
    }

    def __init__(self, paths: ValidationPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def _load_table(self, table_name: str) -> pd.DataFrame:
        file_path = self.paths.processed_dir / f"{table_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing processed table: {file_path}")
        return pd.read_csv(file_path)

    @staticmethod
    def _check_required_columns(table_name: str, frame: pd.DataFrame, required_columns: Iterable[str]) -> ValidationResult:
        missing_columns = [column for column in required_columns if column not in frame.columns]
        passed = len(missing_columns) == 0
        return ValidationResult(
            table_name=table_name,
            check_name="required_columns",
            status="pass" if passed else "fail",
            passed=passed,
            failed_records=len(missing_columns),
            message="All required columns present" if passed else f"Missing columns: {', '.join(missing_columns)}",
        )

    @staticmethod
    def _check_primary_key_uniqueness(table_name: str, frame: pd.DataFrame, key_column: str) -> ValidationResult:
        duplicate_count = int(frame.duplicated(subset=[key_column]).sum())
        passed = duplicate_count == 0
        return ValidationResult(
            table_name=table_name,
            check_name="primary_key_uniqueness",
            status="pass" if passed else "fail",
            passed=passed,
            failed_records=duplicate_count,
            message="Primary key is unique" if passed else f"Duplicate {key_column} values found",
        )

    @staticmethod
    def _check_foreign_key_integrity(
        table_name: str,
        frame: pd.DataFrame,
        column_name: str,
        reference_frame: pd.DataFrame,
        reference_column: str,
        reference_table: str,
    ) -> ValidationResult:
        invalid_mask = ~frame[column_name].isin(reference_frame[reference_column])
        invalid_count = int(invalid_mask.sum())
        passed = invalid_count == 0
        return ValidationResult(
            table_name=table_name,
            check_name=f"foreign_key_{column_name}_to_{reference_table}",
            status="pass" if passed else "fail",
            passed=passed,
            failed_records=invalid_count,
            message="Foreign key integrity verified" if passed else f"{invalid_count} invalid references in {column_name}",
        )

    @staticmethod
    def _check_numeric_ranges(table_name: str, frame: pd.DataFrame, ranges: dict[str, tuple[int | float | None, int | float | None]]) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for column_name, (minimum, maximum) in ranges.items():
            if column_name not in frame.columns:
                results.append(
                    ValidationResult(
                        table_name=table_name,
                        check_name=f"range_{column_name}",
                        status="skip",
                        passed=True,
                        failed_records=0,
                        message="Column not present",
                    )
                )
                continue
            series = frame[column_name]
            invalid_mask = pd.Series(False, index=series.index)
            if minimum is not None:
                invalid_mask |= series < minimum
            if maximum is not None:
                invalid_mask |= series > maximum
            invalid_count = int(invalid_mask.sum())
            passed = invalid_count == 0
            results.append(
                ValidationResult(
                    table_name=table_name,
                    check_name=f"range_{column_name}",
                    status="pass" if passed else "fail",
                    passed=passed,
                    failed_records=invalid_count,
                    message=f"{column_name} within expected range" if passed else f"{invalid_count} values outside expected range",
                )
            )
        return results

    @staticmethod
    def _check_row_count(table_name: str, frame: pd.DataFrame, expected_min_rows: int) -> ValidationResult:
        passed = len(frame) >= expected_min_rows
        return ValidationResult(
            table_name=table_name,
            check_name="minimum_row_count",
            status="pass" if passed else "fail",
            passed=passed,
            failed_records=max(expected_min_rows - len(frame), 0),
            message="Row count meets target" if passed else f"Expected at least {expected_min_rows} rows",
        )

    def validate_all(self) -> pd.DataFrame:
        frames = {table_name: self._load_table(table_name) for table_name in self.REQUIRED_TABLES}
        validation_results: list[ValidationResult] = []

        for table_name, frame in frames.items():
            validation_results.append(
                self._check_required_columns(table_name, frame, self.REQUIRED_COLUMNS[table_name])
            )
            if table_name in self.PRIMARY_KEYS:
                validation_results.append(self._check_primary_key_uniqueness(table_name, frame, self.PRIMARY_KEYS[table_name]))
            validation_results.append(self._check_row_count(table_name, frame, self.EXPECTED_MIN_ROWS[table_name]))
            validation_results.extend(self._check_numeric_ranges(table_name, frame, self.NUMERIC_RANGES.get(table_name, {})))

        for table_name, local_column, reference_table, reference_column in self.FOREIGN_KEYS:
            validation_results.append(
                self._check_foreign_key_integrity(
                    table_name=table_name,
                    frame=frames[table_name],
                    column_name=local_column,
                    reference_frame=frames[reference_table],
                    reference_column=reference_column,
                    reference_table=reference_table,
                )
            )

        report_frame = pd.DataFrame([asdict(result) for result in validation_results])
        report_frame.to_csv(self.paths.reports_dir / "data_validation_report.csv", index=False)

        summary = {
            "checked_tables": len(self.REQUIRED_TABLES),
            "total_checks": len(report_frame),
            "passed_checks": int(report_frame["passed"].sum()),
            "failed_checks": int((~report_frame["passed"]).sum()),
            "pass_rate": round(float(report_frame["passed"].mean()), 4),
        }
        (self.paths.reports_dir / "data_validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return report_frame

    def quality_score(self, validation_report: pd.DataFrame) -> float:
        if validation_report.empty:
            return 0.0
        pass_rate = float(validation_report[validation_report["status"] == "pass"].shape[0] / validation_report.shape[0])
        return round(pass_rate * 100, 2)
