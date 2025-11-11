"""
Connectors Service

Manages data source connectors with secure credential storage.
Supports OAuth flows, API key authentication, and connector testing.
"""

import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Any, cast

from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.connectors.models import (
    ConnectorConfig,
    ConnectorResponse,
    ConnectorStatus,
    ConnectorTestResult,
    SyncFrequency,
)
from packages.connectors.repository import ConnectorRepository as MongoConnectorRepository
from packages.connectors.repository_postgres import ConnectorRepositoryPG
from packages.connectors.testing import ConnectorTester

# Connector marketplace metadata
from packages.connectors.catalog import CONNECTOR_CATALOG

logger = logging.getLogger(__name__)

ERP_MCP_SCRIPT = Path(__file__).with_name("erpnext_mcp.py")
CSV_MCP_SCRIPT = Path(__file__).with_name("csv_mcp.py")
CSV_DATA_DIR = os.getenv("CSV_DATA_DIR", "/data/csv")

# Track per-connector MCP processes
erp_mcp_processes: dict[str, subprocess.Popen] = {}
csv_mcp_processes: dict[str, subprocess.Popen] = {}


def _erp_mcp_is_running(connector_id: str) -> bool:
    proc = erp_mcp_processes.get(connector_id)
    return proc is not None and (proc.poll() is None)


def _start_erp_mcp_for(tenant_id: str, connector_id: str) -> None:
    if not ERP_MCP_SCRIPT.exists():
        logger.warning("ERPNext MCP script not found at %s", ERP_MCP_SCRIPT)
        return
    if _erp_mcp_is_running(connector_id):
        return
    cmd = [sys.executable, str(ERP_MCP_SCRIPT), "--tenant", tenant_id, "--connector", connector_id]
    env = os.environ.copy()
    try:
        proc = subprocess.Popen(cmd, env=env, stdout=sys.stdout, stderr=sys.stderr)
        erp_mcp_processes[connector_id] = proc
        logger.info("Started ERPNext MCP for %s (pid=%s)", connector_id, proc.pid)
    except Exception as exc:
        logger.error("Failed to launch ERPNext MCP for %s: %s", connector_id, exc)


def _stop_erp_mcp_for(connector_id: str) -> None:
    proc = erp_mcp_processes.get(connector_id)
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
        erp_mcp_processes.pop(connector_id, None)
        logger.info("ERPNext MCP for %s terminated", connector_id)
    except Exception as exc:
        logger.warning("Failed to stop ERPNext MCP for %s: %s", connector_id, exc)


def _csv_mcp_is_running(connector_id: str) -> bool:
    proc = csv_mcp_processes.get(connector_id)
    return proc is not None and (proc.poll() is None)

def _start_csv_mcp_for(tenant_id: str, connector_id: str, data_dir: str | None = None) -> None:
    if not CSV_MCP_SCRIPT.exists():
        logger.warning("CSV MCP script not found at %s", CSV_MCP_SCRIPT)
        return
    if _csv_mcp_is_running(connector_id):
        return
    cmd = [sys.executable, str(CSV_MCP_SCRIPT), "--tenant", tenant_id, "--connector", connector_id]
    env = os.environ.copy()
    if data_dir:
        env["CSV_DATA_DIR"] = data_dir
    try:
        proc = subprocess.Popen(cmd, env=env, stdout=sys.stdout, stderr=sys.stderr)
        csv_mcp_processes[connector_id] = proc
        logger.info("Started CSV MCP for %s (pid=%s)", connector_id, proc.pid)
    except Exception as exc:
        logger.error("Failed to launch CSV MCP for %s: %s", connector_id, exc)


def _stop_csv_mcp_for(connector_id: str) -> None:
    proc = csv_mcp_processes.get(connector_id)
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
        csv_mcp_processes.pop(connector_id, None)
        logger.info("CSV MCP for %s terminated", connector_id)
    except Exception as exc:
        logger.warning("Failed to stop CSV MCP for %s: %s", connector_id, exc)


# Back-compat server lifecycle helpers used by lifespan()
def _start_erp_mcp_server() -> None:
    """Server-level ERP MCP startup.

    No-op by design: MCP now starts per-connector when enable_mcp is set during
    create/update. We keep this function to maintain backward compatibility with
    existing lifespan() calls without failing at import time.
    """
    logger.info("ERP MCP server startup deferred; managed per-connector enable_mcp")


