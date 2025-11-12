import { AlertCircle, CheckCircle2, Database, FileUp, Link2, Loader2, Sheet, X } from "lucide-react";
import { useState } from "react";

export type DataSource = {
  id: string;
  type: "file" | "api" | "database" | "spreadsheet";
  name: string;
  status: "uploading" | "processing" | "ready" | "error";
  metadata?: {
    size?: number;
    rows?: number;
    columns?: string[];
    previewData?: any[];
    error?: string;
  };
};

export type DataConnector = {
  id: string;
  name: string;
  type: "api" | "database" | "spreadsheet";
  icon: React.ReactNode;
  description: string;
  fields: {
    name: string;
    label: string;
    type: "text" | "password" | "url";
    required: boolean;
    placeholder: string;
  }[];
};

const AVAILABLE_CONNECTORS: DataConnector[] = [
  {
    id: "rest-api",
    name: "REST API",
    type: "api",
    icon: <Link2 size={20} />,
    description: "Connect to any REST API endpoint",
    fields: [
      { name: "url", label: "API URL", type: "url", required: true, placeholder: "https://api.example.com/data" },
      { name: "method", label: "HTTP Method", type: "text", required: true, placeholder: "GET" },
      { name: "headers", label: "Headers (JSON)", type: "text", required: false, placeholder: '{"Authorization": "Bearer token"}' },
    ],
  },
  {
    id: "google-sheets",
    name: "Google Sheets",
    type: "spreadsheet",
    icon: <Sheet size={20} />,
    description: "Import data from Google Sheets",
    fields: [
      { name: "sheetUrl", label: "Sheet URL", type: "url", required: true, placeholder: "https://docs.google.com/spreadsheets/d/..." },
      { name: "range", label: "Range", type: "text", required: false, placeholder: "Sheet1!A1:Z100" },
    ],
  },
  {
    id: "postgres",
    name: "PostgreSQL",
    type: "database",
    icon: <Database size={20} />,
    description: "Connect to PostgreSQL database",
    fields: [
      { name: "host", label: "Host", type: "text", required: true, placeholder: "localhost" },
      { name: "port", label: "Port", type: "text", required: true, placeholder: "5432" },
      { name: "database", label: "Database", type: "text", required: true, placeholder: "mydb" },
      { name: "username", label: "Username", type: "text", required: true, placeholder: "user" },
      { name: "password", label: "Password", type: "password", required: true, placeholder: "password" },
      { name: "query", label: "SQL Query", type: "text", required: true, placeholder: "SELECT * FROM sales ORDER BY date DESC LIMIT 1000" },
    ],
  },
];

export type DataUploaderProps = {
  onDataSourceAdded: (source: DataSource) => void;
  existingSources: DataSource[];
  // Optional backend ingestion wiring
  tenantId?: string;
  csvConnectorId?: string; // connector_id for csv_upload type
  ingestionApiBase?: string; // e.g. http://localhost:8002 (connectors service)
};

