"""
ERPNext ERP API Connector
Syncs inventory, orders, and supplier data from ERPNext
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ERPNextConfig(BaseModel):
    """ERPNext connector configuration"""
    api_url: str = Field(..., description="ERPNext instance URL (e.g., https://erp.example.com)")
    api_key: str = Field(..., description="API Key from ERPNext")
    api_secret: str = Field(..., description="API Secret from ERPNext")
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_suppliers: bool = True
    lookback_days: int = 90


class ERPNextData(BaseModel):
    """Standardized data from ERPNext"""
    inventory: list[dict[str, Any]] = Field(default_factory=list)
    orders: list[dict[str, Any]] = Field(default_factory=list)
    suppliers: list[dict[str, Any]] = Field(default_factory=list)
    sync_metadata: dict[str, Any] = Field(default_factory=dict)


class ERPNextConnector:
    """
    ERPNext API connector for inventory and order management
    
    Fetches:
    - Inventory (stock levels, reorder points)
    - Sales Orders (revenue, delivery tracking)
    - Suppliers (vendor management, payment terms)
    
    API Documentation: https://frappeframework.com/docs/v14/user/en/api
    """
    
    def __init__(self, config: ERPNextConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.api_url.rstrip('/')
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'token {self.config.api_key}:{self.config.api_secret}',
                'Content-Type': 'application/json',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_connection(self) -> bool:
        """Test API connection and credentials"""
        try:
            # Test with simple API call
            async with self.session.get(f"{self.base_url}/api/method/frappe.auth.get_logged_user") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"ERPNext connection test successful: {data.get('message')}")
                    return True
                return False
        except Exception as e:
            logger.error(f"ERPNext connection test failed: {e}")
            return False
    
    async def sync_all(self) -> ERPNextData:
        """Sync all data types"""
        data = ERPNextData()
        
        if self.config.sync_inventory:
            data.inventory = await self.fetch_inventory()
        
        if self.config.sync_orders:
            data.orders = await self.fetch_orders()
        
        if self.config.sync_suppliers:
            data.suppliers = await self.fetch_suppliers()
        
        data.sync_metadata = {
            'synced_at': datetime.utcnow().isoformat(),
            'inventory_count': len(data.inventory),
            'orders_count': len(data.orders),
            'suppliers_count': len(data.suppliers),
        }
        
        return data
    
    async def fetch_inventory(self) -> list[dict[str, Any]]:
        """
        Fetch inventory items from ERPNext
        
        Returns list of items with stock levels, reorder points, etc.
        """
        try:
            # Fetch items with stock data
            endpoint = f"{self.base_url}/api/resource/Item"
            params = {
                'fields': '["name","item_code","item_name","item_group","stock_uom",'
                          '"valuation_rate","reorder_level","reorder_qty",'
                          '"last_purchase_rate","disabled"]',
                'filters': '[["disabled","=",0]]',
                'limit_page_length': 1000,
            }
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    logger.error(f"ERPNext inventory fetch failed: {response.status}")
                    return []
                
                result = await response.json()
                items = result.get('data', [])
                
                # Enrich with bin data (actual stock quantities)
                enriched_items = []
                for item in items:
                    item_code = item.get('item_code')
                    
                    # Get stock balance
                    stock = await self._get_item_stock(item_code)
                    
                    enriched_items.append({
                        'item_code': item_code,
                        'item_name': item.get('item_name'),
                        'item_group': item.get('item_group'),
                        'stock_qty': stock.get('actual_qty', 0),
                        'available_qty': stock.get('available_qty', 0),
                        'reorder_level': item.get('reorder_level', 0),
                        'reorder_qty': item.get('reorder_qty', 0),
                        'unit_price': item.get('valuation_rate', 0),
                        'last_purchase_rate': item.get('last_purchase_rate', 0),
                        'uom': item.get('stock_uom'),
                        'needs_reorder': stock.get('actual_qty', 0) <= item.get('reorder_level', 0),
                    })
                
                logger.info(f"Fetched {len(enriched_items)} inventory items from ERPNext")
                return enriched_items
                
        except Exception as e:
            logger.error(f"Error fetching ERPNext inventory: {e}")
            return []
    
    async def _get_item_stock(self, item_code: str) -> dict[str, Any]:
        """Get stock balance for specific item"""
        try:
            endpoint = f"{self.base_url}/api/resource/Bin"
            params = {
                'fields': '["actual_qty","reserved_qty","ordered_qty","projected_qty"]',
                'filters': f'[["item_code","=","{item_code}"]]',
                'limit_page_length': 1,
            }
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    bins = result.get('data', [])
                    if bins:
                        bin_data = bins[0]
                        return {
                            'actual_qty': bin_data.get('actual_qty', 0),
                            'reserved_qty': bin_data.get('reserved_qty', 0),
                            'ordered_qty': bin_data.get('ordered_qty', 0),
                            'available_qty': bin_data.get('actual_qty', 0) - bin_data.get('reserved_qty', 0),
                        }
                return {'actual_qty': 0, 'available_qty': 0}
        except Exception as e:
            logger.warning(f"Error fetching stock for {item_code}: {e}")
            return {'actual_qty': 0, 'available_qty': 0}
    
    async def fetch_orders(self) -> list[dict[str, Any]]:
        """
        Fetch sales orders from ERPNext
        
        Returns list of recent sales orders with customer and revenue data
        """
        try:
            # Calculate date range
            from_date = (datetime.utcnow() - timedelta(days=self.config.lookback_days)).strftime('%Y-%m-%d')
            
            endpoint = f"{self.base_url}/api/resource/Sales Order"
            params = {
                'fields': '["name","customer","customer_name","transaction_date",'
                          '"delivery_date","grand_total","status","currency",'
                          '"total_qty","base_net_total","advance_paid"]',
                'filters': f'[["transaction_date",">=","{from_date}"]]',
                'limit_page_length': 1000,
                'order_by': 'transaction_date desc',
            }
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    logger.error(f"ERPNext orders fetch failed: {response.status}")
                    return []
                
                result = await response.json()
                orders = result.get('data', [])
                
                # Transform to standard format
                formatted_orders = []
                for order in orders:
                    formatted_orders.append({
                        'order_id': order.get('name'),
                        'customer_name': order.get('customer_name') or order.get('customer'),
                        'customer_id': order.get('customer'),
                        'order_date': order.get('transaction_date'),
                        'delivery_date': order.get('delivery_date'),
                        'total_amount': order.get('grand_total', 0),
                        'net_amount': order.get('base_net_total', 0),
                        'advance_paid': order.get('advance_paid', 0),
                        'quantity': order.get('total_qty', 0),
                        'status': order.get('status'),
                        'currency': order.get('currency', 'INR'),
                        'is_delivered': order.get('status') == 'Completed',
                        'is_pending': order.get('status') in ['Draft', 'To Deliver and Bill'],
                    })
                
                logger.info(f"Fetched {len(formatted_orders)} orders from ERPNext")
                return formatted_orders
                
        except Exception as e:
            logger.error(f"Error fetching ERPNext orders: {e}")
            return []
    
    async def fetch_suppliers(self) -> list[dict[str, Any]]:
        """
        Fetch suppliers from ERPNext
        
        Returns list of active suppliers with contact and payment info
        """
        try:
            endpoint = f"{self.base_url}/api/resource/Supplier"
            params = {
                'fields': '["name","supplier_name","supplier_group","supplier_type",'
                          '"country","tax_id","payment_terms","default_currency",'
                          '"on_hold","disabled"]',
                'filters': '[["disabled","=",0]]',
                'limit_page_length': 500,
            }
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    logger.error(f"ERPNext suppliers fetch failed: {response.status}")
                    return []
                
                result = await response.json()
                suppliers = result.get('data', [])
                
                # Transform to standard format
                formatted_suppliers = []
                for supplier in suppliers:
                    formatted_suppliers.append({
                        'supplier_id': supplier.get('name'),
                        'supplier_name': supplier.get('supplier_name'),
                        'supplier_group': supplier.get('supplier_group'),
                        'supplier_type': supplier.get('supplier_type'),
                        'country': supplier.get('country'),
                        'tax_id': supplier.get('tax_id'),
                        'payment_terms': supplier.get('payment_terms'),
                        'currency': supplier.get('default_currency', 'INR'),
                        'on_hold': supplier.get('on_hold', 0) == 1,
                        'is_active': supplier.get('disabled', 0) == 0,
                    })
                
                logger.info(f"Fetched {len(formatted_suppliers)} suppliers from ERPNext")
                return formatted_suppliers
                
        except Exception as e:
            logger.error(f"Error fetching ERPNext suppliers: {e}")
            return []


async def sync_erpnext_data(config: ERPNextConfig) -> ERPNextData:
    """
    Convenience function to sync all ERPNext data
    
    Usage:
        config = ERPNextConfig(
            api_url="https://erp.cyclonerake.com",
            api_key="your_api_key",
            api_secret="your_api_secret"
        )
        data = await sync_erpnext_data(config)
    """
    async with ERPNextConnector(config) as connector:
        if not await connector.test_connection():
            raise ConnectionError("Failed to connect to ERPNext API. Check credentials.")
        
        return await connector.sync_all()
