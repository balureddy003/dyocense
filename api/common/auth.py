"""Authentication helpers and middleware for Dyocense services."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from . import context


@dataclass(slots=True)
class AuthContext:
    tenant_id: str
    user_id: Optional[str] = None
    tier: Optional[str] = None
    token: Optional[str] = None


AuthDecoder = Callable[[str], Awaitable[AuthContext]]


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Simple bearer-token middleware with tenant context propagation."""

    def __init__(self, app, decoder: AuthDecoder) -> None:  # type: ignore[override]
        super().__init__(app)
        self._decoder = decoder

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        header = request.headers.get("Authorization")
        if not header or not header.lower().startswith("bearer "):
            return Response(status_code=HTTP_401_UNAUTHORIZED)
        token = header.split(" ", 1)[1]
        try:
            auth_ctx = await self._decoder(token)
        except Exception:
            return Response(status_code=HTTP_401_UNAUTHORIZED)
        context.set_tenant(
            context.TenantContext(
                tenant_id=auth_ctx.tenant_id,
                tier=auth_ctx.tier,
                user_id=auth_ctx.user_id,
            )
        )
        try:
            request.state.auth = auth_ctx
            response = await call_next(request)
            return response
        finally:
            context.clear_tenant()


def _decode_base64_token(token: str) -> AuthContext | None:
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        parts = decoded.split(":")
        tenant_id = parts[0]
        user_id = parts[1] if len(parts) > 1 else "demo-user"
        tier = parts[2] if len(parts) > 2 else "pro"
        return AuthContext(tenant_id=tenant_id, user_id=user_id, tier=tier, token=token)
    except Exception:  # pragma: no cover - graceful fallback
        return None


async def noop_decoder(token: str) -> AuthContext:
    """Default decoder for development that trusts the provided token."""

    context = _decode_base64_token(token)
    if context:
        return context
    tenant_id = token or "demo-tenant"
    return AuthContext(tenant_id=tenant_id, user_id="demo-user", tier="pro", token=token)


async def simple_decoder(token: str) -> AuthContext:
    """Decoder that expects base64-encoded `tenant:user:tier` tokens."""

    context = _decode_base64_token(token)
    if context:
        return context
    tenant_id = token or "demo-tenant"
    return AuthContext(tenant_id=tenant_id, user_id="demo-user", tier="pro", token=token)
