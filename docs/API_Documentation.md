# API Documentation

The Enterprise Decision Intelligence Platform exposes versioned REST endpoints built using FastAPI.

## Swagger Interface
Interactive documentation can be accessed locally at:
`http://localhost:8000/docs`

## Endpoints

### 1. Authentication
* **POST `/api/v1/auth/register`**: Register new user accounts.
* **POST `/api/v1/auth/login`**: Authenticate credentials and receive JWT access tokens.
* **GET `/api/v1/auth/me`**: Get currently authenticated user details.

### 2. Analytics & Overview
* **GET `/api/v1/analytics/overview`**: High level KPIs rolled up across all departments.
* **GET `/api/v1/analytics/finance`**: Departmental cash flow, DSCR, and balance sheet metrics.
* **GET `/api/v1/analytics/operations`**: Daily warehouse throughput, incidents, and delay logs.
* **GET `/api/v1/analytics/customers`**: Engagement, health, and activity levels.

### 3. ML Model Predictions
* **POST `/api/v1/prediction/revenue`**: Run revenue forecast inference on input vector.
* **POST `/api/v1/prediction/churn`**: Predict customer attrition probability.
* **POST `/api/v1/prediction/demand`**: Run product demand forecast inference.
* **POST `/api/v1/prediction/risk`**: Run financial, operational, or customer risk assessment.

### 4. Explainable AI & Recommendations
* **GET `/api/v1/explainability/global`**: Get global SHAP feature importances.
* **POST `/api/v1/explainability/local`**: Get local SHAP feature impacts for an input inference.
* **GET `/api/v1/recommendation`**: Get generated business recommendation matrices.
* **POST `/api/v1/recommendation/generate`**: Manually trigger recommendation calculations.
