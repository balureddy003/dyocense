"""OIDC validation stubs for Phase 4."""

from __future__ import annotations

import os
from typing import Tuple

try:
    from packages.accounts.repository import get_tenant_by_token, decode_jwt, get_api_token
except Exception:  # pragma: no cover - accounts package optional during bootstrap
    get_tenant_by_token = None
    decode_jwt = None
    get_api_token = None


class AuthError(Exception):
    """Raised when authentication fails."""


def validate_bearer_token(token: str) -> Tuple[str, str]:
    """
    Validate an incoming bearer token (stub).

    Returns:
        Tuple of (tenant_id, subject) extracted from the token.

    Raises:
        AuthError: if the token is missing or invalid.
    """
    if not token:
        raise AuthError("Missing bearer token")

    # Phase 4 stub: accept tokens that start with "demo-" and treat suffix as tenant.
    if token.startswith("demo-"):
        tenant_id = token.split("-", 1)[1] or "demo"
        return tenant_id, "stub-user"

    if decode_jwt and token.count(".") == 2:
        payload = decode_jwt(token)
        if payload:
            tenant_id = payload.get("tenant_id")
            subject = payload.get("sub") or payload.get("user_id") or "user"
            if tenant_id:
                return tenant_id, subject

    if get_tenant_by_token:
        tenant = get_tenant_by_token(token)
        if tenant:
            return tenant.tenant_id, "api-key"
    if get_api_token:
        record = get_api_token(token)
        if record:
            return record.tenant_id, record.user_id or "api-key"

    if os.getenv("ALLOW_ANONYMOUS", "false").lower() == "true":
        return "anonymous", "anonymous"

    raise AuthError("Invalid bearer token")


__all__ = ["AuthError", "validate_bearer_token"]
