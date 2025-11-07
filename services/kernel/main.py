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
from services.plan.main import app as planner_app
from services.accounts.main import app as accounts_app
from services.chat.main import app as chat_app
from services.connectors.main import app as connectors_app
from packages.kernel_common import persistence
from packages.kernel_common.auth import get_auth_health

SUB_APPS = [
    accounts_app,
    chat_app,
    connectors_app,
    compiler_app,
    forecast_app,
    policy_app,
    optimiser_app,
    diagnostician_app,
    explainer_app,
    evidence_app,
    marketplace_app,
    orchestrator_app,
    planner_app,
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
    # Add each sub-service router and tag its operations with the service title
    # This keeps a single, flat API surface while grouping docs nicely.
    try:
        service_tag = getattr(sub_app, "title", None) or sub_app.__class__.__name__
        app.include_router(sub_app.router, tags=[service_tag])
        # Additionally, expose accounts routes at root for direct access
        if sub_app is accounts_app:
            app.include_router(accounts_app.router)
        # Mount each sub-app at /api/{service} for backward compatibility
        service_name = service_tag.lower().replace(' ', '_').replace('service', '').replace('api', '').strip('_')
        app.mount(f"/api/{service_name}", sub_app)
    except Exception as e:
        import logging
        logging.getLogger("kernel").warning(f"Skipping router for sub-app due to error: {e}")

# Back-compat: also expose Accounts under /api/accounts for UIs expecting this prefix
try:
    # accounts_app is imported above
    app.mount("/api/accounts", accounts_app)
except Exception as e:  # pragma: no cover
    import logging
    logging.getLogger("kernel").warning(f"Failed to mount accounts under /api/accounts: {e}")


@app.get("/healthz", tags=["system"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/health/detailed", tags=["system"])
def detailed_health() -> dict:
    """Comprehensive health check including external dependencies."""
    health_data = {
        "status": "ok",
        "version": app.version,
        "services": {
            "persistence": persistence.health_check(),
            "authentication": get_auth_health(),
            # Add more health checks as other services are implemented
        }
    }
    
    # Determine overall status
    service_statuses = [s.get("status") for s in health_data["services"].values()]
    if any(s == "unhealthy" for s in service_statuses):
        health_data["status"] = "unhealthy"
    elif any(s == "degraded" for s in service_statuses):
        health_data["status"] = "degraded"
    
    return health_data


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
