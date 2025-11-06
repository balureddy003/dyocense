import { X, AlertCircle } from "lucide-react";
import { useState } from "react";

type Stage = {
  id: string;
  title: string;
  description: string;
  todos: string[];
};

type PlanOverview = {
  title: string;
  summary: string;
  stages: Stage[];
  quickWins: string[];
  estimatedDuration: string;
};

type VersionComparisonModalProps = {
  open: boolean;
  onClose: () => void;
  onKeepNew: () => void;
  onReturnToPrevious: () => void;
  previousVersion: PlanOverview & { version: number };
  newVersion: PlanOverview & { version: number };
  changes: {
    added: string[];
    removed: string[];
    modified: string[];
  };
};

export function VersionComparisonModal({
  open,
  onClose,
  onKeepNew,
  onReturnToPrevious,
  previousVersion,
  newVersion,
  changes,
}: VersionComparisonModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[9999] p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-bold text-gray-900">New Version Generated</h2>
            <p className="text-sm text-gray-600 mt-1">
              Review the changes and decide which version to keep
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Change Summary */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-900 mb-3">What Changed:</h3>
            <div className="space-y-2">
              {changes.added.map((item, idx) => (
                <div key={`add-${idx}`} className="flex items-start gap-2 text-sm">
                  <span className="text-green-600 font-semibold">+</span>
                  <span className="text-gray-700">{item}</span>
                </div>
              ))}
              {changes.removed.map((item, idx) => (
                <div key={`remove-${idx}`} className="flex items-start gap-2 text-sm">
                  <span className="text-red-600 font-semibold">-</span>
                  <span className="text-gray-700">{item}</span>
                </div>
              ))}
              {changes.modified.map((item, idx) => (
                <div key={`mod-${idx}`} className="flex items-start gap-2 text-sm">
                  <span className="text-blue-600 font-semibold">~</span>
                  <span className="text-gray-700">{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Side by side comparison */}
          <div className="grid grid-cols-2 gap-4">
            {/* Previous Version */}
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm text-gray-700">
                  Version {previousVersion.version}
                </h4>
                <span className="text-xs text-gray-500">Previous</span>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-gray-600">
                  <span className="font-medium">Stages:</span> {previousVersion.stages.length}
                </div>
                <div className="text-xs text-gray-600">
                  <span className="font-medium">Quick Wins:</span> {previousVersion.quickWins.length}
                </div>
                <div className="text-xs text-gray-600">
                  <span className="font-medium">Duration:</span> {previousVersion.estimatedDuration}
                </div>
              </div>
            </div>

            {/* New Version */}
            <div className="border-2 border-primary rounded-lg p-4 bg-blue-50">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm text-primary">
                  Version {newVersion.version}
                </h4>
                <span className="text-xs text-primary font-medium">New</span>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-gray-700">
                  <span className="font-medium">Stages:</span> {newVersion.stages.length}
                </div>
                <div className="text-xs text-gray-700">
                  <span className="font-medium">Quick Wins:</span> {newVersion.quickWins.length}
                </div>
                <div className="text-xs text-gray-700">
                  <span className="font-medium">Duration:</span> {newVersion.estimatedDuration}
                </div>
              </div>
            </div>
          </div>

          {/* Info note */}
          <div className="mt-6 flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <AlertCircle size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-700">
              This is your newly generated plan. Do you want to keep it or return to the previous version?
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onReturnToPrevious}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Return to previous version
          </button>
          <button
            onClick={onKeepNew}
            className="flex-1 px-4 py-2.5 bg-primary rounded-lg font-semibold text-white hover:bg-primary/90 transition-colors"
          >
            Keep new version
          </button>
        </div>
      </div>
    </div>
  );
}
