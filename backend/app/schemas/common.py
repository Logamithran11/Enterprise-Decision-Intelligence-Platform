from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    detail: str
    error_type: str
