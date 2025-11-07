/**
 * Setup Progress Checklist - Visual progress indicator for SMB onboarding
 * Shows users what's done and what's next in simple, clear steps
 */

import { CheckCircle2, Circle, ArrowRight } from "lucide-react";
import { useState, useEffect } from "react";

type ChecklistStep = {
  id: string;
  label: string;
  description: string;
  completed: boolean;
  active?: boolean;
};

type SetupProgressChecklistProps = {
  hasIndustry: boolean;
  hasPreferences: boolean;
  hasGoal: boolean;
  hasPlan: boolean;
  hasConnectors: boolean;
  isTracking: boolean;
  onClickStep?: (stepId: string) => void;
};

export function SetupProgressChecklist({
  hasIndustry,
  hasPreferences,
  hasGoal,
  hasPlan,
  hasConnectors,
  isTracking,
  onClickStep,
}: SetupProgressChecklistProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const steps: ChecklistStep[] = [
    {
      id: "industry",
      label: "Tell us about your business",
      description: "What type of business do you run?",
      completed: hasIndustry,
    },
    {
      id: "preferences",
      label: "Share your preferences",
      description: "Team size, goals, and challenges",
      completed: hasPreferences,
    },
    {
      id: "goal",
      label: "Set your first goal",
      description: "What do you want to achieve?",
      completed: hasGoal,
      active: hasPreferences && !hasGoal,
    },
    {
      id: "plan",
      label: "Get your action plan",
      description: "AI-generated steps to reach your goal",
      completed: hasPlan,
      active: hasGoal && !hasPlan,
    },
    {
      id: "connectors",
      label: "Connect your tools (optional)",
      description: "QuickBooks, Shopify, Square, etc.",
      completed: hasConnectors,
    },
    {
      id: "tracking",
      label: "Track your progress",
      description: "Monitor KPIs and adjust as you go",
      completed: isTracking,
      active: hasPlan && !isTracking,
    },
  ];

  const completedCount = steps.filter((s) => s.completed).length;
  const totalCount = steps.length;
  const progressPercent = Math.round((completedCount / totalCount) * 100);
  const allComplete = completedCount === totalCount;

  // Auto-collapse when fully complete
  useEffect(() => {
    if (allComplete) {
      const timer = setTimeout(() => setIsExpanded(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [allComplete]);

  return (
    <div
      className={`bg-white rounded-xl border-2 shadow-md transition-all ${
        allComplete ? "border-green-500" : "border-blue-300"
      }`}
    >
      {/* Header - Always Visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors rounded-t-xl"
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
              allComplete
                ? "bg-green-500 text-white"
                : "bg-blue-500 text-white"
            }`}
          >
            {completedCount}/{totalCount}
          </div>
          <div className="text-left">
            <h3 className="font-bold text-gray-900">
              {allComplete ? "🎉 All Set!" : "Getting Started"}
            </h3>
            <p className="text-xs text-gray-600">
              {allComplete
                ? "You're ready to grow your business"
                : `${completedCount} of ${totalCount} steps complete`}
            </p>
          </div>
        </div>

        {/* Progress Circle */}
        <div className="flex items-center gap-3">
          <div className="relative w-12 h-12">
            <svg className="transform -rotate-90 w-12 h-12">
              <circle
                cx="24"
                cy="24"
                r="20"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-gray-200"
              />
              <circle
                cx="24"
                cy="24"
                r="20"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 20}`}
                strokeDashoffset={`${
                  2 * Math.PI * 20 * (1 - progressPercent / 100)
                }`}
                className={`transition-all duration-500 ${
                  allComplete ? "text-green-500" : "text-blue-500"
                }`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-bold text-gray-700">
                {progressPercent}%
              </span>
            </div>
          </div>
          <ArrowRight
            size={16}
            className={`text-gray-400 transition-transform ${
              isExpanded ? "rotate-90" : ""
            }`}
          />
        </div>
      </button>

      {/* Expandable Checklist */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-2 border-t border-gray-100">
          {steps.map((step, index) => (
            <button
              key={step.id}
              onClick={() => onClickStep?.(step.id)}
              disabled={step.completed}
              className={`w-full text-left p-3 rounded-lg transition-all flex items-start gap-3 ${
                step.active
                  ? "bg-blue-50 border-2 border-blue-300 shadow-sm"
                  : step.completed
                  ? "bg-gray-50 opacity-60"
                  : "hover:bg-gray-50 border border-gray-200"
              }`}
            >
              {/* Icon */}
              <div className="flex-shrink-0 pt-0.5">
                {step.completed ? (
                  <CheckCircle2 className="text-green-500" size={20} />
                ) : step.active ? (
                  <div className="w-5 h-5 rounded-full border-2 border-blue-500 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  </div>
                ) : (
                  <Circle className="text-gray-300" size={20} />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={`font-semibold text-sm ${
                      step.completed
                        ? "text-gray-500 line-through"
                        : step.active
                        ? "text-blue-700"
                        : "text-gray-900"
                    }`}
                  >
                    {step.label}
                  </span>
                  {step.active && (
                    <span className="text-xs font-bold text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">
                      NEXT
                    </span>
                  )}
                </div>
                <p
                  className={`text-xs mt-0.5 ${
                    step.completed
                      ? "text-gray-400"
                      : step.active
                      ? "text-blue-600"
                      : "text-gray-500"
                  }`}
                >
                  {step.description}
                </p>
              </div>

              {/* Arrow for active step */}
              {step.active && !step.completed && (
                <ArrowRight className="text-blue-500 flex-shrink-0" size={16} />
              )}
            </button>
          ))}

          {/* Encouragement Message */}
          {!allComplete && completedCount > 0 && (
            <div className="mt-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <p className="text-xs text-gray-700">
                <span className="font-semibold">Great progress! 🚀</span>{" "}
                {completedCount < 3
                  ? "You're off to a strong start."
                  : "You're almost there!"}
              </p>
            </div>
          )}

          {/* Completion Celebration */}
          {allComplete && (
            <div className="mt-3 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border-2 border-green-300">
              <p className="text-sm font-semibold text-green-800 mb-1">
                🎉 Congratulations!
              </p>
              <p className="text-xs text-green-700">
                You're all set up and ready to grow your business with
                data-driven plans.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
