import { X, FileText, Clock, Calendar, GitBranch } from "lucide-react";
import { useEffect, useRef, useCallback } from "react";
import { SavedPlan } from "./PlanSelector";

type PlanVersionsSidebarProps = {
  open: boolean;
  onClose: () => void;
  plans: SavedPlan[];
  currentPlanId: string | null;
  onSelectPlan: (plan: SavedPlan) => void;
  onCreateNew: () => void;
  projectName?: string;
};

export function PlanVersionsSidebar({
  open,
  onClose,
  plans,
  currentPlanId,
  onSelectPlan,
  onCreateNew,
  projectName,
}: PlanVersionsSidebarProps) {
  const closeBtnRef = useRef<HTMLButtonElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const getFocusable = useCallback(() => {
    const root = containerRef.current;
    if (!root) return [] as HTMLElement[];
    const nodes = root.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select, [tabindex]:not([tabindex="-1"])'
    );
    return Array.from(nodes).filter((el) => !el.hasAttribute("disabled") && !el.getAttribute("aria-hidden"));
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const focusable = getFocusable();
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (e.shiftKey) {
        if (!active || active === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (!active || active === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [getFocusable, onClose]
  );

  useEffect(() => {
    if (open) {
      // Lock body scroll
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      // Focus the close button for accessibility
      setTimeout(() => closeBtnRef.current?.focus(), 0);
      return () => {
        document.body.style.overflow = prev;
      };
    }
  }, [open]);

  if (!open) return null;

  // Group plans by base title or user name
  const groupedPlans = plans.reduce((acc, plan) => {
    const key = plan.userProvidedName || plan.title;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(plan);
    return acc;
  }, {} as Record<string, SavedPlan[]>);

  // Sort plans within each group by version (descending)
  Object.keys(groupedPlans).forEach(key => {
    groupedPlans[key].sort((a, b) => b.version - a.version);
  });

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-[50] animate-in fade-in duration-200 supports-[backdrop-filter]:backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <div
        ref={containerRef}
        className="fixed left-0 top-0 bottom-0 w-[22rem] sm:w-96 lg:w-[28rem] bg-white shadow-2xl z-[60] animate-in slide-in-from-left duration-300 flex flex-col border-r border-gray-100"
        role="dialog"
        aria-modal="true"
        aria-label="Plan versions"
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <FileText size={20} className="text-primary" />
            <span>My Plans ({plans.length})</span>
            {projectName && (
              <span className="ml-2 text-xs font-medium text-gray-500">in {projectName}</span>
            )}
          </h2>
          <button
            ref={closeBtnRef}
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Create New Button */}
        <div className="p-4 border-b">
          <button
            onClick={() => {
              onCreateNew();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white font-semibold rounded-lg hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create New Plan
          </button>
        </div>

        {/* Plans List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-2">
              Recent
            </h3>
            <div className="space-y-1">
              {plans.map((plan) => (
                <button
                  key={plan.id}
                  onClick={() => {
                    onSelectPlan(plan);
                    onClose();
                  }}
                  className={`w-full text-left p-3 rounded-lg transition-all group focus:outline-none focus:ring-2 focus:ring-primary/40 ${
                    plan.id === currentPlanId
                      ? "bg-blue-50 border border-primary"
                      : "hover:bg-gray-50 border border-transparent"
                  }`}
                >
                  {/* Plan Header */}
                  <div className="flex items-start gap-3 mb-2">
                    <div className="w-12 h-12 rounded-lg overflow-hidden bg-gradient-to-br from-blue-100 to-purple-100 flex-shrink-0">
                      {/* Placeholder image - could be replaced with actual plan icon */}
                      <div className="w-full h-full flex items-center justify-center">
                        <FileText size={20} className="text-primary" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 text-sm mb-0.5 truncate">
                        {plan.userProvidedName || plan.title}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <GitBranch size={12} />
                          v{plan.version}
                        </span>
                        <span>•</span>
                        <span>{plan.stages.length} stages</span>
                        <span>•</span>
                        <span>{plan.quickWins.length} wins</span>
                      </div>
                    </div>
                  </div>

                  {/* Plan Meta */}
                  <div className="flex items-center gap-3 text-xs text-gray-500 ml-15">
                    <span className="flex items-center gap-1">
                      <Calendar size={12} />
                      {new Date(plan.createdAt).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric', 
                        year: 'numeric' 
                      })}
                    </span>
                    <span className="text-gray-400">Auto-saved</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
