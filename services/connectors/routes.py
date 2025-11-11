"""
Connector service FastAPI routes
"""
from datetime import datetime
from typing import Any, Optional, List, Dict
import json
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .grandnode import GrandNodeConfig, sync_grandnode_data
from .salesforce import SalesforceConfig, sync_salesforce_data
from .erpnext import ERPNextConfig, sync_erpnext_data


router = APIRouter(prefix="/api/connectors", tags=["connectors"])

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
    """
    Save synced connector data to PostgreSQL
    Uses UPSERT to update existing data or insert new
    """
    import psycopg2
    from psycopg2.extras import Json
    
    conn = await get_pg_connection()
    try:
        with conn.cursor() as cur:
            # UPSERT query
            cur.execute("""
                INSERT INTO connectors.connector_data 
                (tenant_id, connector_id, data_type, data, record_count, synced_at, metadata)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                ON CONFLICT (tenant_id, connector_id, data_type)
                DO UPDATE SET
                    data = EXCLUDED.data,
                    record_count = EXCLUDED.record_count,
                    synced_at = NOW(),
                    metadata = EXCLUDED.metadata
                RETURNING data_id, synced_at
            """, (
                tenant_id,
                connector_id,
                data_type,
                Json(data),
                len(data),
                Json(metadata or {})
            ))
            
            result = cur.fetchone()
            conn.commit()
            
            return {
                "data_id": result['data_id'],
                "synced_at": result['synced_at'],
                "record_count": len(data)
            }
    finally:
        conn.close()


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
            
            return result
    finally:
        conn.close()


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
        
        return {
            "success": True,
            "connector_id": connector_id,
            "message": "Salesforce connector setup successfully",
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/erpnext/setup")
async def setup_erpnext(tenant_id: str, user_id: str, request: ERPNextSetupRequest):
    """Setup ERPNext connector"""
    try:
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
        
        return {
            "success": True,
            "connector_id": connector_id,
            "message": "ERPNext connector setup successfully",
        }
    
    except Exception as e:
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
