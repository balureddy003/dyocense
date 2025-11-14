from __future__ import annotations

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, pk_uuid


class User(Base, TimestampMixin):
    # Use v4-specific table to avoid collision with legacy schema in backend.models.__init__
    __tablename__ = "users_v4"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_email_per_tenant"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=pk_uuid)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants_v4.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user")
    is_active: Mapped[bool] = mapped_column(default=True)
