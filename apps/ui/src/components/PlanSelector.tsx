import { Calendar, Clock, FileText, GitBranch, Lightbulb, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

export type SavedPlan = {
  id: string;
  projectId?: string;
  title: string;
  summary: string;
  createdAt: string;
  updatedAt: string;
  version: number;
  userProvidedName?: string;
  stages: Array<{
    id: string;
    title: string;
    description: string;
    todos: string[];
  }>;
  quickWins: string[];
  estimatedDuration: string;
  dataSources?: Array<{
    id: string;
    name: string;
    type: string;
    size: number;
  }>;
};

type PlanSelectorProps = {
  plans: SavedPlan[];
  onSelectPlan: (plan: SavedPlan) => void;
  onCreateNew: () => void;
  onDeletePlan: (planId: string) => void;
  currentProjectName?: string;
  tenantName?: string;
  onStartWithGoal?: (goal: string) => void;
};

export function PlanSelector({ plans, onSelectPlan, onCreateNew, onDeletePlan, currentProjectName, tenantName, onStartWithGoal }: PlanSelectorProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [goalInput, setGoalInput] = useState("");
  const suggestedGoals = [
    "Cut operating costs 15%",
    "Increase sales 20%",
    "Improve stock accuracy",
    "Reduce spoilage 30%",
  ];

  const handleDelete = (e: React.MouseEvent, planId: string) => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this plan? This action cannot be undone.")) {
      onDeletePlan(planId);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-6">
      <div className="w-full max-w-5xl">
        {/* Hierarchy Context */}
        {(tenantName || currentProjectName) && (
          <div className="mb-6 flex items-center justify-center">
            <div className="inline-flex items-center gap-2 text-sm text-gray-600 bg-white px-4 py-2 rounded-full border border-gray-200 shadow-sm">
              {tenantName && (
                <>
                  <span className="font-semibold text-gray-700">📊 {tenantName}</span>
                  <span className="text-gray-400">→</span>
                </>
              )}
              {currentProjectName && (
                <>
                  <span className="font-semibold text-primary">📁 {currentProjectName}</span>
                  <span className="text-gray-400">→</span>
                </>
              )}
              <span className="font-semibold text-gray-700">📋 Plans</span>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Welcome to AI Business Planner
          </h1>
          <p className="text-lg text-gray-600">
            {plans.length > 0
              ? `Choose an existing plan ${currentProjectName ? `in ${currentProjectName}` : ''} or create a new one`
              : `Get started by creating your first business plan ${currentProjectName ? `in ${currentProjectName}` : ''}`}
          </p>
        </div>

        {/* Goal-first quick start */}
        <div className="mb-6">
          <div className="flex flex-wrap gap-2 justify-center mb-3">
            {suggestedGoals.map((g) => (
              <button
                key={g}
                onClick={() => onStartWithGoal ? onStartWithGoal(g) : onCreateNew()}
                className="px-3 py-1.5 text-sm rounded-full border border-gray-200 bg-white hover:border-primary hover:text-primary"
              >
                {g}
              </button>
            ))}
          </div>
          <div className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              placeholder="Describe your top goal (e.g., Reduce costs by 15% in 90 days)"
              className="flex-1 rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
            <button
              onClick={() => {
                const g = goalInput.trim();
                if (!g) return;
                onStartWithGoal ? onStartWithGoal(g) : onCreateNew();
              }}
              className="px-4 py-3 rounded-lg bg-primary text-white text-sm font-semibold hover:bg-primary/90"
            >
              Generate plan
            </button>
          </div>
        </div>

        {/* Create New Plan Button */}
        <button
          onClick={onCreateNew}
          className="w-full mb-8 rounded-2xl border-2 border-dashed border-primary bg-blue-50 hover:bg-blue-100 p-8 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <div className="flex items-center justify-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center">
              <Plus size={32} className="text-white" />
            </div>
            <div className="text-left">
              <h3 className="text-2xl font-bold text-gray-900 mb-1">Create New Plan</h3>
              <p className="text-gray-600">
                Start fresh with AI-powered business planning {currentProjectName ? `in ${currentProjectName}` : ''}
              </p>
            </div>
          </div>
        </button>

        {/* Info Card: Understanding the Hierarchy */}
        {plans.length === 0 && (
          <div className="mb-8 rounded-xl bg-gradient-to-r from-blue-100 via-purple-100 to-pink-100 p-6 border border-blue-200">
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Lightbulb size={20} className="text-primary" />
              How It Works: Organize Your Business Plans
            </h3>
            <div className="space-y-3 text-sm text-gray-700">
              <div className="flex items-start gap-3">
                <span className="text-2xl">📊</span>
                <div>
                  <strong className="font-semibold">Workspace (Tenant):</strong> Your company's main account where all your business data lives
                </div>
              </div>
              <div className="flex items-center justify-center text-gray-400">
                <span className="text-xl">↓</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-2xl">📁</span>
                <div>
                  <strong className="font-semibold">Projects:</strong> Organize plans by department, initiative, or business unit (e.g., "Q1 2024", "Restaurant A", "Cost Optimization")
                </div>
              </div>
              <div className="flex items-center justify-center text-gray-400">
                <span className="text-xl">↓</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-2xl">📋</span>
                <div>
                  <strong className="font-semibold">Plans:</strong> Specific business plans with goals, stages, and actions (e.g., "Reduce food waste 20%", "Increase revenue 15%")
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Existing Plans */}
        {plans.length > 0 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <FileText size={24} className="text-primary" />
              Your Plans ({plans.length})
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {plans.map((plan) => (
                <button
                  key={plan.id}
                  onClick={() => onSelectPlan(plan)}
                  className="group relative rounded-xl border border-gray-200 bg-white p-6 text-left shadow-sm hover:shadow-lg hover:border-primary transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  {/* Delete Button */}
                  <button
                    onClick={(e) => handleDelete(e, plan.id)}
                    className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-white border border-gray-200 hover:bg-red-50 hover:border-red-300 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all z-10"
                    title="Delete plan"
                  >
                    <Trash2 size={16} className="text-red-600" />
                  </button>

                  {/* Plan Content */}
                  <div className="mb-3">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-bold text-gray-900 pr-10">
                        {plan.userProvidedName || plan.title}
                      </h3>
                      <span className="flex items-center gap-1 text-xs font-semibold text-primary bg-blue-50 px-2 py-0.5 rounded-full">
                        <GitBranch size={12} />
                        v{plan.version}
                      </span>
                    </div>
                    {plan.userProvidedName && (
                      <p className="text-xs text-gray-500 italic mb-1">{plan.title}</p>
                    )}
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {plan.summary}
                    </p>
                  </div>

                  {/* Plan Metadata */}
                  <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-3">
                    <div className="flex items-center gap-1">
                      <Calendar size={14} />
                      <span>Created {new Date(plan.createdAt).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={14} />
                      <span>{plan.estimatedDuration}</span>
                    </div>
                  </div>

                  {/* Plan Stats */}
                  <div className="flex gap-4 pt-3 border-t border-gray-100">
                    <div className="text-sm">
                      <span className="font-semibold text-gray-900">
                        {plan.stages.length}
                      </span>
                      <span className="text-gray-600 ml-1">stages</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-semibold text-gray-900">
                        {plan.quickWins.length}
                      </span>
                      <span className="text-gray-600 ml-1">quick wins</span>
                    </div>
                    {plan.dataSources && plan.dataSources.length > 0 && (
                      <div className="text-sm">
                        <span className="font-semibold text-gray-900">
                          {plan.dataSources.length}
                        </span>
                        <span className="text-gray-600 ml-1">data sources</span>
                      </div>
                    )}
                  </div>

                  {/* Last Updated */}
                  <div className="mt-3 text-xs text-gray-400">
                    Last updated {new Date(plan.updatedAt).toLocaleString()}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
