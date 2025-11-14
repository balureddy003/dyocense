"""
API Routes - Export all routers

This module exports all API routers for easy import in main.py
"""

from backend.routes.health import router as health_router
from backend.routes.tenant import router as tenant_router
from backend.routes.user import router as user_router
from backend.routes.workspace import router as workspace_router
from backend.routes.auth import router as auth_router
from backend.routes.coach import router as coach_router
from backend.routes.optimizer import router as optimizer_router
from backend.routes.forecaster import router as forecaster_router
from backend.routes.evidence import router as evidence_router
from backend.routes.connector import router as connector_router

__all__ = [
    "health_router",
    "tenant_router",
    "user_router",
    "workspace_router",
    "auth_router",
    "coach_router",
    "optimizer_router",
    "forecaster_router",
    "evidence_router",
    "connector_router",
]
