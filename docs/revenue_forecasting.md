# Revenue Forecasting

## Objective

Build a production-grade monthly revenue forecasting workflow for the enterprise platform.

## Business Context

Revenue forecasting is one of the core decision-intelligence use cases. Leadership needs to know whether revenue is trending up or down, which operational signals are driving movement, and how confident the forecast is.

## Methodology

The revenue forecasting module uses the processed finance table generated from the synthetic enterprise dataset. It creates a supervised learning dataset with:

- calendar features
- lag features
- rolling statistics
- margin and liquidity ratios
- a next-period revenue target

Candidate models are evaluated with time-series cross-validation, and the best model is persisted to the model registry.

## Outputs

- `trained_models/model_registry.json`
- `trained_models/revenue_forecast_model.joblib`
- `reports/revenue_model_comparison.csv`
- `reports/revenue_forecast_summary.json`
- `exports/revenue_forecast.csv`
- `exports/revenue_forecast_plot.png`

## Design Decisions

- Time-series cross-validation is used instead of random shuffling because revenue is sequential.
- The latest available month is used to generate the next-period forecast.
- XGBoost is tuned separately with Optuna to provide an optimized candidate alongside deterministic baselines.
- Model registration keeps training and inference decoupled.

## Next Step

This module becomes the backbone for the remaining ML notebooks: churn, risk, demand, segmentation, model evaluation, explainability, and recommendations.
