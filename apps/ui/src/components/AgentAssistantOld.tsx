import { ChevronDown, ChevronUp, FileUp, Loader2, Send, Sparkles, CheckCircle2, Clock, AlertCircle, Settings, Lightbulb } from "lucide-react";
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
      text: "Hi! I'm your AI business assistant. Let's start by setting your preferences so I can create a personalized plan for you.",
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [researchStatus, setResearchStatus] = useState<ResearchStatus>("idle");
  const [prefsOpen, setPrefsOpen] = useState(false);
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

  function toggleSet<K extends keyof typeof prefs>(key: K, value: string) {
    setPrefs((prev) => {
      const next = new Set(prev[key] as unknown as Set<string>);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return { ...prev, [key]: next } as typeof prev;
    });
  }

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

    // Simulate AI research and planning
    await simulateResearch(msgText);
  };

  const simulateResearch = async (userGoal: string) => {
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
      title: `Plan: ${userGoal.slice(0, 60)}`,
      summary: `Based on your goal to ${userGoal.toLowerCase()}, I've created a 3-stage plan that balances quick wins with long-term improvements.`,
      estimatedDuration: "4-6 weeks",
      quickWins: [
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

    setMessages((m) => [
      ...m,
      {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: `Great! I've created a detailed plan for you. Here's the overview:\n\n**${generatedPlan.title}**\n\n${generatedPlan.summary}\n\nYou can see the full execution steps in the middle panel. Want me to explain any stage in detail?`,
        timestamp: Date.now(),
      },
    ]);

    setResearchStatus("ready");
    setLoading(false);
  };

  const applyPreferences = () => {
    const parts: string[] = [];
    if (prefs.businessType.size) parts.push(`Business: ${Array.from(prefs.businessType).join(", ")}`);
    if (prefs.objectiveFocus.size) parts.push(`Focus: ${Array.from(prefs.objectiveFocus).join(", ")}`);
    if (prefs.operatingPace.size) parts.push(`Pace: ${Array.from(prefs.operatingPace).join(", ")}`);
    if (prefs.budget.size) parts.push(`Budget: ${Array.from(prefs.budget).join(", ")}`);
    if (prefs.markets.size) parts.push(`Markets: ${Array.from(prefs.markets).join(", ")}`);
    if (prefs.otherNeeds.trim()) parts.push(`Notes: ${prefs.otherNeeds.trim()}`);

    const prefText = parts.length ? parts.join(" • ") : "No preferences set";
    handleSend(`My preferences: ${prefText}`);
    setPrefsOpen(false);
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
          Tell me your goal, upload your data, and I'll research and create a detailed execution plan for you.
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

      {/* Preferences */}
      <section className="border-b px-5 py-4">
        <button
          className="flex w-full items-center justify-between rounded-xl border border-gray-200 px-3 py-2 text-left text-sm text-gray-700 hover:border-primary/60 hover:bg-blue-50/30"
          onClick={() => setPrefsOpen((v) => !v)}
        >
          <span className="font-semibold">My Preferences</span>
          {prefsOpen ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
        </button>
        {prefsOpen && (
          <div className="mt-3 space-y-4">
            {/* Business Type */}
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Business Type</div>
              <div className="flex flex-wrap gap-2">
                {["Restaurant", "Retail", "eCommerce", "Services", "Manufacturing"].map((opt) => (
                  <Chip key={opt} label={opt} selected={prefs.businessType.has(opt)} onToggle={() => toggleSet("businessType", opt)} />
                ))}
              </div>
            </div>
            {/* Objective Focus */}
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Objective Focus</div>
              <div className="flex flex-wrap gap-2">
                {["Reduce Cost", "Increase Revenue", "Improve Service", "Reduce Carbon"].map((opt) => (
                  <Chip key={opt} label={opt} selected={prefs.objectiveFocus.has(opt)} onToggle={() => toggleSet("objectiveFocus", opt)} />
                ))}
              </div>
            </div>
            {/* Operating Pace */}
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Operating Pace</div>
              <div className="flex flex-wrap gap-2">
                {["Ambitious", "Conservative", "Pilot-first"].map((opt) => (
                  <Chip key={opt} label={opt} selected={prefs.operatingPace.has(opt)} onToggle={() => toggleSet("operatingPace", opt)} />
                ))}
              </div>
            </div>
            {/* Budget */}
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Budget</div>
              <div className="flex flex-wrap gap-2">
                {["Lean", "Standard", "Premium"].map((opt) => (
                  <Chip key={opt} label={opt} selected={prefs.budget.has(opt)} onToggle={() => toggleSet("budget", opt)} />
                ))}
              </div>
            </div>
            {/* Markets */}
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Markets</div>
              <div className="flex flex-wrap gap-2">
                {["Local", "Multi-city", "Online", "US", "EU", "APAC"].map((opt) => (
                  <Chip key={opt} label={opt} selected={prefs.markets.has(opt)} onToggle={() => toggleSet("markets", opt)} />
                ))}
              </div>
            </div>
            {/* Other Needs */}
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Other Needs</div>
              <textarea
                className="w-full rounded-lg border p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                rows={3}
                maxLength={1000}
                placeholder="Any constraints or notes (e.g., supplier list missing, freezer capacity)"
                value={prefs.otherNeeds}
                onChange={(e) => setPrefs((p) => ({ ...p, otherNeeds: e.target.value }))}
              />
              <div className="text-right text-[11px] text-gray-400">{prefs.otherNeeds.length}/1000</div>
            </div>
            <div className="flex items-center justify-between">
              <button
                className="text-sm text-gray-500 hover:text-gray-700"
                onClick={() =>
                  setPrefs({ businessType: new Set(), objectiveFocus: new Set(), operatingPace: new Set(), budget: new Set(), markets: new Set(), otherNeeds: "" })
                }
              >
                Clear
              </button>
              <button className="rounded-lg bg-primary px-3 py-1.5 text-sm font-semibold text-white" onClick={applyPreferences}>
                Apply
              </button>
            </div>
          </div>
        )}
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
    </aside>
  );
}

function Chip({ label, selected, onToggle }: { label: string; selected?: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`rounded-lg border px-3 py-1.5 text-sm ${selected ? "border-primary bg-blue-50 text-primary" : "border-gray-200 hover:bg-gray-50"}`}
    >
      {label}
    </button>
  );
}
