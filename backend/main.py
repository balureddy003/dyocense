"""
Dyocense v4.0 Unified Backend - FastAPI Monolith Entry Point

This replaces 19 microservices with a single, cost-optimized application.
Architecture: Modular monolith with clear separation of concerns.

Key features:
- Multi-tenant isolation via Row-Level Security (RLS)
- PostgreSQL with TimescaleDB, pgvector, Apache AGE
- Hybrid LLM routing (70% local, 30% cloud)
- OpenTelemetry instrumentation
- Prometheus metrics
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy import text

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from backend.config import settings
from backend.dependencies import get_db
from backend.routes import (
    coach_router,
    optimizer_router,
    forecaster_router,
    evidence_router,
    connector_router,
    tenant_router,
    user_router,
    workspace_router,
    auth_router,
    health_router,
)
from backend.utils.logging import setup_logging
from backend.utils.observability import setup_tracing, setup_metrics

# Configure logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager - handles startup and shutdown tasks.
    
    Startup:
    - Initialize database connections
    - Setup observability (tracing, metrics)
    - Warm up LLM connections
    
    Shutdown:
    - Close database connections
    - Flush metrics
    - Cleanup resources
    """
    logger.info("Starting Dyocense v4.0 backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    
    # Initialize database
    try:
        # Test database connection
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            logger.info("Database connection verified")
            break
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    # Setup observability
    if settings.ENABLE_PROMETHEUS:
        setup_metrics()
        logger.info("Prometheus metrics enabled")
    
    # Warm up LLM connections (optional)
    # TODO: Implement backend/services/coach/llm_router.py
    # if settings.ENABLE_LOCAL_LLM:
    #     from backend.services.coach.llm_router import warm_up_llm
    #     await warm_up_llm()
    #     logger.info("Local LLM warmed up")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down Dyocense v4.0 backend...")
    # Database connections will be closed automatically by SQLAlchemy
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Dyocense v4.0",
    description="""
    AI-Powered Business Intelligence Platform for SMBs
    
    Features:
    - **AI Coach**: Natural language business insights and recommendations
    - **Optimization**: Inventory, staffing, and budget optimization
    - **Forecasting**: ARIMA, Prophet, XGBoost with uncertainty quantification
    - **Causal Inference**: Understand why metrics changed
    - **External Benchmarks**: Compare against industry standards
    
    Cost: <$30/month per tenant (vs $500-1500 for traditional BI tools)
    """,
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Instrument tracing before server start to avoid middleware errors
if settings.ENABLE_TRACING:
    setup_tracing(app, settings.OTEL_SERVICE_NAME, settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    logger.info("OpenTelemetry tracing enabled")

# CORS middleware - must be added early
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(tenant_router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(workspace_router, prefix="/api/v1/workspaces", tags=["Workspaces"])
app.include_router(coach_router, prefix="/api/v1/coach", tags=["AI Coach"])
app.include_router(optimizer_router, prefix="/api/v1/optimize", tags=["Optimization"])
app.include_router(forecaster_router, prefix="/api/v1/forecast", tags=["Forecasting"])
app.include_router(evidence_router, prefix="/api/v1/evidence", tags=["Evidence"])
app.include_router(connector_router, prefix="/api/v1/connectors", tags=["Connectors"])

# Mount Prometheus metrics endpoint
if settings.ENABLE_PROMETHEUS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors gracefully"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.ENVIRONMENT != "production" else "An error occurred",
        },
    )


# Root endpoint
@app.get("/")
async def root():
    """API root - basic info"""
    return {
        "name": "Dyocense v4.0",
        "version": "4.0.0",
        "description": "AI-Powered Business Intelligence for SMBs",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else None,
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
