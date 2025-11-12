"""
Connector service FastAPI routes
"""
from datetime import datetime
from typing import Any, Optional, List, Dict
import json
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from .grandnode import GrandNodeConfig, sync_grandnode_data
from .salesforce import SalesforceConfig, sync_salesforce_data
from .erpnext import ERPNextConfig, sync_erpnext_data
from packages.connectors.data_store_pg import get_store
from packages.kernel_common.logging import configure_logging, log_flow_event


router = APIRouter(prefix="/api/connectors", tags=["connectors"])

# Align console logs to show flow transitions between UI, service, and DB.
logger = configure_logging("connectors-routes")
# PostgreSQL connection string (from environment)
_pg_conn_str: Optional[str] = os.getenv("POSTGRES_URL")


async def get_pg_connection():
    """Get PostgreSQL connection using psycopg2"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import psycopg2.pool
    
    if not _pg_conn_str:
        raise HTTPException(status_code=500, detail="PostgreSQL connection not configured")
    
    return psycopg2.connect(_pg_conn_str, cursor_factory=RealDictCursor)


async def save_connector_data(
    tenant_id: str,
    connector_id: str,
    data_type: str,
    data: List[Dict],
    metadata: Optional[Dict] = None
):
    """Save connector data using pooled backend with smart ingestion.

    Small payloads use compact upsert; larger payloads are split into chunks
    to minimize contention and memory overhead.
    """
    store = get_store()
    # Normalize keys to strings for JSONB consistency
    norm = [{str(k): v for k, v in r.items()} for r in data]
    log_flow_event(
        logger,
        stage="persist",
        source="service",
        target="db",
        message="Ingressing connector payload",
        metadata={
            "tenant_id": tenant_id,
            "connector_id": connector_id,
            "data_type": data_type,
            "records": len(norm),
        },
    )
    result = store.ingest(tenant_id, connector_id, data_type, norm, metadata or {})
    log_flow_event(
        logger,
        stage="persist",
        source="db",
        target="service",
        message="Connector payload persisted",
        metadata={
            "tenant_id": tenant_id,
            "connector_id": connector_id,
            "data_type": data_type,
            "record_count": result.get("record_count"),
            "mode": result.get("mode"),
        },
    )
    return result


async def get_connector_data(
    tenant_id: str,
    data_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get cached connector data for tenant from PostgreSQL
    Returns dict with data_type as keys
    """
    import psycopg2
    
    conn = await get_pg_connection()
    try:
        with conn.cursor() as cur:
            if data_types:
                cur.execute("""
                    SELECT data_type, data, synced_at, record_count
                    FROM connectors.connector_data
                    WHERE tenant_id = %s AND data_type = ANY(%s)
                    ORDER BY synced_at DESC
                """, (tenant_id, data_types))
            else:
                cur.execute("""
                    SELECT data_type, data, synced_at, record_count
                    FROM connectors.connector_data
                    WHERE tenant_id = %s
                    ORDER BY synced_at DESC
                """, (tenant_id,))
            
            rows = cur.fetchall()
            
            # Build result dict
            result = {}
            for row in rows:
                result[row['data_type']] = {
                    'data': row['data'],
                    'synced_at': row['synced_at'],
                    'record_count': row['record_count']
                }
            
            total_records = sum(len(entry["data"]) for entry in result.values())
            log_flow_event(
                logger,
                stage="read",
                source="db",
                target="service",
                message="Fetched connector cache",
                metadata={
                    "tenant_id": tenant_id,
                    "requested_types": data_types or "all",
                    "returned_types": list(result.keys()),
                    "record_count": total_records,
                },
            )
            return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CSV Upload Ingestion Endpoint
# ---------------------------------------------------------------------------
def _infer_data_type_from_columns(columns: List[str]) -> str:
    lowered = {c.lower() for c in columns}
    if {"order_id", "total", "customer"} & lowered:
        return "orders"
    if {"sku", "qty", "stock", "quantity"} & lowered:
        return "inventory"
    if {"customer_id", "email", "first_name", "last_name"} & lowered:
        return "customers"
    if {"product_id", "price", "category"} & lowered:
        return "products"
    return "generic"


