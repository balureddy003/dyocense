"""Unified Dyocense backend service aggregating all domain APIs."""
from __future__ import annotations

from typing import Iterable, Tuple

from fastapi import FastAPI
from fastapi.routing import APIRoute

from api.common import BearerAuthMiddleware, simple_decoder

# Import existing service apps so we can reuse their routers and dependencies.
from api.modules.plan.app import app as plan_app
from api.modules.goal.app import app as goal_app
from api.modules.evidence.app import app as evidence_app
from api.modules.feedback.app import app as feedback_app
from api.modules.policy.app import app as policy_app
from api.modules.scheduler.app import app as scheduler_app
from api.modules.market.app import app as market_app
from api.modules.negotiation.app import app as negotiation_app
from api.modules.auth.app import router as auth_router
from api.modules.llm_router.app import router as llm_router


def _dedupe_routes(app: FastAPI) -> None:
    """Remove duplicate routes (same path + methods) keeping the first entry."""

    seen: set[Tuple[str, Tuple[str, ...]]] = set()
    unique = []
    for route in app.router.routes:
        if isinstance(route, APIRoute):
            methods = tuple(sorted(route.methods or []))
            key = (route.path, methods)
            if key in seen:
                continue
            seen.add(key)
        unique.append(route)
    app.router.routes = unique


def _include_service_routes(app: FastAPI, service_app: FastAPI) -> None:
    """Include routes from a service FastAPI app, deduping overlaps."""

    app.include_router(service_app.router)
    _dedupe_routes(app)


def create_app() -> FastAPI:
    app = FastAPI(title="Dyocense Backend Service", version="0.1.0")
    app.add_middleware(BearerAuthMiddleware, decoder=simple_decoder)

    @app.get("/health", tags=["health"])
    def backend_health() -> dict:
        return {"status": "ok", "services": [svc.title for svc in _service_apps()]}

    for service in _service_apps():
        _include_service_routes(app, service)

    app.include_router(auth_router)
    app.include_router(llm_router)

    return app


def _service_apps() -> Iterable[FastAPI]:
    return (
        plan_app,
        goal_app,
        evidence_app,
        feedback_app,
        policy_app,
        scheduler_app,
        market_app,
        negotiation_app,
    )


app = create_app()
