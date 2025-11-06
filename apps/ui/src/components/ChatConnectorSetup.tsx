/**
 * Chat-Based Connector Configuration
 * Guides users through connector setup conversationally
 */

import React, { useState } from "react";
import {
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ExternalLink,
  Shield,
  Key,
  Link as LinkIcon,
} from "lucide-react";
import type { ConnectorConfig, ConnectorField } from "../lib/connectorMarketplace";
import { tenantConnectorStore } from "../lib/tenantConnectors";

type SetupStep =
  | "intro"
  | "auth_explain"
  | "field_collection"
  | "testing"
  | "success"
  | "error";

type ChatConnectorSetupProps = {
  connector: ConnectorConfig;
  tenantId: string;
  userId: string;
  onComplete: (connectorId: string) => void;
  onCancel: () => void;
};

export function ChatConnectorSetup({
  connector,
  tenantId,
  userId,
  onComplete,
  onCancel,
}: ChatConnectorSetupProps) {
  const [currentStep, setCurrentStep] = useState<SetupStep>("intro");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState(connector.displayName);

  const chatMessages = generateChatMessages(
    currentStep,
    connector,
    currentFieldIndex,
    error
  );

  const handleNext = async () => {
    if (currentStep === "intro") {
      setCurrentStep("auth_explain");
    } else if (currentStep === "auth_explain") {
      setCurrentStep("field_collection");
    } else if (currentStep === "field_collection") {
      const currentField = connector.fields[currentFieldIndex];

      // Validate current field
      if (currentField.required && !fieldValues[currentField.name]) {
        setError(`${currentField.label} is required`);
        return;
      }

      if (currentField.validation?.pattern) {
        const regex = new RegExp(currentField.validation.pattern);
        if (!regex.test(fieldValues[currentField.name] || "")) {
          setError(
            currentField.validation.message || `Invalid ${currentField.label}`
          );
          return;
        }
      }

      setError(null);

      // Move to next field or testing
      if (currentFieldIndex < connector.fields.length - 1) {
        setCurrentFieldIndex(currentFieldIndex + 1);
      } else {
        setCurrentStep("testing");
        await testConnection();
      }
    }
  };

  const handleBack = () => {
    if (currentStep === "auth_explain") {
      setCurrentStep("intro");
    } else if (currentStep === "field_collection") {
      if (currentFieldIndex > 0) {
        setCurrentFieldIndex(currentFieldIndex - 1);
        setError(null);
      } else {
        setCurrentStep("auth_explain");
      }
    }
  };

  const testConnection = async () => {
    try {
      // Simulate connection test (replace with actual API call when backend connector endpoint is ready)
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Save connector to tenant
      const savedConnector = tenantConnectorStore.add({
        tenantId,
        connectorId: connector.id,
        connectorName: connector.name,
        displayName,
        category: connector.category,
        icon: connector.icon,
        config: fieldValues,
        dataTypes: connector.dataTypes,
        status: "active",
        createdBy: userId,
      });

      setCurrentStep("success");
      setTimeout(() => onComplete(savedConnector.id), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
      setCurrentStep("error");
    }
  };

  const handleRetry = () => {
    setError(null);
    setCurrentStep("field_collection");
    setCurrentFieldIndex(0);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <LinkIcon className="text-blue-600" size={20} />
            </div>
            <div>
              <h2 className="font-semibold text-lg">Connect {connector.displayName}</h2>
              <p className="text-sm text-gray-500">
                {currentStep === "intro" && "Let's get started"}
                {currentStep === "auth_explain" && "Understanding authentication"}
                {currentStep === "field_collection" &&
                  `Step ${currentFieldIndex + 1} of ${connector.fields.length}`}
                {currentStep === "testing" && "Testing connection"}
                {currentStep === "success" && "Connected successfully"}
                {currentStep === "error" && "Connection failed"}
              </p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {chatMessages.map((msg, idx) => (
            <ChatMessage key={idx} {...msg} />
          ))}

          {/* Field Input */}
          {currentStep === "field_collection" && (
            <FieldInput
              field={connector.fields[currentFieldIndex]}
              value={fieldValues[connector.fields[currentFieldIndex].name] || ""}
              onChange={(value) =>
                setFieldValues({
                  ...fieldValues,
                  [connector.fields[currentFieldIndex].name]: value,
                })
              }
              error={error}
            />
          )}

          {/* Display Name Input */}
          {currentStep === "intro" && (
            <div className="bg-gray-50 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Give this connection a name (optional)
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={connector.displayName}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                E.g., "Main Xero Account" or "Production Shopify"
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="border-t p-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {currentStep === "field_collection" && (
              <span className="text-sm text-gray-500">
                {currentFieldIndex + 1} of {connector.fields.length} completed
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {currentStep !== "intro" &&
              currentStep !== "testing" &&
              currentStep !== "success" && (
                <button
                  onClick={handleBack}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Back
                </button>
              )}
            {currentStep === "error" && (
              <button
                onClick={handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
            )}
            {currentStep !== "testing" && currentStep !== "success" && currentStep !== "error" && (
              <button
                onClick={handleNext}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                {currentStep === "field_collection" &&
                currentFieldIndex === connector.fields.length - 1
                  ? "Connect"
                  : "Continue"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

type ChatMessageProps = {
  type: "agent" | "user" | "system";
  content: React.ReactNode;
  icon?: "info" | "success" | "error" | "loading";
};

function ChatMessage({ type, content, icon }: ChatMessageProps) {
  return (
    <div
      className={`flex gap-3 ${
        type === "user" ? "justify-end" : "justify-start"
      }`}
    >
      {type !== "user" && (
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
          {icon === "loading" && <Loader2 className="animate-spin text-blue-600" size={16} />}
          {icon === "success" && <CheckCircle2 className="text-green-600" size={16} />}
          {icon === "error" && <AlertCircle className="text-red-600" size={16} />}
          {!icon && <span className="text-blue-600 text-sm font-medium">AI</span>}
        </div>
      )}
      <div
        className={`rounded-lg px-4 py-3 max-w-[80%] ${
          type === "user"
            ? "bg-blue-600 text-white"
            : type === "system"
            ? "bg-gray-100 text-gray-700 border border-gray-200"
            : "bg-gray-50 text-gray-800"
        }`}
      >
        <div className="text-sm">{content}</div>
      </div>
    </div>
  );
}

type FieldInputProps = {
  field: ConnectorField;
  value: string;
  onChange: (value: string) => void;
  error: string | null;
};

function FieldInput({ field, value, onChange, error }: FieldInputProps) {
  const renderInput = () => {
    if (field.type === "select" && field.options) {
      return (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required={field.required}
        >
          <option value="">Select {field.label}</option>
          {field.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      );
    }

    const inputType = field.type === "password" ? "password" : "text";

    return (
      <input
        type={inputType}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.placeholder}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        required={field.required}
      />
    );
  };

  return (
    <div className="bg-white border-2 border-blue-500 rounded-lg p-4 space-y-3">
      <div className="flex items-start gap-2">
        {field.type === "password" ? (
          <Key className="text-blue-600 mt-1" size={18} />
        ) : (
          <Shield className="text-blue-600 mt-1" size={18} />
        )}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-900 mb-1">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {field.description && (
            <p className="text-xs text-gray-500 mb-2">{field.description}</p>
          )}
          {renderInput()}
          {error && (
            <div className="flex items-center gap-1 mt-2 text-red-600 text-xs">
              <AlertCircle size={12} />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function generateChatMessages(
  step: SetupStep,
  connector: ConnectorConfig,
  fieldIndex: number,
  error: string | null
): ChatMessageProps[] {
  const messages: ChatMessageProps[] = [];

  if (step === "intro") {
    messages.push({
      type: "agent",
      content: (
        <>
          <p className="mb-2">
            Great! Let's connect your <strong>{connector.displayName}</strong>.
          </p>
          <p className="text-xs text-gray-600">
            {connector.description}
          </p>
        </>
      ),
    });
    messages.push({
      type: "agent",
      content: (
        <>
          <p className="mb-2">This connection will give me access to:</p>
          <ul className="text-xs space-y-1 ml-4 list-disc">
            {connector.dataTypes.map((dt) => (
              <li key={dt}>{dt}</li>
            ))}
          </ul>
        </>
      ),
    });
  }

  if (step === "auth_explain") {
    messages.push({
      type: "agent",
      content: (
        <>
          <p className="mb-2">
            {connector.authType === "oauth2" ? (
              <>
                <strong>{connector.displayName}</strong> uses secure OAuth 2.0
                authentication.
              </>
            ) : (
              <>
                To connect, I'll need your <strong>API credentials</strong> from{" "}
                {connector.displayName}.
              </>
            )}
          </p>
          {connector.authType === "oauth2" ? (
            <div className="bg-blue-50 rounded p-2 text-xs mt-2">
              <p className="font-medium mb-1">🔒 What is OAuth?</p>
              <p>
                Instead of sharing your password with me, you'll log in directly
                on {connector.provider.name}'s website. They'll give me limited
                access to only the data you approve.
              </p>
            </div>
          ) : (
            <div className="bg-yellow-50 rounded p-2 text-xs mt-2">
              <p className="font-medium mb-1">🔐 Your API keys are safe</p>
              <p>
                Your credentials are encrypted and stored securely. We never
                share them with third parties.
              </p>
            </div>
          )}
          {connector.setupGuide?.docUrl && (
            <a
              href={connector.setupGuide.docUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2"
            >
              <ExternalLink size={12} />
              View setup guide
            </a>
          )}
        </>
      ),
    });
  }

  if (step === "field_collection") {
    const currentField = connector.fields[fieldIndex];
    messages.push({
      type: "agent",
      content: (
        <>
          <p className="mb-2">
            {fieldIndex === 0 ? "Let's start with" : "Next, I need"} your{" "}
            <strong>{currentField.label.toLowerCase()}</strong>.
          </p>
          {currentField.description && (
            <p className="text-xs text-gray-600">{currentField.description}</p>
          )}
        </>
      ),
    });
  }

  if (step === "testing") {
    messages.push({
      type: "agent",
      icon: "loading",
      content: (
        <>
          <p>Testing connection to {connector.displayName}...</p>
          <p className="text-xs text-gray-600 mt-1">
            This may take a few seconds
          </p>
        </>
      ),
    });
  }

  if (step === "success") {
    messages.push({
      type: "agent",
      icon: "success",
      content: (
        <>
          <p className="font-medium">
            Successfully connected to {connector.displayName}!
          </p>
          <p className="text-xs text-gray-600 mt-1">
            I can now access your data and help you with insights.
          </p>
        </>
      ),
    });
  }

  if (step === "error") {
    messages.push({
      type: "agent",
      icon: "error",
      content: (
        <>
          <p className="font-medium">Connection failed</p>
          <p className="text-xs text-red-600 mt-1">{error}</p>
          <p className="text-xs text-gray-600 mt-2">
            Please check your credentials and try again.
          </p>
        </>
      ),
    });
  }

  return messages;
}
