"""
Integration Hub - Third-party service integration management
Supports QuickBooks, Stripe, Square, and custom API access
"""

import asyncio
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class IntegrationType(str, Enum):
    """Supported integration types"""
    QUICKBOOKS = "quickbooks"
    STRIPE = "stripe"
    SQUARE = "square"
    CUSTOM_API = "custom_api"


class IntegrationStatus(str, Enum):
    """Integration connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class WebhookEventType(str, Enum):
    """Webhook event types"""
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    PAYMENT_RECEIVED = "payment.received"
    CUSTOMER_CREATED = "customer.created"
    ORDER_CREATED = "order.created"
    PRODUCT_UPDATED = "product.updated"


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    integration_id: str
    tenant_id: str
    integration_type: IntegrationType
    status: IntegrationStatus
    display_name: str
    
    # OAuth credentials
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    
    # API credentials
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    
    # Connection details
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookConfig:
    """Webhook endpoint configuration"""
    webhook_id: str
    tenant_id: str
    integration_id: str
    url: str
    events: List[WebhookEventType]
    secret: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    
    # Stats
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0


@dataclass
class APIKey:
    """API access key for programmatic access"""
    key_id: str
    tenant_id: str
    key_hash: str  # Hashed API key
    name: str
    description: str
    
    # Permissions
    scopes: List[str] = field(default_factory=list)
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    # Usage stats
    total_requests: int = 0
    rate_limit_per_hour: int = 1000


@dataclass
class SyncResult:
    """Result of a data synchronization"""
    integration_id: str
    sync_started_at: datetime
    sync_completed_at: datetime
    status: str  # "success", "partial", "failed"
    
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class QuickBooksConnector:
    """QuickBooks Online integration connector"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.base_url = "https://quickbooks.api.intuit.com/v3"
    
    async def connect(self, auth_code: str) -> IntegrationConfig:
        """Complete OAuth connection flow"""
        # In production, exchange auth_code for tokens
        self.config.access_token = f"qb_access_{uuid4().hex[:16]}"
        self.config.refresh_token = f"qb_refresh_{uuid4().hex[:16]}"
        self.config.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        self.config.connected_at = datetime.utcnow()
        self.config.status = IntegrationStatus.ACTIVE
        return self.config
    
    async def sync_customers(self) -> SyncResult:
        """Sync customers from QuickBooks"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=45,
            records_created=12,
            records_updated=33,
            metadata={"source": "quickbooks", "entity": "customers"}
        )
    
    async def sync_invoices(self) -> SyncResult:
        """Sync invoices from QuickBooks"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=128,
            records_created=24,
            records_updated=104,
            metadata={"source": "quickbooks", "entity": "invoices"}
        )
    
    async def sync_payments(self) -> SyncResult:
        """Sync payments from QuickBooks"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=86,
            records_created=18,
            records_updated=68,
            metadata={"source": "quickbooks", "entity": "payments"}
        )
    
    async def get_company_info(self) -> Dict[str, Any]:
        """Get company information"""
        return {
            "company_name": "Demo Company",
            "fiscal_year_start": "January",
            "currency": "USD",
            "country": "US"
        }


class StripeConnector:
    """Stripe payment integration connector"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.base_url = "https://api.stripe.com/v1"
    
    async def connect(self, api_key: str) -> IntegrationConfig:
        """Connect using Stripe API key"""
        self.config.api_key = api_key
        self.config.connected_at = datetime.utcnow()
        self.config.status = IntegrationStatus.ACTIVE
        return self.config
    
    async def sync_customers(self) -> SyncResult:
        """Sync customers from Stripe"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=67,
            records_created=15,
            records_updated=52,
            metadata={"source": "stripe", "entity": "customers"}
        )
    
    async def sync_payments(self) -> SyncResult:
        """Sync payments from Stripe"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=245,
            records_created=52,
            records_updated=193,
            metadata={"source": "stripe", "entity": "charges"}
        )
    
    async def sync_subscriptions(self) -> SyncResult:
        """Sync subscriptions from Stripe"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=34,
            records_created=8,
            records_updated=26,
            metadata={"source": "stripe", "entity": "subscriptions"}
        )


class SquareConnector:
    """Square POS integration connector"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.base_url = "https://connect.squareup.com/v2"
    
    async def connect(self, access_token: str) -> IntegrationConfig:
        """Connect using Square access token"""
        self.config.access_token = access_token
        self.config.connected_at = datetime.utcnow()
        self.config.status = IntegrationStatus.ACTIVE
        return self.config
    
    async def sync_customers(self) -> SyncResult:
        """Sync customers from Square"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=89,
            records_created=22,
            records_updated=67,
            metadata={"source": "square", "entity": "customers"}
        )
    
    async def sync_orders(self) -> SyncResult:
        """Sync orders from Square"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=312,
            records_created=78,
            records_updated=234,
            metadata={"source": "square", "entity": "orders"}
        )
    
    async def sync_inventory(self) -> SyncResult:
        """Sync inventory from Square"""
        start = datetime.utcnow()
        
        # Simulate sync
        await asyncio.sleep(0.1)
        
        return SyncResult(
            integration_id=self.config.integration_id,
            sync_started_at=start,
            sync_completed_at=datetime.utcnow(),
            status="success",
            records_processed=156,
            records_created=12,
            records_updated=144,
            metadata={"source": "square", "entity": "inventory"}
        )


