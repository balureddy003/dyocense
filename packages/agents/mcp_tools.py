"""
MCP Tools Integration for Agents

Provides tools from MCP servers (ERPNext, CSV) to LangGraph agents.
"""

import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# MCP server configurations
# To add new MCP connector:
# 1. Add entry here with env flag and script path
# 2. Add connector_type mapping in CONNECTOR_TYPE_TO_MCP
# 3. Add tools definition function (e.g., _get_newconnector_tools)
# 4. Add tool execution in _execute_newconnector_tool
# 5. Update connectors service main.py to launch the MCP server

MCP_SERVERS = {
    "erpnext": {
        "enabled": os.getenv("CONNECTOR_ENABLE_ERP_MCP", "false").lower() in {"1", "true", "yes", "on"},
        "script": "services/connectors/erpnext_mcp.py",
        "env_vars": ["ERP_URL", "ERP_KEY", "ERP_SECRET"],
        "description": "ERPNext ERP system integration with sales, inventory, and purchasing",
    },
    "csv": {
        "enabled": os.getenv("CONNECTOR_ENABLE_CSV_MCP", "false").lower() in {"1", "true", "yes", "on"},
        "script": "services/connectors/csv_mcp.py",
        "env_vars": ["CSV_DATA_DIR"],
        "description": "CSV file data analysis and querying",
    },
    # Add new MCP servers here:
    # "shopify": {
    #     "enabled": os.getenv("CONNECTOR_ENABLE_SHOPIFY_MCP", "false").lower() in {"1", "true", "yes", "on"},
    #     "script": "services/connectors/shopify_mcp.py",
    #     "env_vars": ["SHOPIFY_STORE_URL", "SHOPIFY_API_KEY"],
    #     "description": "Shopify e-commerce integration",
    # },
}

# Map connector types (from database) to MCP server names
CONNECTOR_TYPE_TO_MCP = {
    "erpnext": "erpnext",
    "csv_upload": "csv",
    "google-drive": "csv",
    # Add new mappings here when adding connector types:
    # "shopify": "shopify",
    # "grandnode": "grandnode",
}


def get_available_mcp_tools(tenant_id: str) -> List[Dict[str, Any]]:
    """Return all MCP tools enabled per-connector for tenant.

    Previous implementation relied solely on global env flags. We now inspect
    connector metadata (mcp_enabled) so tools only appear when the tenant has
    explicitly enabled MCP for that connector.
    """
    tools: List[Dict[str, Any]] = []
    try:
        from services.connectors.main import connector_repo  # type: ignore
        from packages.connectors.models import ConnectorStatus  # type: ignore
        tenant_connectors = connector_repo.list_by_tenant(tenant_id)
        for conn in tenant_connectors:
            if conn.status == ConnectorStatus.ACTIVE and getattr(conn.metadata, "mcp_enabled", False):
                if conn.connector_type == "erpnext":
                    tools.extend(_get_erpnext_tools())
                elif conn.connector_type in {"csv_upload", "google-drive"}:
                    tools.extend(_get_csv_tools(tenant_id))
    except Exception as e:
        logger.warning(
            "MCP tool discovery fallback (tenant=%s, error=%s) - using env flags only",
            tenant_id,
            e,
        )
        # Fallback to legacy env behavior
        if MCP_SERVERS["erpnext"]["enabled"]:
            tools.extend(_get_erpnext_tools())
        if MCP_SERVERS["csv"]["enabled"]:
            tools.extend(_get_csv_tools(tenant_id))
    return tools


def _get_erpnext_tools() -> List[Dict[str, Any]]:
    """Get ERPNext MCP tools in OpenAI function format."""
    return [
        {
            "type": "function",
            "function": {
                "name": "erp_get_sales_orders",
                "description": "Get sales orders from ERPNext with optional filtering by status or customer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter by order status (Draft, Submitted, Completed, Cancelled)",
                        },
                        "customer": {
                            "type": "string",
                            "description": "Filter by customer name",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of orders to return",
                            "default": 50,
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "erp_get_purchase_orders",
                "description": "Get purchase orders from ERPNext",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "supplier": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "erp_get_stock_summary",
                "description": "Get inventory stock levels across warehouses from ERPNext",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_code": {
                            "type": "string",
                            "description": "Filter by specific item code",
                        },
                        "warehouse": {
                            "type": "string",
                            "description": "Filter by specific warehouse",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "erp_get_customers",
                "description": "Get customer list from ERPNext",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "active_only": {
                            "type": "boolean",
                            "description": "Only return active customers",
                            "default": True,
                        },
                        "limit": {"type": "integer", "default": 100},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "erp_get_items",
                "description": "Get item master data from ERPNext",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_group": {"type": "string"},
                        "limit": {"type": "integer", "default": 100},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "erp_get_low_stock_items",
                "description": "Get items that are low in stock or need reordering from ERPNext",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reorder_level_only": {
                            "type": "boolean",
                            "default": True,
                        },
                        "limit": {"type": "integer", "default": 100},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "erp_create_purchase_order",
                "description": "Create a new purchase order in ERPNext",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "supplier": {
                            "type": "string",
                            "description": "Supplier name",
                        },
                        "items": {
                            "type": "array",
                            "description": "List of items with item_code, qty, rate",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "item_code": {"type": "string"},
                                    "qty": {"type": "number"},
                                    "rate": {"type": "number"},
                                },
                            },
                        },
                        "schedule_date": {
                            "type": "string",
                            "description": "Delivery date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["supplier", "items", "schedule_date"],
                },
            },
        },
    ]


