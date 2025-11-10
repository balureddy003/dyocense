"""
Salesforce Kennedy ERP Connector
Syncs inventory, orders, and supplier data from Salesforce
"""
import logging
from datetime import datetime
from typing import Any, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SalesforceConfig(BaseModel):
    """Salesforce connector configuration"""
    instance_url: str = Field(..., description="Salesforce instance URL")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    username: str = Field(..., description="Salesforce username")
    password: str = Field(..., description="Salesforce password")
    security_token: str = Field(..., description="Salesforce security token")
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_suppliers: bool = True
    api_version: str = "v58.0"


class SalesforceData(BaseModel):
    """Standardized data from Salesforce"""
    inventory: list[dict[str, Any]] = Field(default_factory=list)
    orders: list[dict[str, Any]] = Field(default_factory=list)
    suppliers: list[dict[str, Any]] = Field(default_factory=list)
    sync_metadata: dict[str, Any] = Field(default_factory=dict)


class SalesforceConnector:
    """
    Salesforce Kennedy ERP connector
    
    Fetches:
    - Inventory levels and turnover rates
    - Purchase orders and fulfillment data
    - Supplier information and performance
    """
    
    def __init__(self, config: SalesforceConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self):
        """Authenticate with Salesforce OAuth"""
        try:
            auth_url = f"{self.config.instance_url}/services/oauth2/token"
            payload = {
                'grant_type': 'password',
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret,
                'username': self.config.username,
                'password': f"{self.config.password}{self.config.security_token}",
            }
            
            async with self.session.post(auth_url, data=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Authentication failed: {error_text}")
                
                auth_data = await response.json()
                self.access_token = auth_data.get('access_token')
                
                # Update session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json',
                })
                
                logger.info("Salesforce authentication successful")
        
        except Exception as e:
            logger.error(f"Salesforce authentication error: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test Salesforce connection"""
        try:
            url = f"{self.config.instance_url}/services/data/{self.config.api_version}/limits"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def sync_all(self) -> SalesforceData:
        """Sync all data types"""
        data = SalesforceData()
        
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
        """Fetch inventory data using SOQL query"""
        try:
            # Example SOQL query for Kennedy ERP custom objects
            # Adjust based on actual Salesforce schema
            query = """
                SELECT Id, Name, Product__c, Product__r.Name, Quantity__c, 
                       Warehouse__c, LastRestockDate__c, TurnoverRate__c,
                       MinimumStockLevel__c, ReorderPoint__c
                FROM Inventory__c
                WHERE IsActive__c = true
                LIMIT 10000
            """
            
            data = await self._execute_soql(query)
            return [self._transform_inventory(record) for record in data]
        
        except Exception as e:
            logger.error(f"Error fetching inventory: {e}")
            return []
    
    async def fetch_orders(self) -> list[dict[str, Any]]:
        """Fetch purchase orders"""
        try:
            query = """
                SELECT Id, OrderNumber, Account.Name, OrderDate, Status,
                       TotalAmount, DeliveryDate__c, FulfillmentStatus__c
                FROM Order
                WHERE CreatedDate = LAST_N_DAYS:90
                LIMIT 10000
            """
            
            data = await self._execute_soql(query)
            return [self._transform_order(record) for record in data]
        
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    async def fetch_suppliers(self) -> list[dict[str, Any]]:
        """Fetch supplier information"""
        try:
            query = """
                SELECT Id, Name, SupplierCode__c, ContactEmail__c,
                       LeadTime__c, OnTimeDeliveryRate__c, QualityRating__c
                FROM Supplier__c
                WHERE IsActive__c = true
                LIMIT 5000
            """
            
            data = await self._execute_soql(query)
            return [self._transform_supplier(record) for record in data]
        
        except Exception as e:
            logger.error(f"Error fetching suppliers: {e}")
            return []
    
    async def _execute_soql(self, query: str) -> list[dict]:
        """Execute SOQL query"""
        try:
            url = f"{self.config.instance_url}/services/data/{self.config.api_version}/query"
            params = {'q': query}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"SOQL query failed: {error_text}")
                
                result = await response.json()
                records = result.get('records', [])
                
                # Handle pagination if needed
                while result.get('nextRecordsUrl'):
                    next_url = f"{self.config.instance_url}{result['nextRecordsUrl']}"
                    async with self.session.get(next_url) as next_response:
                        result = await next_response.json()
                        records.extend(result.get('records', []))
                
                return records
        
        except Exception as e:
            logger.error(f"SOQL execution error: {e}")
            return []
    
    def _transform_inventory(self, record: dict) -> dict:
        """Transform Salesforce inventory record"""
        return {
            'id': record.get('Id'),
            'product_id': record.get('Product__c'),
            'product_name': record.get('Product__r', {}).get('Name'),
            'quantity': record.get('Quantity__c', 0),
            'warehouse': record.get('Warehouse__c'),
            'last_restock': record.get('LastRestockDate__c'),
            'turnover_rate': record.get('TurnoverRate__c', 0),
            'min_stock': record.get('MinimumStockLevel__c'),
            'reorder_point': record.get('ReorderPoint__c'),
            'needs_reorder': record.get('Quantity__c', 0) <= record.get('ReorderPoint__c', 0),
            'source': 'salesforce',
            'raw_data': record,
        }
    
    def _transform_order(self, record: dict) -> dict:
        """Transform Salesforce order record"""
        return {
            'id': record.get('Id'),
            'order_number': record.get('OrderNumber'),
            'supplier_name': record.get('Account', {}).get('Name'),
            'order_date': record.get('OrderDate'),
            'status': record.get('Status'),
            'total_amount': record.get('TotalAmount', 0),
            'delivery_date': record.get('DeliveryDate__c'),
            'fulfillment_status': record.get('FulfillmentStatus__c'),
            'source': 'salesforce',
            'raw_data': record,
        }
    
    def _transform_supplier(self, record: dict) -> dict:
        """Transform Salesforce supplier record"""
        return {
            'id': record.get('Id'),
            'name': record.get('Name'),
            'supplier_code': record.get('SupplierCode__c'),
            'contact_email': record.get('ContactEmail__c'),
            'lead_time_days': record.get('LeadTime__c', 0),
            'on_time_rate': record.get('OnTimeDeliveryRate__c', 0),
            'quality_rating': record.get('QualityRating__c', 0),
            'source': 'salesforce',
            'raw_data': record,
        }


async def sync_salesforce_data(config: SalesforceConfig) -> SalesforceData:
    """Sync data from Salesforce"""
    async with SalesforceConnector(config) as connector:
        # Test connection first
        if not await connector.test_connection():
            raise ConnectionError("Failed to connect to Salesforce")
        
        # Sync all data
        data = await connector.sync_all()
        
        logger.info(f"Salesforce sync complete: {data.sync_metadata}")
        return data
