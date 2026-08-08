# Architecture Overview

## Goals

Build a modular enterprise SaaS platform that supports decision intelligence across sales, finance, customer, operations, inventory, and risk domains.

## Layered Architecture

### Presentation Layer
- React and TypeScript dashboard application
- Recharts visualizations
- Role-aware navigation and executive-grade UI surfaces

### API Layer
- FastAPI REST services
- Versioned routes under `/api/v1`
- Pydantic contracts for validation and OpenAPI generation

### Application Layer
- Business services orchestrating analytics, recommendations, and ML inference
- Shared cross-domain abstractions for alerts, exports, and scenario analysis

### Domain Layer
- Models for customers, products, orders, inventory, suppliers, marketing, employees, finance, and operations
- Repository interfaces for persistence isolation

### Infrastructure Layer
- PostgreSQL for transactional data
- Alembic for schema migrations
- Celery for asynchronous jobs and notification workflows
- Redis for broker & caching
- Docker Compose for local orchestration

---

## Diagrams

### 1. Platform Architecture Diagram
```mermaid
graph TD
    UI[React Frontend - Nginx] -->|HTTP / JSON| API[FastAPI Backend - Uvicorn]
    API --> DB[(PostgreSQL Database)]
    API --> Broker{Redis Message Broker}
    Broker --> Worker[Celery Background Workers]
    Worker --> DB
    Worker --> Registry[Model Registry - Joblib]
```

### 2. Entity-Relationship (ER) Diagram
```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER ||--|| RISK_METRIC : assesses
    PRODUCT ||--o{ ORDER_ITEM : contains
    ORDER ||--|{ ORDER_ITEM : "consists of"
    ORDER ||--|| FINANCE : "triggers billing"
    PRODUCT ||--|| INVENTORY : "tracked in"
    WAREHOUSE ||--o{ INVENTORY : stocks
    WAREHOUSE ||--o{ OPERATION : "logs performance"
```

### 3. Data Flow Diagram
```mermaid
graph LR
    RawData[Raw CSV Ingestion] --> Cleaner[Data Cleaner]
    Cleaner --> Validator[Data Validator]
    Validator --> FeatureEng[Feature Engineering]
    FeatureEng --> MLModels[Model Training / Inference]
    MLModels --> RecEngine[Prescriptive Recommendation Engine]
    RecEngine --> Dashboard[React Business Dashboards]
```

### 4. Machine Learning Pipeline Diagram
```mermaid
graph TD
    Raw[Ingested Features] --> Split[Train/Test Stratified Split]
    Split --> SMOTE[Imbalance Handling]
    SMOTE --> Optuna[Optuna Hyperparameter Tuning]
    Optuna --> RF[Random Forest]
    Optuna --> XGB[XGBoost]
    RF --> Select[Best Model Selection]
    XGB --> Select
    Select --> SHAP[SHAP Explainability Calculation]
    SHAP --> Register[Register Model Registry]
```

### 5. Deployment Diagram
```mermaid
graph TD
    subgraph "Docker Compose Mesh"
        Nginx[Nginx Container - Port 3000] -->|Reverse Proxy| FastAPI[FastAPI Container - Port 8000]
        FastAPI --> Postgres[Postgres DB Container - Port 5432]
        FastAPI --> Redis[Redis Cache/Broker Container - Port 6379]
        Redis --> Celery[Celery Worker Container]
        Celery --> Postgres
    end
```

