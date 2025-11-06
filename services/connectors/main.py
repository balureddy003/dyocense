"""
Connectors Service

Manages data source connectors with secure credential storage.
Supports OAuth flows, API key authentication, and connector testing.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.connectors.models import (
    ConnectorConfig,
    ConnectorResponse,
    ConnectorStatus,
    ConnectorTestResult,
    SyncFrequency,
)
from packages.connectors.repository import ConnectorRepository
from packages.connectors.testing import ConnectorTester

# Connector marketplace metadata
from packages.connectors.catalog import CONNECTOR_CATALOG

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)

# Initialize repository
connector_repo = ConnectorRepository(mongo_client)
connector_tester = ConnectorTester()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Connectors service...")
    yield
    logger.info("Shutting down Connectors service...")
    mongo_client.close()


app = FastAPI(
    title="Dyocense Connectors Service",
    version="0.1.0",
    description="Secure connector management for data source integration",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


class UpdateConnectorRequest(BaseModel):
    """Request to update a connector."""
    display_name: Optional[str] = None
    config: Optional[dict] = None
    sync_frequency: Optional[SyncFrequency] = None
    status: Optional[ConnectorStatus] = None


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
    "/v1/connectors",
    response_model=ConnectorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["connectors"]
)
async def create_connector(
    payload: CreateConnectorRequest,
    identity: dict = Depends(require_auth)
) -> ConnectorResponse:
    """
    Create a new connector for the authenticated tenant.
    
    Credentials are encrypted and stored securely.
    The connector is initially in 'testing' status.
    """
    tenant_id = identity["tenant_id"]
    user_id = identity["subject"]
    
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
    
    logger.info(f"Created connector {connector.connector_id} for tenant {tenant_id}")
    
    return ConnectorResponse.from_model(connector)


@app.get("/v1/connectors", response_model=list[ConnectorResponse], tags=["connectors"])
def list_connectors(
    status_filter: Optional[str] = None,
    identity: dict = Depends(require_auth)
) -> list[ConnectorResponse]:
    """
    List all connectors for the authenticated tenant.
    
    Optionally filter by status (active, inactive, error, syncing).
    """
    tenant_id = identity["tenant_id"]
    
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
    return [ConnectorResponse.from_model(c) for c in connectors]


@app.get("/v1/connectors/{connector_id}", response_model=ConnectorResponse, tags=["connectors"])
def get_connector(
    connector_id: str,
    identity: dict = Depends(require_auth)
) -> ConnectorResponse:
    """Get a specific connector by ID."""
    tenant_id = identity["tenant_id"]
    
    connector = connector_repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Verify tenant ownership
    if connector.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return ConnectorResponse.from_model(connector)


@app.put("/v1/connectors/{connector_id}", response_model=ConnectorResponse, tags=["connectors"])
async def update_connector(
    connector_id: str,
    payload: UpdateConnectorRequest,
    identity: dict = Depends(require_auth)
) -> ConnectorResponse:
    """
    Update a connector's configuration.
    
    Can update display name, config (re-encrypts credentials), sync frequency, or status.
    """
    tenant_id = identity["tenant_id"]
    
    connector = connector_repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    if connector.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # TODO: Implement update logic in repository
    # For now, return error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Connector updates not yet implemented"
    )


@app.delete("/v1/connectors/{connector_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["connectors"])
def delete_connector(
    connector_id: str,
    identity: dict = Depends(require_auth)
):
    """
    Delete a connector.
    
    This permanently removes the connector and its encrypted credentials.
    """
    tenant_id = identity["tenant_id"]
    
    success = connector_repo.delete(connector_id, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    logger.info(f"Deleted connector {connector_id} for tenant {tenant_id}")
    return


@app.post("/v1/connectors/{connector_id}/test", response_model=ConnectorTestResult, tags=["connectors"])
async def test_connector_by_id(
    connector_id: str,
    identity: dict = Depends(require_auth)
) -> ConnectorTestResult:
    """
    Test an existing connector's configuration.
    
    Validates that the credentials work and the connector can connect to the data source.
    """
    tenant_id = identity["tenant_id"]
    
    connector = connector_repo.get_by_id(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    if connector.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get decrypted config
    config = connector_repo.get_decrypted_config(connector_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt connector configuration"
        )
    
    # Test the connection
    result = await connector_tester.test_connector(connector.connector_type, config)
    
    # Update connector status based on test result
    if result.success:
        connector_repo.update_status(connector_id, ConnectorStatus.ACTIVE)
    else:
        connector_repo.update_status(
            connector_id,
            ConnectorStatus.ERROR,
            result.message
        )
    
    return result


@app.post("/v1/connectors/test", response_model=ConnectorTestResult, tags=["connectors"])
async def test_connector_config(
    payload: TestConnectorRequest,
    identity: dict = Depends(require_auth)
) -> ConnectorTestResult:
    """
    Test a connector configuration without saving it.
    
    Useful for validating credentials before creating a connector.
    """
    result = await connector_tester.test_connector(
        payload.connector_type,
        payload.config
    )
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009, reload=True)
