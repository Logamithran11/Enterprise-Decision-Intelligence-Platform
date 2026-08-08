# Platform Demo Script (5-Minute Walkthrough)

This script outlines a 5-minute verbal and visual walkthrough of the platform for stakeholders.

## 00:00 - 00:45: Problem Statement & Value Proposition
- **Speaker**: "Welcome. Today I am showing the Enterprise Decision Intelligence Platform. Large e-commerce operators like Olist face a massive challenge: they capture huge transaction databases but fail to turn that raw data into proactive decisions. They react to churn, stockouts, and margin decay after they occur."
- **Speaker**: "Our platform connects ERP, CRM, and supply chain data directly to machine learning pipelines, providing explainable predictions and real-time business recommendations."

## 00:45 - 01:30: Platform Architecture & Data Pipeline
- **Speaker**: "We use a clean architecture. Raw data is ingested, cleaned, and validated using rigorous schemas. We calculate time-series lag variables, rolling margins, and customer activity metrics."
- **Speaker**: "All enterprise tables—finance, inventory, employees, marketing, operations, and risk metrics—are synthesized using business correlation logic. If inventory levels fall, stockout risks automatically propagate through warehouse downtime and delivery delays, which in turn spikes customer risk."

## 01:30 - 02:45: Machine Learning & Explainable AI (SHAP)
- **Speaker**: "Our ML core deploys optimized XGBoost and Random Forest models. In our Forecast Center, users can run simulated predictions."
- **Speaker**: "But black-box predictions are not enough. We implement SHAP—Explainable AI—at both local and global levels. When a customer's churn prediction is run, the dashboard decomposes the output showing exactly how variables like days since last order (+) or low engagement (+) pushed the model's decision."

## 02:45 - 03:45: Prescriptive Recommendation Engine
- **Speaker**: "Predictions are only valuable if they lead to action. The Recommendation Desk evaluates the risk outputs and ML forecasts against logical business constraints."
- **Speaker**: "It outlines exact corrective actions: e.g., 'Execute localized retention campaigns' for high-churn accounts, or 'Optimize safety stock limits' for at-risk warehouses. Each recommendation is tagged with Estimated ROI, Priority, and Time to Benefit."

## 03:45 - 05:00: Frontend Dashboard, Deployment & DevOps
- **Speaker**: "The frontend is a React TypeScript SPA served using Nginx. It utilizes live backend APIs with full type safety."
- **Speaker**: "The deployment setup is completely containerized. A simple `docker-compose up` orchestrates PostgreSQL, Redis, FastAPI backend workers, Celery task runners, and the Nginx frontend."
- **Speaker**: "Our robust CI/CD pipeline enforces Ruff formatting, MyPy checks, test compliance, and automated Docker build checks on every pull request."
- **Speaker**: "This is a complete, scalable framework for modern Enterprise Decision Intelligence."
