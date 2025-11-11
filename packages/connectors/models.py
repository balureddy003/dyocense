"""Data models for connector management."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ConnectorStatus(str, Enum):
    """Status of a configured connector."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"
    TESTING = "testing"


class SyncFrequency(str, Enum):
    """How often to sync data from the connector."""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class ConnectorMetadata(BaseModel):
    """Metadata about connector sync status."""
    total_records: Optional[int] = None
    last_sync_duration: Optional[float] = None  # seconds
    error_message: Optional[str] = None
    last_error_at: Optional[datetime] = None
    mcp_enabled: bool = False  # whether MCP tooling is enabled for this connector
    mcp_process_id: Optional[int] = None  # PID of spawned MCP server if any
    mcp_started_at: Optional[datetime] = None
    mcp_last_heartbeat: Optional[datetime] = None


class TenantConnector(BaseModel):
    """A configured connector for a tenant."""
    connector_id: str = Field(..., description="Unique connector instance ID")
    tenant_id: str = Field(..., description="Tenant this connector belongs to")
    connector_type: str = Field(..., description="Type of connector (google-drive, xero, etc)")
    connector_name: str = Field(..., description="Internal name of connector")
    display_name: str = Field(..., description="User-friendly name for this connection")
    category: str = Field(..., description="Category (finance, ecommerce, etc)")
    icon: str = Field(..., description="Icon name")
    
    # Encrypted credentials - never expose these in API responses
    encrypted_config: str = Field(..., description="Encrypted configuration and credentials")
    
    data_types: list[str] = Field(default_factory=list, description="Types of data this connector provides")
    status: ConnectorStatus = Field(default=ConnectorStatus.TESTING)
    last_sync: Optional[datetime] = None
    sync_frequency: SyncFrequency = Field(default=SyncFrequency.MANUAL)
    metadata: ConnectorMetadata = Field(default_factory=ConnectorMetadata)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User ID who created this connector")
    
    class Config:
        json_schema_extra = {
            "example": {
                "connector_id": "conn-123",
                "tenant_id": "tenant-abc",
                "connector_type": "xero",
                "connector_name": "xero",
                "display_name": "Main Xero Account",
                "category": "finance",
                "icon": "FileText",
                "encrypted_config": "<encrypted>",
                "data_types": ["invoices", "expenses", "customers"],
                "status": "active",
                "sync_frequency": "daily",
                "created_by": "user-123"
            }
        }


class ConnectorConfig(BaseModel):
    """Configuration for creating/updating a connector (input from user)."""
    connector_type: str
    display_name: str
    config: dict[str, Any] = Field(..., description="Connector-specific configuration (will be encrypted)")
    sync_frequency: SyncFrequency = SyncFrequency.MANUAL


class ConnectorResponse(BaseModel):
    """API response for a connector (without sensitive data)."""
    connector_id: str
    tenant_id: str
    connector_type: str
    connector_name: str
    display_name: str
    category: str
    icon: str
    data_types: list[str]
    status: ConnectorStatus
    last_sync: Optional[datetime] = None
    sync_frequency: SyncFrequency
    metadata: ConnectorMetadata
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    @classmethod
    def from_model(cls, connector: TenantConnector) -> "ConnectorResponse":
        """Convert internal model to API response (strips encrypted config)."""
        return cls(
            connector_id=connector.connector_id,
            tenant_id=connector.tenant_id,
            connector_type=connector.connector_type,
            connector_name=connector.connector_name,
            display_name=connector.display_name,
            category=connector.category,
            icon=connector.icon,
            data_types=connector.data_types,
            status=connector.status,
            last_sync=connector.last_sync,
            sync_frequency=connector.sync_frequency,
            metadata=connector.metadata,
            created_at=connector.created_at,
            updated_at=connector.updated_at,
            created_by=connector.created_by,
        )


class ConnectorTestResult(BaseModel):
    """Result of testing a connector configuration."""
    success: bool
    message: str
    details: Optional[dict[str, Any]] = None
    error_code: Optional[str] = None
