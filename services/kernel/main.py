from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from services.compiler.main import app as compiler_app
from services.forecast.main import app as forecast_app
from services.policy.main import app as policy_app
from services.optimiser.main import app as optimiser_app
from services.diagnostician.main import app as diagnostician_app
from services.explainer.main import app as explainer_app
from services.evidence.main import app as evidence_app
from services.marketplace.main import app as marketplace_app
from services.orchestrator.main import app as orchestrator_app

SUB_APPS = [
    compiler_app,
    forecast_app,
    policy_app,
    optimiser_app,
    diagnostician_app,
    explainer_app,
    evidence_app,
    marketplace_app,
    orchestrator_app,
]

app = FastAPI(
    title="Dyocense Kernel API",
    version="0.6.0",
    description="Unified entrypoint for Dyocense Decision Kernel services.",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for sub_app in SUB_APPS:
    app.include_router(sub_app.router)


@app.get("/healthz", tags=["system"])
def health() -> dict:
    return {"status": "ok"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path in openapi_schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation.setdefault("security", []).append({"bearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
