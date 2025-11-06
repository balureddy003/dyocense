/**
 * Connector Marketplace for Small Business Data Integration
 * Focus: UK Market - Google Drive, Small ERPs, Finance Systems
 * Features: Chat-based configuration, Tenant-level management, Extensible marketplace
 */

export type ConnectorCategory = "finance" | "ecommerce" | "erp" | "storage" | "pos" | "crm" | "accounting" | "inventory";

export type ConnectorTier = "free" | "basic" | "premium" | "enterprise";

export type ConnectorAuthType = "api_key" | "oauth2" | "basic_auth" | "mcp" | "custom";

export type ConnectorField = {
  name: string;
  label: string;
  type: "text" | "password" | "url" | "select" | "number" | "email";
  required: boolean;
  placeholder?: string;
  description?: string;
  options?: { value: string; label: string }[];
  validation?: {
    pattern?: string;
    minLength?: number;
    maxLength?: number;
    message?: string;
  };
};

export type ConnectorConfig = {
  id: string;
  name: string;
  displayName: string;
  category: ConnectorCategory;
  tier: ConnectorTier;
  region: string; // "UK", "EU", "US", "Global"
  icon: string; // Icon name from lucide-react
  description: string;
  longDescription: string;
  authType: ConnectorAuthType;
  fields: ConnectorField[];
  dataTypes: string[]; // ["sales", "inventory", "customers", "finances"]
  sampleQueries: string[]; // Chat prompts to help configure
  setupGuide: {
    steps: string[];
    videoUrl?: string;
    docUrl?: string;
  };
  provider: {
    name: string;
    website: string;
    supportEmail: string;
  };
  pricing?: {
    freeQuota?: string;
    paidPlans?: { name: string; price: string; features: string[] }[];
  };
  popular: boolean; // Show in "Popular" section
  verified: boolean; // Verified by Dyocense
  customizable: boolean; // Can be extended by users
  mcpCompatible: boolean; // Supports MCP protocol
};

/**
 * UK Small Business Connector Marketplace
 */
