/**
 * Tenant-Level Connector Management
 * Stores configured connectors at tenant level for reuse across chat sessions
 */

import type { ConnectorConfig } from "./connectorMarketplace";

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
import { listConnectors, createConnector, deleteConnector, getConnector } from "./api";

class TenantConnectorStore {
  // Cache for performance (optional)
  private cache: Map<string, Connector[]> = new Map();
  private cacheTimeout = 60000; // 1 minute
  private cacheTimestamps: Map<string, number> = new Map();

  /**
   * Get all connectors for a tenant from the backend API
   */
  async getAll(tenantId: string): Promise<TenantConnector[]> {
    try {
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
      
      // Fallback to localStorage for offline support
      return this._getFromLocalStorage(tenantId);
    }
  }

  /**
   * Get connector by ID
   */
  async getById(id: string): Promise<TenantConnector | null> {
    try {
      const connector = await getConnector(id);
      return this._convertSingleToLegacyFormat(connector);
    } catch (error) {
      console.error("Failed to fetch connector:", error);
      return null;
    }
  }

  /**
   * Add a new connector
   */
  async add(connector: Omit<TenantConnector, "id" | "createdAt" | "updatedAt">): Promise<TenantConnector> {
    try {
      const created = await createConnector({
        connector_type: connector.connectorId,
        display_name: connector.displayName,
        config: connector.config,
        sync_frequency: connector.syncFrequency,
      });
      
      // Clear cache
      this.cache.delete(connector.tenantId);
      
      return this._convertSingleToLegacyFormat(created);
    } catch (error) {
      console.error("Failed to create connector:", error);
      throw error;
    }
  }

  /**
   * Delete a connector
   */
  async delete(id: string): Promise<boolean> {
    try {
      await deleteConnector(id);
      
      // Clear cache
      this.cache.clear();
      
      return true;
    } catch (error) {
      console.error("Failed to delete connector:", error);
      return false;
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
        totalRecords: connector.metadata.total_records,
        lastSyncDuration: connector.metadata.last_sync_duration,
        errorMessage: connector.metadata.error_message,
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
export function checkDataAvailability(
  tenantId: string,
  requiredDataTypes: string[]
): {
  available: string[];
  missing: string[];
  suggestions: string[];
} {
  const connectors = tenantConnectorStore.getAll(tenantId).filter((c) => c.status === "active");
  
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
  const connectors = tenantConnectorStore.getAll(tenantId).filter((c) => c.status === "active");
  
  let success = 0;
  let failed = 0;
  const errors: string[] = [];
  
  for (const connector of connectors) {
    try {
      // Update status to syncing
      tenantConnectorStore.update(connector.id, { status: "syncing" });
      
      // Simulate sync (replace with actual API call)
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      // Update success
      tenantConnectorStore.update(connector.id, {
        status: "active",
        lastSync: new Date(),
        metadata: {
          ...connector.metadata,
          totalRecords: Math.floor(Math.random() * 10000) + 100,
        },
      });
      
      success++;
    } catch (error) {
      failed++;
      errors.push(`${connector.displayName}: ${error instanceof Error ? error.message : "Unknown error"}`);
      
      tenantConnectorStore.update(connector.id, {
        status: "error",
        metadata: {
          ...connector.metadata,
          errorMessage: error instanceof Error ? error.message : "Sync failed",
        },
      });
    }
  }
  
  return { success, failed, errors };
}
