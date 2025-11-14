"""
Data Connector API Routes

Endpoints for integrating external data sources (Salesforce, Google Drive, CSV/Excel).
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, CurrentUser
from backend.services.connectors.mcp_connectors import create_connector
from backend.models import DataSource

router = APIRouter()


# Request/Response Models
# =================================================================

class ConnectorCreate(BaseModel):
    """Create new data source connector."""
    connector_type: str = Field(..., description="Type: salesforce, google_drive, file_upload")
    name: str = Field(..., min_length=1, max_length=255)
    credentials: dict = Field(..., description="Auth credentials (encrypted)")
    config: dict = Field(default_factory=dict, description="Connector config")
    sync_frequency: str = Field(default="daily", description="Sync schedule")


class ConnectorUpdate(BaseModel):
    """Update connector configuration."""
    name: Optional[str] = None
    credentials: Optional[dict] = None
    config: Optional[dict] = None
    sync_frequency: Optional[str] = None
    status: Optional[str] = None


class SyncTrigger(BaseModel):
    """Trigger manual sync."""
    force: bool = Field(default=False, description="Force sync even if recent")


class ConnectorResponse(BaseModel):
    """Connector details."""
    source_id: str
    connector_type: str
    name: str
    status: str
    last_sync: Optional[datetime]
    created_at: datetime


# Endpoints
# =================================================================

@router.post("/", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    request: ConnectorCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new data source connector.
    
    Supported types:
    - **salesforce**: Sync Accounts, Opportunities, Leads
    - **google_drive**: Read CSV/Excel from Google Drive folder
    - **file_upload**: Direct CSV/Excel file upload
    
    Credentials format varies by connector type. See docs for details.
    """
    import uuid
    
    # Create DataSource record
    source = DataSource(
        source_id=uuid.uuid4(),
        tenant_id=UUID(user["tenant_id"]),
        connector_type=request.connector_type,
        name=request.name,
        credentials=request.credentials,  # Should be encrypted in production
        config=request.config,
        status="active",
        sync_frequency=request.sync_frequency
    )
    
    db.add(source)
    await db.commit()
    await db.refresh(source)
    
    # Validate configuration
    try:
        connector = create_connector(
            connector_type=request.connector_type,
            source_id=source.source_id,
            tenant_id=UUID(user["tenant_id"]),
            credentials=request.credentials,
            config=request.config,
            db=db
        )
        
        # Test authentication
        is_valid, error_msg = await connector.validate_config()
        if not is_valid:
            await db.delete(source)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration: {error_msg}"
            )
        
        await connector.authenticate()
        
    except Exception as e:
        await db.delete(source)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connector validation failed: {str(e)}"
        )
    
    return ConnectorResponse(
        source_id=str(source.source_id),
        connector_type=source.connector_type,
        name=source.name,
        status=source.status,
        last_sync=source.last_sync,
        created_at=source.created_at
    )


@router.get("/", response_model=list[ConnectorResponse])
async def list_connectors(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """List all data source connectors for tenant."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(DataSource).where(
            DataSource.tenant_id == UUID(user["tenant_id"])
        )
    )
    sources = result.scalars().all()
    
    return [
        ConnectorResponse(
            source_id=str(s.source_id),
            connector_type=s.connector_type,
            name=s.name,
            status=s.status,
            last_sync=s.last_sync,
            created_at=s.created_at
        )
        for s in sources
    ]


@router.get("/{source_id}", response_model=ConnectorResponse)
async def get_connector(
    source_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get connector details."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(DataSource).where(
            DataSource.source_id == source_id,
            DataSource.tenant_id == UUID(user["tenant_id"])
        )
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    return ConnectorResponse(
        source_id=str(source.source_id),
        connector_type=source.connector_type,
        name=source.name,
        status=source.status,
        last_sync=source.last_sync,
        created_at=source.created_at
    )


@router.post("/{source_id}/sync")
async def trigger_sync(
    source_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger manual data sync.
    
    Fetches latest data from source and saves to database.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(DataSource).where(
            DataSource.source_id == source_id,
            DataSource.tenant_id == UUID(user["tenant_id"])
        )
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    # Create connector and sync
    try:
        connector = create_connector(
            connector_type=source.connector_type,
            source_id=source.source_id,
            tenant_id=UUID(user["tenant_id"]),
            credentials=source.credentials,
            config=source.config,
            db=db
        )
        
        sync_result = await connector.sync()
        
        return {
            "source_id": str(source_id),
            "status": sync_result["status"],
            "records_synced": sync_result.get("records_synced", 0),
            "method": sync_result.get("method", "unknown"),
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_db),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload CSV or Excel file for processing.
    
    File will be processed immediately and metrics extracted.
    """
    import tempfile
    import os
    import uuid
    
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel files supported"
        )
    
    # Save to temp file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        # Write uploaded file
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Create temporary DataSource
        source = DataSource(
            source_id=uuid.uuid4(),
            tenant_id=UUID(user["tenant_id"]),
            connector_type="file_upload",
            name=f"Upload: {file.filename}",
            credentials={},
            config={"file_path": temp_path}
        )
        
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        # Process file
        connector = create_connector(
            connector_type="file_upload",
            source_id=source.source_id,
            tenant_id=UUID(user["tenant_id"]),
            credentials={},
            config={"file_path": temp_path},
            db=db
        )
        
        sync_result = await connector.sync()
        
        return {
            "source_id": str(source.source_id),
            "filename": file.filename,
            "status": sync_result["status"],
            "records_synced": sync_result.get("records_synced", 0),
            "rows_processed": sync_result.get("rows_processed", 0),
            "columns": sync_result.get("columns", [])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