class IntegrationHub:
    """Central hub for managing all integrations"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self._integrations: Dict[str, IntegrationConfig] = {}
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._api_keys: Dict[str, APIKey] = {}
    
    # Integration Management
    
    async def create_integration(
        self,
        tenant_id: str,
        integration_type: IntegrationType,
        display_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> IntegrationConfig:
        """Create a new integration"""
        integration = IntegrationConfig(
            integration_id=str(uuid4()),
            tenant_id=tenant_id,
            integration_type=integration_type,
            status=IntegrationStatus.PENDING,
            display_name=display_name,
            config=config or {}
        )
        
        self._integrations[integration.integration_id] = integration
        return integration
    
    async def get_integration(self, integration_id: str) -> Optional[IntegrationConfig]:
        """Get integration by ID"""
        return self._integrations.get(integration_id)
    
    async def list_integrations(self, tenant_id: str) -> List[IntegrationConfig]:
        """List all integrations for a tenant"""
        return [
            integration for integration in self._integrations.values()
            if integration.tenant_id == tenant_id
        ]
    
    async def update_integration(
        self,
        integration_id: str,
        updates: Dict[str, Any]
    ) -> Optional[IntegrationConfig]:
        """Update integration configuration"""
        integration = self._integrations.get(integration_id)
        if not integration:
            return None
        
        for key, value in updates.items():
            if hasattr(integration, key):
                setattr(integration, key, value)
        
        return integration
    
    async def delete_integration(self, integration_id: str) -> bool:
        """Delete an integration"""
        if integration_id in self._integrations:
            del self._integrations[integration_id]
            
            # Delete associated webhooks
            webhook_ids = [
                wh_id for wh_id, wh in self._webhooks.items()
                if wh.integration_id == integration_id
            ]
            for wh_id in webhook_ids:
                del self._webhooks[wh_id]
            
            return True
        return False
    
    # Connector Factory
    
    def get_connector(self, integration: IntegrationConfig):
        """Get appropriate connector for integration type"""
        if integration.integration_type == IntegrationType.QUICKBOOKS:
            return QuickBooksConnector(integration)
        elif integration.integration_type == IntegrationType.STRIPE:
            return StripeConnector(integration)
        elif integration.integration_type == IntegrationType.SQUARE:
            return SquareConnector(integration)
        else:
            raise ValueError(f"Unsupported integration type: {integration.integration_type}")
    
    # OAuth Flow
    
    async def initiate_oauth(
        self,
        integration_id: str,
        redirect_uri: str
    ) -> Dict[str, str]:
        """Initiate OAuth authorization flow"""
        integration = await self.get_integration(integration_id)
        if not integration:
            raise ValueError("Integration not found")
        
        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL based on integration type
        if integration.integration_type == IntegrationType.QUICKBOOKS:
            auth_url = (
                f"https://appcenter.intuit.com/connect/oauth2"
                f"?client_id=YOUR_CLIENT_ID"
                f"&redirect_uri={redirect_uri}"
                f"&response_type=code"
                f"&scope=com.intuit.quickbooks.accounting"
                f"&state={state}"
            )
        elif integration.integration_type == IntegrationType.SQUARE:
            auth_url = (
                f"https://connect.squareup.com/oauth2/authorize"
                f"?client_id=YOUR_CLIENT_ID"
                f"&redirect_uri={redirect_uri}"
                f"&response_type=code"
                f"&scope=CUSTOMERS_READ+ORDERS_READ+ITEMS_READ"
                f"&state={state}"
            )
        else:
            raise ValueError("OAuth not supported for this integration")
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
    
    async def complete_oauth(
        self,
        integration_id: str,
        auth_code: str
    ) -> IntegrationConfig:
        """Complete OAuth flow with authorization code"""
        integration = await self.get_integration(integration_id)
        if not integration:
            raise ValueError("Integration not found")
        
        connector = self.get_connector(integration)
        updated_integration = await connector.connect(auth_code)
        
        self._integrations[integration_id] = updated_integration
        return updated_integration
    
    # Data Synchronization
    
    async def sync_integration_data(
        self,
        integration_id: str,
        entities: Optional[List[str]] = None
    ) -> List[SyncResult]:
        """Synchronize data from integration"""
        integration = await self.get_integration(integration_id)
        if not integration:
            raise ValueError("Integration not found")
        
        if integration.status != IntegrationStatus.ACTIVE:
            raise ValueError("Integration is not active")
        
        connector = self.get_connector(integration)
        results = []
        
        # Determine which entities to sync
        if not entities:
            if integration.integration_type == IntegrationType.QUICKBOOKS:
                entities = ["customers", "invoices", "payments"]
            elif integration.integration_type == IntegrationType.STRIPE:
                entities = ["customers", "payments", "subscriptions"]
            elif integration.integration_type == IntegrationType.SQUARE:
                entities = ["customers", "orders", "inventory"]
        
        # Sync each entity
        for entity in entities:
            method_name = f"sync_{entity}"
            if hasattr(connector, method_name):
                result = await getattr(connector, method_name)()
                results.append(result)
        
        # Update last sync time
        integration.last_sync_at = datetime.utcnow()
        
        return results
    
    # Webhook Management
    
    async def create_webhook(
        self,
        tenant_id: str,
        integration_id: str,
        url: str,
        events: List[WebhookEventType]
    ) -> WebhookConfig:
        """Create a webhook endpoint"""
        # Generate secure webhook secret
        secret = secrets.token_urlsafe(32)
        
        webhook = WebhookConfig(
            webhook_id=str(uuid4()),
            tenant_id=tenant_id,
            integration_id=integration_id,
            url=url,
            events=events,
            secret=secret
        )
        
        self._webhooks[webhook.webhook_id] = webhook
        return webhook
    
    async def list_webhooks(self, tenant_id: str) -> List[WebhookConfig]:
        """List all webhooks for a tenant"""
        return [
            webhook for webhook in self._webhooks.values()
            if webhook.tenant_id == tenant_id
        ]
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False
    
    async def verify_webhook_signature(
        self,
        webhook_id: str,
        payload: bytes,
        signature: str
    ) -> bool:
        """Verify webhook signature"""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return False
        
        # Compute HMAC
        expected_signature = hmac.new(
            webhook.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def process_webhook(
        self,
        webhook_id: str,
        event_type: WebhookEventType,
        payload: Dict[str, Any]
    ) -> None:
        """Process incoming webhook event"""
        webhook = self._webhooks.get(webhook_id)
        if not webhook or not webhook.is_active:
            return
        
        if event_type not in webhook.events:
            return
        
        # Update stats
        webhook.last_triggered_at = datetime.utcnow()
        webhook.total_deliveries += 1
        
        # Process event based on type
        # In production, this would trigger business logic
        webhook.successful_deliveries += 1
    
    # API Key Management
    
    async def create_api_key(
        self,
        tenant_id: str,
        name: str,
        description: str,
        scopes: List[str],
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """Create a new API key - returns (APIKey, raw_key)"""
        # Generate secure API key
        raw_key = f"dyc_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        api_key = APIKey(
            key_id=str(uuid4()),
            tenant_id=tenant_id,
            key_hash=key_hash,
            name=name,
            description=description,
            scopes=scopes,
            expires_at=expires_at
        )
        
        self._api_keys[api_key.key_id] = api_key
        
        # Return both the API key object and the raw key (only shown once)
        return api_key, raw_key
    
    async def list_api_keys(self, tenant_id: str) -> List[APIKey]:
        """List all API keys for a tenant"""
        return [
            key for key in self._api_keys.values()
            if key.tenant_id == tenant_id
        ]
    
    async def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Verify and return API key"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        for api_key in self._api_keys.values():
            if api_key.key_hash == key_hash:
                if not api_key.is_active:
                    return None
                
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    return None
                
                # Update usage stats
                api_key.last_used_at = datetime.utcnow()
                api_key.total_requests += 1
                
                return api_key
        
        return None
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        api_key = self._api_keys.get(key_id)
        if api_key:
            api_key.is_active = False
            return True
        return False
    
    async def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key"""
        if key_id in self._api_keys:
            del self._api_keys[key_id]
            return True
        return False


# Global integration hub instance
integration_hub = IntegrationHub()
