from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_serializer


class WorkspaceCreate(BaseModel):
    name: str
    description: str | None = None


class WorkspaceOut(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    created_at: datetime

    @field_serializer('id', 'tenant_id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True
