"""
Auth Routes

JWT-based authentication with bcrypt password hashing.
Issues access token with user claims (sub, tenant_id, email, role).
Instrumented with Prometheus metrics for observability.
"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.dependencies import get_current_user, get_db
from backend.models.user import User
from backend.utils.auth import verify_password, create_access_token
from backend.utils.metrics import record_auth_login

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """
    Authenticate user with email and password, return JWT access token.
    
    Args:
        payload: Login credentials
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    start_time = time.time()
    tenant_id = payload.tenant_id or "00000000-0000-0000-0000-000000000000"
    
    # Lookup user by email and tenant_id
    result = await db.execute(
        select(User).where(User.email == payload.email, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        duration = time.time() - start_time
        record_auth_login(tenant_id=tenant_id, status="user_not_found", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(payload.password, user.hashed_password):
        duration = time.time() - start_time
        record_auth_login(tenant_id=tenant_id, status="invalid_credentials", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        duration = time.time() - start_time
        record_auth_login(tenant_id=tenant_id, status="account_disabled", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Create access token
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(token_data)
    
    # Record successful login
    duration = time.time() - start_time
    record_auth_login(tenant_id=tenant_id, status="success", duration=duration)
    
    return TokenResponse(access_token=access_token)


class MeResponse(BaseModel):
    sub: str
    tenant_id: str
    email: EmailStr
    role: str


@router.get("/me", response_model=MeResponse)
async def me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    """
    Get current authenticated user info from JWT.
    
    Args:
        current_user: Decoded JWT payload
        
    Returns:
        User info
    """
    return MeResponse(
        sub=current_user["sub"],
        tenant_id=current_user["tenant_id"],
        email=current_user["email"],
        role=current_user.get("role", "user"),
    )