@router.post("/upload_csv")
async def upload_csv(
    tenant_id: str = Form(...),
    connector_id: str = Form(...),
    file: UploadFile = File(...),
    data_type: Optional[str] = Form(None),
):
    """Ingest a CSV file directly into connector storage (chunk aware).

    For large files this will automatically chunk; small files use compact upsert.
    """
    log_flow_event(
        logger,
        stage="ingest",
        source="ui",
        target="service",
        message="Upload CSV request received",
        metadata={
            "tenant_id": tenant_id,
            "connector_id": connector_id,
            "filename": file.filename,
            "requested_type": data_type,
        },
    )

    if not file.filename or not file.filename.lower().endswith(".csv"):
        log_flow_event(
            logger,
            stage="ingest",
            source="service",
            target="ui",
            message="Rejected invalid file upload",
            metadata={"filename": file.filename, "reason": "invalid extension"},
            level="WARNING",
        )
        raise HTTPException(status_code=415, detail="Only .csv files supported")

    content_bytes = await file.read()
    log_flow_event(
        logger,
        stage="ingest",
        source="service",
        target="service",
        message="CSV payload read from request",
        metadata={"bytes": len(content_bytes)},
    )
    
    try:
        text = content_bytes.decode("utf-8")
    except Exception as e:
        logger.warning(f"[upload_csv] UTF-8 decode failed, trying latin-1: {e}")
        # Attempt latin-1 fallback
        text = content_bytes.decode("latin-1")

    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        logger.error("[upload_csv] REJECTED: Empty CSV")
        raise HTTPException(status_code=400, detail="Empty CSV")
    
    log_flow_event(
        logger,
        stage="ingest",
        source="service",
        target="service",
        message="Parsed CSV lines",
        metadata={"lines": len(lines)},
    )
    
    header = [h.strip() for h in lines[0].split(",")]
    log_flow_event(
        logger,
        stage="ingest",
        source="service",
        target="service",
        message="CSV header identified",
        metadata={"columns": header},
    )
    
    rows_data: List[Dict[str, Any]] = []
    for raw in lines[1:]:
        parts = [p.strip() for p in raw.split(",")]
        row_obj = {header[i]: (parts[i] if i < len(parts) else None) for i in range(len(header))}
        rows_data.append(row_obj)
    
    log_flow_event(
        logger,
        stage="ingest",
        source="service",
        target="service",
        message="CSV data rows assembled",
        metadata={
            "data_rows": len(rows_data),
            "first_row": rows_data[0] if rows_data else "EMPTY",
        },
    )

    inferred_type = data_type or _infer_data_type_from_columns(header)
    log_flow_event(
        logger,
        stage="ingest",
        source="service",
        target="service",
        message="Data type inferred",
        metadata={"inferred_type": inferred_type},
    )
    
    store = get_store()
    log_flow_event(
        logger,
        stage="ingest",
        source="service",
        target="db",
        message="Persisting parsed CSV rows",
        metadata={
            "tenant_id": tenant_id,
            "connector_id": connector_id,
            "data_type": inferred_type,
            "records": len(rows_data),
        },
    )
    
    ingest_result = store.ingest(tenant_id, connector_id, inferred_type, rows_data, {"filename": file.filename})
    log_flow_event(
        logger,
        stage="ingest",
        source="db",
        target="service",
        message="CSV rows persisted",
        metadata={
            "mode": ingest_result.get("mode"),
            "record_count": ingest_result.get("record_count"),
        },
    )

    # Export CSV data to disk for MCP tools access
    # Use same default as main.py to ensure consistency
    _default_csv_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "csv")
    csv_data_dir = os.getenv("CSV_DATA_DIR", _default_csv_dir)
    tenant_csv_dir = os.path.join(csv_data_dir, tenant_id)
    os.makedirs(tenant_csv_dir, exist_ok=True)
    
    # Create CSV file with data_type and connector_id in filename for uniqueness
    csv_filename = f"{connector_id}_{inferred_type}.csv"
    csv_filepath = os.path.join(tenant_csv_dir, csv_filename)
    
    try:
        import csv as csv_module
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if rows_data:
                writer = csv_module.DictWriter(csvfile, fieldnames=header)
                writer.writeheader()
                writer.writerows(rows_data)
        
        log_flow_event(
            logger,
            stage="export",
            source="service",
            target="filesystem",
            message="CSV data exported to disk for MCP tools",
            metadata={
                "filepath": csv_filepath,
                "records": len(rows_data),
                "data_type": inferred_type,
            },
        )
    except Exception as e:
        logger.warning(f"Failed to export CSV to disk for MCP tools: {e}")
        # Don't fail the whole upload if export fails

    response = {
        "success": True,
        "connector_id": connector_id,
        "tenant_id": tenant_id,
        "data_type": inferred_type,
        "records_ingested": ingest_result.get("record_count"),
        "mode": ingest_result.get("mode"),
        "chunks": ingest_result.get("chunks"),
        "csv_file_exported": csv_filename,
        "message": f"Ingested {ingest_result.get('record_count')} {inferred_type} records (mode={ingest_result.get('mode')})"
    }
    log_flow_event(
        logger,
        stage="response",
        source="service",
        target="ui",
        message="CSV upload response ready",
        metadata={
            "record_count": ingest_result.get("record_count"),
            "data_type": inferred_type,
        },
    )
    return response


