"""Authentication helpers and middleware for Dyocense services."""
from __future__ import annotations

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
        auth_ctx = await self._decoder(token)
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


async def noop_decoder(token: str) -> AuthContext:
    """Default decoder for local development that trusts the provided token."""

    tenant_id = token or "demo-tenant"
    return AuthContext(tenant_id=tenant_id, user_id="demo-user", tier="pro", token=token)
