import { UK_CONNECTOR_MARKETPLACE, type ConnectorConfig } from "../lib/connectorMarketplace";

interface InlineConnectorSelectorProps {
    connectors: string[];
    reason?: string;
    onSelect: (connector: ConnectorConfig) => void;
}

export function InlineConnectorSelector({ connectors, reason, onSelect }: InlineConnectorSelectorProps) {
    // Filter available connectors to show only suggested ones
    const suggestedConnectors = UK_CONNECTOR_MARKETPLACE.filter((c: ConnectorConfig) =>
        connectors.includes(c.id) ||
        connectors.includes(c.name.toLowerCase()) ||
        connectors.includes(c.category.toLowerCase())
    );

    return (
        <div className="my-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
            {reason && (
                <p className="mb-3 text-sm text-gray-700">{reason}</p>
            )}

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {suggestedConnectors.map((connector: ConnectorConfig) => (
                    <button
                        key={connector.id}
                        onClick={() => onSelect(connector)}
                        className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 text-left transition-all hover:border-blue-400 hover:bg-blue-50 hover:shadow-sm"
                    >
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                            {connector.icon ? (
                                <span className="text-xl">{connector.icon}</span>
                            ) : (
                                <span className="text-xs font-bold">{connector.name.slice(0, 2).toUpperCase()}</span>
                            )}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="font-medium text-gray-900 truncate">{connector.name}</div>
                            <div className="text-xs text-gray-500 truncate">{connector.category}</div>
                        </div>
                    </button>
                ))}
            </div>

            {suggestedConnectors.length === 0 && (
                <div className="text-center py-4">
                    <p className="text-sm text-gray-600">
                        No matching connectors found. Try browsing the full marketplace.
                    </p>
                </div>
            )}
        </div>
    );
}
