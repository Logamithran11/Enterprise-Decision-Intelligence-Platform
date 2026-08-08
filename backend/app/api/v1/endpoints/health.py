from __future__ import annotations

from datetime import datetime, timezone
import time
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.sql import text
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_database_session
from app.core.config import Settings
from app.schemas.common import HealthResponse

router = APIRouter()

# Keep track of startup time to compute uptime
START_TIME = time.time()


@router.get("", response_model=HealthResponse, summary="Liveness Probe Check")
def health(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready", summary="Readiness Probe Check")
def ready(
    db: Session = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings)
) -> dict[str, str]:
    # Check Database connection
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {e}"
        )

    # Check Redis / Celery broker connectivity
    try:
        import redis
        # Extract host and port from broker url
        # e.g., redis://localhost:6379/0
        broker_url = settings.celery_broker_url
        if broker_url.startswith("redis://"):
            conn_str = broker_url.split("redis://")[1].split("/")[0]
            host = conn_str.split(":")[0]
            port = int(conn_str.split(":")[1]) if ":" in conn_str else 6379
            r = redis.Redis(host=host, port=port, socket_timeout=2.0)
            r.ping()
    except Exception as e:
        # If redis is not installed or unreachable, log warning.
        # We make it optional in local environment to not block uvicorn startup.
        if settings.environment == "production":
            raise HTTPException(
                status_code=503,
                detail=f"Redis connection failed: {e}"
            )
            
    return {
        "status": "ready",
        "service": settings.app_name,
        "database": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/metrics", summary="Application Metrics")
def metrics(settings: Settings = Depends(get_app_settings)) -> Response:
    uptime = time.time() - START_TIME
    
    # Prometheus exposition format
    metrics_str = (
        f"# HELP app_uptime_seconds Uptime of the application in seconds.\n"
        f"# TYPE app_uptime_seconds gauge\n"
        f"app_uptime_seconds {uptime:.2f}\n"
        f"# HELP app_info Info metadata about the application.\n"
        f"# TYPE app_info gauge\n"
        f'app_info{{service="{settings.app_name}",version="{settings.app_version}",environment="{settings.environment}"}} 1\n'
    )
    return Response(content=metrics_str, media_type="text/plain")
