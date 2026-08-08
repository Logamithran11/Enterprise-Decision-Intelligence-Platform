from __future__ import annotations

from datetime import timedelta

from app.core.config import Settings
from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_settings_support_production_flags() -> None:
    settings = Settings(APP_ENVIRONMENT="production", APP_DEBUG="false")

    assert settings.environment == "production"
    assert settings.is_production is True


def test_password_hashing_round_trip() -> None:
    hashed_password = hash_password("StrongPassword123!")

    assert verify_password("StrongPassword123!", hashed_password) is True


def test_jwt_token_round_trip() -> None:
    token = create_access_token(
        subject="user-123",
        secret_key="unit-test-secret",
        algorithm="HS256",
        expires_delta=timedelta(minutes=15),
    )

    decoded = decode_token(token, "unit-test-secret", "HS256")

    assert decoded["sub"] == "user-123"
