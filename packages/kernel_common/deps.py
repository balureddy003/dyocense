"""Common FastAPI dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from .auth import AuthError, validate_bearer_token


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

    return {"tenant_id": tenant_id, "subject": subject}


__all__ = ["require_auth"]
