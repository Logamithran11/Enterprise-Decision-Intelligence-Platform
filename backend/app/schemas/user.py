from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "analyst"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str
