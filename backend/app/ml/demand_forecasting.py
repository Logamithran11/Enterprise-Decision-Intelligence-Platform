from __future__ import annotations

import json
from dataclasses import asdict, dataclass
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from app.ml.evaluate import evaluate_regression, RegressionEvaluation
from app.ml.model_registry import ModelRegistry
from app.ml.predict import ModelPredictor

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class DemandForecastingPaths:
    processed_dir: Path
    trained_models_dir: Path
    reports_dir: Path
    exports_dir: Path

    def ensure(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.trained_models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class DemandArtifact:
    model_name: str
    path: str
    mae: float
    rmse: float
    r2: float
    description: str


class DemandForecastingService:
    """Forecast product-level demand and inventory requirements using machine learning."""

    def __init__(self, paths: DemandForecastingPaths) -> None:
        self.paths = paths
        self.paths.ensure()
        self.registry = ModelRegistry(self.paths.trained_models_dir)
        self.predictor = ModelPredictor(self.registry)

    def load_orders(self) -> pd.DataFrame:
        orders_path = self.paths.processed_dir / "orders.csv"
        if not orders_path.exists():
            raise FileNotFoundError(f"Missing processed orders table: {orders_path}")
        return pd.read_csv(orders_path)

    def load_products(self) -> pd.DataFrame:
        products_path = self.paths.processed_dir / "products.csv"
        if not products_path.exists():
            raise FileNotFoundError(f"Missing processed products table: {products_path}")
        return pd.read_csv(products_path)

    def load_suppliers(self) -> pd.DataFrame:
        suppliers_path = self.paths.processed_dir / "suppliers.csv"
        if not suppliers_path.exists():
            raise FileNotFoundError(f"Missing processed suppliers table: {suppliers_path}")
        return pd.read_csv(suppliers_path)

    def prepare_demand_dataset(self) -> tuple[pd.DataFrame, list[str]]:
        orders = self.load_orders()
        products = self.load_products()

        # Parse date and format as month string
        orders["order_date"] = pd.to_datetime(orders["order_date"], utc=True)
        orders["order_month"] = orders["order_date"].dt.strftime("%Y-%m")

        # Group by product and month
        monthly_demand = orders.groupby(["product_id", "order_month"]).agg(
            quantity_sold=("quantity", "sum"),
            revenue_generated=("order_amount", "sum"),
            order_count=("order_id", "count")
        ).reset_index()

        # Build complete grid of products & months to handle zero-demand months
        all_months = sorted(orders["order_month"].unique())
        all_products = products["product_id"].unique()
        
        index_grid = pd.MultiIndex.from_product([all_products, all_months], names=["product_id", "order_month"])
        grid_df = pd.DataFrame(index=index_grid).reset_index()

        # Merge monthly demand into grid
        demand_df = grid_df.merge(monthly_demand, on=["product_id", "order_month"], how="left").fillna(0)
        
        # Add product category and subcategory info
        demand_df = demand_df.merge(products[["product_id", "category", "subcategory"]], on="product_id", how="left")

        # Sort values
        demand_df = demand_df.sort_values(["product_id", "order_month"]).reset_index(drop=True)

        # Create lag and rolling features per product
        lags = [1, 2, 3]
        for lag in lags:
            demand_df[f"demand_lag_{lag}"] = demand_df.groupby("product_id")["quantity_sold"].shift(lag)
            
        windows = [3, 6]
        for window in windows:
            demand_df[f"demand_roll_mean_{window}"] = demand_df.groupby("product_id")["quantity_sold"].shift(1).rolling(window, min_periods=1).mean()
            demand_df[f"demand_roll_std_{window}"] = demand_df.groupby("product_id")["quantity_sold"].shift(1).rolling(window, min_periods=1).std()

        # Target is next month's quantity_sold
        demand_df["target_demand"] = demand_df.groupby("product_id")["quantity_sold"].shift(-1)
        
        # Drop rows with missing features or targets
        demand_df = demand_df.dropna(subset=["target_demand", "demand_lag_3"]).reset_index(drop=True)
        
        feature_cols = [
            "quantity_sold", "revenue_generated", "order_count",
            "demand_lag_1", "demand_lag_2", "demand_lag_3",
            "demand_roll_mean_3", "demand_roll_std_3",
            "demand_roll_mean_6", "demand_roll_std_6"
        ]
        
        return demand_df, feature_cols

    def train_and_register(self) -> tuple[pd.DataFrame, DemandArtifact, pd.DataFrame]:
        demand_df, feature_cols = self.prepare_demand_dataset()
        
        X = demand_df[feature_cols].fillna(0)
        y = demand_df["target_demand"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        candidate_models = {
            "random_forest": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
            "xgboost": XGBRegressor(n_estimators=120, max_depth=5, learning_rate=0.08, objective="reg:squarederror", random_state=42)
        }
        
        comparison_rows = []
        fitted_models = {}
        
        for name, reg in candidate_models.items():
            reg.fit(X_train, y_train)
            fitted_models[name] = reg
            
            preds = reg.predict(X_test)
            evals = evaluate_regression(y_test, preds)
            
            comparison_rows.append({
                "model_name": name,
                "mae": evals.mae,
                "rmse": evals.rmse,
                "r2": evals.r2
            })
            
        comparison_frame = pd.DataFrame(comparison_rows).sort_values("mae").reset_index(drop=True)
        comparison_frame.to_csv(self.paths.reports_dir / "demand_model_comparison.csv", index=False)
        
        best_name = comparison_frame.iloc[0]["model_name"]
        best_model = fitted_models[best_name]
        
        test_preds = best_model.predict(X_test)
        test_evals = evaluate_regression(y_test, test_preds)
        
        registered = self.registry.register_model(
            name="demand_forecast_model",
            model=best_model,
            metrics={"mae": test_evals.mae, "rmse": test_evals.rmse, "r2": test_evals.r2},
            feature_names=feature_cols,
            model_type=best_name,
            description="Regression model forecasting monthly product unit demand."
        )
        
        artifact = DemandArtifact(
            model_name=registered.name,
            path=registered.model_path,
            mae=test_evals.mae,
            rmse=test_evals.rmse,
            r2=test_evals.r2,
            description=registered.description
        )
        
        # Generate predictions for all rows
        all_preds = best_model.predict(X)
        output_df = demand_df[["product_id", "order_month", "target_demand"]].copy()
        output_df["predicted_demand"] = all_preds
        output_df.to_csv(self.paths.exports_dir / "product_demand_forecasts.csv", index=False)
        
        # Calculate seasonality and inventory requirements
        self._calculate_seasonality(orders_path=self.paths.processed_dir / "orders.csv")
        self._calculate_inventory_requirements(output_df)
        
        return comparison_frame, artifact, output_df

    def _calculate_seasonality(self, orders_path: Path) -> pd.DataFrame:
        orders = pd.read_csv(orders_path)
        orders["order_date"] = pd.to_datetime(orders["order_date"], utc=True)
        orders["month_of_year"] = orders["order_date"].dt.month
        
        # Calculate demand per category per month of year
        monthly_sales = orders.groupby(["category", "month_of_year"])["quantity"].sum().reset_index()
        
        # Overall monthly average per category
        category_avg = orders.groupby("category")["quantity"].sum().reset_index()
        category_avg["quantity"] /= 12.0
        
        seasonality = monthly_sales.merge(category_avg, on="category", suffixes=("", "_avg"))
        seasonality["seasonal_index"] = seasonality["quantity"] / seasonality["quantity_avg"].replace(0, 1.0)
        
        seasonality_path = self.paths.exports_dir / "category_seasonality.csv"
        seasonality.to_csv(seasonality_path, index=False)
        return seasonality

    def _calculate_inventory_requirements(self, predictions_df: pd.DataFrame) -> pd.DataFrame:
        products = self.load_products()
        suppliers = self.load_suppliers()
        
        # Link products to suppliers for lead time
        prod_sup = products.merge(suppliers[["supplier_id", "lead_time_days"]], on="supplier_id", how="left")
        prod_sup["lead_time_days"] = prod_sup["lead_time_days"].fillna(14)
        
        # Calculate mean & std of monthly demand prediction per product
        pred_stats = predictions_df.groupby("product_id").agg(
            avg_predicted_demand=("predicted_demand", "mean"),
            std_predicted_demand=("predicted_demand", "std")
        ).reset_index()
        pred_stats["std_predicted_demand"] = pred_stats["std_predicted_demand"].fillna(1.0)
        
        inventory_req = prod_sup.merge(pred_stats, on="product_id", how="left")
        inventory_req["avg_predicted_demand"] = inventory_req["avg_predicted_demand"].fillna(10.0)
        inventory_req["std_predicted_demand"] = inventory_req["std_predicted_demand"].fillna(2.0)
        
        # Safety Stock formula (95% service level = Z score of 1.65)
        # safety_stock = 1.65 * std_of_demand * sqrt(lead_time_days / 30)
        inventory_req["safety_stock"] = (
            1.65 * inventory_req["std_predicted_demand"] * np.sqrt(inventory_req["lead_time_days"] / 30.0)
        ).round(2)
        
        # Reorder Point = (daily demand * lead time) + safety stock
        inventory_req["reorder_point"] = (
            (inventory_req["avg_predicted_demand"] / 30.0) * inventory_req["lead_time_days"] + inventory_req["safety_stock"]
        ).round(2)
        
        # Max stock level / target inventory
        inventory_req["optimal_inventory_target"] = (
            inventory_req["reorder_point"] + inventory_req["avg_predicted_demand"]
        ).round(2)
        
        output_path = self.paths.exports_dir / "inventory_requirements.csv"
        inventory_req.to_csv(output_path, index=False)
        return inventory_req
