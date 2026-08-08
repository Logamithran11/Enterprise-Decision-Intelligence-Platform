# Enterprise Decision Intelligence & Business Insight Generation Platform

A production-grade decision intelligence monorepo turning enterprise business metrics into predictive forecasts, explainable risk assessments, and prescriptive recommendations.

## Platform Architecture

The monorepo contains a FastAPI backend service, a Vite React TypeScript dashboard frontend, and offline Jupyter research notebooks.

```text
├── backend/                  # FastAPI Application, Celery Workers, & Python ML Services
│   ├── app/
│   │   ├── api/              # Versioned REST Controllers (Health, Auth, Predictions, Recs)
│   │   ├── core/             # Application Configurations, JWT Security, logging
│   │   ├── db/               # SQLAlchemy Models, Session, and base declarations
│   │   ├── ml/               # Predictive Models (Revenue, Churn, Demand, Risk, Segments, SHAP)
│   │   └── schemas/          # Pydantic schema validation models
│   └── tests/                # Automated unit and integration test suites
├── frontend/                 # Vite + React + TypeScript + Tailwind CSS Dashboard
│   ├── src/
│   │   ├── components/       # Reusable layout and chart components
│   │   ├── layouts/          # Navigation Sidebars, profiles, theme handlers
│   │   ├── pages/            # Executive, Sales, Finance, Operations, Customer tabs
│   │   └── services/         # REST API fetch clients
├── notebooks/                # Model development, EDA, and Storytelling walkthroughs
├── exports/                  # Persisted CSV prediction outputs
├── reports/                  # Markdown evaluations, segment personas, and risk profiles
└── trained_models/           # Serialized Joblib models and registered metadata
```

---

## Backend ML Pipeline Primitives (Modules 02 - 13)

### 02 & 03 Data Cleaning & Validation
* Standardizes transactional, product, customer, and supplier data fields.
* Audits schema profiles, key integrity, value constraints, and exports Markdown data quality logs.

### 04 & 05 Exploratory Analysis & Feature Engineering
* Extracts aggregate KPIs, time lags, rolling averages, log transforms, and MinMax scaling.
* Computes feature correlation matrixes and saves target schema drift JSON mappings.

### 06 & 07 Revenue & Churn Prediction
* Trains and optimises XGBoost regressors and classifiers with Optuna hyperparameter tuning.
* Evaluates accuracy, precision, recall, F1, and MAE across time-series validations.

### 08 & 09 Business Risk & Demand Forecasting
* Scores Customer, Financial (DSCR and liquidity), and Operational (inventory stockout) risks.
* Predicts product-level demand volumes and logs safety reorder quantities.

### 10 Customer Segmentation
* Segments accounts using KMeans clustering and silhouette validation.
* Identifies persona descriptions (VIP, Active, Churn Risk, Dormant) and charts PCA distribution maps.

### 11 Model Registry & Version Control
* Seals feature schemas, hyperparameter sets, model binaries, and logs metrics metadata.
* Monitors incoming data drift using Kolmogorov-Smirnov statistical tests.

### 12 Explainable AI (SHAP)
* Computes global feature importances and local feature impact values for specific inferences.

### 13 Prescriptive Recommendation Desk
* Feeds forecast outputs and risk matrices into root-cause rules.
* Outlines corrective actions with estimated ROI, horizons, confidence, and priority tags.

---

## Running the Platform

### Local Development

1. **Backend API**:
   ```bash
   cd backend
   # Install dependencies
   pip install -e ".[ml]"
   # Run model training orchestrator
   python run_training.py
   # Start Uvicorn Dev Server
   uvicorn app.main:app --reload
   ```

2. **Frontend UI**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker Compose Deployment

Build and orchestrate the full stack (FastAPI Backend, Redis, Postgres DB, Celery worker, React UI) in a single command:
```bash
docker-compose up --build
```
* **Frontend Dashboard**: View at `http://localhost:3000`
* **API Documentation**: Inspect Swagger docs at `http://localhost:8000/docs`

---

## Testing & CI/CD

Run the comprehensive unit and integration test suite:
```bash
cd backend
pytest
```
We also ship GitHub Actions workflows (`.github/workflows/ci.yml`) validating Ruff linting, MyPy type checks, pytest suites, frontend builds, and Docker compile tasks.
