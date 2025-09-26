"""Tenant and request context helpers for Dyocense services."""
from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class TenantContext:
    tenant_id: str
    tier: Optional[str] = None
    user_id: Optional[str] = None


_current_tenant: contextvars.ContextVar[Optional[TenantContext]] = contextvars.ContextVar(
    "current_tenant", default=None
)


def set_tenant(context: TenantContext) -> None:
    """Bind the tenant context to the current task."""
    _current_tenant.set(context)


def clear_tenant() -> None:
    _current_tenant.set(None)


def get_tenant() -> Optional[TenantContext]:
    return _current_tenant.get()
