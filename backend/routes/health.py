"""
Health Check Routes

Provides health and readiness endpoints for monitoring.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check - returns 200 if service is running.
    
    Used by load balancers and monitoring systems.
    """
    return {
        "status": "healthy",
        "service": "dyocense-backend",
        "version": "4.0.0",
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - verifies dependencies are available.
    
    Checks:
    - Database connection
    - Redis connection (if configured)
    
    Returns 200 if ready to serve traffic, 503 otherwise.
    """
    try:
        # Check database
        result = await db.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
        # TODO: Check Redis if configured
        # TODO: Check LLM availability
        
        return {
            "status": "ready",
            "checks": {
                "database": "ok",
                # "redis": "ok",
                # "llm": "ok",
            },
        }
    
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e),
        }, 503
