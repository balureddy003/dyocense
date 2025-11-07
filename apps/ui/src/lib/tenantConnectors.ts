/**
 * Tenant-Level Connector Management
 * Stores configured connectors at tenant level for reuse across chat sessions
 */


export type TenantConnector = {
  id: string;
  tenantId: string;
  connectorId: string; // Reference to ConnectorConfig.id
  connectorName: string;
  displayName: string; // Custom name given by user
  category: string;
  icon: string;
  config: Record<string, string>; // Encrypted credentials - never populated from backend
  dataTypes: string[];
  status: "active" | "inactive" | "error" | "syncing" | "testing";
  lastSync?: Date;
  syncFrequency?: "realtime" | "hourly" | "daily" | "weekly" | "manual";
  metadata?: {
    totalRecords?: number;
    lastSyncDuration?: number;
    errorMessage?: string;
  };
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
};

export type ConnectorDataContext = {
  connectorId: string;
  connectorName: string;
  displayName: string;
  dataTypes: string[];
  sampleData?: {
    type: string;
    count: number;
    columns: string[];
    preview: any[];
  }[];
};

/**
 * Tenant Connector Store - API-backed version
 * Replace localStorage with real backend API calls
 */
import type { Connector } from "./api";
import { createConnector, deleteConnector, getConnector, listConnectors } from "./api";

class TenantConnectorStore {
  // Cache for performance (optional)
  private cache: Map<string, Connector[]> = new Map();
  private cacheTimeout = 60000; // 1 minute
  private cacheTimestamps: Map<string, number> = new Map();
  // When true, operate purely via localStorage and avoid backend calls
  private localMode = false;

  /**
   * Get all connectors for a tenant from the backend API
   */
  async getAll(tenantId: string): Promise<TenantConnector[]> {
    try {
      if (this.localMode) {
        return this._getFromLocalStorage(tenantId);
      }
      // Check cache first
      const cached = this.cache.get(tenantId);
      const cacheTime = this.cacheTimestamps.get(tenantId);
      if (cached && cacheTime && Date.now() - cacheTime < this.cacheTimeout) {
        return this._convertToLegacyFormat(cached);
      }

      // Fetch from API
      const connectors = await listConnectors();

      // Update cache
      this.cache.set(tenantId, connectors);
      this.cacheTimestamps.set(tenantId, Date.now());

      return this._convertToLegacyFormat(connectors);
    } catch (error) {
      console.error("Failed to fetch connectors:", error);
      // Switch to local-only mode after first backend failure
      this.localMode = true;
      // Fallback to localStorage for offline support
      return this._getFromLocalStorage(tenantId);
    }
  }

  /**
   * Get connector by ID
   */
  async getById(id: string): Promise<TenantConnector | null> {
    try {
      // If we've determined backend connectors are disabled, or this is a locally-generated id, read from localStorage directly
      if (this.localMode || id.startsWith("connector-")) {
        const fromLocal = this._getFromLocalStorageAny(id);
        if (fromLocal) return fromLocal;
        // If not found locally and not in local mode, fall through to backend attempt
        if (this.localMode) return null;
      }
      const connector = await getConnector(id);
      return this._convertSingleToLegacyFormat(connector);
    } catch (error) {
      console.warn("Backend connector API not available, checking localStorage:", error);

      // Fallback to localStorage
      this.localMode = true;
      const fromLocal = this._getFromLocalStorageAny(id);
      if (fromLocal) return fromLocal;
      return null;
    }
  }

  /**
   * Add a new connector
   */
  async add(connector: Omit<TenantConnector, "id" | "createdAt" | "updatedAt">): Promise<TenantConnector> {
    try {
      if (this.localMode) {
        return this._addToLocalStorage(connector);
      }
      const created = await createConnector({
        connector_type: connector.connectorId,
        display_name: connector.displayName,
        config: connector.config,
        sync_frequency: connector.syncFrequency,
      });

      // Clear cache
      this.cache.delete(connector.tenantId);
      // Ensure we keep using backend
      this.localMode = false;

      return this._convertSingleToLegacyFormat(created);
    } catch (error) {
      console.warn("Backend connector API not available, falling back to localStorage:", error);
      // Switch permanently to local-only mode for this session
      this.localMode = true;
      return this._addToLocalStorage(connector);
    }
  }

  /**
   * Delete a connector
   */
  async delete(id: string): Promise<boolean> {
    try {
      if (this.localMode || id.startsWith("connector-")) {
        return this._deleteFromLocalStorage(id);
      }
      await deleteConnector(id);

      // Clear cache
      this.cache.clear();

      return true;
    } catch (error) {
      console.warn("Backend connector API not available, deleting from localStorage:", error);
      this.localMode = true;
      // Fallback: delete from localStorage
      return this._deleteFromLocalStorage(id);
    }
  }

  /**
   * Get connectors by data type
   */
  async getByDataType(tenantId: string, dataType: string): Promise<TenantConnector[]> {
    const all = await this.getAll(tenantId);
    return all.filter((c) =>
      c.status === "active" && c.dataTypes.includes(dataType)
    );
  }

