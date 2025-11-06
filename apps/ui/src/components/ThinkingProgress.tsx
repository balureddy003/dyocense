import { useState } from "react";
import { ChevronDown, ChevronUp, Check, Loader2 } from "lucide-react";

export type ThinkingStep = {
  id: string;
  label: string;
  status: "pending" | "in-progress" | "completed";
  subItems?: string[];
};

type ThinkingProgressProps = {
  steps: ThinkingStep[];
  isCollapsed?: boolean;
  onToggle?: () => void;
};

export function ThinkingProgress({ steps, isCollapsed = false, onToggle }: ThinkingProgressProps) {
  const [collapsed, setCollapsed] = useState(isCollapsed);
  
  const handleToggle = () => {
    setCollapsed(!collapsed);
    onToggle?.();
  };

  const allCompleted = steps.every(s => s.status === "completed");
  const hasInProgress = steps.some(s => s.status === "in-progress");

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          {hasInProgress && !allCompleted && (
            <Loader2 size={16} className="text-primary animate-spin" />
          )}
          {allCompleted && (
            <Check size={16} className="text-green-600" />
          )}
          <span className="font-semibold text-sm text-gray-900">
            {allCompleted ? "Analysis Complete" : "Analyzing Your Goal"}
          </span>
        </div>
        {collapsed ? (
          <ChevronDown size={18} className="text-gray-500" />
        ) : (
          <ChevronUp size={18} className="text-gray-500" />
        )}
      </button>

      {/* Steps */}
      {!collapsed && (
        <div className="px-4 pb-4 space-y-3">
          {steps.map((step) => (
            <div key={step.id} className="space-y-1">
              <div className="flex items-start gap-2">
                {step.status === "completed" && (
                  <Check size={16} className="text-green-600 mt-0.5 flex-shrink-0" />
                )}
                {step.status === "in-progress" && (
                  <Loader2 size={16} className="text-primary animate-spin mt-0.5 flex-shrink-0" />
                )}
                {step.status === "pending" && (
                  <div className="w-4 h-4 rounded-full border-2 border-gray-300 mt-0.5 flex-shrink-0" />
                )}
                <span className={`text-sm ${step.status === "completed" ? "text-gray-900" : "text-gray-600"}`}>
                  {step.label}
                </span>
              </div>
              
              {/* Sub-items */}
              {step.subItems && step.subItems.length > 0 && step.status !== "pending" && (
                <div className="ml-6 space-y-1">
                  {step.subItems.map((item, idx) => (
                    <div key={idx} className="text-xs text-gray-600">
                      {item}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
