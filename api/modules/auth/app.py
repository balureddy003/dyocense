"""Authentication stub inspired by LibreChat."""
from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.common.auth import AuthContext, noop_decoder

from .schemas import AuthUser, TokenRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])


def _encode_token(username: str, tenant_id: str) -> str:
    payload = f"{tenant_id}:{username}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def _decode_token(token: str) -> AuthContext:
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        tenant_id, username = decoded.split(":", 1)
        return AuthContext(tenant_id=tenant_id, user_id=username, tier="pro", token=token)
    except Exception:  # pragma: no cover - fallback to noop
        return noop_decoder.__wrapped__(token)  # type: ignore[attr-defined]


@router.post("/token", response_model=TokenResponse)
def issue_token(payload: TokenRequest) -> TokenResponse:
    if not payload.username or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username and password required")
    tenant_id = payload.tenant_id or "tenant_demo"
    token = _encode_token(payload.username, tenant_id)
    return TokenResponse(access_token=token, tenant_id=tenant_id)


@router.get("/me", response_model=AuthUser)
def read_current_user(request: Request) -> AuthUser:
    auth: AuthContext | None = getattr(request.state, "auth", None)
    if auth is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return AuthUser(username=auth.user_id or "unknown", tenant_id=auth.tenant_id, tier=auth.tier or "unknown")
