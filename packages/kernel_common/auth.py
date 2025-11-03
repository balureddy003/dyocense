"""OIDC validation stubs for Phase 4."""

from __future__ import annotations

import os
from typing import Tuple


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

    if os.getenv("ALLOW_ANONYMOUS", "false").lower() == "true":
        return "anonymous", "anonymous"

    raise AuthError("Invalid bearer token")


__all__ = ["AuthError", "validate_bearer_token"]
