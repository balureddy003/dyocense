from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_serializer


class TenantCreate(BaseModel):
    name: str


class TenantOut(BaseModel):
    id: UUID
    name: str
    subscription_status: str
    created_at: datetime

    @field_serializer('id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True
