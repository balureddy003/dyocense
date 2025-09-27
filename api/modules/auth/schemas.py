"""Schemas for auth endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str
    password: str
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthUser(BaseModel):
    username: str
    tenant_id: str
    tier: str
