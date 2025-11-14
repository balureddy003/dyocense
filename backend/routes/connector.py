"""
Data Connector Routes

Manage integrations with ERPNext, QuickBooks, Stripe, etc.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_connectors():
    """List available connectors"""
    return {"message": "List connectors - to be implemented"}


@router.post("/{connector_type}/connect")
async def connect(connector_type: str):
    """Connect to external data source"""
    return {"message": f"Connect {connector_type} - to be implemented"}


@router.post("/{connector_id}/sync")
async def sync_data(connector_id: str):
    """Sync data from connector"""
    return {"message": f"Sync connector {connector_id} - to be implemented"}
