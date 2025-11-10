"""
GrandNode E-commerce API Connector
Syncs orders, products, and customer data from GrandNode
"""
import logging
from datetime import datetime
from typing import Any, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GrandNodeConfig(BaseModel):
    """GrandNode connector configuration"""
    api_url: str = Field(..., description="GrandNode API base URL")
    api_key: str = Field(..., description="API key for authentication")
    store_id: Optional[str] = Field(None, description="Store ID (if multi-store)")
    sync_orders: bool = True
    sync_products: bool = True
    sync_customers: bool = True
    lookback_days: int = 90


class GrandNodeData(BaseModel):
    """Standardized data from GrandNode"""
    orders: list[dict[str, Any]] = Field(default_factory=list)
    products: list[dict[str, Any]] = Field(default_factory=list)
    customers: list[dict[str, Any]] = Field(default_factory=list)
    sync_metadata: dict[str, Any] = Field(default_factory=dict)


class GrandNodeConnector:
    """
    GrandNode API connector for CycloneRake.com
    
    Fetches:
    - Orders (revenue, cart abandonment data)
    - Products (inventory levels, bestsellers)
    - Customers (repeat rate, loyalty data)
    """
    
    def __init__(self, config: GrandNodeConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.config.api_key}',
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
            async with self.session.get(f"{self.config.api_url}/api/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def sync_all(self) -> GrandNodeData:
        """Sync all data types"""
        data = GrandNodeData()
        
        if self.config.sync_orders:
            data.orders = await self.fetch_orders()
        
        if self.config.sync_products:
            data.products = await self.fetch_products()
        
        if self.config.sync_customers:
            data.customers = await self.fetch_customers()
        
        data.sync_metadata = {
            'synced_at': datetime.utcnow().isoformat(),
            'orders_count': len(data.orders),
            'products_count': len(data.products),
            'customers_count': len(data.customers),
        }
        
        return data
    
    async def fetch_orders(self) -> list[dict[str, Any]]:
        """Fetch orders from GrandNode"""
        try:
            # GrandNode API endpoint (adjust based on actual API)
            endpoint = f"{self.config.api_url}/api/orders"
            params = {
                'limit': 1000,
                'days': self.config.lookback_days,
            }
            
            if self.config.store_id:
                params['storeId'] = self.config.store_id
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch orders: {response.status}")
                    return []
                
                api_data = await response.json()
                orders = api_data.get('data', [])
                
                # Transform to standardized format
                return [self._transform_order(order) for order in orders]
        
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    async def fetch_products(self) -> list[dict[str, Any]]:
        """Fetch products from GrandNode"""
        try:
            endpoint = f"{self.config.api_url}/api/products"
            params = {'limit': 5000}
            
            if self.config.store_id:
                params['storeId'] = self.config.store_id
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch products: {response.status}")
                    return []
                
                api_data = await response.json()
                products = api_data.get('data', [])
                
                return [self._transform_product(product) for product in products]
        
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    async def fetch_customers(self) -> list[dict[str, Any]]:
        """Fetch customers from GrandNode"""
        try:
            endpoint = f"{self.config.api_url}/api/customers"
            params = {'limit': 10000}
            
            if self.config.store_id:
                params['storeId'] = self.config.store_id
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch customers: {response.status}")
                    return []
                
                api_data = await response.json()
                customers = api_data.get('data', [])
                
                return [self._transform_customer(customer) for customer in customers]
        
        except Exception as e:
            logger.error(f"Error fetching customers: {e}")
            return []
    
    def _transform_order(self, order: dict) -> dict:
        """Transform GrandNode order to standard format"""
        return {
            'id': order.get('id'),
            'external_id': order.get('orderNumber'),
            'customer_id': order.get('customerId'),
            'order_date': order.get('createdOnUtc'),
            'total': float(order.get('orderTotal', 0)),
            'currency': order.get('customerCurrencyCode', 'USD'),
            'status': order.get('orderStatus'),
            'payment_status': order.get('paymentStatus'),
            'shipping_status': order.get('shippingStatus'),
            'items': [
                {
                    'product_id': item.get('productId'),
                    'product_name': item.get('productName'),
                    'quantity': item.get('quantity'),
                    'price': float(item.get('unitPriceInclTax', 0)),
                    'total': float(item.get('priceInclTax', 0)),
                }
                for item in order.get('orderItems', [])
            ],
            'source': 'grandnode',
            'raw_data': order,
        }
    
    def _transform_product(self, product: dict) -> dict:
        """Transform GrandNode product to standard format"""
        return {
            'id': product.get('id'),
            'sku': product.get('sku'),
            'name': product.get('name'),
            'price': float(product.get('price', 0)),
            'stock_quantity': product.get('stockQuantity', 0),
            'category': product.get('categoryName'),
            'published': product.get('published', False),
            'available': product.get('stockQuantity', 0) > 0,
            'source': 'grandnode',
            'raw_data': product,
        }
    
    def _transform_customer(self, customer: dict) -> dict:
        """Transform GrandNode customer to standard format"""
        return {
            'id': customer.get('id'),
            'email': customer.get('email'),
            'name': f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
            'created_date': customer.get('createdOnUtc'),
            'last_order_date': customer.get('lastActivityDateUtc'),
            'total_orders': customer.get('orderCount', 0),
            'total_spent': float(customer.get('totalSpent', 0)),
            'is_repeat': customer.get('orderCount', 0) > 1,
            'source': 'grandnode',
            'raw_data': customer,
        }


async def sync_grandnode_data(config: GrandNodeConfig) -> GrandNodeData:
    """Sync data from GrandNode"""
    async with GrandNodeConnector(config) as connector:
        # Test connection first
        if not await connector.test_connection():
            raise ConnectionError("Failed to connect to GrandNode API")
        
        # Sync all data
        data = await connector.sync_all()
        
        logger.info(f"GrandNode sync complete: {data.sync_metadata}")
        return data