export const UK_CONNECTOR_MARKETPLACE: ConnectorConfig[] = [
  // Google Drive (Most common for UK small businesses)
  {
    id: "google-drive",
    name: "google-drive",
    displayName: "Google Drive",
    category: "storage",
    tier: "free",
    region: "Global",
    icon: "FileText",
    description: "Import spreadsheets and documents from Google Drive",
    longDescription: "Connect to your Google Drive to import sales data, inventory spreadsheets, customer lists, and financial reports. Perfect for small businesses managing data in Google Sheets.",
    authType: "oauth2",
    fields: [
      {
        name: "folderPath",
        label: "Folder Path (optional)",
        type: "text",
        required: false,
        placeholder: "/Business Data/Sales",
        description: "Specific folder to sync from (leave empty for root)",
      },
      {
        name: "filePattern",
        label: "File Pattern (optional)",
        type: "text",
        required: false,
        placeholder: "*.csv, *.xlsx",
        description: "Filter files by name pattern",
      },
    ],
    dataTypes: ["sales", "inventory", "customers", "finances", "documents"],
    sampleQueries: [
      "Connect my Google Drive sales spreadsheet",
      "Import customer data from Google Sheets",
      "Sync my inventory spreadsheet from Drive",
    ],
    setupGuide: {
      steps: [
        "Click 'Connect with Google' and sign in",
        "Grant access to your Drive",
        "Select the folder or files to sync",
        "Choose data refresh frequency",
      ],
      docUrl: "https://docs.dyocense.com/connectors/google-drive",
    },
    provider: {
      name: "Google",
      website: "https://drive.google.com",
      supportEmail: "support@google.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: false,
  },

  // Xero (UK's most popular accounting software for small businesses)
  {
    id: "xero",
    name: "xero",
    displayName: "Xero Accounting",
    category: "accounting",
    tier: "free",
    region: "UK",
    icon: "CreditCard",
    description: "Sync invoices, expenses, and financial data from Xero",
    longDescription: "Connect to Xero to automatically import invoices, bills, bank transactions, and financial reports. Get real-time insights into your cash flow and profitability.",
    authType: "oauth2",
    fields: [
      {
        name: "organization",
        label: "Xero Organization",
        type: "select",
        required: true,
        description: "Select your Xero organization",
        options: [], // Populated after OAuth
      },
      {
        name: "syncFrequency",
        label: "Sync Frequency",
        type: "select",
        required: true,
        options: [
          { value: "realtime", label: "Real-time" },
          { value: "hourly", label: "Every hour" },
          { value: "daily", label: "Daily" },
        ],
      },
    ],
    dataTypes: ["invoices", "expenses", "bank_transactions", "profit_loss", "balance_sheet"],
    sampleQueries: [
      "Connect my Xero accounting data",
      "Show me last month's invoices from Xero",
      "Import expenses from Xero",
    ],
    setupGuide: {
      steps: [
        "Click 'Connect to Xero' and sign in",
        "Select your organization",
        "Choose which data to sync",
        "Set sync frequency",
      ],
      videoUrl: "https://www.youtube.com/watch?v=xero-setup",
      docUrl: "https://docs.dyocense.com/connectors/xero",
    },
    provider: {
      name: "Xero",
      website: "https://www.xero.com/uk/",
      supportEmail: "support@xero.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: true,
  },

  // Sage (Another popular UK accounting system)
  {
    id: "sage",
    name: "sage",
    displayName: "Sage Accounting",
    category: "accounting",
    tier: "basic",
    region: "UK",
    icon: "TrendingUp",
    description: "Connect to Sage 50, Sage Business Cloud, or Sage Intacct",
    longDescription: "Import financial data, invoices, and reports from Sage accounting systems. Supports Sage 50, Sage Business Cloud Accounting, and Sage Intacct.",
    authType: "api_key",
    fields: [
      {
        name: "product",
        label: "Sage Product",
        type: "select",
        required: true,
        options: [
          { value: "sage50", label: "Sage 50" },
          { value: "sage-business-cloud", label: "Sage Business Cloud" },
          { value: "sage-intacct", label: "Sage Intacct" },
        ],
      },
      {
        name: "apiKey",
        label: "API Key",
        type: "password",
        required: true,
        placeholder: "sk_live_...",
        description: "Found in Sage Developer Portal",
      },
      {
        name: "companyId",
        label: "Company ID",
        type: "text",
        required: true,
        placeholder: "12345",
      },
    ],
    dataTypes: ["invoices", "payments", "customers", "suppliers", "financial_reports"],
    sampleQueries: [
      "Connect my Sage accounting system",
      "Import customer invoices from Sage",
      "Show me Sage profit and loss data",
    ],
    setupGuide: {
      steps: [
        "Log into Sage Developer Portal",
        "Create API credentials",
        "Copy your API key",
        "Enter credentials here",
      ],
      docUrl: "https://docs.dyocense.com/connectors/sage",
    },
    provider: {
      name: "Sage",
      website: "https://www.sage.com/en-gb/",
      supportEmail: "support@sage.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: true,
  },

  // Shopify (E-commerce)
  {
    id: "shopify",
    name: "shopify",
    displayName: "Shopify",
    category: "ecommerce",
    tier: "free",
    region: "Global",
    icon: "ShoppingCart",
    description: "Import orders, products, and customer data from Shopify",
    longDescription: "Connect your Shopify store to analyze sales trends, inventory levels, and customer behavior. Perfect for online retailers.",
    authType: "oauth2",
    fields: [
      {
        name: "storeName",
        label: "Store Name",
        type: "text",
        required: true,
        placeholder: "my-store.myshopify.com",
        description: "Your Shopify store URL",
      },
    ],
    dataTypes: ["orders", "products", "customers", "inventory", "analytics"],
    sampleQueries: [
      "Connect my Shopify store",
      "Show me this week's Shopify orders",
      "Import product inventory from Shopify",
    ],
    setupGuide: {
      steps: [
        "Enter your store URL (e.g., mystore.myshopify.com)",
        "Click 'Connect to Shopify'",
        "Approve app in your Shopify admin",
        "Data will sync automatically",
      ],
      videoUrl: "https://www.youtube.com/watch?v=shopify-connect",
      docUrl: "https://docs.dyocense.com/connectors/shopify",
    },
    provider: {
      name: "Shopify",
      website: "https://www.shopify.com",
      supportEmail: "support@shopify.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: true,
  },

  // Square (POS popular in UK)
  {
    id: "square",
    name: "square",
    displayName: "Square POS",
    category: "pos",
    tier: "free",
    region: "UK",
    icon: "Store",
    description: "Connect Square Point of Sale for transaction and inventory data",
    longDescription: "Import sales transactions, inventory movements, and customer data from Square POS. Ideal for retail shops, restaurants, and cafes.",
    authType: "oauth2",
    fields: [
      {
        name: "locationId",
        label: "Location (optional)",
        type: "select",
        required: false,
        description: "Specific location to sync (leave empty for all)",
        options: [], // Populated after OAuth
      },
    ],
    dataTypes: ["transactions", "inventory", "customers", "employees", "reports"],
    sampleQueries: [
      "Connect my Square POS system",
      "Show me today's Square transactions",
      "Import inventory from Square",
    ],
    setupGuide: {
      steps: [
        "Click 'Connect with Square'",
        "Sign in to your Square account",
        "Grant access permissions",
        "Select locations to sync",
      ],
      docUrl: "https://docs.dyocense.com/connectors/square",
    },
    provider: {
      name: "Square",
      website: "https://squareup.com/gb/en",
      supportEmail: "support@squareup.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: true,
  },

  // QuickBooks (Popular UK accounting)
  {
    id: "quickbooks",
    name: "quickbooks",
    displayName: "QuickBooks",
    category: "accounting",
    tier: "free",
    region: "UK",
    icon: "Package",
    description: "Sync QuickBooks invoices, expenses, and financial data",
    longDescription: "Connect QuickBooks Online to import invoices, bills, payments, and financial reports. Keep your financial data in sync automatically.",
    authType: "oauth2",
    fields: [
      {
        name: "companyId",
        label: "Company",
        type: "select",
        required: true,
        description: "Select your QuickBooks company",
        options: [], // Populated after OAuth
      },
    ],
    dataTypes: ["invoices", "bills", "payments", "customers", "vendors", "reports"],
    sampleQueries: [
      "Connect my QuickBooks account",
      "Import invoices from QuickBooks",
      "Show me QuickBooks cash flow",
    ],
    setupGuide: {
      steps: [
        "Click 'Connect to QuickBooks'",
        "Sign in with your Intuit account",
        "Select your company",
        "Approve data access",
      ],
      docUrl: "https://docs.dyocense.com/connectors/quickbooks",
    },
    provider: {
      name: "Intuit QuickBooks",
      website: "https://quickbooks.intuit.com/uk/",
      supportEmail: "support@intuit.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: true,
  },

  // WooCommerce (Popular UK e-commerce)
  {
    id: "woocommerce",
    name: "woocommerce",
    displayName: "WooCommerce",
    category: "ecommerce",
    tier: "free",
    region: "Global",
    icon: "ShoppingCart",
    description: "Connect WooCommerce store for orders and products",
    longDescription: "Import orders, products, and customer data from your WooCommerce store. Analyze sales trends and inventory levels.",
    authType: "api_key",
    fields: [
      {
        name: "storeUrl",
        label: "Store URL",
        type: "url",
        required: true,
        placeholder: "https://mystore.com",
        description: "Your WooCommerce store URL",
      },
      {
        name: "consumerKey",
        label: "Consumer Key",
        type: "text",
        required: true,
        placeholder: "ck_...",
        description: "Found in WooCommerce > Settings > Advanced > REST API",
      },
      {
        name: "consumerSecret",
        label: "Consumer Secret",
        type: "password",
        required: true,
        placeholder: "cs_...",
      },
    ],
    dataTypes: ["orders", "products", "customers", "coupons", "reports"],
    sampleQueries: [
      "Connect my WooCommerce store",
      "Show me WooCommerce orders",
      "Import product data from WooCommerce",
    ],
    setupGuide: {
      steps: [
        "Go to WooCommerce > Settings > Advanced > REST API",
        "Click 'Add key' to create API credentials",
        "Copy Consumer Key and Secret",
        "Paste them here",
      ],
      videoUrl: "https://www.youtube.com/watch?v=woocommerce-api",
      docUrl: "https://docs.dyocense.com/connectors/woocommerce",
    },
    provider: {
      name: "WooCommerce",
      website: "https://woocommerce.com",
      supportEmail: "support@woocommerce.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: false,
  },

  // Stripe (Payment processing)
  {
    id: "stripe",
    name: "stripe",
    displayName: "Stripe Payments",
    category: "finance",
    tier: "free",
    region: "Global",
    icon: "CreditCard",
    description: "Import payment transactions and customer data from Stripe",
    longDescription: "Connect Stripe to analyze payment trends, track revenue, and monitor subscription metrics. Essential for online businesses.",
    authType: "api_key",
    fields: [
      {
        name: "apiKey",
        label: "Secret Key",
        type: "password",
        required: true,
        placeholder: "sk_live_...",
        description: "Found in Stripe Dashboard > Developers > API keys",
        validation: {
          pattern: "^sk_(test|live)_[a-zA-Z0-9]+$",
          message: "Must be a valid Stripe secret key",
        },
      },
    ],
    dataTypes: ["payments", "customers", "subscriptions", "invoices", "disputes"],
    sampleQueries: [
      "Connect my Stripe payments",
      "Show me this month's Stripe revenue",
      "Import subscription data from Stripe",
    ],
    setupGuide: {
      steps: [
        "Log into Stripe Dashboard",
        "Go to Developers > API keys",
        "Reveal and copy your Secret key",
        "Paste it here (use test key for testing)",
      ],
      docUrl: "https://docs.dyocense.com/connectors/stripe",
    },
    provider: {
      name: "Stripe",
      website: "https://stripe.com/gb",
      supportEmail: "support@stripe.com",
    },
    popular: true,
    verified: true,
    customizable: false,
    mcpCompatible: true,
  },

  // HubSpot (CRM)
  {
    id: "hubspot",
    name: "hubspot",
    displayName: "HubSpot CRM",
    category: "crm",
    tier: "free",
    region: "Global",
    icon: "Users",
    description: "Sync contacts, deals, and sales pipeline from HubSpot",
    longDescription: "Connect HubSpot CRM to import contacts, deals, companies, and sales activities. Track your sales pipeline and customer relationships.",
    authType: "oauth2",
    fields: [
      {
        name: "portal",
        label: "HubSpot Portal",
        type: "select",
        required: true,
        description: "Select your HubSpot portal",
        options: [], // Populated after OAuth
      },
    ],
    dataTypes: ["contacts", "companies", "deals", "tickets", "activities"],
    sampleQueries: [
      "Connect my HubSpot CRM",
      "Show me open deals from HubSpot",
      "Import contacts from HubSpot",
    ],
    setupGuide: {
      steps: [
        "Click 'Connect with HubSpot'",
        "Sign in to your HubSpot account",
        "Select your portal",
        "Approve data access",
      ],
      docUrl: "https://docs.dyocense.com/connectors/hubspot",
    },
    provider: {
      name: "HubSpot",
      website: "https://www.hubspot.com",
      supportEmail: "support@hubspot.com",
    },
    popular: false,
    verified: true,
    customizable: false,
    mcpCompatible: true,
  },

  // Generic REST API (MCP Compatible)
  {
    id: "rest-api-mcp",
    name: "rest-api-mcp",
    displayName: "Custom REST API (MCP)",
    category: "storage",
    tier: "free",
    region: "Global",
    icon: "Boxes",
    description: "Connect to any REST API using Model Context Protocol",
    longDescription: "Use MCP to connect to any custom REST API endpoint. Perfect for proprietary systems or unsupported integrations. Can be published to marketplace.",
    authType: "mcp",
    fields: [
      {
        name: "apiUrl",
        label: "API Base URL",
        type: "url",
        required: true,
        placeholder: "https://api.yourcompany.com",
      },
      {
        name: "authMethod",
        label: "Authentication",
        type: "select",
        required: true,
        options: [
          { value: "api_key", label: "API Key" },
          { value: "bearer", label: "Bearer Token" },
          { value: "basic", label: "Basic Auth" },
          { value: "oauth2", label: "OAuth 2.0" },
        ],
      },
      {
        name: "apiKey",
        label: "API Key / Token",
        type: "password",
        required: true,
        placeholder: "Your API key or token",
      },
      {
        name: "endpoints",
        label: "Endpoints (JSON)",
        type: "text",
        required: false,
        placeholder: '{"sales": "/api/sales", "customers": "/api/customers"}',
        description: "Map data types to API endpoints",
      },
    ],
    dataTypes: ["custom"],
    sampleQueries: [
      "Connect my custom ERP system",
      "Set up REST API connection",
      "Import data from my API",
    ],
    setupGuide: {
      steps: [
        "Enter your API base URL",
        "Choose authentication method",
        "Provide credentials",
        "Map endpoints to data types (optional)",
        "Test connection",
      ],
      docUrl: "https://docs.dyocense.com/connectors/custom-rest-api",
    },
    provider: {
      name: "Custom",
      website: "",
      supportEmail: "support@dyocense.com",
    },
    popular: false,
    verified: true,
    customizable: true,
    mcpCompatible: true,
  },
];

/**
 * Get connectors by category
 */
export function getConnectorsByCategory(category: ConnectorCategory): ConnectorConfig[] {
  return UK_CONNECTOR_MARKETPLACE.filter((c) => c.category === category);
}

/**
 * Get popular connectors
 */
export function getPopularConnectors(): ConnectorConfig[] {
  return UK_CONNECTOR_MARKETPLACE.filter((c) => c.popular);
}

/**
 * Get connectors by region
 */
export function getConnectorsByRegion(region: string): ConnectorConfig[] {
  return UK_CONNECTOR_MARKETPLACE.filter((c) => c.region === region || c.region === "Global");
}

/**
 * Search connectors
 */
export function searchConnectors(query: string): ConnectorConfig[] {
  const lowerQuery = query.toLowerCase();
  return UK_CONNECTOR_MARKETPLACE.filter(
    (c) =>
      c.displayName.toLowerCase().includes(lowerQuery) ||
      c.description.toLowerCase().includes(lowerQuery) ||
      c.dataTypes.some((dt) => dt.toLowerCase().includes(lowerQuery))
  );
}

/**
 * Get connector by ID
 */
export function getConnectorById(id: string): ConnectorConfig | undefined {
  return UK_CONNECTOR_MARKETPLACE.find((c) => c.id === id);
}

/**
 * Categories for marketplace navigation
 */
export const CONNECTOR_CATEGORIES = [
  { id: "finance", label: "Finance & Accounting", icon: "CreditCard" },
  { id: "ecommerce", label: "E-commerce", icon: "ShoppingCart" },
  { id: "pos", label: "Point of Sale", icon: "Store" },
  { id: "crm", label: "CRM & Sales", icon: "Users" },
  { id: "storage", label: "Storage & Files", icon: "FileText" },
  { id: "inventory", label: "Inventory", icon: "Boxes" },
];
