import { RunSummary } from "../hooks/usePlaybook";
import { X, Plus, Clock4, MapPin } from "lucide-react";

interface PlanDrawerProps {
  open: boolean;
  onClose: () => void;
  runs: RunSummary[];
  selectedRunId?: string | null;
  onSelect: (runId: string) => void;
  onCreateNew?: () => void;
}

const formatMeta = (run: RunSummary) => {
  const updated = run.updatedAt ? new Date(run.updatedAt).toLocaleString() : "";
  return `${run.status}${updated ? ` • ${updated}` : ""}`;
};

export const PlanDrawer = ({ open, onClose, runs, selectedRunId, onSelect, onCreateNew }: PlanDrawerProps) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-gray-900/40" onClick={onClose} />
      <div className="absolute left-0 top-0 h-full w-[360px] bg-white shadow-2xl flex flex-col">
        <header className="flex items-center justify-between px-5 py-4 border-b">
          <div>
            <h2 className="text-base font-semibold text-gray-900">My playbooks</h2>
            <p className="text-xs text-gray-500">Recent Dyocense runs</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="flex items-center gap-1 text-sm text-primary font-medium"
              onClick={() => {
                onClose();
                onCreateNew?.();
              }}
            >
              <Plus size={16} /> New playbook
            </button>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {runs.map((run) => {
            const isActive = run.id === selectedRunId;
            return (
              <article
                key={run.id}
                className={`border rounded-xl p-3 flex gap-3 cursor-pointer transition ${
                  isActive ? "border-primary bg-blue-50/50" : "border-gray-100 hover:border-primary/60"
                }`}
                onClick={() => {
                  onSelect(run.id);
                  onClose();
                }}
              >
                <div className="h-16 w-16 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 text-sm font-semibold">
                  Run
                </div>
                <div className="flex-1 space-y-1">
                  <h3 className="text-sm font-semibold text-gray-900 line-clamp-2">{run.goal}</h3>
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <Clock4 size={14} /> {formatMeta(run)}
                  </p>
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <MapPin size={14} /> {run.id}
                  </p>
                </div>
              </article>
            );
          })}
          {!runs.length && <p className="text-sm text-gray-500">No runs yet. Create your first playbook to get started.</p>}
        </div>
      </div>
    </div>
  );
};
