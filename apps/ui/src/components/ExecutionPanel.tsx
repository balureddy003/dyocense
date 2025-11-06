import { Check, Circle, Clock, ChevronRight, AlertCircle } from "lucide-react";
import { useState } from "react";

type Stage = {
  id: string;
  title: string;
  description: string;
  todos: string[];
};

type TodoStatus = "not-started" | "in-progress" | "completed";

export type ExecutionPanelProps = {
  stages: Stage[];
  title?: string;
  estimatedDuration?: string;
  hideHeader?: boolean; // allow callers to remove header when a global header exists
};

export function ExecutionPanel({ stages, title = "Execution Playbook", estimatedDuration, hideHeader = false }: ExecutionPanelProps) {
  const [expandedStage, setExpandedStage] = useState<string | null>(stages.length > 0 ? stages[0].id : null);
  const [todoStatus, setTodoStatus] = useState<Record<string, TodoStatus>>({});

  const toggleTodo = (stageId: string, todoIdx: number) => {
    const key = `${stageId}-${todoIdx}`;
    setTodoStatus((prev) => {
      const current = prev[key] || "not-started";
      const next = current === "not-started" ? "in-progress" : current === "in-progress" ? "completed" : "not-started";
      return { ...prev, [key]: next };
    });
  };

  const getStageProgress = (stage: Stage): { completed: number; total: number; percentage: number } => {
    const total = stage.todos.length;
    const completed = stage.todos.filter((_, idx) => {
      const key = `${stage.id}-${idx}`;
      return todoStatus[key] === "completed";
    }).length;
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { completed, total, percentage };
  };

  return (
    <main className="flex h-full w-full flex-col overflow-hidden bg-white">
      {/* Header */}
      {!hideHeader && (
        <header className="border-b bg-gradient-to-b from-gray-50 to-white px-6 py-5 flex-shrink-0">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            {estimatedDuration && (
              <div className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-1 text-xs font-medium text-primary">
                <Clock size={14} />
                {estimatedDuration}
              </div>
            )}
          </div>
          <p className="text-sm text-gray-600">Follow these stages to execute your plan. Track progress and mark todos as you complete them.</p>
        </header>
      )}

      {/* Stages */}
      <div className="flex-1 space-y-4 overflow-y-auto px-6 pb-6 pt-5">
        {stages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle size={48} className="mb-4 text-gray-300" />
            <div className="text-sm font-medium text-gray-500">No execution plan yet</div>
            <div className="text-xs text-gray-400">Chat with the AI assistant to generate your plan</div>
          </div>
        ) : (
          stages.map((stage, stageIdx) => {
            const progress = getStageProgress(stage);
            const isExpanded = expandedStage === stage.id;
            const isCompleted = progress.percentage === 100;
            return (
              <div key={stage.id} className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                {/* Stage Header */}
                <button
                  className="flex w-full items-start gap-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white px-5 py-4 text-left hover:bg-gray-50"
                  onClick={() => setExpandedStage(isExpanded ? null : stage.id)}
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 font-semibold text-primary">
                    {stageIdx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="mb-1 flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900">{stage.title}</h3>
                      <ChevronRight
                        size={18}
                        className={`text-gray-400 transition-transform ${isExpanded ? "rotate-90" : ""}`}
                      />
                    </div>
                    <p className="mb-3 text-sm text-gray-600">{stage.description}</p>
                    {/* Progress Bar */}
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                          <div
                            className={`h-full transition-all ${isCompleted ? "bg-green-500" : "bg-primary"}`}
                            style={{ width: `${progress.percentage}%` }}
                          />
                        </div>
                      </div>
                      <div className="text-xs font-medium text-gray-500">
                        {progress.completed}/{progress.total}
                      </div>
                    </div>
                  </div>
                </button>

                {/* Todos */}
                {isExpanded && (
                  <div className="space-y-1 p-5">
                    {stage.todos.map((todo, todoIdx) => {
                      const key = `${stage.id}-${todoIdx}`;
                      const status = todoStatus[key] || "not-started";
                      return (
                        <button
                          key={todoIdx}
                          className="flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left hover:bg-gray-50"
                          onClick={() => toggleTodo(stage.id, todoIdx)}
                        >
                          {/* Status Icon */}
                          <div className="shrink-0 pt-0.5">
                            {status === "completed" ? (
                              <Check size={18} className="text-green-600" />
                            ) : status === "in-progress" ? (
                              <Circle size={18} className="animate-pulse fill-blue-200 text-primary" />
                            ) : (
                              <Circle size={18} className="text-gray-300" />
                            )}
                          </div>
                          {/* Todo Text */}
                          <div className="flex-1">
                            <div
                              className={`text-sm leading-relaxed ${
                                status === "completed" ? "text-gray-500 line-through" : "text-gray-900"
                              }`}
                            >
                              {todo}
                            </div>
                          </div>
                          {/* Status Badge */}
                          {status === "in-progress" && (
                            <div className="shrink-0 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-primary">
                              In Progress
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </main>
  );
}