def _stop_erp_mcp_server() -> None:
    """Terminate all running ERP MCP processes (if any)."""
    for connector_id in list(erp_mcp_processes.keys()):
        try:
            _stop_erp_mcp_for(connector_id)
        except Exception as e:
            logger.warning("Error stopping ERP MCP for %s: %s", connector_id, e)


def _start_csv_mcp_server() -> None:
    """Server-level CSV MCP startup is a no-op; handled per-connector."""
    logger.info("CSV MCP server startup deferred; managed per-connector enable_mcp")


def _stop_csv_mcp_server() -> None:
    """Terminate all running CSV MCP processes (if any)."""
    for connector_id in list(csv_mcp_processes.keys()):
        try:
            _stop_csv_mcp_for(connector_id)
        except Exception as e:
            logger.warning("Error stopping CSV MCP for %s: %s", connector_id, e)


def _is_truthy(value: str | None, default: bool = False) -> bool:
    """Helper to interpret environment variables as booleans."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Initialize repository based on configured backend
BACKEND = os.getenv("PERSISTENCE_BACKEND", "postgres").lower()
USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() == "true"

connector_repo: Any
mongo_client = None
if USE_MONGODB or BACKEND == "mongodb":
    try:
        from pymongo import MongoClient  # local import to avoid hard dependency
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        mongo_client = MongoClient(MONGO_URI)
        connector_repo = MongoConnectorRepository(mongo_client)
        logger.info("Connectors repository: MongoDB")
    except Exception as e:
        logger.error(f"Failed to initialize Mongo repository: {e}")
        logger.info("Falling back to Postgres repository.")
        connector_repo = ConnectorRepositoryPG()
else:
    connector_repo = ConnectorRepositoryPG()
    logger.info("Connectors repository: Postgres")
connector_tester = ConnectorTester()

DEV_AUTH_BYPASS = _is_truthy(os.getenv("CONNECTOR_DEV_DISABLE_AUTH"))
DEV_AUTH_TENANT = os.getenv("CONNECTOR_DEV_TENANT_ID")
DEV_AUTH_SUBJECT = os.getenv("CONNECTOR_DEV_SUBJECT", "dev-bypass")


async def connector_identity(authorization: str = Header(default="")) -> dict:
    """
    Development-friendly auth shim.

    When CONNECTOR_DEV_DISABLE_AUTH is enabled we only require a tenant identifier
    from the environment and allow requests without a bearer token. In all other
    scenarios we fall back to the shared require_auth dependency.
    """
    if not DEV_AUTH_BYPASS:
        return await require_auth(authorization)

    if authorization:
        try:
            return await require_auth(authorization)
        except HTTPException as exc:
            logger.warning("Bearer token rejected (%s); falling back to dev bypass", exc.detail)

    tenant_id = DEV_AUTH_TENANT or os.getenv("DEFAULT_TENANT_ID") or "dev-tenant"
    logger.debug("CONNECTOR_DEV_DISABLE_AUTH active. Using tenant_id=%s", tenant_id)
    return {"tenant_id": tenant_id, "sub": DEV_AUTH_SUBJECT}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Connectors service...")
    _start_erp_mcp_server()
    _start_csv_mcp_server()
    yield
    _stop_erp_mcp_server()
    _stop_csv_mcp_server()
    logger.info("Shutting down Connectors service...")
    if mongo_client is not None:
        try:
            mongo_client.close()
        except Exception:
            pass


app = FastAPI(
    title="Dyocense Connectors Service",
    version="0.1.0",
    description="Secure connector management for data source integration",
    lifespan=lifespan,
)

# CORS middleware (allow overriding via env to match the frontend dev server)
raw_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5178,http://127.0.0.1:5178",
)
cors_origins = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]
allow_origin_regex = None
if cors_origins == ["*"]:
    # Starlette blocks '*' when credentials are allowed, so fall back to regex
    cors_origins = []
    allow_origin_regex = ".*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConnectorRequest(BaseModel):
    """Request to create a new connector."""
    connector_type: str = Field(..., description="Type of connector (e.g., xero, google-drive)")
    display_name: str = Field(..., description="User-friendly name for this connection")
    config: dict = Field(..., description="Connector configuration and credentials")
    sync_frequency: SyncFrequency = Field(default=SyncFrequency.MANUAL)
    enable_mcp: bool = Field(default=False, description="Enable MCP server for this connector")


class UpdateConnectorRequest(BaseModel):
    """Request to update a connector."""
    display_name: Optional[str] = None
    config: Optional[dict] = None
    sync_frequency: Optional[SyncFrequency] = None
    status: Optional[ConnectorStatus] = None
    enable_mcp: Optional[bool] = Field(default=None, description="Toggle MCP server for this connector")


class TestConnectorRequest(BaseModel):
    """Request to test a connector configuration (without saving)."""
    connector_type: str
    config: dict


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Service health check."""
    return {
        "status": "healthy",
        "service": "connectors",
        "features": {
            "encryption": True,
            "oauth": "planned",
            "testing": True
        }
    }


