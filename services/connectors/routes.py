"""
Connector service FastAPI routes
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .grandnode import GrandNodeConfig, sync_grandnode_data
from .salesforce import SalesforceConfig, sync_salesforce_data

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


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


@router.post("/sync")
async def sync_connector(request: SyncConnectorRequest):
    """Trigger connector sync"""
    connector = _connectors.get(request.connector_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    try:
        # Update status to syncing
        connector['status'] = 'syncing'
        
        # Sync based on connector type
        if connector['type'] == 'grandnode':
            config = GrandNodeConfig(**connector['config'])
            data = await sync_grandnode_data(config)
            record_count = (
                len(data.orders) + 
                len(data.products) + 
                len(data.customers)
            )
        
        elif connector['type'] == 'salesforce':
            # Reconstruct full config (in production, fetch from secure storage)
            config_dict = connector['config'].copy()
            # These would be fetched from secure storage in production
            config_dict['password'] = '***'
            config_dict['security_token'] = '***'
            config_dict['client_secret'] = '***'
            
            config = SalesforceConfig(**config_dict)
            data = await sync_salesforce_data(config)
            record_count = (
                len(data.inventory) + 
                len(data.orders) + 
                len(data.suppliers)
            )
        
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
