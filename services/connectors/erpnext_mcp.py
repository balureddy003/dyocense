"""MCP server wrapping the ERPNext REST API for model/context tooling.

Enhancements:
- Supports per-connector credential loading from Postgres using --tenant/--connector
- Falls back to environment variables ERP_URL/ERP_KEY/ERP_SECRET when DB not available
- Avoids import-time failures; initializes credentials at runtime before mcp.run()
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Globals populated at runtime via _init_credentials()
ERP_URL: Optional[str] = None
ERP_KEY: Optional[str] = None
ERP_SECRET: Optional[str] = None

session = requests.Session()


def _normalize_url(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    url = raw.strip()
    if not url:
        return None
    if not (url.startswith("http://") or url.startswith("https://")):
        url = f"https://{url}"
    return url.rstrip("/")


def _init_credentials(tenant_id: Optional[str], connector_id: Optional[str]) -> Tuple[str, str, str]:
    """Initialize ERP credentials from DB (preferred) or environment.

    Returns a tuple (api_url, api_key, api_secret). Raises RuntimeError if not resolvable.
    """
    # 1) Try database by connector_id
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    if connector_id:
        try:
            # Local import to avoid hard dependency when DB not configured
            from packages.connectors.repository_postgres import ConnectorRepositoryPG  # type: ignore
            repo = ConnectorRepositoryPG()
            cfg = repo.get_decrypted_config(connector_id) or {}
            if cfg:
                api_url = _normalize_url(
                    cfg.get("api_url")
                    or cfg.get("site_url")
                    or cfg.get("url")
                )
                api_key = cfg.get("api_key") or cfg.get("key") or cfg.get("token")
                api_secret = cfg.get("api_secret") or cfg.get("secret")
                logger.info(
                    "ERPNext MCP loading credentials from DB for connector=%s tenant=%s",
                    connector_id,
                    tenant_id or "unknown",
                )
        except Exception as e:
            logger.warning("Falling back to environment for ERPNext MCP (DB load failed): %s", e)

    # 2) Fallback to environment variables
    if not (api_url and api_key and api_secret):
        env_url = _normalize_url(os.getenv("ERP_URL"))
        env_key = os.getenv("ERP_KEY") or os.getenv("ERP_NEXT_API_KEY")
        env_secret = os.getenv("ERP_SECRET") or os.getenv("ERP_NEXT_API_SECRET")
        api_url = api_url or env_url
        api_key = api_key or env_key
        api_secret = api_secret or env_secret

    if not (api_url and api_key and api_secret):
        raise RuntimeError(
            "ERPNext MCP requires credentials. Provide connector_id with DB config or set ERP_URL, ERP_KEY, ERP_SECRET."
        )

    # Update globals and session headers safely (avoid logging secrets)
    global ERP_URL, ERP_KEY, ERP_SECRET
    ERP_URL, ERP_KEY, ERP_SECRET = api_url, api_key, api_secret
    session.headers.update(
        {
            "Authorization": f"token {ERP_KEY}:{ERP_SECRET}",
            "Content-Type": "application/json",
        }
    )
    return api_url, api_key, api_secret


def _erp_url(path: str) -> str:
    """Build full ERPNext URL."""
    if not ERP_URL:
        raise RuntimeError("ERP_URL not initialized; _init_credentials() must be called before use")
    return f"{ERP_URL.rstrip('/')}{path}"


def _erp_request(method: str, path: str, **kwargs) -> dict[str, Any]:
    """Make a single call to the ERPNext API (raises for HTTP errors)."""
    url = _erp_url(path)
    response = session.request(method, url, timeout=30, **kwargs)
    response.raise_for_status()
    payload = response.json()
    logger.debug("ERPNext %s %s -> %s", method.upper(), url, payload.get("data") or payload.get("message"))
    return payload


def _resource_path(doctype: str, name: Optional[str] = None) -> str:
    path = f"/api/resource/{doctype}"
    if name:
        path += f"/{name}"
    return path


mcp = FastMCP("ERPNext Connector", description="Pack ERPNext documents as an MCP toolset.")


@mcp.resource("erp://document/{doctype}/{name}")
def read_document(doctype: str, name: str) -> Dict[str, Any]:
    """Load a specific ERPNext document (doctype + name)."""
    return _erp_request("get", _resource_path(doctype, name))["data"]


@mcp.resource("erp://list/{doctype}")
def list_documents(doctype: str, filters: Optional[List[List[str]]] = None, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """List documents with optional filters & field selection."""
    params: Dict[str, Any] = {}
    if filters:
        params["filters"] = json.dumps(filters)
    if fields:
        params["fields"] = json.dumps(fields)
    return _erp_request("get", _resource_path(doctype), params=params)


@mcp.resource("erp://stock/{item_code}")
def stock_levels(item_code: str, warehouse: Optional[str] = None) -> Dict[str, Any]:
    """Return stock ledger entries for a given item (useful for availability)."""
    filters = [["item_code", "=", item_code]]
    if warehouse:
        filters.append(["warehouse", "=", warehouse])
    params = {"filters": json.dumps(filters), "fields": json.dumps(["name", "warehouse", "actual_qty", "reserved_qty", "ordered_qty", "projected_qty"])}
    return _erp_request("get", "/api/resource/Bin", params=params)


@mcp.tool()
def create_document(doctype: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new ERPNext document."""
    return _erp_request("post", _resource_path(doctype), json=data)