@app.get("/v1/catalog", tags=["catalog"])
def get_connector_catalog() -> dict:
    """
    Get the connector marketplace catalog.
    Returns available connector types with metadata.
    """
    return {
        "connectors": CONNECTOR_CATALOG,
        "total": len(CONNECTOR_CATALOG)
    }


@app.post(
    "/v1/tenants/{tenant_id}/connectors",
    response_model=ConnectorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["connectors"]
)
async def create_connector(
    tenant_id: str,
    payload: CreateConnectorRequest
) -> ConnectorResponse:
    """
    Create a new connector for the specified tenant.
    
    Credentials are encrypted and stored securely.
    The connector is initially in 'inactive' status.
    """
    # Default user_id since we don't have auth context
    user_id = f"user-{tenant_id[:10]}"
    
    # Look up connector metadata from catalog
    connector_meta = next(
        (c for c in CONNECTOR_CATALOG if c["id"] == payload.connector_type),
        None
    )
    
    if not connector_meta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown connector type: {payload.connector_type}"
        )
    
    # Create connector with encrypted config
    connector = connector_repo.create(
        tenant_id=tenant_id,
        connector_type=payload.connector_type,
        connector_name=connector_meta["name"],
        display_name=payload.display_name,
        category=connector_meta["category"],
        icon=connector_meta["icon"],
        config=payload.config,
        data_types=connector_meta["dataTypes"],
        created_by=user_id,
        sync_frequency=payload.sync_frequency.value,
    )
    # Optionally enable MCP right after creation
    if payload.enable_mcp:
        try:
            # Mark metadata and start MCP depending on connector type
            if connector.connector_type == "erpnext":
                _start_erp_mcp_for(tenant_id, connector.connector_id)
            elif connector.connector_type in {"csv_upload", "google-drive"}:
                _start_csv_mcp_for(tenant_id, connector.connector_id)
            # Update metadata
            connector_repo.update_metadata_flag(connector.connector_id, mcp_enabled=True)
        except Exception as e:
            logger.warning("Failed to start MCP for %s: %s", connector.connector_id, e)
    
    logger.info(f"Created connector {connector.connector_id} for tenant {tenant_id}")
    
    return ConnectorResponse.from_model(connector)


@app.get("/v1/tenants/{tenant_id}/connectors", response_model=list[ConnectorResponse], tags=["connectors"])
def list_connectors(
    tenant_id: str,
    status_filter: Optional[str] = None,
) -> list[ConnectorResponse]:
    """
    List all connectors for the specified tenant.
    
    Optionally filter by status (active, inactive, error).
    """
    logger.info(f"Listing connectors for tenant: {tenant_id}, status_filter: {status_filter}")
    
    status_enum = None
    if status_filter:
        try:
            status_enum = ConnectorStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    connectors = connector_repo.list_by_tenant(tenant_id, status_enum)
    logger.info(f"Found {len(connectors)} connectors for tenant {tenant_id}")
    return [ConnectorResponse.from_model(c) for c in connectors]


