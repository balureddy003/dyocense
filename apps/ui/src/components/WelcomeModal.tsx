import { X, Sparkles, BookOpen, Users, Zap } from "lucide-react";
import { useState } from "react";

interface WelcomeModalProps {
  open: boolean;
  onClose: () => void;
  companyName?: string;
}

export const WelcomeModal = ({ open, onClose, companyName }: WelcomeModalProps) => {
  const [currentStep, setCurrentStep] = useState(0);

  if (!open) return null;

  const steps = [
    {
      icon: Sparkles,
      title: "Welcome to Dyocense!",
      description: companyName
        ? `We're excited to help ${companyName} make smarter decisions with AI.`
        : "We're excited to help you make smarter decisions with AI.",
      content: (
        <div className="space-y-4 text-left">
          <p className="text-sm text-gray-700">
            Dyocense is your <strong>Decision Intelligence Platform</strong> - combining AI insights, forecasting, and optimization to help you:
          </p>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-primary font-bold mt-0.5">✓</span>
              <span>Optimize inventory and reduce waste</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary font-bold mt-0.5">✓</span>
              <span>Plan workforce and staffing efficiently</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary font-bold mt-0.5">✓</span>
              <span>Make data-driven supply chain decisions</span>
            </li>
          </ul>
        </div>
      ),
    },
    {
      icon: BookOpen,
      title: "Create AI Playbooks",
      description: "Pre-built templates for common business scenarios",
      content: (
        <div className="space-y-3 text-left">
          <p className="text-sm text-gray-700">
            Playbooks are your automated decision workflows. Each playbook combines:
          </p>
          <div className="grid gap-3">
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
              <h4 className="text-xs font-semibold text-blue-900 mb-1">📊 Forecasting</h4>
              <p className="text-xs text-blue-700">Predict demand, sales, and trends</p>
            </div>
            <div className="p-3 rounded-lg bg-purple-50 border border-purple-100">
              <h4 className="text-xs font-semibold text-purple-900 mb-1">🎯 Optimization</h4>
              <p className="text-xs text-purple-700">Find the best plan within your constraints</p>
            </div>
            <div className="p-3 rounded-lg bg-green-50 border border-green-100">
              <h4 className="text-xs font-semibold text-green-900 mb-1">💡 Explanations</h4>
              <p className="text-xs text-green-700">Understand why each decision was made</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      icon: Zap,
      title: "Quick Start Guide",
      description: "Get your first playbook running in minutes",
      content: (
        <div className="space-y-3 text-left">
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                1
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-900">Create a Project</h4>
                <p className="text-xs text-gray-600 mt-0.5">Organize your playbooks by business area</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                2
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-900">Choose a Template</h4>
                <p className="text-xs text-gray-600 mt-0.5">Select from inventory, staffing, or supply chain playbooks</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                3
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-900">Connect Your Data</h4>
                <p className="text-xs text-gray-600 mt-0.5">Upload CSV files or connect Google Sheets</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                4
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-900">Review AI Recommendations</h4>
                <p className="text-xs text-gray-600 mt-0.5">Get optimized plans with full explanations</p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
  ];

  const currentStepData = steps[currentStep];
  const StepIcon = currentStepData.icon;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <StepIcon size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{currentStepData.title}</h2>
              <p className="text-xs text-gray-600">{currentStepData.description}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {currentStepData.content}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {steps.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={`w-2 h-2 rounded-full transition ${
                  index === currentStep ? "bg-primary w-6" : "bg-gray-300 hover:bg-gray-400"
                }`}
                aria-label={`Go to step ${index + 1}`}
              />
            ))}
          </div>
          <div className="flex items-center gap-3">
            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep(currentStep - 1)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
              >
                Back
              </button>
            )}
            {currentStep < steps.length - 1 ? (
              <button
                onClick={() => setCurrentStep(currentStep + 1)}
                className="px-5 py-2 rounded-lg bg-primary text-white font-semibold text-sm shadow-sm hover:bg-blue-700 transition"
              >
                Next
              </button>
            ) : (
              <button
                onClick={onClose}
                className="px-5 py-2 rounded-lg bg-primary text-white font-semibold text-sm shadow-sm hover:bg-blue-700 transition"
              >
                Get Started
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