@mcp.tool()
def update_document(doctype: str, name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update fields on an existing document."""
    return _erp_request("put", _resource_path(doctype, name), json=fields)


@mcp.tool()
def search_documents(doctype: str, filters: List[List[str]], limit: int = 20) -> Dict[str, Any]:
    """Search for documents matching filters."""
    params = {"filters": json.dumps(filters), "limit_page_length": limit}
    return _erp_request("get", _resource_path(doctype), params=params)


@mcp.prompt(title="Create purchase order", description="Generate a purchase order with supplier, item, and quantity.")
def purchase_order_prompt(supplier: str, item_code: str, quantity: float) -> str:
    return f"""
Create a Purchase Order in ERPNext:
- Supplier: {supplier}
- Item: {item_code}
- Quantity: {quantity}
"""


@mcp.prompt(title="Check stock availability", description="Return the latest stock metrics for an item.")
def stock_prompt(item_code: str, warehouse: Optional[str] = None) -> str:
    location = f" in {warehouse}" if warehouse else ""
    return f"Check stock availability for {item_code}{location} and summarize actual vs reserved quantity."


# Additional tools for all ERPNext document types

@mcp.tool()
def get_sales_orders(status: Optional[str] = None, customer: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Get sales orders with optional filtering by status or customer."""
    filters = []
    if status:
        filters.append(["status", "=", status])
    if customer:
        filters.append(["customer", "=", customer])
    
    params = {
        "filters": json.dumps(filters) if filters else "[]",
        "fields": json.dumps(["name", "customer", "status", "grand_total", "delivery_date", "transaction_date"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Sales Order", params=params)


@mcp.tool()
def get_purchase_orders(status: Optional[str] = None, supplier: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Get purchase orders with optional filtering."""
    filters = []
    if status:
        filters.append(["status", "=", status])
    if supplier:
        filters.append(["supplier", "=", supplier])
    
    params = {
        "filters": json.dumps(filters) if filters else "[]",
        "fields": json.dumps(["name", "supplier", "status", "grand_total", "schedule_date", "transaction_date"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Purchase Order", params=params)


@mcp.tool()
def get_customers(active_only: bool = True, limit: int = 100) -> Dict[str, Any]:
    """Get customer list."""
    filters = [["disabled", "=", 0]] if active_only else []
    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(["name", "customer_name", "customer_type", "customer_group", "territory"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Customer", params=params)


@mcp.tool()
def get_suppliers(active_only: bool = True, limit: int = 100) -> Dict[str, Any]:
    """Get supplier list."""
    filters = [["disabled", "=", 0]] if active_only else []
    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(["name", "supplier_name", "supplier_type", "supplier_group", "country"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Supplier", params=params)


@mcp.tool()
def get_items(item_group: Optional[str] = None, has_variants: Optional[bool] = None, limit: int = 100) -> Dict[str, Any]:
    """Get item master data."""
    filters = [["disabled", "=", 0]]
    if item_group:
        filters.append(["item_group", "=", item_group])
    if has_variants is not None:
        filters.append(["has_variants", "=", 1 if has_variants else 0])
    
    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(["name", "item_name", "item_group", "stock_uom", "standard_rate", "description"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Item", params=params)


@mcp.tool()
def get_invoices(invoice_type: str = "Sales Invoice", status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Get sales or purchase invoices."""
    filters = []
    if status:
        filters.append(["status", "=", status])
    
    params = {
        "filters": json.dumps(filters) if filters else "[]",
        "fields": json.dumps(["name", "customer" if invoice_type == "Sales Invoice" else "supplier", "status", "grand_total", "posting_date", "due_date", "outstanding_amount"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", f"/api/resource/{invoice_type}", params=params)


@mcp.tool()
def get_stock_summary(item_code: Optional[str] = None, warehouse: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive stock summary across warehouses."""
    filters = []
    if item_code:
        filters.append(["item_code", "=", item_code])
    if warehouse:
        filters.append(["warehouse", "=", warehouse])
    
    params = {
        "filters": json.dumps(filters) if filters else "[]",
        "fields": json.dumps(["item_code", "warehouse", "actual_qty", "reserved_qty", "ordered_qty", "projected_qty", "valuation_rate"]),
        "limit_page_length": 500,
    }
    return _erp_request("get", "/api/resource/Bin", params=params)


@mcp.tool()
def get_quotations(status: Optional[str] = None, customer: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Get quotations sent to customers."""
    filters = []
    if status:
        filters.append(["status", "=", status])
    if customer:
        filters.append(["party_name", "=", customer])
    
    params = {
        "filters": json.dumps(filters) if filters else "[]",
        "fields": json.dumps(["name", "party_name", "status", "grand_total", "quotation_to", "transaction_date", "valid_till"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Quotation", params=params)


@mcp.tool()
def get_delivery_notes(status: Optional[str] = None, customer: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Get delivery notes for shipped orders."""
    filters = []
    if status:
        filters.append(["status", "=", status])
    if customer:
        filters.append(["customer", "=", customer])
    
    params = {
        "filters": json.dumps(filters) if filters else "[]",
        "fields": json.dumps(["name", "customer", "status", "posting_date", "lr_date", "total_qty"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Delivery Note", params=params)


@mcp.tool()
def get_warehouses(limit: int = 50) -> Dict[str, Any]:
    """Get list of warehouses."""
    params = {
        "filters": json.dumps([["disabled", "=", 0]]),
        "fields": json.dumps(["name", "warehouse_name", "warehouse_type", "parent_warehouse", "company"]),
        "limit_page_length": limit,
    }
    return _erp_request("get", "/api/resource/Warehouse", params=params)


@mcp.tool()
def create_sales_order(customer: str, items: List[Dict[str, Any]], delivery_date: str) -> Dict[str, Any]:
    """Create a new sales order with items."""
    data = {
        "doctype": "Sales Order",
        "customer": customer,
        "delivery_date": delivery_date,
        "items": items,  # Each item should have: item_code, qty, rate
    }
    return _erp_request("post", "/api/resource/Sales Order", json=data)


@mcp.tool()
def create_purchase_order(supplier: str, items: List[Dict[str, Any]], schedule_date: str) -> Dict[str, Any]:
    """Create a new purchase order with items."""
    data = {
        "doctype": "Purchase Order",
        "supplier": supplier,
        "schedule_date": schedule_date,
        "items": items,  # Each item should have: item_code, qty, rate
    }
    return _erp_request("post", "/api/resource/Purchase Order", json=data)


@mcp.tool()
def get_low_stock_items(reorder_level_only: bool = True, limit: int = 100) -> Dict[str, Any]:
    """Get items that are low in stock or need reordering."""
    # First get items with reorder level set
    item_filters = [["disabled", "=", 0]]
    if reorder_level_only:
        # We'll filter in code after fetching bins
        pass
    
    # Get stock bins
    bin_params = {
        "fields": json.dumps(["item_code", "warehouse", "actual_qty", "projected_qty"]),
        "limit_page_length": limit,
    }
    bins_response = _erp_request("get", "/api/resource/Bin", params=bin_params)
    
    # Get item details with reorder levels
    item_params = {
        "filters": json.dumps([["disabled", "=", 0]]),
        "fields": json.dumps(["name", "item_name", "item_group", "stock_uom"]),
        "limit_page_length": limit,
    }
    items_response = _erp_request("get", "/api/resource/Item", params=item_params)
    
    # Get reorder levels
    reorder_params = {
        "fields": json.dumps(["parent", "warehouse", "warehouse_reorder_level", "warehouse_reorder_qty"]),
        "limit_page_length": 500,
    }
    reorder_response = _erp_request("get", "/api/resource/Item Reorder", params=reorder_params)
    
    return {
        "bins": bins_response.get("data", []),
        "items": items_response.get("data", []),
        "reorder_levels": reorder_response.get("data", []),
    }


@mcp.prompt(title="Analyze sales performance", description="Get sales metrics and trends.")
def sales_analysis_prompt(days: int = 30) -> str:
    return f"""
Analyze sales performance for the last {days} days:
1. Get all sales orders and invoices from this period
2. Calculate total revenue, average order value, number of orders
3. Identify top customers and products
4. Note any trends or patterns
5. Provide actionable recommendations
"""


@mcp.prompt(title="Inventory health check", description="Review inventory status and identify issues.")
def inventory_health_prompt() -> str:
    return """
Perform a comprehensive inventory health check:
1. Get all stock levels across warehouses
2. Identify low stock items that need reordering
3. Find items with excess stock or slow movement
4. Check for stock discrepancies
5. Recommend reorder quantities and priorities
"""


@mcp.prompt(title="Customer order status", description="Check status of orders for a specific customer.")
def customer_order_status_prompt(customer_name: str) -> str:
    return f"""
Get complete order status for customer '{customer_name}':
1. List all open sales orders
2. Show recent invoices and payment status
3. Check pending deliveries
4. Identify any overdue items
5. Summarize customer's current standing
"""


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    # Parse runtime args for tenant/connector context
    parser = argparse.ArgumentParser(description="ERPNext MCP Server")
    parser.add_argument("--tenant", dest="tenant_id", type=str, required=False)
    parser.add_argument("--connector", dest="connector_id", type=str, required=False)
    args = parser.parse_args()

    # Initialize credentials prior to running MCP
    _init_credentials(args.tenant_id, args.connector_id)
    mcp.run()
