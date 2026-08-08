from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.api.deps import get_database_session
from app.main import app
from app.models.user import User

# In-memory SQLite database setup for test isolation using StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the in-memory database
Base.metadata.create_all(bind=engine)


def override_get_database_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_database_session] = override_get_database_session
client = TestClient(app)


def test_liveness_readiness_metrics() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # ready checks database status
    ready_resp = client.get("/api/v1/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"

    # metrics endpoint returns plain text
    metrics_resp = client.get("/api/v1/health/metrics")
    assert metrics_resp.status_code == 200
    assert "app_uptime_seconds" in metrics_resp.text


def test_auth_workflow() -> None:
    # 1. Register a user
    reg_payload = {
        "username": "tester",
        "email": "tester@enterprise.com",
        "password": "securepassword",
        "role": "admin"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    assert reg_resp.json()["username"] == "tester"
    assert reg_resp.json()["role"] == "admin"

    # 2. Login
    login_data = {
        "username": "tester",
        "password": "securepassword"
    }
    login_resp = client.post("/api/v1/auth/login", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token is not None
    assert login_resp.json()["role"] == "admin"

    # 3. Access current user endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "tester"