export function DataUploader({ onDataSourceAdded, existingSources, tenantId, csvConnectorId, ingestionApiBase }: DataUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [showConnectors, setShowConnectors] = useState(false);
  const [selectedConnector, setSelectedConnector] = useState<DataConnector | null>(null);
  const [connectorData, setConnectorData] = useState<Record<string, string>>({});

  const handleFileUpload = async (files: FileList) => {
    Array.from(files).forEach(async (file) => {
      const source: DataSource = {
        id: `file-${Date.now()}-${Math.random()}`,
        type: "file",
        name: file.name,
        status: "uploading",
        metadata: { size: file.size },
      };

      onDataSourceAdded(source);

      // Simulate file processing
      setTimeout(() => {
        processFile(file, source.id);
      }, 1000);
    });
  };

  const processFile = async (file: File, sourceId: string) => {
    try {
      // Read file content
      const content = await file.text();

      // Parse based on file type
      let parsedData: any[] = [];
      let columns: string[] = [];

      if (file.name.endsWith('.csv')) {
        const lines = content.split('\n').filter(l => l.trim());
        if (lines.length > 0) {
          columns = lines[0].split(',').map(c => c.trim());
          parsedData = lines.slice(1).map(line => {
            const values = line.split(',');
            const row: any = {};
            columns.forEach((col, idx) => {
              row[col] = values[idx]?.trim();
            });
            return row;
          });
        }
      } else if (file.name.endsWith('.json')) {
        const json = JSON.parse(content);
        parsedData = Array.isArray(json) ? json : [json];
        if (parsedData.length > 0) {
          columns = Object.keys(parsedData[0]);
        }
      }

      // Update source with processed data
      const updatedSource: DataSource = {
        id: sourceId,
        type: "file",
        name: file.name,
        status: "ready",
        metadata: {
          size: file.size,
          rows: parsedData.length,
          columns,
          previewData: parsedData.slice(0, 5),
        },
      };

      onDataSourceAdded(updatedSource);

      // Optional server ingestion if wiring provided and looks like CSV connector context
      if (tenantId && csvConnectorId && ingestionApiBase && file.name.endsWith('.csv')) {
        try {
          const form = new FormData();
          form.append('tenant_id', tenantId);
          form.append('connector_id', csvConnectorId);
          form.append('file', new File([content], file.name, { type: 'text/csv' }));
          // No explicit data_type; let server infer
          const resp = await fetch(`${ingestionApiBase}/api/connectors/upload_csv`, {
            method: 'POST',
            body: form
          });
          if (!resp.ok) {
            console.error('CSV ingestion failed', await resp.text());
          } else {
            const payload = await resp.json();
            console.log('CSV ingestion success', payload);
          }
        } catch (ingestErr) {
          console.error('Error posting CSV to backend', ingestErr);
        }
      }
    } catch (error) {
      const errorSource: DataSource = {
        id: sourceId,
        type: "file",
        name: file.name,
        status: "error",
        metadata: {
          size: file.size,
          error: error instanceof Error ? error.message : "Failed to process file",
        },
      };
      onDataSourceAdded(errorSource);
    }
  };

  const handleConnectorSubmit = async () => {
    if (!selectedConnector) return;

    const source: DataSource = {
      id: `connector-${Date.now()}`,
      type: selectedConnector.type,
      name: `${selectedConnector.name}: ${connectorData[selectedConnector.fields[0].name]}`,
      status: "processing",
    };

    onDataSourceAdded(source);
    setSelectedConnector(null);
    setConnectorData({});
    setShowConnectors(false);

    // Simulate connector processing
    setTimeout(() => {
      const updatedSource: DataSource = {
        ...source,
        status: "ready",
        metadata: {
          rows: 1250,
          columns: ["date", "revenue", "cost", "profit", "customer_count"],
          previewData: [
            { date: "2025-11-01", revenue: 15000, cost: 8000, profit: 7000, customer_count: 45 },
            { date: "2025-11-02", revenue: 18000, cost: 9000, profit: 9000, customer_count: 52 },
            { date: "2025-11-03", revenue: 16500, cost: 8500, profit: 8000, customer_count: 48 },
          ],
        },
      };
      onDataSourceAdded(updatedSource);
    }, 2000);
  };

  return (
    <div className="space-y-4">
      {/* File Drop Zone */}
      <div
        className={`relative rounded-xl border-2 border-dashed p-8 text-center transition-colors ${dragActive ? "border-primary bg-blue-50" : "border-gray-300 bg-gray-50"
          }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (e.dataTransfer.files) {
            handleFileUpload(e.dataTransfer.files);
          }
        }}
      >
        <FileUp size={40} className="mx-auto mb-3 text-gray-400" />
        <div className="mb-2 text-sm font-semibold text-gray-900">Drop files here or click to upload</div>
        <div className="mb-4 text-xs text-gray-600">Supports CSV, JSON, Excel (max 50MB)</div>
        <input
          type="file"
          multiple
          accept=".csv,.json,.xlsx,.xls"
          className="hidden"
          id="file-upload"
          onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
        />
        <label
          htmlFor="file-upload"
          className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-primary bg-white px-4 py-2 text-sm font-semibold text-primary hover:bg-blue-50"
        >
          <FileUp size={16} />
          Choose Files
        </label>
      </div>

      {/* Connect to Data Sources */}
      <button
        onClick={() => setShowConnectors(!showConnectors)}
        className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-gray-300 bg-white px-4 py-3 text-sm font-semibold text-gray-700 hover:border-primary hover:bg-blue-50"
      >
        <Database size={18} />
        Connect to Data Source
      </button>

      {/* Connector Options */}
      {showConnectors && (
        <div className="space-y-3 rounded-xl border border-gray-200 bg-gray-50 p-4">
          <div className="text-sm font-semibold text-gray-900">Choose a connector</div>
          <div className="grid gap-2">
            {AVAILABLE_CONNECTORS.map((connector) => (
              <button
                key={connector.id}
                onClick={() => setSelectedConnector(connector)}
                className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 text-left hover:border-primary hover:bg-blue-50"
              >
                <div className="text-primary">{connector.icon}</div>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-gray-900">{connector.name}</div>
                  <div className="text-xs text-gray-600">{connector.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Connector Configuration Modal */}
      {selectedConnector && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900">{selectedConnector.name}</h3>
              <button onClick={() => setSelectedConnector(null)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              {selectedConnector.fields.map((field) => (
                <div key={field.name}>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">
                    {field.label} {field.required && <span className="text-red-500">*</span>}
                  </label>
                  <input
                    type={field.type}
                    placeholder={field.placeholder}
                    value={connectorData[field.name] || ""}
                    onChange={(e) => setConnectorData({ ...connectorData, [field.name]: e.target.value })}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              ))}
            </div>
            <div className="mt-6 flex gap-2">
              <button
                onClick={() => setSelectedConnector(null)}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConnectorSubmit}
                className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary/90"
              >
                Connect
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Existing Data Sources */}
      {existingSources.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-semibold text-gray-700">Connected Data Sources ({existingSources.length})</div>
          {existingSources.map((source) => (
            <div key={source.id} className="rounded-lg border border-gray-200 bg-white p-3">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  {source.status === "uploading" && <Loader2 size={20} className="animate-spin text-primary" />}
                  {source.status === "processing" && <Loader2 size={20} className="animate-spin text-amber-500" />}
                  {source.status === "ready" && <CheckCircle2 size={20} className="text-green-600" />}
                  {source.status === "error" && <AlertCircle size={20} className="text-red-600" />}
                </div>
                <div className="flex-1">
                  <div className="mb-1 text-sm font-semibold text-gray-900">{source.name}</div>
                  {source.status === "ready" && source.metadata && (
                    <div className="space-y-1 text-xs text-gray-600">
                      <div>
                        {source.metadata.rows} rows • {source.metadata.columns?.length} columns
                      </div>
                      {source.metadata.columns && (
                        <div className="flex flex-wrap gap-1">
                          {source.metadata.columns.slice(0, 5).map((col) => (
                            <span key={col} className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px]">
                              {col}
                            </span>
                          ))}
                          {source.metadata.columns.length > 5 && (
                            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px]">
                              +{source.metadata.columns.length - 5} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  {source.status === "error" && source.metadata?.error && (
                    <div className="text-xs text-red-600">{source.metadata.error}</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
