import { FileUp, Loader2, Send, Sparkles, CheckCircle2, Clock, Settings, Lightbulb, Target } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { TenantProfile } from "../lib/api";
import { PreferencesModal } from "./PreferencesModal";
import { generateSuggestedGoals, generateGoalStatement, SuggestedGoal } from "../lib/goalGenerator";

type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  files?: Array<{ name: string; size: number }>;
  timestamp: number;
};

type ResearchStatus = "idle" | "researching" | "planning" | "ready";

type PlanOverview = {
  title: string;
  summary: string;
  stages: Array<{
    id: string;
    title: string;
    description: string;
    todos: string[];
  }>;
  quickWins: string[];
  estimatedDuration: string;
};

type PreferencesState = {
  businessType: Set<string>;
  objectiveFocus: Set<string>;
  operatingPace: Set<string>;
  budget: Set<string>;
  markets: Set<string>;
  otherNeeds: string;
};

export type AgentAssistantProps = {
  onPlanGenerated?: (plan: PlanOverview) => void;
  profile?: TenantProfile | null;
};

export function AgentAssistant({ onPlanGenerated, profile }: AgentAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Hi! I'm your AI business assistant. Click 'Set Preferences' to get started, and I'll suggest personalized goals for your business.",
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [researchStatus, setResearchStatus] = useState<ResearchStatus>("idle");
  const [prefsModalOpen, setPrefsModalOpen] = useState(false);
  const [plan, setPlan] = useState<PlanOverview | null>(null);
  const [preferences, setPreferences] = useState<PreferencesState | null>(null);
  const [suggestedGoals, setSuggestedGoals] = useState<SuggestedGoal[]>([]);
  const [showGoalSuggestions, setShowGoalSuggestions] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Safely handle scrollIntoView for environments that don't support it (tests)
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handlePreferencesConfirm = (summary: string, prefs: PreferencesState) => {
    setPreferences(prefs);
    
    // Add message about preferences
    setMessages((m) => [
      ...m,
      {
        id: `user-prefs-${Date.now()}`,
        role: "user",
        text: `My preferences: ${summary}`,
        timestamp: Date.now(),
      },
    ]);

    // Generate goal suggestions
    const businessType = Array.from(prefs.businessType)[0] || "";
    const objectives = Array.from(prefs.objectiveFocus);
    const pace = Array.from(prefs.operatingPace)[0] || "";
    const budget = Array.from(prefs.budget)[0] || "";
    const markets = Array.from(prefs.markets);

    const goals = generateSuggestedGoals(profile || null, {
      businessType,
      objectives,
      pace,
      budget,
      markets,
    });

    setSuggestedGoals(goals);
    setShowGoalSuggestions(true);

    // Add assistant message with suggestions
    setMessages((m) => [
      ...m,
      {
        id: `assistant-goals-${Date.now()}`,
        role: "assistant",
        text: `Great! Based on your preferences, I've generated ${goals.length} personalized goal suggestions below. Pick one to create a detailed execution plan, or describe your own goal.`,
        timestamp: Date.now(),
      },
    ]);
  };

  const handleGoalSelect = async (goal: SuggestedGoal) => {
    if (!preferences) return;

    const businessType = Array.from(preferences.businessType)[0] || "";
    const markets = Array.from(preferences.markets);
    const goalStatement = generateGoalStatement(goal, {
      businessType,
      objectives: Array.from(preferences.objectiveFocus),
      pace: Array.from(preferences.operatingPace)[0] || "",
      budget: Array.from(preferences.budget)[0] || "",
      markets,
    });

    // Add user selection message
    setMessages((m) => [
      ...m,
      {
        id: `user-goal-${Date.now()}`,
        role: "user",
        text: `Selected goal: ${goalStatement}`,
        timestamp: Date.now(),
      },
    ]);

    setShowGoalSuggestions(false);
    setLoading(true);

    // Simulate research and planning
    await simulateResearch(goalStatement, goal);
  };

  const handleSend = async (text?: string, files?: FileList | null) => {
    const msgText = text || input;
    if (!msgText.trim() && (!files || files.length === 0)) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      text: msgText,
      files: files ? Array.from(files).map((f) => ({ name: f.name, size: f.size })) : undefined,
      timestamp: Date.now(),
    };

    setMessages((m) => [...m, userMsg]);
    setInput("");
    if (fileRef.current) fileRef.current.value = "";
    setLoading(true);
    setShowGoalSuggestions(false);

    // Simulate AI research and planning
    await simulateResearch(msgText);
  };

  const simulateResearch = async (userGoal: string, selectedGoal?: SuggestedGoal) => {
    setResearchStatus("researching");
    
    // Step 1: Analyzing goal
    await new Promise((r) => setTimeout(r, 1500));
    setMessages((m) => [
      ...m,
      {
        id: `sys-${Date.now()}`,
        role: "system",
        text: "🔍 Analyzing your goal and business context...",
        timestamp: Date.now(),
      },
    ]);

    // Step 2: Research best practices
    await new Promise((r) => setTimeout(r, 2000));
    setMessages((m) => [
      ...m,
      {
        id: `sys-${Date.now()}`,
        role: "system",
        text: "📚 Researching industry best practices and similar cases...",
        timestamp: Date.now(),
      },
    ]);

    setResearchStatus("planning");

    // Step 3: Creating plan
    await new Promise((r) => setTimeout(r, 2000));
    setMessages((m) => [
      ...m,
      {
        id: `sys-${Date.now()}`,
        role: "system",
        text: "📋 Creating your customized execution plan...",
        timestamp: Date.now(),
      },
    ]);

    // Step 4: Present plan
    const generatedPlan: PlanOverview = {
      title: selectedGoal?.title || `Plan: ${userGoal.slice(0, 60)}`,
      summary: selectedGoal?.description || `Based on your goal to ${userGoal.toLowerCase()}, I've created a 3-stage plan that balances quick wins with long-term improvements.`,
      estimatedDuration: selectedGoal?.estimatedDuration || "4-6 weeks",
      quickWins: selectedGoal
        ? [
            "Review current baseline metrics",
            "Identify quick optimization opportunities",
            "Set up tracking dashboard",
          ]
        : [
            "Review current supplier contracts for immediate savings",
            "Implement daily inventory tracking",
            "Set up automated low-stock alerts",
          ],
      stages: [
        {
          id: "stage-1",
          title: "Stage 1: Data Collection & Baseline",
          description: "Gather current performance data and establish benchmarks",
          todos: [
            "Export 6 months of sales history",
            "Document current inventory levels by SKU",
            "Calculate baseline holding costs",
            "Identify slow-moving items",
          ],
        },
        {
          id: "stage-2",
          title: "Stage 2: Analysis & Optimization",
          description: "Analyze patterns and implement improvements",
          todos: [
            "Run demand forecasting model",
            "Calculate optimal reorder points",
            "Identify consolidation opportunities",
            "Negotiate with top 3 suppliers",
          ],
        },
        {
          id: "stage-3",
          title: "Stage 3: Execute & Monitor",
          description: "Roll out changes and track impact",
          todos: [
            "Implement new ordering rules",
            "Train team on new process",
            "Set up weekly KPI dashboard",
            "Schedule monthly review meetings",
          ],
        },
      ],
    };

    setPlan(generatedPlan);
    onPlanGenerated?.(generatedPlan);

    const impactNote = selectedGoal ? `\n\n**Expected Impact:** ${selectedGoal.expectedImpact}` : "";

    setMessages((m) => [
      ...m,
      {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: `Great! I've created a detailed plan for you. Here's the overview:\n\n**${generatedPlan.title}**\n\n${generatedPlan.summary}${impactNote}\n\nYou can see the full execution steps in the middle panel. Want me to explain any stage in detail?`,
        timestamp: Date.now(),
      },
    ]);

    setResearchStatus("ready");
    setLoading(false);
  };

  return (
    <aside className="flex w-[380px] flex-col border-r bg-white">
      {/* Header */}
      <header className="border-b bg-gradient-to-b from-blue-50/60 to-white px-5 py-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-primary">
          <Sparkles size={16} /> AI Assistant
        </div>
        <h2 className="mb-1 text-lg font-semibold text-gray-900">Get a customized plan</h2>
        <p className="text-xs leading-relaxed text-gray-600">
          Set preferences, choose a goal, and I'll create a detailed execution plan
        </p>
        {researchStatus !== "idle" && (
          <div className="mt-3 flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-xs">
            {researchStatus === "researching" && (
              <>
                <Loader2 size={14} className="animate-spin text-primary" />
                <span className="text-gray-700">Researching...</span>
              </>
            )}
            {researchStatus === "planning" && (
              <>
                <Clock size={14} className="text-amber-500" />
                <span className="text-gray-700">Creating plan...</span>
              </>
            )}
            {researchStatus === "ready" && (
              <>
                <CheckCircle2 size={14} className="text-green-600" />
                <span className="text-gray-700">Plan ready!</span>
              </>
            )}
          </div>
        )}
      </header>

      {/* Set Preferences Button */}
      <section className="border-b bg-gradient-to-r from-blue-50/50 to-purple-50/50 px-5 py-3">
        <button
          className="flex w-full items-center justify-between rounded-xl border-2 border-primary/30 bg-white px-4 py-3 text-left shadow-sm hover:border-primary hover:shadow-md transition-all"
          onClick={() => setPrefsModalOpen(true)}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <Settings size={18} className="text-primary" />
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900">
                {preferences ? "Update Preferences" : "Set Preferences"}
              </div>
              <div className="text-xs text-gray-600">
                {preferences
                  ? `${Array.from(preferences.businessType)[0]} • ${Array.from(preferences.objectiveFocus).length} goals`
                  : "Tell us about your business"}
              </div>
            </div>
          </div>
          <Sparkles size={16} className="text-primary" />
        </button>
      </section>

      {/* Quick Plan Overview (if generated) */}
      {plan && (
        <section className="border-b px-5 py-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500">Plan Overview</h3>
          <div className="space-y-2 rounded-xl border border-gray-100 bg-gray-50 p-3">
            <div className="text-sm font-semibold text-gray-800">{plan.title}</div>
            <div className="text-xs text-gray-600">{plan.summary}</div>
            <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
              <span>📅 {plan.estimatedDuration}</span>
              <span>📍 {plan.stages.length} stages</span>
            </div>
          </div>
          <div className="mt-3">
            <div className="mb-1 text-xs font-semibold text-gray-500">Quick Wins</div>
            <ul className="space-y-1 text-xs text-gray-700">
              {plan.quickWins.slice(0, 2).map((win, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  {win}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Suggested Goals */}
      {showGoalSuggestions && suggestedGoals.length > 0 && (
        <section className="border-b bg-gradient-to-b from-amber-50/30 to-white px-5 py-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-amber-700">
            <Lightbulb size={16} />
            Suggested Goals for You
          </div>
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {suggestedGoals.map((goal) => (
              <button
                key={goal.id}
                onClick={() => handleGoalSelect(goal)}
                className="group w-full rounded-xl border-2 border-gray-200 bg-white p-3 text-left hover:border-primary hover:bg-blue-50 hover:shadow-md transition-all"
              >
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{goal.icon}</span>
                    <span className="text-sm font-semibold text-gray-900">{goal.title}</span>
                  </div>
                  {goal.priority === "high" && (
                    <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700">
                      HIGH PRIORITY
                    </span>
                  )}
                </div>
                <p className="mb-2 text-xs text-gray-600">{goal.description}</p>
                <div className="flex items-center justify-between text-[11px] text-gray-500">
                  <span>⏱️ {goal.estimatedDuration}</span>
                  <span className="text-green-600">📈 {goal.expectedImpact}</span>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Conversation */}
      <div className="flex flex-1 flex-col overflow-hidden bg-gray-50">
        <div className="flex-1 space-y-3 overflow-y-auto px-5 pb-4 pt-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`rounded-xl p-3 text-sm leading-relaxed shadow-sm ${
                msg.role === "user"
                  ? "ml-auto max-w-[85%] bg-blue-50 text-blue-900"
                  : msg.role === "system"
                    ? "border border-gray-200 bg-white text-gray-600 italic"
                    : "border border-gray-100 bg-white text-gray-800"
              }`}
            >
              {msg.text}
              {msg.files && msg.files.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.files.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-2 rounded bg-gray-100 px-2 py-1 text-xs text-gray-600">
                      <FileUp size={12} />
                      {file.name} ({(file.size / 1024).toFixed(1)} KB)
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Loader2 size={14} className="animate-spin" /> Thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          className="border-t border-gray-200 bg-white px-5 pb-4 pt-3 shadow-[0_-12px_24px_-20px_rgba(15,23,42,0.35)]"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <div className="flex gap-2 rounded-2xl border border-gray-200 bg-white px-4 py-2.5">
            <input
              className="flex-1 bg-transparent text-sm outline-none"
              placeholder="Describe your business goal..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <input ref={fileRef} type="file" className="hidden" multiple onChange={(e) => handleSend(input, e.target.files)} />
            <button
              type="button"
              className="text-gray-400 hover:text-gray-600"
              onClick={() => fileRef.current?.click()}
              title="Upload data files"
            >
              <FileUp size={18} />
            </button>
            <button type="submit" className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white disabled:bg-gray-300" disabled={loading}>
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>

      {/* Preferences Modal */}
      <PreferencesModal
        open={prefsModalOpen}
        onClose={() => setPrefsModalOpen(false)}
        onConfirm={handlePreferencesConfirm}
        profile={profile}
      />
    </aside>
  );
}
