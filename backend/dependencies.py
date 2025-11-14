"""
Dependency Injection for Dyocense v4.0

Provides reusable dependencies for FastAPI endpoints:
- Database sessions
- Authentication
- Tenant context
- LLM clients
- External API clients
"""

from __future__ import annotations

from typing import AsyncIterator, Annotated

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.config import settings

# =================================================================
# DATABASE SESSION
# =================================================================

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    Provide database session.
    
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =================================================================
# AUTHENTICATION
# =================================================================

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Verify JWT token and return current user.
    
    Raises:
        HTTPException: If token is invalid or expired
    
    Returns:
        dict: User payload from JWT (user_id, tenant_id, email, etc.)
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        
        if user_id is None or tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Verify user is active (not disabled).
    
    Can be extended to check user status in database.
    """
    # TODO: Check user status in database
    # For now, assume all authenticated users are active
    return current_user


# =================================================================
# TENANT CONTEXT (Row-Level Security)
# =================================================================

async def get_tenant_id(
    current_user: dict = Depends(get_current_user),
) -> str:
    """
    Extract tenant_id from authenticated user.
    
    This is used to set PostgreSQL session variable for RLS:
    SET app.current_tenant = '<tenant_id>'
    """
    return current_user["tenant_id"]


async def set_tenant_context(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
) -> AsyncSession:
    """
    Set tenant context for Row-Level Security (RLS).
    
    This ensures queries automatically filter by tenant_id.
    
    Usage:
        @app.get("/metrics")
        async def get_metrics(db: AsyncSession = Depends(set_tenant_context)):
            # RLS automatically filters to current tenant
            result = await db.execute(select(BusinessMetric))
            return result.scalars().all()
    """
    # Set PostgreSQL session variable for RLS
    from sqlalchemy import text
    await db.execute(text("SET app.current_tenant = :tenant_id"), {"tenant_id": tenant_id})
    return db
    return db


# =================================================================
# OPTIONAL DEPENDENCIES (Header-based)
# =================================================================

async def get_tenant_from_header(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> str | None:
    """
    Get tenant_id from X-Tenant-Id header (for public APIs).
    
    This is used for public endpoints that don't require full authentication.
    """
    return x_tenant_id


# =================================================================
# REDIS CLIENT (Caching - Optional)
# =================================================================

_redis_client = None


async def get_redis():
    """
    Get Redis client for caching.
    
    Returns None if Redis is not configured.
    """
    global _redis_client
    
    if settings.REDIS_URL is None:
        return None
    
    if _redis_client is None:
        import redis.asyncio as redis
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    
    return _redis_client


# =================================================================
# LLM CLIENT
# =================================================================

# TODO: Implement backend/services/coach/llm_router.py
# async def get_llm_client():
#     """
#     Get LLM client (hybrid routing between local and cloud).
#     
#     This will be implemented in backend/services/coach/llm_router.py
#     """
#     from backend.services.coach.llm_router import LLMRouter
#     return LLMRouter()


# =================================================================
# TYPE ANNOTATIONS (for FastAPI Depends)
# =================================================================

# Database session dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]

# Database session with tenant context (RLS enabled)
TenantDBSession = Annotated[AsyncSession, Depends(set_tenant_context)]

# Current authenticated user
CurrentUser = Annotated[dict, Depends(get_current_user)]

# Current active user
ActiveUser = Annotated[dict, Depends(get_current_active_user)]

# Tenant ID
TenantID = Annotated[str, Depends(get_tenant_id)]

# Redis client (optional)
RedisClient = Annotated[any, Depends(get_redis)]
