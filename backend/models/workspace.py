from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, pk_uuid


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=pk_uuid)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants_v4.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
