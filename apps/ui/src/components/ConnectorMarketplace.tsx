import { useState } from "react";
import { 
  Store, FileText, ShoppingCart, Package, CreditCard, TrendingUp, 
  Users, Boxes, Check, ArrowRight, HelpCircle, ExternalLink, Play 
} from "lucide-react";
import {
  ConnectorConfig,
  UK_CONNECTOR_MARKETPLACE,
  getPopularConnectors,
  getConnectorsByCategory,
  searchConnectors,
  CONNECTOR_CATEGORIES,
} from "../lib/connectorMarketplace";

// Map icon names to components
const ICON_MAP: Record<string, React.ComponentType<any>> = {
  FileText,
  CreditCard,
  TrendingUp,
  ShoppingCart,
  Store,
  Package,
  Users,
  Boxes,
};

export type ConnectorMarketplaceProps = {
  onConnectorSelected: (connector: ConnectorConfig) => void;
  tenantId: string;
};

export function ConnectorMarketplace({ onConnectorSelected, tenantId }: ConnectorMarketplaceProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"popular" | "all" | "category">("popular");

  const filteredConnectors =
    viewMode === "popular"
      ? getPopularConnectors()
      : viewMode === "category" && selectedCategory
      ? getConnectorsByCategory(selectedCategory as any)
      : searchQuery
      ? searchConnectors(searchQuery)
      : UK_CONNECTOR_MARKETPLACE;

  const handleConnectorClick = (connector: ConnectorConfig) => {
    onConnectorSelected(connector);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-gray-900">Connect Your Business Data</h2>
        <p className="mt-1 text-sm text-gray-600">
          Choose from popular UK business tools or connect any custom system
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setViewMode("all");
          }}
          placeholder="Search connectors (e.g., Xero, Shopify, Google Drive)..."
          className="w-full rounded-lg border border-gray-300 px-4 py-3 pr-10 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
        {searchQuery && (
          <button
            onClick={() => {
              setSearchQuery("");
              setViewMode("popular");
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        )}
      </div>

      {/* Categories */}
      {!searchQuery && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => {
              setViewMode("popular");
              setSelectedCategory(null);
            }}
            className={`flex-shrink-0 rounded-lg px-4 py-2 text-sm font-semibold ${
              viewMode === "popular"
                ? "bg-primary text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Popular
          </button>
          {CONNECTOR_CATEGORIES.map((cat) => {
            const Icon = ICON_MAP[cat.icon] || Boxes;
            return (
              <button
                key={cat.id}
                onClick={() => {
                  setViewMode("category");
                  setSelectedCategory(cat.id);
                }}
                className={`flex flex-shrink-0 items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold ${
                  viewMode === "category" && selectedCategory === cat.id
                    ? "bg-primary text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                <Icon size={16} />
                {cat.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Connectors Grid */}
      <div className="grid gap-4 sm:grid-cols-2">
        {filteredConnectors.map((connector) => {
          const Icon = ICON_MAP[connector.icon] || Boxes;
          return (
            <button
              key={connector.id}
              onClick={() => handleConnectorClick(connector)}
              className="group relative rounded-xl border border-gray-200 bg-white p-4 text-left transition-all hover:border-primary hover:shadow-md"
            >
              {/* Badges */}
              <div className="absolute right-3 top-3 flex gap-1">
                {connector.verified && (
                  <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
                    <Check size={10} className="inline" /> Verified
                  </span>
                )}
                {connector.mcpCompatible && (
                  <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-semibold text-purple-700">
                    MCP
                  </span>
                )}
                {connector.customizable && (
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-semibold text-green-700">
                    Custom
                  </span>
                )}
              </div>

              {/* Icon and Title */}
              <div className="mb-3 flex items-start gap-3">
                <div className="flex-shrink-0 rounded-lg bg-gray-100 p-2 text-primary group-hover:bg-blue-100">
                  <Icon size={24} />
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="font-semibold text-gray-900 group-hover:text-primary">
                    {connector.displayName}
                  </h3>
                  <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                    <span className="capitalize">{connector.category}</span>
                    <span>•</span>
                    <span>{connector.region}</span>
                    {connector.tier !== "free" && (
                      <>
                        <span>•</span>
                        <span className="capitalize">{connector.tier}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="mb-3 text-sm text-gray-600">{connector.description}</p>

              {/* Data Types */}
              <div className="mb-3 flex flex-wrap gap-1">
                {connector.dataTypes.slice(0, 4).map((type) => (
                  <span
                    key={type}
                    className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                  >
                    {type}
                  </span>
                ))}
                {connector.dataTypes.length > 4 && (
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                    +{connector.dataTypes.length - 4} more
                  </span>
                )}
              </div>

              {/* Connect Button */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                <span className="text-sm font-semibold text-primary group-hover:underline">
                  Connect →
                </span>
                {connector.authType === "oauth2" ? (
                  <span className="text-xs text-gray-500">OAuth 2.0</span>
                ) : (
                  <span className="text-xs text-gray-500">API Key</span>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredConnectors.length === 0 && (
        <div className="py-12 text-center">
          <div className="mx-auto mb-3 h-16 w-16 rounded-full bg-gray-100 p-4">
            <HelpCircle className="h-full w-full text-gray-400" />
          </div>
          <h3 className="mb-1 font-semibold text-gray-900">No connectors found</h3>
          <p className="mb-4 text-sm text-gray-600">
            Try a different search term or browse by category
          </p>
          <button
            onClick={() => {
              setSearchQuery("");
              setViewMode("popular");
            }}
            className="text-sm font-semibold text-primary hover:underline"
          >
            View popular connectors
          </button>
        </div>
      )}

      {/* Help Section */}
      <div className="rounded-lg border border-blue-100 bg-blue-50 p-4">
        <div className="flex items-start gap-3">
          <HelpCircle size={20} className="flex-shrink-0 text-blue-600" />
          <div className="flex-1">
            <h4 className="mb-1 font-semibold text-gray-900">Need help choosing?</h4>
            <p className="mb-2 text-sm text-gray-700">
              Not sure which connector to use? Chat with our AI assistant to get personalized recommendations
              based on your business needs.
            </p>
            <button className="text-sm font-semibold text-primary hover:underline">
              Ask AI for help →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export type ConnectorSetupWizardProps = {
  connector: ConnectorConfig;
  tenantId: string;
  onComplete: (config: Record<string, string>) => void;
  onCancel: () => void;
};

export function ConnectorSetupWizard({
  connector,
  tenantId,
  onComplete,
  onCancel,
}: ConnectorSetupWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isConnecting, setIsConnecting] = useState(false);

  const Icon = ICON_MAP[connector.icon] || Boxes;
  const totalSteps = connector.setupGuide.steps.length;

  const handleFieldChange = (fieldName: string, value: string) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    // Clear error when user starts typing
    if (errors[fieldName]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  const validateCurrentFields = (): boolean => {
    const newErrors: Record<string, string> = {};
    const currentFields = connector.fields;

    currentFields.forEach((field) => {
      if (field.required && !formData[field.name]?.trim()) {
        newErrors[field.name] = `${field.label} is required`;
      } else if (field.validation) {
        const value = formData[field.name] || "";
        if (field.validation.pattern && !new RegExp(field.validation.pattern).test(value)) {
          newErrors[field.name] = field.validation.message || "Invalid format";
        }
        if (field.validation.minLength && value.length < field.validation.minLength) {
          newErrors[field.name] = `Minimum ${field.validation.minLength} characters required`;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateCurrentFields()) {
      if (currentStep < totalSteps - 1) {
        setCurrentStep((prev) => prev + 1);
      } else {
        handleConnect();
      }
    }
  };

  const handleConnect = async () => {
    setIsConnecting(true);
    // Simulate connection
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsConnecting(false);
    onComplete(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-xl bg-white shadow-2xl">
        {/* Header */}
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-gray-100 p-3">
              <Icon size={32} className="text-primary" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-900">Connect {connector.displayName}</h2>
              <p className="text-sm text-gray-600">{connector.longDescription}</p>
            </div>
          </div>

          {/* Progress */}
          <div className="mt-6">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-semibold text-gray-700">
                Step {currentStep + 1} of {totalSteps}
              </span>
              <span className="text-gray-500">{Math.round(((currentStep + 1) / totalSteps) * 100)}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-200">
              <div
                className="h-full rounded-full bg-primary transition-all duration-300"
                style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Current Step Guide */}
          <div className="mb-6 rounded-lg border border-blue-100 bg-blue-50 p-4">
            <h3 className="mb-2 font-semibold text-gray-900">
              {connector.setupGuide.steps[currentStep]}
            </h3>
            {connector.setupGuide.docUrl && (
              <a
                href={connector.setupGuide.docUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline"
              >
                View setup guide
                <ExternalLink size={14} />
              </a>
            )}
          </div>

          {/* Form Fields */}
          <div className="space-y-4">
            {connector.fields.map((field) => (
              <div key={field.name}>
                <label className="mb-1 block text-sm font-semibold text-gray-700">
                  {field.label}
                  {field.required && <span className="text-red-500">*</span>}
                </label>
                {field.description && (
                  <p className="mb-2 text-xs text-gray-600">{field.description}</p>
                )}
                {field.type === "select" ? (
                  <select
                    value={formData[field.name] || ""}
                    onChange={(e) => handleFieldChange(field.name, e.target.value)}
                    className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
                      errors[field.name]
                        ? "border-red-300 focus:border-red-500 focus:ring-red-500/20"
                        : "border-gray-300 focus:border-primary focus:ring-primary/20"
                    }`}
                  >
                    <option value="">Select {field.label}</option>
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={field.type}
                    value={formData[field.name] || ""}
                    onChange={(e) => handleFieldChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                    className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
                      errors[field.name]
                        ? "border-red-300 focus:border-red-500 focus:ring-red-500/20"
                        : "border-gray-300 focus:border-primary focus:ring-primary/20"
                    }`}
                  />
                )}
                {errors[field.name] && (
                  <p className="mt-1 text-xs text-red-600">{errors[field.name]}</p>
                )}
              </div>
            ))}
          </div>

          {/* OAuth Help */}
          {connector.authType === "oauth2" && currentStep === 0 && (
            <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
              <p className="text-sm text-gray-700">
                <strong>What is OAuth?</strong> You'll be securely redirected to {connector.provider.name} to
                authorize access. We never see your password.
              </p>
            </div>
          )}

          {/* Sample Queries */}
          {connector.sampleQueries.length > 0 && (
            <div className="mt-6">
              <h4 className="mb-2 text-sm font-semibold text-gray-700">
                After connecting, you can ask things like:
              </h4>
              <div className="space-y-2">
                {connector.sampleQueries.slice(0, 3).map((query, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                    <Play size={14} className="text-primary" />
                    "{query}"
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-200 p-6">
          <button
            onClick={onCancel}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <div className="flex gap-2">
            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep((prev) => prev - 1)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              >
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              disabled={isConnecting}
              className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-semibold text-white hover:bg-primary/90 disabled:opacity-50"
            >
              {isConnecting ? (
                "Connecting..."
              ) : currentStep === totalSteps - 1 ? (
                <>
                  <Check size={16} />
                  Connect
                </>
              ) : (
                <>
                  Next
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
