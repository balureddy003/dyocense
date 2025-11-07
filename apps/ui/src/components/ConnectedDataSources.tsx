/**
 * Connected Data Sources Panel
 * Shows active tenant connectors and allows management
 */

import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  Loader2,
  Plus,
  RefreshCw,
  Settings,
  Trash2,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getConnectorById } from "../lib/connectorMarketplace";
import { syncAllConnectors, tenantConnectorStore, type TenantConnector } from "../lib/tenantConnectors";

type ConnectedDataSourcesProps = {
  tenantId: string;
  onAddConnector: () => void;
  onConfigureConnector?: (connectorId: string) => void;
};

export function ConnectedDataSources({
  tenantId,
  onAddConnector,
  onConfigureConnector,
}: ConnectedDataSourcesProps) {
  const [connectors, setConnectors] = useState<TenantConnector[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<{ success: number; failed: number } | null>(null);

  useEffect(() => {
    loadConnectors();
  }, [tenantId]);

  const loadConnectors = async () => {
    try {
      const loaded = await tenantConnectorStore.getAll(tenantId);
      // Defensive: ensure it's always an array
      setConnectors(Array.isArray(loaded) ? loaded : []);
    } catch (e) {
      console.warn("Failed to load connectors", e);
      setConnectors([]);
    }
  };

  const handleSyncAll = async () => {
    setSyncing(true);
    setSyncResult(null);

    try {
      const result = await syncAllConnectors(tenantId);
      setSyncResult(result);
      loadConnectors();
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  const handleDelete = (connectorId: string) => {
    if (confirm("Are you sure you want to disconnect this data source?")) {
      tenantConnectorStore.delete(connectorId);
      loadConnectors();
    }
  };

  const activeCount = connectors.filter((c) => c.status === "active").length;
  const errorCount = connectors.filter((c) => c.status === "error").length;

  if (connectors.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center">
          <Database className="mx-auto text-gray-400 mb-3" size={40} />
          <h3 className="font-semibold text-gray-900 mb-2">No data sources connected</h3>
          <p className="text-sm text-gray-600 mb-4">
            Connect your business data to get personalized insights and recommendations.
          </p>
          <button
            onClick={onAddConnector}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={18} />
            Connect Data Source
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="text-blue-600" size={20} />
          <div>
            <h3 className="font-semibold text-gray-900">Connected Data Sources</h3>
            <p className="text-xs text-gray-600">
              {activeCount} active • {errorCount > 0 && `${errorCount} with errors`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSyncAll}
            disabled={syncing}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            title="Sync all data sources"
          >
            <RefreshCw className={syncing ? "animate-spin" : ""} size={18} />
          </button>
          <button
            onClick={onAddConnector}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={16} />
            Add
          </button>
        </div>
      </div>

      {/* Sync Result */}
      {syncResult && (
        <div className="px-6 py-3 bg-blue-50 border-b border-blue-100">
          <p className="text-sm text-blue-900">
            ✓ Synced {syncResult.success} data source{syncResult.success !== 1 ? "s" : ""}
            {syncResult.failed > 0 && ` • ${syncResult.failed} failed`}
          </p>
        </div>
      )}

      {/* Connector List */}
      <div className="divide-y">
        {connectors.map((connector) => (
          <ConnectorRow
            key={connector.id}
            connector={connector}
            onDelete={() => handleDelete(connector.id)}
            onConfigure={onConfigureConnector}
          />
        ))}
      </div>
    </div>
  );
}

type ConnectorRowProps = {
  connector: TenantConnector;
  onDelete: () => void;
  onConfigure?: (connectorId: string) => void;
};

function ConnectorRow({ connector, onDelete, onConfigure }: ConnectorRowProps) {
  const config = getConnectorById(connector.connectorId);
  const [expanded, setExpanded] = useState(false);

  const StatusIcon = {
    active: CheckCircle2,
    inactive: AlertCircle,
    error: AlertCircle,
    syncing: Loader2,
    testing: Loader2,
  }[connector.status] || AlertCircle;

  const statusColor = {
    active: "text-green-600",
    inactive: "text-gray-400",
    error: "text-red-600",
    syncing: "text-blue-600",
    testing: "text-blue-600",
  }[connector.status] || "text-gray-400";

  const statusBgColor = {
    active: "bg-green-50",
    inactive: "bg-gray-50",
    error: "bg-red-50",
    syncing: "bg-blue-50",
    testing: "bg-blue-50",
  }[connector.status] || "bg-gray-50";

  return (
    <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1">
          <div className={`w-10 h-10 rounded-lg ${statusBgColor} flex items-center justify-center`}>
            <StatusIcon
              className={`${statusColor} ${connector.status === "syncing" ? "animate-spin" : ""}`}
              size={20}
            />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-medium text-gray-900 truncate">{connector.displayName}</h4>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${connector.status === "active"
                  ? "bg-green-100 text-green-700"
                  : connector.status === "error"
                    ? "bg-red-100 text-red-700"
                    : "bg-gray-100 text-gray-700"
                  }`}
              >
                {connector.status}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-600">
              <span>{connector.category}</span>
              {connector.lastSync && (
                <>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    <Clock size={12} />
                    <span>
                      Synced {formatRelativeTime(connector.lastSync)}
                    </span>
                  </div>
                </>
              )}
              {connector.metadata?.totalRecords && (
                <>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    <TrendingUp size={12} />
                    <span>{connector.metadata.totalRecords.toLocaleString()} records</span>
                  </div>
                </>
              )}
            </div>
            {connector.status === "error" && connector.metadata?.errorMessage && (
              <p className="text-xs text-red-600 mt-1">
                {connector.metadata.errorMessage}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1 ml-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-xs"
          >
            {expanded ? "Less" : "More"}
          </button>
          {onConfigure && (
            <button
              onClick={() => onConfigure(connector.id)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Configure"
            >
              <Settings size={16} />
            </button>
          )}
          <button
            onClick={onDelete}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Disconnect"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-4 pl-13 space-y-3">
          <div>
            <h5 className="text-xs font-medium text-gray-700 mb-1">Data Types</h5>
            <div className="flex flex-wrap gap-1">
              {connector.dataTypes.map((dt) => (
                <span
                  key={dt}
                  className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded"
                >
                  {dt}
                </span>
              ))}
            </div>
          </div>
          {config?.sampleQueries && config.sampleQueries.length > 0 && (
            <div>
              <h5 className="text-xs font-medium text-gray-700 mb-1">
                What you can ask:
              </h5>
              <ul className="text-xs text-gray-600 space-y-1">
                {config.sampleQueries.slice(0, 3).map((query, idx) => (
                  <li key={idx}>• {query}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="text-xs text-gray-500">
            <p>Connected {formatRelativeTime(connector.createdAt)}</p>
            {connector.syncFrequency && (
              <p>Sync frequency: {connector.syncFrequency}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