  /**
   * Clear cache for a tenant
   */
  clearCache(tenantId?: string) {
    if (tenantId) {
      this.cache.delete(tenantId);
      this.cacheTimestamps.delete(tenantId);
    } else {
      this.cache.clear();
      this.cacheTimestamps.clear();
    }
  }

  // ==================== Private Helper Methods ====================

  /**
   * Convert backend API format to legacy TenantConnector format
   */
  private _convertToLegacyFormat(connectors: Connector[]): TenantConnector[] {
    return connectors.map(c => this._convertSingleToLegacyFormat(c));
  }

  private _convertSingleToLegacyFormat(connector: Connector): TenantConnector {
    return {
      id: connector.connector_id,
      tenantId: connector.tenant_id,
      connectorId: connector.connector_type,
      connectorName: connector.connector_name,
      displayName: connector.display_name,
      category: connector.category,
      icon: connector.icon,
      config: {}, // Never expose config from backend
      dataTypes: connector.data_types,
      status: connector.status,
      lastSync: connector.last_sync ? new Date(connector.last_sync) : undefined,
      syncFrequency: connector.sync_frequency,
      metadata: {
        totalRecords: connector.metadata?.total_records,
        lastSyncDuration: connector.metadata?.last_sync_duration,
        errorMessage: connector.metadata?.error_message,
      },
      createdAt: new Date(connector.created_at),
      updatedAt: new Date(connector.updated_at),
      createdBy: connector.created_by,
    };
  }

  /**
   * Fallback to localStorage (for offline support or development)
   */
  private _getFromLocalStorage(tenantId: string): TenantConnector[] {
    const storageKey = "dyocense_tenant_connectors";
    const stored = localStorage.getItem(storageKey);
    if (!stored) return [];

    try {
      const all: TenantConnector[] = JSON.parse(stored);
      return all.filter((c) => c.tenantId === tenantId).map((c) => ({
        ...c,
        createdAt: new Date(c.createdAt),
        updatedAt: new Date(c.updatedAt),
        lastSync: c.lastSync ? new Date(c.lastSync) : undefined,
      }));
    } catch (error) {
      console.error("Failed to parse localStorage:", error);
      return [];
    }
  }

  /** Helper: find any connector by id from localStorage */
  private _getFromLocalStorageAny(id: string): TenantConnector | null {
    const storageKey = "dyocense_tenant_connectors";
    const stored = localStorage.getItem(storageKey);
    if (!stored) return null;
    try {
      const all: TenantConnector[] = JSON.parse(stored);
      const found = all.find(c => c.id === id);
      if (!found) return null;
      return {
        ...found,
        createdAt: new Date(found.createdAt),
        updatedAt: new Date(found.updatedAt),
        lastSync: found.lastSync ? new Date(found.lastSync) : undefined,
      };
    } catch (err) {
      console.error("Failed to parse localStorage:", err);
      return null;
    }
  }