@app.get("/v1/tenants/{tenant_id}/connectors/{connector_id}", response_model=ConnectorResponse, tags=["connectors"])
def get_connector(
    tenant_id: str,
    connector_id: str,
    identity: dict = Depends(require_auth)
) -> ConnectorResponse:
    """Get a specific connector by ID."""
    auth_tenant_id = identity["tenant_id"]
    
    # Verify tenant ownership
    if tenant_id != auth_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    connector = connector_repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Verify connector belongs to tenant
    if connector.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    return ConnectorResponse.from_model(connector)


@app.put("/v1/tenants/{tenant_id}/connectors/{connector_id}", response_model=ConnectorResponse, tags=["connectors"])
async def update_connector(
    tenant_id: str,
    connector_id: str,
    payload: UpdateConnectorRequest,
    identity: dict = Depends(connector_identity)
) -> ConnectorResponse:
    """
    Update a connector's configuration.
    
    Can update display name, config (re-encrypts credentials), sync frequency, or status.
    """
    auth_tenant_id = identity["tenant_id"]
    
    # Verify tenant ownership
    if not DEV_AUTH_BYPASS and tenant_id != auth_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    connector = connector_repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    if connector.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Determine new status: explicit override or fall back to inactive when credentials change
    requested_status = payload.status or (ConnectorStatus.TESTING if payload.config is not None else connector.status)
    if requested_status == ConnectorStatus.TESTING:
        # Database constraint only allows active/inactive/error/deleted; treat "testing" as "inactive"
        requested_status = ConnectorStatus.INACTIVE

    updated = connector_repo.update(
        connector_id,
        tenant_id,
        display_name=payload.display_name,
        config=payload.config,
        sync_frequency=payload.sync_frequency.value if payload.sync_frequency else None,
        status=requested_status,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update connector"
        )

    # Handle MCP enable/disable toggle
    if payload.enable_mcp is not None:
        try:
            if payload.enable_mcp:
                if updated.connector_type == "erpnext":
                    _start_erp_mcp_for(tenant_id, connector_id)
                elif updated.connector_type in {"csv_upload", "google-drive"}:
                    _start_csv_mcp_for(tenant_id, connector_id)
                connector_repo.update_metadata_flag(connector_id, mcp_enabled=True)
            else:
                # Stop processes if running
                if updated.connector_type == "erpnext":
                    _stop_erp_mcp_for(connector_id)
                elif updated.connector_type in {"csv_upload", "google-drive"}:
                    _stop_csv_mcp_for(connector_id)
                connector_repo.update_metadata_flag(connector_id, mcp_enabled=False, mcp_process_id=None)
        except Exception as e:
            logger.warning("Failed MCP toggle for %s: %s", connector_id, e)

    actor = identity.get("sub") if isinstance(identity, dict) else "system"
    logger.info("Connector %s updated by %s", connector_id, actor)
    return ConnectorResponse.from_model(updated)


