from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI

from packages.kernel_common import load_schema
from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging
from packages.archetypes import REGISTRY

logger = configure_logging("marketplace-service")

app = FastAPI(
    title="Dyocense Marketplace Service",
    version="0.5.0",
    description="Phase 5 stub exposing marketplace catalog entries.",
)


@app.get("/v1/catalog")
def get_catalog(identity: dict = Depends(require_auth)) -> dict:
    """Return a static catalog referencing OCI bundles."""
    logger.info("Catalog requested by tenant %s", identity["tenant_id"])
    catalog_schema = load_schema("catalog.schema.json")
    return {
        "$schema": catalog_schema.get("$schema"),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "items": [
            {
                "id": archetype.id,
                "name": archetype.name,
                "category": "archetype",
                "version": "0.1.0",
                "description": archetype.description,
                "data_inputs": archetype.data_inputs,
                "artifact": {
                    "type": "oci",
                    "uri": f"oci://registry.example.com/dyocense/archetypes/{archetype.id}:0.1.0",
                },
            }
            for archetype in REGISTRY.values()
        ],
    }