class ConnectorStatus(BaseModel):
    """Connector status information"""
    id: str
    name: str
    type: str
    status: str  # connected, disconnected, syncing, error
    last_sync: Optional[datetime] = None
    record_count: int = 0
    error_message: Optional[str] = None


class SyncConnectorRequest(BaseModel):
    """Request to sync connector"""
    connector_id: str
    force: bool = False


class GrandNodeSetupRequest(BaseModel):
    """Setup GrandNode connector"""
    name: str
    api_url: str
    api_key: str
    store_id: Optional[str] = None
    sync_orders: bool = True
    sync_products: bool = True
    sync_customers: bool = True


class SalesforceSetupRequest(BaseModel):
    """Setup Salesforce connector"""
    name: str
    instance_url: str
    client_id: str
    client_secret: str
    username: str
    password: str
    security_token: str
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_suppliers: bool = True


class ERPNextSetupRequest(BaseModel):
    """Setup ERPNext connector"""
    name: str
    api_url: str
    api_key: str
    api_secret: str
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_suppliers: bool = True


# In-memory connector registry (replace with database in production)
_connectors: dict[str, Any] = {}


@router.get("/list")
async def list_connectors(tenant_id: str):
    """List all connectors for tenant"""
    tenant_connectors = [
        c for c in _connectors.values()
        if c.get('tenant_id') == tenant_id
    ]
    
    return {
        "connectors": tenant_connectors,
        "total": len(tenant_connectors),
    }


