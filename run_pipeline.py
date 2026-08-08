import sys
from pathlib import Path

# Add backend directory to path
project_root = Path(__file__).resolve().parent
backend_root = project_root / 'backend'
sys.path.insert(0, str(backend_root))

from app.pipelines.synthetic_dataset import generate_synthetic_enterprise_dataset, SyntheticDatasetConfig
from app.pipelines.data_cleaning import EnterpriseDataCleaner, CleaningPaths
from app.pipelines.data_validation import EnterpriseDataValidator, ValidationPaths
from app.features.feature_engineering import EnterpriseFeatureEngineer, FeatureEngineeringPaths

def main():
    print("Starting execution of data pipeline...")
    raw_dir = project_root / 'datasets'
    processed_dir = project_root / 'processed'
    features_dir = project_root / 'features'
    reports_dir = project_root / 'reports'
    
    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate datasets
    print("1. Generating synthetic enterprise datasets...")
    config = SyntheticDatasetConfig()
    generate_synthetic_enterprise_dataset(raw_dir, config)
    print("Datasets generated successfully.")
    
    # 2. Clean datasets
    print("2. Standardizing and cleaning raw datasets...")
    cleaner = EnterpriseDataCleaner(CleaningPaths(raw_dir=raw_dir, processed_dir=processed_dir, features_dir=features_dir, reports_dir=reports_dir))
    TABLES = ["customers", "products", "suppliers", "employees", "marketing_campaigns", "orders", "inventory_snapshots", "finance_monthly", "operations_daily", "customer_kpis"]
    cleaner.clean_all(TABLES)
    print("Data cleaning completed.")
    
    # 3. Validate processed datasets
    print("3. Running data validation checks...")
    validator = EnterpriseDataValidator(ValidationPaths(processed_dir=processed_dir, reports_dir=reports_dir))
    validation_results = validator.validate_all()
    print("Validation completed. Results written to reports.")
    
    # 4. Feature engineering
    print("4. Engineering model features...")
    engineer = EnterpriseFeatureEngineer(FeatureEngineeringPaths(processed_dir=processed_dir, features_dir=features_dir, reports_dir=reports_dir))
    engineer.build_feature_package()
    print("Feature package built successfully. Feature engineering finished!")

if __name__ == "__main__":
    main()
