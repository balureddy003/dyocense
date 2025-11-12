from __future__ import annotations

from fastapi import FastAPI
import importlib
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from packages.kernel_common import persistence
from packages.kernel_common.auth import get_auth_health
from packages.kernel_common.keystone import health_check as get_keystone_health
from packages.kernel_common.logging import configure_logging

logger = configure_logging("kernel")


def _load_service(module_path: str) -> FastAPI | None:
    try:
        module = importlib.import_module(module_path)
        return getattr(module, "app")
    except Exception as exc:  # pragma: no cover - best effort import
        logger.warning("Skipping %s because it failed to import: %s", module_path, exc)
        return None


accounts_app = _load_service("services.accounts.main")
chat_app = _load_service("services.chat.main")
compiler_app = _load_service("services.compiler.main")
forecast_app = _load_service("services.forecast.main")
policy_app = _load_service("services.policy.main")
optimiser_app = _load_service("services.optimiser.main")
diagnostician_app = _load_service("services.diagnostician.main")
explainer_app = _load_service("services.explainer.main")
evidence_app = _load_service("services.evidence.main")
marketplace_app = _load_service("services.marketplace.main")
orchestrator_app = _load_service("services.orchestrator.main")
planner_app = _load_service("services.plan.main")
analyze_app = _load_service("services.analyze.main")
smb_gateway_app = _load_service("services.smb_gateway.main")

SUB_APPS = [
    app
    for app in [
        accounts_app,
        chat_app,
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
        analyze_app,
        smb_gateway_app,
    ]
    if app is not None
]

if os.getenv("ENABLE_CONNECTORS_SERVICE", "false").lower() in ("1", "true", "yes", "on"):
    connectors_app = _load_service("services.connectors.main")
    if connectors_app:
        SUB_APPS.insert(2, connectors_app)

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
        logger.warning(f"Skipping router for sub-app due to error: {e}")

# Back-compat: also expose Accounts under /api/accounts for UIs expecting this prefix
if accounts_app is not None:
    try:
        app.mount("/api/accounts", accounts_app)
    except Exception as e:  # pragma: no cover
        logger.warning("Failed to mount accounts under /api/accounts: %s", e)
else:
    logger.warning("Accounts service unavailable; skipping /api/accounts mount.")


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
            "keystone": get_keystone_health(),
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