def _get_csv_tools(tenant_id: str) -> List[Dict[str, Any]]:
    """Get CSV MCP tools in OpenAI function format."""
    return [
        {
            "type": "function",
            "function": {
                "name": "csv_list_files",
                "description": "List all available CSV files for analysis",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "csv_get_info",
                "description": "Get metadata about a CSV file (columns, data types, sample rows)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Name of the CSV file",
                        },
                    },
                    "required": ["filename"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "csv_query",
                "description": "Query CSV file with filtering and column selection",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific columns to return",
                        },
                        "filters": {
                            "type": "object",
                            "description": "Column:value pairs for filtering",
                        },
                        "limit": {"type": "integer", "default": 100},
                    },
                    "required": ["filename"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "csv_analyze",
                "description": "Perform statistical analysis on CSV data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "analysis_type": {
                            "type": "string",
                            "enum": ["summary", "describe", "missing", "unique"],
                            "description": "Type of analysis to perform",
                        },
                    },
                    "required": ["filename", "analysis_type"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "csv_aggregate",
                "description": "Group and aggregate CSV data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "group_by": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Columns to group by",
                        },
                        "aggregations": {
                            "type": "object",
                            "description": "Column:function pairs (e.g., sales:sum, quantity:mean)",
                        },
                    },
                    "required": ["filename", "group_by", "aggregations"],
                },
            },
        },
    ]


def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an MCP tool call.
    
    This is a placeholder - actual implementation would use MCP protocol
    to communicate with the running MCP servers.
    
    For now, this directly calls the backend connector service REST API
    or invokes MCP server scripts.
    """
    logger.info(f"Executing MCP tool: {tool_name} with args: {arguments}")
    
    # Map tool names to MCP server calls
    if tool_name.startswith("erp_"):
        return _execute_erpnext_tool(tool_name, arguments)
    elif tool_name.startswith("csv_"):
        return _execute_csv_tool(tool_name, arguments)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def _execute_erpnext_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute ERPNext MCP tool."""
    # Strip erp_ prefix
    method = tool_name[4:]
    
    # This would ideally use MCP protocol client
    # For now, return placeholder
    return {
        "tool": tool_name,
        "method": method,
        "arguments": arguments,
        "result": f"ERPNext MCP tool {method} called with {arguments}",
        "status": "mcp_integration_pending",
    }


def _execute_csv_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute CSV MCP tool."""
    # Strip csv_ prefix
    method = tool_name[4:]
    
    return {
        "tool": tool_name,
        "method": method,
        "arguments": arguments,
        "result": f"CSV MCP tool {method} called with {arguments}",
        "status": "mcp_integration_pending",
    }


def get_tenant_connectors(tenant_id: str) -> List[str]:
    """
    Get list of enabled connectors for a tenant.
    
    Automatically discovers tenant's active connectors by:
    1. Querying tenant's connectors from database
    2. Checking which MCP servers are running
    3. Returning intersection of active connectors with enabled MCP servers
    
    This means:
    - When user adds ERPNext connector in UI → it appears here if MCP is enabled
    - When admin enables new MCP server → tenants with that connector type get it automatically
    - No code changes needed when adding new connector types (just update CONNECTOR_TYPE_TO_MCP)
    """
    connectors: List[str] = []
    try:
        from services.connectors.main import connector_repo  # type: ignore
        from packages.connectors.models import ConnectorStatus  # type: ignore
        tenant_connectors = connector_repo.list_by_tenant(tenant_id)
        for conn in tenant_connectors:
            if conn.status == ConnectorStatus.ACTIVE and getattr(conn.metadata, "mcp_enabled", False):
                mcp_name = CONNECTOR_TYPE_TO_MCP.get(conn.connector_type)
                if mcp_name and mcp_name not in connectors:
                    connectors.append(mcp_name)
                    logger.info(
                        "Tenant %s: connector %s (id=%s) has MCP enabled (mapped=%s)",
                        tenant_id,
                        conn.connector_type,
                        conn.connector_id,
                        mcp_name,
                    )
    except Exception as e:
        logger.warning("MCP connector discovery failed for tenant %s: %s", tenant_id, e)
        # Fallback to env enabled servers (legacy)
        for name, cfg in MCP_SERVERS.items():
            if cfg.get("enabled") and name not in connectors:
                connectors.append(name)
    logger.info("Tenant %s active MCP connectors: %s", tenant_id, connectors)
    return connectors
