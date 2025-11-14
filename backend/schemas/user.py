from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_serializer


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"


class UserOut(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    @field_serializer('id', 'tenant_id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True
