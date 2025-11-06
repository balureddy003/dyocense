import { useState, useEffect } from "react";
import { FileText, X } from "lucide-react";

type PlanNameModalProps = {
  open: boolean;
  onClose: () => void;
  onSave: (name: string) => void;
  onSkip?: () => void;
  currentName?: string;
  aiGeneratedTitle?: string;
};

export function PlanNameModal({ open, onClose, onSave, onSkip, currentName, aiGeneratedTitle }: PlanNameModalProps) {
  const [name, setName] = useState(currentName || "");

  useEffect(() => {
    if (open) {
      setName(currentName || "");
    }
  }, [open, currentName]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onSave(name.trim());
      onClose();
    }
  };

  const handleSkip = () => {
    if (onSkip) {
      onSkip();
    }
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[9999] p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
              <FileText size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Name Your Plan</h2>
              <p className="text-xs text-gray-500">Give your plan a memorable name</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {aiGeneratedTitle && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs text-gray-600 mb-1">AI Generated Title:</p>
              <p className="text-sm font-semibold text-gray-900">{aiGeneratedTitle}</p>
            </div>
          )}

          <div className="mb-6">
            <label htmlFor="plan-name" className="block text-sm font-semibold text-gray-700 mb-2">
              Plan Name
            </label>
            <input
              id="plan-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Q4 2025 Growth Strategy"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none"
              autoFocus
            />
            <p className="mt-2 text-xs text-gray-500">
              Choose a name that helps you identify this plan later
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleSkip}
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Skip for Now
            </button>
            <button
              type="submit"
              disabled={!name.trim()}
              className="flex-1 px-4 py-2.5 bg-primary rounded-lg font-semibold text-white hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Save Name
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
