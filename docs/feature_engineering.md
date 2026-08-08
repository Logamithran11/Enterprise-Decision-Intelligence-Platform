# Feature Engineering

## Objective

Transform validated enterprise tables into reusable, model-ready feature datasets for forecasting, segmentation, churn analysis, risk scoring, and KPI prediction.

## Why This Module Exists

Raw enterprise tables are useful for auditing and analytics, but machine learning models require transformed inputs:

- time-based features for trend and seasonality capture
- lag and rolling statistics for customer and commercial behavior
- categorical encodings for high-cardinality business attributes
- scaled numeric features for model stability
- feature selection to reduce noise and improve generalization

## Architecture

The feature engineering layer lives in `backend/app/features/feature_engineering.py` and follows the same clean architecture conventions as the rest of the backend:

- a dedicated paths object for input/output directories
- deterministic feature builders for each domain table
- reusable encoding and scaling helpers
- feature selection utilities for downstream model training
- explicit persistence of feature datasets, schema, and metadata

## Produced Artifacts

- `features/customer_features.csv`
- `features/sales_features.csv`
- `features/finance_features.csv`
- `features/marketing_features.csv`
- `features/inventory_features.csv`
- `features/employee_features.csv`
- `features/kpi_features.csv`
- `features/feature_schema.json`
- `features/feature_metadata.json`
- `reports/feature_selection_report.csv`

## Design Decisions

- Customer, sales, finance, marketing, inventory, employee, and KPI feature sets are generated separately so model training can target the right grain.
- Lag and rolling features are computed on ordered transactional data to preserve time dependence.
- One-hot, ordinal, frequency, and target encoding are exposed as reusable helpers rather than hard-coded into a single dataset builder.
- Standard, MinMax, and Robust scaling are implemented as reusable transformations so model pipelines can pick the most appropriate distribution handling.
- Feature selection is treated as a first-class output so model training notebooks can start from smaller, more informative feature sets.

## Operational Guidance

Run the feature engineering notebook after cleaning and validation. The module assumes the processed tables exist in `processed/` and writes all derived datasets to `features/`.

## Next Step

The next module after feature engineering is model training and evaluation, which will consume the saved feature datasets.
