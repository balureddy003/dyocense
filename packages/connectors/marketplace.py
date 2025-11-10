"""
Connector Marketplace - Comprehensive catalog of available integrations
Organized by category with detailed metadata for discovery and onboarding
"""

from typing import List, Dict, Any, Optional
from enum import Enum


class ConnectorCategory(str, Enum):
    """Categories for organizing connectors"""
    ECOMMERCE = "ecommerce"
    FINANCE = "finance"
    CRM = "crm"
    ERP = "erp"
    INVENTORY = "inventory"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    COMMUNICATION = "communication"
    STORAGE = "storage"
    POS = "pos"
    SHIPPING = "shipping"
    PAYMENTS = "payments"
    HR = "hr"
    ALL = "all"


class AuthType(str, Enum):
    """Authentication methods"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC = "basic"
    JWT = "jwt"
    SERVICE_ACCOUNT = "service_account"


class DataType(str, Enum):
    """Types of data connectors can provide"""
    ORDERS = "orders"
    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    INVOICES = "invoices"
    EXPENSES = "expenses"
    PAYMENTS = "payments"
    SHIPMENTS = "shipments"
    ANALYTICS = "analytics"
    CONTACTS = "contacts"
    DEALS = "deals"
    TICKETS = "tickets"
    EMPLOYEES = "employees"
    DOCUMENTS = "documents"


class ConnectorTier(str, Enum):
    """Feature tier for connectors"""
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ConnectorDefinition:
    """Metadata for a connector in the marketplace"""
    
    def __init__(
        self,
        id: str,
        name: str,
        display_name: str,
        category: ConnectorCategory,
        description: str,
        icon: str,
        data_types: List[DataType],
        auth_type: AuthType,
        tier: ConnectorTier = ConnectorTier.FREE,
        popular: bool = False,
        verified: bool = False,
        region: str = "Global",
        documentation_url: Optional[str] = None,
        setup_complexity: str = "Easy",  # Easy, Medium, Advanced
        sync_realtime: bool = False,
        config_fields: Optional[List[Dict[str, Any]]] = None,
        features: Optional[List[str]] = None,
        limitations: Optional[List[str]] = None,
    ):
        self.id = id
        self.name = name
        self.display_name = display_name
        self.category = category
        self.description = description
        self.icon = icon
        self.data_types = data_types
        self.auth_type = auth_type
        self.tier = tier
        self.popular = popular
        self.verified = verified
        self.region = region
        self.documentation_url = documentation_url
        self.setup_complexity = setup_complexity
        self.sync_realtime = sync_realtime
        self.config_fields = config_fields or []
        self.features = features or []
        self.limitations = limitations or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "id": self.id,
            "name": self.name,
            "displayName": self.display_name,
            "category": self.category.value,
            "description": self.description,
            "icon": self.icon,
            "dataTypes": [dt.value for dt in self.data_types],
            "authType": self.auth_type.value,
            "tier": self.tier.value,
            "popular": self.popular,
            "verified": self.verified,
            "region": self.region,
            "documentationUrl": self.documentation_url,
            "setupComplexity": self.setup_complexity,
            "syncRealtime": self.sync_realtime,
            "configFields": self.config_fields,
            "features": self.features,
            "limitations": self.limitations,
        }


# ===================================
# ECOMMERCE CONNECTORS
# ===================================

SHOPIFY = ConnectorDefinition(
    id="shopify",
    name="shopify",
    display_name="Shopify",
    category=ConnectorCategory.ECOMMERCE,
    description="Connect your Shopify store to sync orders, inventory, products, and customers in real-time.",
    icon="ShoppingCart",
    data_types=[DataType.ORDERS, DataType.INVENTORY, DataType.CUSTOMERS, DataType.PRODUCTS, DataType.SALES],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="Global",
    documentation_url="https://help.shopify.com/en/api",
    setup_complexity="Easy",
    sync_realtime=True,
    config_fields=[
        {"name": "store_url", "label": "Store URL", "type": "text", "required": True, "placeholder": "yourstore.myshopify.com"},
        {"name": "api_key", "label": "Admin API Access Token", "type": "password", "required": True},
    ],
    features=[
        "Real-time order sync",
        "Inventory level tracking",
        "Customer profiles",
        "Product catalog sync",
        "Abandoned cart recovery data",
        "Multi-location support",
    ],
    limitations=[
        "API rate limit: 2 requests/second",
        "Historical data limited to 60 days",
    ]
)

WOOCOMMERCE = ConnectorDefinition(
    id="woocommerce",
    name="woocommerce",
    display_name="WooCommerce",
    category=ConnectorCategory.ECOMMERCE,
    description="Sync your WordPress WooCommerce store data including orders, products, and customer information.",
    icon="ShoppingBag",
    data_types=[DataType.ORDERS, DataType.INVENTORY, DataType.CUSTOMERS, DataType.PRODUCTS],
    auth_type=AuthType.API_KEY,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Easy",
    config_fields=[
        {"name": "store_url", "label": "Store URL", "type": "text", "required": True, "placeholder": "https://yourstore.com"},
        {"name": "consumer_key", "label": "Consumer Key", "type": "text", "required": True},
        {"name": "consumer_secret", "label": "Consumer Secret", "type": "password", "required": True},
    ],
    features=[
        "Order management",
        "Product sync",
        "Customer data",
        "Inventory tracking",
        "Coupon and discount data",
    ],
)

GRANDNODE = ConnectorDefinition(
    id="grandnode",
    name="grandnode",
    display_name="GrandNode",
    category=ConnectorCategory.ECOMMERCE,
    description="Enterprise-level eCommerce platform built on .NET. Sync sales, inventory, and customer data.",
    icon="ShoppingCart",
    data_types=[DataType.ORDERS, DataType.INVENTORY, DataType.CUSTOMERS, DataType.PRODUCTS],
    auth_type=AuthType.API_KEY,
    tier=ConnectorTier.STANDARD,
    popular=False,
    verified=True,
    region="Global",
    setup_complexity="Medium",
    config_fields=[
        {"name": "store_url", "label": "Store URL", "type": "text", "required": True},
        {"name": "api_key", "label": "API Key", "type": "password", "required": True},
    ],
    features=[
        "Multi-store support",
        "Advanced inventory management",
        "B2B and B2C capabilities",
    ],
)

BIGCOMMERCE = ConnectorDefinition(
    id="bigcommerce",
    name="bigcommerce",
    display_name="BigCommerce",
    category=ConnectorCategory.ECOMMERCE,
    description="Connect BigCommerce to track sales, manage inventory, and analyze customer behavior.",
    icon="ShoppingCart",
    data_types=[DataType.ORDERS, DataType.INVENTORY, DataType.CUSTOMERS, DataType.PRODUCTS, DataType.ANALYTICS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Easy",
    sync_realtime=True,
    features=[
        "Real-time webhook support",
        "Advanced analytics",
        "Multi-channel integration",
        "Abandoned cart data",
    ],
)

# ===================================
# FINANCE & ACCOUNTING CONNECTORS
# ===================================

QUICKBOOKS = ConnectorDefinition(
    id="quickbooks",
    name="quickbooks",
    display_name="QuickBooks Online",
    category=ConnectorCategory.FINANCE,
    description="Sync invoices, expenses, customers, and financial data from QuickBooks Online.",
    icon="FileText",
    data_types=[DataType.INVOICES, DataType.EXPENSES, DataType.CUSTOMERS, DataType.PAYMENTS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.STANDARD,
    popular=True,
    verified=True,
    region="US, CA, UK, AU",
    setup_complexity="Easy",
    config_fields=[
        {"name": "realm_id", "label": "Company ID (Realm ID)", "type": "text", "required": True},
    ],
    features=[
        "Invoice tracking",
        "Expense categorization",
        "Customer/Vendor management",
        "Payment reconciliation",
        "P&L and balance sheet data",
    ],
)

XERO = ConnectorDefinition(
    id="xero",
    name="xero",
    display_name="Xero Accounting",
    category=ConnectorCategory.FINANCE,
    description="Cloud accounting platform trusted by millions. Sync financial data, invoices, and expenses.",
    icon="DollarSign",
    data_types=[DataType.INVOICES, DataType.EXPENSES, DataType.CUSTOMERS, DataType.PAYMENTS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.STANDARD,
    popular=True,
    verified=True,
    region="UK, AU, NZ",
    setup_complexity="Easy",
    features=[
        "Multi-currency support",
        "Bank reconciliation",
        "Invoice automation",
        "Expense claims",
    ],
)

STRIPE = ConnectorDefinition(
    id="stripe",
    name="stripe",
    display_name="Stripe",
    category=ConnectorCategory.PAYMENTS,
    description="Payment processing platform. Track transactions, subscriptions, and customer payments.",
    icon="CreditCard",
    data_types=[DataType.PAYMENTS, DataType.CUSTOMERS, DataType.INVOICES],
    auth_type=AuthType.API_KEY,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Easy",
    sync_realtime=True,
    config_fields=[
        {"name": "secret_key", "label": "Secret Key", "type": "password", "required": True},
    ],
    features=[
        "Real-time payment tracking",
        "Subscription analytics",
        "Customer lifetime value",
        "Refund management",
        "Webhook support",
    ],
)

# ===================================
# CRM CONNECTORS
# ===================================

SALESFORCE = ConnectorDefinition(
    id="salesforce",
    name="salesforce",
    display_name="Salesforce",
    category=ConnectorCategory.CRM,
    description="World's #1 CRM. Sync leads, opportunities, accounts, and sales pipeline data.",
    icon="Users",
    data_types=[DataType.CONTACTS, DataType.DEALS, DataType.CUSTOMERS, DataType.ANALYTICS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.PREMIUM,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Medium",
    sync_realtime=True,
    features=[
        "Lead and opportunity tracking",
        "Account management",
        "Sales forecasting",
        "Custom object support",
        "Real-time sync via Streaming API",
    ],
)

HUBSPOT = ConnectorDefinition(
    id="hubspot",
    name="hubspot",
    display_name="HubSpot CRM",
    category=ConnectorCategory.CRM,
    description="All-in-one CRM, marketing, and sales platform. Track contacts, deals, and customer interactions.",
    icon="Users",
    data_types=[DataType.CONTACTS, DataType.DEALS, DataType.CUSTOMERS, DataType.ANALYTICS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Easy",
    features=[
        "Contact lifecycle stages",
        "Deal pipeline tracking",
        "Email engagement",
        "Marketing analytics",
    ],
)

# ===================================
# ERP & INVENTORY CONNECTORS
# ===================================

ERPNEXT = ConnectorDefinition(
    id="erpnext",
    name="erpnext",
    display_name="ERPNext",
    category=ConnectorCategory.ERP,
    description="Open-source ERP for manufacturing and distribution. Sync orders, inventory, and fulfillment.",
    icon="Database",
    data_types=[DataType.ORDERS, DataType.INVENTORY, DataType.CUSTOMERS, DataType.PRODUCTS],
    auth_type=AuthType.API_KEY,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Advanced",
    config_fields=[
        {"name": "site_url", "label": "ERPNext Site URL", "type": "text", "required": True},
        {"name": "api_key", "label": "API Key", "type": "password", "required": True},
        {"name": "api_secret", "label": "API Secret", "type": "password", "required": True},
    ],
    features=[
        "Manufacturing orders",
        "Purchase orders",
        "Stock levels",
        "Warehouse management",
    ],
)

NETSUITE = ConnectorDefinition(
    id="netsuite",
    name="netsuite",
    display_name="Oracle NetSuite",
    category=ConnectorCategory.ERP,
    description="Cloud-based ERP system. Comprehensive business management including financials, inventory, and CRM.",
    icon="Database",
    data_types=[DataType.ORDERS, DataType.INVENTORY, DataType.INVOICES, DataType.CUSTOMERS, DataType.EXPENSES],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.ENTERPRISE,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Advanced",
    features=[
        "Enterprise resource planning",
        "Financial management",
        "Supply chain",
        "Multi-subsidiary support",
    ],
)

# ===================================
# POS CONNECTORS
# ===================================

SQUARE = ConnectorDefinition(
    id="square",
    name="square",
    display_name="Square POS",
    category=ConnectorCategory.POS,
    description="Point of sale and payment processing. Track sales, inventory, and customer data.",
    icon="CreditCard",
    data_types=[DataType.SALES, DataType.INVENTORY, DataType.CUSTOMERS, DataType.PAYMENTS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="US, CA, UK, AU, JP",
    setup_complexity="Easy",
    sync_realtime=True,
    features=[
        "Real-time sales tracking",
        "Inventory management",
        "Customer profiles",
        "Payment processing",
        "Multi-location support",
    ],
)

CLOVER = ConnectorDefinition(
    id="clover",
    name="clover",
    display_name="Clover POS",
    category=ConnectorCategory.POS,
    description="Modern point-of-sale system. Sync transactions, inventory, and customer data.",
    icon="CreditCard",
    data_types=[DataType.SALES, DataType.INVENTORY, DataType.CUSTOMERS, DataType.PAYMENTS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.STANDARD,
    popular=False,
    verified=True,
    region="US, CA",
    setup_complexity="Medium",
)

# ===================================
# STORAGE & DATA CONNECTORS
# ===================================

GOOGLE_DRIVE = ConnectorDefinition(
    id="google-drive",
    name="google-drive",
    display_name="Google Drive",
    category=ConnectorCategory.STORAGE,
    description="Import spreadsheets and documents from Google Drive. Perfect for CSV exports and manual data.",
    icon="FileText",
    data_types=[DataType.DOCUMENTS, DataType.ORDERS, DataType.INVENTORY, DataType.CUSTOMERS],
    auth_type=AuthType.SERVICE_ACCOUNT,
    tier=ConnectorTier.FREE,
    popular=False,
    verified=True,
    region="Global",
    setup_complexity="Medium",
    config_fields=[
        {"name": "folder_id", "label": "Folder ID", "type": "text", "required": True},
        {"name": "service_account_json", "label": "Service Account JSON", "type": "textarea", "required": True},
    ],
    features=[
        "Spreadsheet parsing",
        "Auto-detect data structure",
        "Scheduled sync",
        "Multiple file support",
    ],
)

DROPBOX = ConnectorDefinition(
    id="dropbox",
    name="dropbox",
    display_name="Dropbox",
    category=ConnectorCategory.STORAGE,
    description="Access files and spreadsheets from Dropbox for data import.",
    icon="FileText",
    data_types=[DataType.DOCUMENTS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.FREE,
    popular=False,
    verified=True,
    region="Global",
    setup_complexity="Easy",
)

# ===================================
# SHIPPING CONNECTORS
# ===================================

SHIPSTATION = ConnectorDefinition(
    id="shipstation",
    name="shipstation",
    display_name="ShipStation",
    category=ConnectorCategory.SHIPPING,
    description="Multi-carrier shipping software. Track shipments, orders, and delivery status.",
    icon="Truck",
    data_types=[DataType.SHIPMENTS, DataType.ORDERS],
    auth_type=AuthType.API_KEY,
    tier=ConnectorTier.STANDARD,
    popular=True,
    verified=True,
    region="US, Global",
    setup_complexity="Easy",
    config_fields=[
        {"name": "api_key", "label": "API Key", "type": "password", "required": True},
        {"name": "api_secret", "label": "API Secret", "type": "password", "required": True},
    ],
    features=[
        "Multi-carrier support",
        "Order fulfillment tracking",
        "Shipping labels",
        "Delivery notifications",
    ],
)

# ===================================
# MARKETING CONNECTORS
# ===================================

MAILCHIMP = ConnectorDefinition(
    id="mailchimp",
    name="mailchimp",
    display_name="Mailchimp",
    category=ConnectorCategory.MARKETING,
    description="Email marketing platform. Track campaigns, subscribers, and engagement metrics.",
    icon="Mail",
    data_types=[DataType.CONTACTS, DataType.ANALYTICS],
    auth_type=AuthType.OAUTH2,
    tier=ConnectorTier.FREE,
    popular=True,
    verified=True,
    region="Global",
    setup_complexity="Easy",
)

# ===================================
# MARKETPLACE CATALOG
# ===================================

MARKETPLACE_CONNECTORS = [
    # E-commerce
    SHOPIFY,
    WOOCOMMERCE,
    BIGCOMMERCE,
    GRANDNODE,
    
    # Finance & Payments
    QUICKBOOKS,
    XERO,
    STRIPE,
    
    # CRM
    SALESFORCE,
    HUBSPOT,
    
    # ERP & Inventory
    ERPNEXT,
    NETSUITE,
    
    # POS
    SQUARE,
    CLOVER,
    
    # Storage
    GOOGLE_DRIVE,
    DROPBOX,
    
    # Shipping
    SHIPSTATION,
    
    # Marketing
    MAILCHIMP,
]


class ConnectorMarketplace:
    """Marketplace service for browsing and discovering connectors"""
    
    def __init__(self):
        self.connectors = {c.id: c for c in MARKETPLACE_CONNECTORS}
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all connectors"""
        return [c.to_dict() for c in MARKETPLACE_CONNECTORS]
    
    def get_by_id(self, connector_id: str) -> Optional[Dict[str, Any]]:
        """Get connector by ID"""
        connector = self.connectors.get(connector_id)
        return connector.to_dict() if connector else None
    
    def get_by_category(self, category: ConnectorCategory) -> List[Dict[str, Any]]:
        """Get connectors by category"""
        if category == ConnectorCategory.ALL:
            return self.get_all()
        return [
            c.to_dict() 
            for c in MARKETPLACE_CONNECTORS 
            if c.category == category
        ]
    
    def get_popular(self) -> List[Dict[str, Any]]:
        """Get popular connectors"""
        return [
            c.to_dict() 
            for c in MARKETPLACE_CONNECTORS 
            if c.popular
        ]
    
    def get_by_tier(self, tier: ConnectorTier) -> List[Dict[str, Any]]:
        """Get connectors by pricing tier"""
        return [
            c.to_dict() 
            for c in MARKETPLACE_CONNECTORS 
            if c.tier == tier
        ]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search connectors by name or description"""
        query_lower = query.lower()
        return [
            c.to_dict()
            for c in MARKETPLACE_CONNECTORS
            if query_lower in c.display_name.lower() 
            or query_lower in c.description.lower()
            or query_lower in c.category.value.lower()
        ]
    
    def get_config_fields(self, connector_id: str) -> List[Dict[str, Any]]:
        """Get configuration fields for a connector"""
        connector = self.connectors.get(connector_id)
        return connector.config_fields if connector else []


# Singleton instance
marketplace = ConnectorMarketplace()
