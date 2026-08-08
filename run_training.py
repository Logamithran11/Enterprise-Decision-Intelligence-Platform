import sys
from pathlib import Path

# Add backend directory to path
project_root = Path(__file__).resolve().parent
backend_root = project_root / 'backend'
sys.path.insert(0, str(backend_root))

from app.ml.revenue_forecasting import RevenueForecastingPaths, RevenueForecastingService
from app.ml.churn_prediction import ChurnPredictionPaths, ChurnPredictionService
from app.ml.business_risk import BusinessRiskPaths, BusinessRiskService
from app.ml.demand_forecasting import DemandForecastingPaths, DemandForecastingService
from app.ml.customer_segmentation import CustomerSegmentationPaths, CustomerSegmentationService
from app.ml.model_evaluation import ModelEvaluationService
from app.ml.explainability import ExplainabilityService
from app.ml.recommendation_engine import BusinessRecommendationService

import pandas as pd

def main():
    print("Starting ML Model training pipeline...")
    processed_dir = project_root / 'processed'
    features_dir = project_root / 'features'
    trained_models_dir = project_root / 'trained_models'
    reports_dir = project_root / 'reports'
    exports_dir = project_root / 'exports'
    
    # 1. Revenue Forecasting Model
    print("1/8 Training Revenue Forecasting model...")
    revenue_service = RevenueForecastingService(
        RevenueForecastingPaths(
            processed_dir=processed_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
    )
    revenue_service.train_and_register(n_trials=3)
    
    # 2. Churn Prediction Model
    print("2/8 Training Customer Churn Prediction model...")
    churn_service = ChurnPredictionService(
        ChurnPredictionPaths(
            processed_dir=processed_dir,
            features_dir=features_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
    )
    churn_service.train_and_register(n_trials=3)
    
    # 3. Business Risk Model
    print("3/8 Training Business Risk classification models...")
    risk_service = BusinessRiskService(
        BusinessRiskPaths(
            features_dir=features_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
    )
    risk_service.train_all()
    risk_service.generate_enterprise_risk_report()
    
    # 4. Demand Forecasting Model
    print("4/8 Training Demand Forecasting model...")
    demand_service = DemandForecastingService(
        DemandForecastingPaths(
            processed_dir=processed_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
    )
    demand_service.train_and_register()
    
    # 5. Customer Segmentation model
    print("5/8 Training Customer Segmentation KMeans model...")
    segmentation_service = CustomerSegmentationService(
        CustomerSegmentationPaths(
            features_dir=features_dir,
            trained_models_dir=trained_models_dir,
            reports_dir=reports_dir,
            exports_dir=exports_dir
        )
    )
    segmentation_service.train_and_register(n_clusters=4)
    
    # 6. Model Evaluation Leaderboard
    print("6/8 Generating Model Leaderboard report...")
    eval_service = ModelEvaluationService(
        trained_models_dir=trained_models_dir,
        reports_dir=reports_dir
    )
    eval_service.generate_leaderboard()
    
    # 7. Explainable AI with SHAP
    print("7/8 Generating SHAP Global and Local explanations...")
    explain_service = ExplainabilityService(
        trained_models_dir=trained_models_dir,
        exports_dir=exports_dir
    )
    cust_df = pd.read_csv(features_dir / 'customer_features.csv')
    explain_service.explain_global('churn_prediction_model', cust_df.head(100))
    explain_service.explain_local('churn_prediction_model', cust_df.iloc[[0]])
    
    # 8. Business Recommendations Engine
    print("8/8 Executing business recommendations calculations...")
    rec_service = BusinessRecommendationService(
        exports_dir=exports_dir,
        reports_dir=reports_dir
    )
    rec_service.generate_recommendations()
    
    print("ML Pipeline training completed successfully. All models registered and outputs exported!")

if __name__ == "__main__":
    main()