@router.post("/grandnode/setup")
async def setup_grandnode(tenant_id: str, user_id: str, request: GrandNodeSetupRequest):
    """Setup GrandNode connector"""
    try:
        connector_id = f"grandnode_{datetime.utcnow().timestamp()}"
        
        config = GrandNodeConfig(
            api_url=request.api_url,
            api_key=request.api_key,
            store_id=request.store_id,
            sync_orders=request.sync_orders,
            sync_products=request.sync_products,
            sync_customers=request.sync_customers,
        )
        
        # Test connection
        # async with GrandNodeConnector(config) as connector:
        #     if not await connector.test_connection():
        #         raise HTTPException(status_code=400, detail="Failed to connect to GrandNode API")
        
        # Save connector
        _connectors[connector_id] = {
            'id': connector_id,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'name': request.name,
            'type': 'grandnode',
            'status': 'connected',
            'config': config.dict(),
            'created_at': datetime.utcnow().isoformat(),
            'last_sync': None,
            'record_count': 0,
        }
        
        return {
            "success": True,
            "connector_id": connector_id,
            "message": "GrandNode connector setup successfully",
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/salesforce/setup")
async def setup_salesforce(tenant_id: str, user_id: str, request: SalesforceSetupRequest):
    """Setup Salesforce connector"""
    try:
        log_flow_event(
            logger,
            stage="setup",
            source="ui",
            target="service",
            message="Salesforce connector setup requested",
            metadata={"tenant_id": tenant_id, "user_id": user_id},
        )
        connector_id = f"salesforce_{datetime.utcnow().timestamp()}"
        
        config = SalesforceConfig(
            instance_url=request.instance_url,
            client_id=request.client_id,
            client_secret=request.client_secret,
            username=request.username,
            password=request.password,
            security_token=request.security_token,
            sync_inventory=request.sync_inventory,
            sync_orders=request.sync_orders,
            sync_suppliers=request.sync_suppliers,
        )
        
        # Save connector
        _connectors[connector_id] = {
            'id': connector_id,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'name': request.name,
            'type': 'salesforce',
            'status': 'connected',
            'config': config.dict(exclude={'password', 'security_token', 'client_secret'}),
            'created_at': datetime.utcnow().isoformat(),
            'last_sync': None,
            'record_count': 0,
        }
        log_flow_event(
            logger,
            stage="setup",
            source="service",
            target="db",
            message="Salesforce connector metadata stored",
            metadata={"connector_id": connector_id, "tenant_id": tenant_id},
        )
        
        return {
            "success": True,
            "connector_id": connector_id,
            "message": "Salesforce connector setup successfully",
        }

    except Exception as e:
        log_flow_event(
            logger,
            stage="setup",
            source="service",
            target="ui",
            message="Salesforce connector setup failed",
            metadata={"tenant_id": tenant_id, "error": str(e)},
            level="WARNING",
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/erpnext/setup")
async def setup_erpnext(tenant_id: str, user_id: str, request: ERPNextSetupRequest):
    """Setup ERPNext connector"""
    try:
        log_flow_event(
            logger,
            stage="setup",
            source="ui",
            target="service",
            message="ERPNext connector setup requested",
            metadata={"tenant_id": tenant_id, "user_id": user_id},
        )
        connector_id = f"erpnext_{datetime.utcnow().timestamp()}"
        
        config = ERPNextConfig(
            api_url=request.api_url,
            api_key=request.api_key,
            api_secret=request.api_secret,
            sync_inventory=request.sync_inventory,
            sync_orders=request.sync_orders,
            sync_suppliers=request.sync_suppliers,
        )
        
        # Test connection
        # async with ERPNextConnector(config) as connector:
        #     if not await connector.test_connection():
        #         raise HTTPException(status_code=400, detail="Failed to connect to ERPNext API")
        
        # Save connector (credentials encrypted in production)
        _connectors[connector_id] = {
            'id': connector_id,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'name': request.name,
            'type': 'erpnext',
            'status': 'connected',
            'config': config.dict(exclude={'api_secret'}),  # Don't expose secret
            'created_at': datetime.utcnow().isoformat(),
            'last_sync': None,
            'record_count': 0,
        }
        log_flow_event(
            logger,
            stage="setup",
            source="service",
            target="db",
            message="ERPNext connector metadata stored",
            metadata={"connector_id": connector_id, "tenant_id": tenant_id},
        )
        
        return {
            "success": True,
            "connector_id": connector_id,
            "message": "ERPNext connector setup successfully",
        }
    
    except Exception as e:
        log_flow_event(
            logger,
            stage="setup",
            source="service",
            target="ui",
            message="ERPNext connector setup failed",
            metadata={"tenant_id": tenant_id, "error": str(e)},
            level="WARNING",
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_connector(request: SyncConnectorRequest):
    """Trigger connector sync and persist data to PostgreSQL"""
    connector = _connectors.get(request.connector_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    try:
        # Update status to syncing
        connector['status'] = 'syncing'
        
        tenant_id = connector['tenant_id']
        connector_id = connector['id']
        
        # Sync based on connector type
        if connector['type'] == 'grandnode':
            config = GrandNodeConfig(**connector['config'])
            data = await sync_grandnode_data(config)
            
            # Save to PostgreSQL
            await save_connector_data(tenant_id, connector_id, 'orders', data.orders)
            await save_connector_data(tenant_id, connector_id, 'products', data.products)
            await save_connector_data(tenant_id, connector_id, 'customers', data.customers)
            
            record_count = len(data.orders) + len(data.products) + len(data.customers)
        
        elif connector['type'] == 'salesforce':
            # Reconstruct full config (in production, fetch from secure storage)
            config_dict = connector['config'].copy()
            # These would be fetched from secure storage in production
            config_dict['password'] = '***'
            config_dict['security_token'] = '***'
            config_dict['client_secret'] = '***'
            
            config = SalesforceConfig(**config_dict)
            data = await sync_salesforce_data(config)
            
            # Save to PostgreSQL
            await save_connector_data(tenant_id, connector_id, 'inventory', data.inventory)
            await save_connector_data(tenant_id, connector_id, 'orders', data.orders)
            await save_connector_data(tenant_id, connector_id, 'suppliers', data.suppliers)
            
            record_count = len(data.inventory) + len(data.orders) + len(data.suppliers)
        
        elif connector['type'] == 'erpnext':
            # Reconstruct full config (in production, fetch from secure storage)
            config_dict = connector['config'].copy()
            # API secret would be fetched from secure storage in production
            config_dict['api_secret'] = '***'  # Placeholder - fetch from vault
            
            config = ERPNextConfig(**config_dict)
            data = await sync_erpnext_data(config)
            
            # Save to PostgreSQL
            await save_connector_data(tenant_id, connector_id, 'inventory', data.inventory)
            await save_connector_data(tenant_id, connector_id, 'orders', data.orders)
            await save_connector_data(tenant_id, connector_id, 'suppliers', data.suppliers)
            
            record_count = len(data.inventory) + len(data.orders) + len(data.suppliers)
        
        else:
            raise HTTPException(status_code=400, detail="Unknown connector type")
        
        # Update connector status
        connector['status'] = 'connected'
        connector['last_sync'] = datetime.utcnow().isoformat()
        connector['record_count'] = record_count
        
        return {
            "success": True,
            "record_count": record_count,
            "synced_at": connector['last_sync'],
            "message": f"Successfully synced {record_count} records to PostgreSQL",
        }
    
    except Exception as e:
        connector['status'] = 'error'
        connector['error_message'] = str(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{connector_id}")
async def delete_connector(connector_id: str):
    """Delete connector"""
    if connector_id not in _connectors:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    del _connectors[connector_id]
    
    return {
        "success": True,
        "message": "Connector deleted successfully",
    }


@router.get("/{connector_id}/status")
async def get_connector_status(connector_id: str):
    """Get connector status"""
    connector = _connectors.get(connector_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    return ConnectorStatus(
        id=connector['id'],
        name=connector['name'],
        type=connector['type'],
        status=connector['status'],
        last_sync=connector.get('last_sync'),
        record_count=connector.get('record_count', 0),
        error_message=connector.get('error_message'),
    )
