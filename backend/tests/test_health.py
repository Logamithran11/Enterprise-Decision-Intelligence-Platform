from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_endpoint_returns_expected_metadata() -> None:
    app = create_app(Settings(APP_ENVIRONMENT="local", APP_DEBUG="true"))

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "Enterprise Decision Intelligence Platform"
    assert payload["environment"] == "local"


def test_root_endpoint_reports_service_status() -> None:
    app = create_app(Settings(APP_ENVIRONMENT="development"))

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"
    assert payload["version"] == "0.1.0"