@app.delete("/v1/tenants/{tenant_id}/connectors/{connector_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["connectors"])
def delete_connector(
    tenant_id: str,
    connector_id: str,
    identity: dict = Depends(connector_identity)
):
    """
    Delete a connector.
    
    This permanently removes the connector and its encrypted credentials.
    """
    auth_tenant_id = identity["tenant_id"]
    
    # Verify tenant ownership
    if not DEV_AUTH_BYPASS and tenant_id != auth_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = connector_repo.delete(connector_id, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    logger.info(f"Deleted connector {connector_id} for tenant {tenant_id}")
    return


@app.post("/v1/tenants/{tenant_id}/connectors/{connector_id}/test", response_model=ConnectorTestResult, tags=["connectors"])
async def test_connector_by_id(
    tenant_id: str,
    connector_id: str,
) -> ConnectorTestResult:
    """
    Test an existing connector's configuration.
    
    Validates credentials and connectivity. Auth removed to match SMB Gateway pattern.
    """
    connector = connector_repo.get_by_id(connector_id)
    if not connector or connector.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Decrypt config
    config = connector_repo.get_decrypted_config(connector_id) or {}
    if not config:
        logger.warning(
            "Connector %s has no decryptable configuration; running test with empty payload",
            connector_id,
        )
    
    # ERPNext specialized test path
    if connector.connector_type == "erpnext":
        try:
            from services.connectors.erpnext import ERPNextConfig, sync_erpnext_data
            raw_url = (config.get("api_url") or "").strip()
            if raw_url and not raw_url.startswith("http://") and not raw_url.startswith("https://"):
                raw_url = f"https://{raw_url}"
            api_url = raw_url.rstrip('/')
            api_key = config.get("api_key") or config.get("key") or config.get("token")
            api_secret = config.get("api_secret") or config.get("secret")
            if not all([api_url, api_key, api_secret]):
                return ConnectorTestResult(
                    success=False,
                    message="Missing ERPNext credentials (api_url, api_key, api_secret required)",
                    error_code="MISSING_CREDENTIALS"
                )
            erp_config = ERPNextConfig(api_url=api_url, api_key=cast(str, api_key), api_secret=cast(str, api_secret))
            try:
                data = await sync_erpnext_data(erp_config)
                connector_repo.update_status(connector_id, ConnectorStatus.ACTIVE)
                return ConnectorTestResult(
                    success=True,
                    message=f"ERPNext connection successful. Inventory: {len(data.inventory)}, Orders: {len(data.orders)}, Suppliers: {len(data.suppliers)}",
                    details={
                        "inventory_count": len(data.inventory),
                        "orders_count": len(data.orders),
                        "suppliers_count": len(data.suppliers),
                        "synced_at": data.sync_metadata.get("synced_at")
                    }
                )
            except Exception as sync_err:
                connector_repo.update_status(connector_id, ConnectorStatus.ERROR, str(sync_err))
                return ConnectorTestResult(
                    success=False,
                    message=f"ERPNext connection failed: {sync_err}",
                    error_code="CONNECTION_FAILED"
                )
        except Exception as e:
            logger.error(f"ERPNext test flow crashed: {e}")
            connector_repo.update_status(connector_id, ConnectorStatus.ERROR, str(e))
            return ConnectorTestResult(
                success=False,
                message=f"ERPNext test error: {e}",
                error_code="TEST_FAILED"
            )
    
    # Generic tester fallback
    result = await connector_tester.test_connector(connector.connector_type, config)
    connector_repo.update_status(
        connector_id,
        ConnectorStatus.ACTIVE if result.success else ConnectorStatus.ERROR,
        None if result.success else result.message
    )
    return result


@app.post("/v1/tenants/{tenant_id}/connectors/test", response_model=ConnectorTestResult, tags=["connectors"])
async def test_connector_config(
    tenant_id: str,
    payload: TestConnectorRequest,
) -> ConnectorTestResult:
    """
    Test a connector configuration without saving it.
    
    Useful for validating credentials before creating a connector.
    """
    # If ERPNext, run specialized flow for better diagnostics
    if payload.connector_type == "erpnext":
        try:
            from services.connectors.erpnext import ERPNextConfig, ERPNextConnector
            raw_url = (payload.config.get("api_url") or "").strip()
            if raw_url and not raw_url.startswith("http://") and not raw_url.startswith("https://"):
                raw_url = f"https://{raw_url}"
            api_url = raw_url.rstrip('/')
            api_key = payload.config.get("api_key")
            api_secret = payload.config.get("api_secret")
            if not all([api_url, api_key, api_secret]):
                return ConnectorTestResult(
                    success=False,
                    message="Missing ERPNext credentials (api_url, api_key, api_secret required)",
                    error_code="MISSING_CREDENTIALS"
                )
            cfg = ERPNextConfig(api_url=api_url, api_key=cast(str, api_key), api_secret=cast(str, api_secret))
            # Just test connectivity without syncing everything
            import aiohttp
            async with ERPNextConnector(cfg) as conn:
                ok = await conn.test_connection()
                if ok:
                    return ConnectorTestResult(success=True, message="ERPNext connection successful")
                return ConnectorTestResult(success=False, message="Unable to reach ERPNext with provided credentials", error_code="CONNECTION_FAILED")
        except Exception as e:
            logger.error(f"ERPNext test config error: {e}")
            return ConnectorTestResult(success=False, message=str(e), error_code="TEST_FAILED")
    
    # Generic connectors
    result = await connector_tester.test_connector(payload.connector_type, payload.config)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009, reload=True)
