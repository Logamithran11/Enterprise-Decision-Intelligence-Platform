from __future__ import annotations

from datetime import timedelta
from jose import jwt

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.config import get_settings


def test_auth_password_cryptography() -> None:
    raw_pwd = "my-secure-password"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed)
    assert not verify_password("wrong-password", hashed)


def test_auth_token_claims() -> None:
    claims = {"sub": "enterprise_user", "role": "executive"}
    token = create_access_token(claims, expires_delta=timedelta(minutes=10))
    assert isinstance(token, str)

    settings = get_settings()
    decoded = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm]
    )
    assert decoded["sub"] == "enterprise_user"
    assert decoded["role"] == "executive"
