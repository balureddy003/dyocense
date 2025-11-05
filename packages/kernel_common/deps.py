"""Common FastAPI dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from .auth import AuthError, validate_bearer_token

try:
    from packages.accounts.repository import decode_jwt
except Exception:  # pragma: no cover
    decode_jwt = None


async def require_auth(authorization: str = Header(default="")) -> dict:
    """Validate bearer token and expose identity to route handlers."""
    token = authorization.replace("Bearer ", "")
    try:
        tenant_id, subject = validate_bearer_token(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    identity = {"tenant_id": tenant_id, "subject": subject}
    if decode_jwt and token.count(".") == 2:
        payload = decode_jwt(token)
        if payload:
            identity.update(
                {
                    "email": payload.get("email"),
                    "name": payload.get("name"),
                    "roles": payload.get("roles", []),
                }
            )

    return identity


__all__ = ["require_auth"]
