from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.prediction import router as prediction_router
from app.api.v1.endpoints.recommendation import router as recommendation_router
from app.api.v1.endpoints.explainability import router as explainability_router
from app.api.v1.endpoints.admin import router as admin_router

api_router = APIRouter()

# Liveness/Readiness probes and metrics
api_router.include_router(health_router, prefix="/health", tags=["Monitoring"])

# Auth operations
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Aggregated historical reports
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

# ML Model serving endpoints
api_router.include_router(prediction_router, prefix="/prediction", tags=["Predictions"])

# Prescriptive recommendations
api_router.include_router(recommendation_router, prefix="/recommendation", tags=["Recommendations"])

# Explainable AI features
api_router.include_router(explainability_router, prefix="/explainability", tags=["Explainability"])

# Drift detection and registry inspection
api_router.include_router(admin_router, prefix="/admin", tags=["Administration"])