  /** Helper: add connector to localStorage with generated id */
  private _addToLocalStorage(connector: Omit<TenantConnector, "id" | "createdAt" | "updatedAt">): TenantConnector {
    const newConnector: TenantConnector = {
      ...connector,
      id: `connector-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    const storageKey = "dyocense_tenant_connectors";
    const stored = localStorage.getItem(storageKey);
    const all: TenantConnector[] = stored ? JSON.parse(stored) : [];
    all.push(newConnector);
    localStorage.setItem(storageKey, JSON.stringify(all));
    // Clear cache
    this.cache.delete(connector.tenantId);
    return newConnector;
  }

  /** Helper: delete connector from localStorage */
  private _deleteFromLocalStorage(id: string): boolean {
    const storageKey = "dyocense_tenant_connectors";
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      try {
        const all: TenantConnector[] = JSON.parse(stored);
        const filtered = all.filter(c => c.id !== id);
        localStorage.setItem(storageKey, JSON.stringify(filtered));
        // Clear cache
        this.cache.clear();
        return true;
      } catch (parseError) {
        console.error("Failed to parse localStorage:", parseError);
      }
    }
    return false;
  }
}

export const tenantConnectorStore = new TenantConnectorStore();

/**
 * Chat context builder - creates data context summary for AI
 */
export async function buildDataContext(tenantId: string): Promise<ConnectorDataContext[]> {
  const connectors = await tenantConnectorStore.getAll(tenantId);

  return connectors
    .filter((c) => c.status === "active")
    .map((c) => ({
      connectorId: c.id,
      connectorName: c.connectorName,
      displayName: c.displayName,
      dataTypes: c.dataTypes,
      sampleData: c.metadata?.totalRecords
        ? [
          {
            type: c.dataTypes[0] || "unknown",
            count: c.metadata.totalRecords,
            columns: [], // Would be populated from actual data
            preview: [],
          },
        ]
        : undefined,
    }));
}

/**
 * Generate chat prompt with available data sources
 */
export async function generateDataContextPrompt(tenantId: string): Promise<string> {
  const connectors = await tenantConnectorStore.getAll(tenantId);

  if (connectors.length === 0) {
    return "No data sources connected yet. Would you like to connect your business data?";
  }

  const activeConnectors = connectors.filter((c) => c.status === "active");

  if (activeConnectors.length === 0) {
    return "You have data sources configured but none are currently active. Would you like me to help you activate them?";
  }

  const dataByType: Record<string, string[]> = {};
  activeConnectors.forEach((c) => {
    c.dataTypes.forEach((type) => {
      if (!dataByType[type]) dataByType[type] = [];
      dataByType[type].push(c.displayName);
    });
  });

  const parts = Object.entries(dataByType).map(
    ([type, sources]) => `${type} data from ${sources.join(", ")}`
  );

  return `I have access to your: ${parts.join("; ")}. How can I help you analyze this data?`;
}

/**
 * Suggest connectors based on chat intent
 */
export function suggestConnectorFromIntent(intent: string): {
  connectorIds: string[];
  reason: string;
} | null {
  const lowerIntent = intent.toLowerCase();

  // Financial/Accounting
  if (
    lowerIntent.includes("invoice") ||
    lowerIntent.includes("expense") ||
    lowerIntent.includes("accounting") ||
    lowerIntent.includes("profit") ||
    lowerIntent.includes("cash flow")
  ) {
    return {
      connectorIds: ["xero", "sage", "quickbooks"],
      reason: "To analyze your financial data, I recommend connecting your accounting system.",
    };
  }

  // E-commerce
  if (
    lowerIntent.includes("sales") ||
    lowerIntent.includes("order") ||
    lowerIntent.includes("product") ||
    lowerIntent.includes("customer") ||
    lowerIntent.includes("revenue")
  ) {
    return {
      connectorIds: ["shopify", "woocommerce", "square"],
      reason: "To analyze sales and customer data, connect your e-commerce platform or POS system.",
    };
  }

  // Inventory
  if (
    lowerIntent.includes("inventory") ||
    lowerIntent.includes("stock") ||
    lowerIntent.includes("product level") ||
    lowerIntent.includes("warehouse")
  ) {
    return {
      connectorIds: ["shopify", "square", "rest-api-mcp"],
      reason: "To track inventory levels, connect your inventory management system.",
    };
  }

  // CRM/Sales Pipeline
  if (
    lowerIntent.includes("lead") ||
    lowerIntent.includes("deal") ||
    lowerIntent.includes("pipeline") ||
    lowerIntent.includes("crm")
  ) {
    return {
      connectorIds: ["hubspot"],
      reason: "To analyze your sales pipeline, connect your CRM system.",
    };
  }

  // Google Drive/Sheets
  if (
    lowerIntent.includes("spreadsheet") ||
    lowerIntent.includes("google") ||
    lowerIntent.includes("drive") ||
    lowerIntent.includes("sheet")
  ) {
    return {
      connectorIds: ["google-drive"],
      reason: "I can import data from your Google Drive spreadsheets.",
    };
  }

  return null;
}

/**
 * Check if tenant has required data for a goal
 */
export async function checkDataAvailability(
  tenantId: string,
  requiredDataTypes: string[]
): Promise<{
  available: string[];
  missing: string[];
  suggestions: string[];
}> {
  const all = await tenantConnectorStore.getAll(tenantId);
  const connectors = all.filter((c) => c.status === "active");

  const availableTypes = new Set<string>();
  connectors.forEach((c) => {
    c.dataTypes.forEach((type) => availableTypes.add(type));
  });

  const available = requiredDataTypes.filter((type) => availableTypes.has(type));
  const missing = requiredDataTypes.filter((type) => !availableTypes.has(type));

  const suggestions: string[] = [];
  missing.forEach((type) => {
    if (type === "invoices" || type === "expenses") {
      suggestions.push("Connect Xero or Sage to import financial data");
    } else if (type === "orders" || type === "sales") {
      suggestions.push("Connect Shopify or Square to import sales data");
    } else if (type === "inventory") {
      suggestions.push("Connect your inventory system via API");
    } else if (type === "customers") {
      suggestions.push("Connect HubSpot CRM or your e-commerce platform");
    } else {
      suggestions.push(`Upload ${type} data or connect via custom API`);
    }
  });

  return { available, missing, suggestions };
}

/**
 * Sync all active connectors
 */
export async function syncAllConnectors(tenantId: string): Promise<{
  success: number;
  failed: number;
  errors: string[];
}> {
  const all = await tenantConnectorStore.getAll(tenantId);
  const connectors = all.filter((c) => c.status === "active");

  let success = 0;
  let failed = 0;
  const errors: string[] = [];

  for (const connector of connectors) {
    try {
      // Simulate sync (replace with actual API call)
      await new Promise((resolve) => setTimeout(resolve, 1000));

      success++;
    } catch (error) {
      failed++;
      errors.push(`${connector.displayName}: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  }
  // Clear cache so a subsequent getAll fetches latest
  tenantConnectorStore.clearCache(tenantId);
  return { success, failed, errors };
}
