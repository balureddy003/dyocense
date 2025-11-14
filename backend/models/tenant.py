from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, pk_uuid


class Tenant(Base, TimestampMixin):
    # Use v4-specific table to avoid collision with legacy schema in backend.models.__init__
    __tablename__ = "tenants_v4"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=pk_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(32), default="active")
