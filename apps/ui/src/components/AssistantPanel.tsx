import { ChevronDown, ChevronUp, Loader2, MessageSquareMore, Send, Sparkles, Star } from "lucide-react";
import { Playbook } from "../hooks/usePlaybook";
import { useChat } from "../hooks/useChat";
import { useState } from "react";

interface AssistantPanelProps {
  playbook: Playbook;
  onPreferencesConfirm?: (summary: string) => void;
}

export const AssistantPanel = ({ playbook, onPreferencesConfirm }: AssistantPanelProps) => {
  const { messages, sendMessage, loading } = useChat();
  const [input, setInput] = useState("");
  const [prefsOpen, setPrefsOpen] = useState<boolean>(false);
  // Business-centric preferences for small businesses
  const [prefs, setPrefs] = useState({
    businessType: new Set<string>(),
    objectiveFocus: new Set<string>(),
    operatingPace: new Set<string>(),
    budget: new Set<string>(),
    markets: new Set<string>(),
    otherNeeds: "",
  });
  const suggestionPrompts =
    playbook.whatIfs.map((scenario) => scenario.title) ||
    playbook.plan.map((stage) => stage.title.slice(0, 60)) ||
    [];

  function toggleSet<K extends keyof typeof prefs>(key: K, value: string) {
    setPrefs((prev) => {
      const next = new Set(prev[key] as unknown as Set<string>);
      if (next.has(value)) next.delete(value); else next.add(value);
      return { ...prev, [key]: next } as typeof prev;
    });
  }

  function confirmPrefs() {
    const parts: string[] = [];
    if (prefs.businessType.size) parts.push(`business type: ${Array.from(prefs.businessType).join(", ")}`);
    if (prefs.objectiveFocus.size) parts.push(`focus: ${Array.from(prefs.objectiveFocus).join(", ")}`);
    if (prefs.operatingPace.size) parts.push(`pace: ${Array.from(prefs.operatingPace).join(", ")}`);
    if (prefs.budget.size) parts.push(`budget: ${Array.from(prefs.budget).join(", ")}`);
    if (prefs.markets.size) parts.push(`markets: ${Array.from(prefs.markets).join(", ")}`);
    if (prefs.otherNeeds.trim()) parts.push(`other: ${prefs.otherNeeds.trim()}`);
    const text = parts.length ? `My preferences → ${parts.join("; ")}` : "No specific preferences";
    if (!loading) {
      sendMessage(text);
      onPreferencesConfirm?.(text);
      setPrefsOpen(false);
    }
  }

  return (
    <aside className="hidden xl:flex xl:w-[360px] 2xl:w-[380px] flex-col border-r bg-white">
      <header className="px-5 py-5 border-b space-y-3 bg-gradient-to-b from-blue-50/60 to-white">
        <div className="flex items-center gap-2 text-primary font-semibold text-sm uppercase tracking-wide">
          <Sparkles size={16} /> Dyocense Copilot
        </div>
        <div className="text-[11px] text-gray-400 uppercase tracking-wide">Scroll down to see history</div>
        <div className="space-y-1">
          <h2 className="text-lg font-semibold text-gray-900">Resume planning with Copilot</h2>
          <p className="text-sm text-gray-600 leading-5">
            Need help tuning scenarios or explaining the next action? I can summarize outcomes, compare
            what-ifs, or draft hand-off notes.
          </p>
        </div>
      </header>

      {/* Preferences - aligned to Dyocense small business needs */}
      <section className="px-5 py-4 border-b">
        <button
          className="w-full flex items-center justify-between rounded-xl border border-gray-200 px-3 py-2 text-left text-sm text-gray-700 hover:border-primary/60 hover:bg-blue-50/30"
          onClick={() => setPrefsOpen((v) => !v)}
        >
          <span className="font-semibold">Preferences</span>
          {prefsOpen ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
        </button>
        {prefsOpen && (
          <div className="mt-3 space-y-4">
            {/* Business Type */}
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Business Type</div>
              <div className="flex flex-wrap gap-2">
                {["Restaurant", "Retail", "eCommerce", "Services", "Manufacturing"].map((opt) => (
                  <Chip
                    key={opt}
                    label={opt}
                    selected={prefs.businessType.has(opt)}
                    onToggle={() => toggleSet("businessType", opt)}
                  />
                ))}
              </div>
            </div>
            {/* Objective Focus */}
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Objective Focus</div>
              <div className="flex flex-wrap gap-2">
                {["Reduce Cost", "Increase Revenue", "Improve Service", "Reduce Carbon"].map((opt) => (
                  <Chip
                    key={opt}
                    label={opt}
                    selected={prefs.objectiveFocus.has(opt)}
                    onToggle={() => toggleSet("objectiveFocus", opt)}
                  />
                ))}
              </div>
            </div>
            {/* Operating Pace */}
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Operating Pace</div>
              <div className="flex flex-wrap gap-2">
                {["Ambitious", "Conservative", "Pilot-first"].map((opt) => (
                  <Chip
                    key={opt}
                    label={opt}
                    selected={prefs.operatingPace.has(opt)}
                    onToggle={() => toggleSet("operatingPace", opt)}
                  />
                ))}
              </div>
            </div>
            {/* Budget */}
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Budget</div>
              <div className="flex flex-wrap gap-2">
                {["Lean", "Standard", "Premium"].map((opt) => (
                  <Chip
                    key={opt}
                    label={opt}
                    selected={prefs.budget.has(opt)}
                    onToggle={() => toggleSet("budget", opt)}
                  />
                ))}
              </div>
            </div>
            {/* Markets */}
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Markets</div>
              <div className="flex flex-wrap gap-2">
                {["Local", "Multi-city", "Online", "US", "EU", "APAC"].map((opt) => (
                  <Chip
                    key={opt}
                    label={opt}
                    selected={prefs.markets.has(opt)}
                    onToggle={() => toggleSet("markets", opt)}
                  />
                ))}
              </div>
            </div>
            {/* Other Needs */}
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Other Needs</div>
              <textarea
                className="w-full border rounded-lg p-2 text-sm focus:outline-none"
                rows={3}
                maxLength={1000}
                placeholder="Enter constraints, data gaps, or notes (e.g., supplier list missing, limited freezer capacity)"
                value={prefs.otherNeeds}
                onChange={(e) => setPrefs((p) => ({ ...p, otherNeeds: e.target.value }))}
              />
              <div className="text-[11px] text-gray-400 text-right">{prefs.otherNeeds.length}/1000</div>
            </div>
            <div className="flex items-center justify-between">
              <button
                className="text-sm text-gray-500 hover:text-gray-700"
                onClick={() => setPrefs({ businessType: new Set(), objectiveFocus: new Set(), operatingPace: new Set(), budget: new Set(), markets: new Set(), otherNeeds: "" })}
              >
                Clear
              </button>
              <button
                className="px-3 py-1.5 rounded-lg bg-primary text-white text-sm font-semibold"
                onClick={() => confirmPrefs()}
              >
                Confirm
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="px-5 py-4 border-b space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Popular prompts</h3>
        <div className="space-y-2">
          {suggestionPrompts.slice(0, 3).map((prompt) => (
            <button
              key={prompt}
              className="w-full flex items-center justify-between gap-2 rounded-xl border border-gray-200 px-3 py-2 text-left text-sm text-gray-700 hover:border-primary/60 hover:bg-blue-50/50"
              onClick={() => {
                if (!loading) {
                  sendMessage(prompt);
                }
              }}
            >
              <span className="line-clamp-2">{prompt}</span>
              <Send size={15} className="text-primary shrink-0" />
            </button>
          ))}
        </div>
      </section>

      <section className="px-5 py-4 border-b space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Stage outline</h3>
          <span className="text-xs text-gray-400">{playbook.itinerary.length} stages</span>
        </div>
        <div className="space-y-3">
          {playbook.itinerary.map((day, index) => (
            <div key={day.id} className="rounded-xl border border-gray-100 p-3 bg-gray-50">
              <div className="flex items-center justify-between text-xs text-gray-500 uppercase tracking-wide">
                <span>{day.date}</span>
                <span>Stage {index + 1}</span>
              </div>
              <p className="text-sm font-medium text-gray-800 mt-1">{day.title}</p>
              <ul className="mt-2 space-y-1 text-sm text-gray-600">
                {day.entries.slice(0, 2).map((entry) => (
                  <li key={entry}>{entry}</li>
                ))}
                {day.entries.length > 2 && (
                  <li className="text-primary text-xs">+ {day.entries.length - 2} more</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="px-5 py-4 border-b space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Quick wins</h3>
        <ul className="space-y-2 text-sm text-gray-600">
          {playbook.summary.quickWins.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <Star size={14} className="mt-1 text-primary" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      <div className="flex-1 bg-gray-50 flex flex-col">
        <section className="flex-1 overflow-y-auto px-5 pt-4 pb-6 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
            <MessageSquareMore size={14} /> Conversation
          </div>
          <div className="space-y-3">
            {messages.map((msg, idx) => (
              <div
                key={`${msg.role}-${idx}`}
                className={`p-3 rounded-xl text-sm leading-5 shadow-sm max-w-full ${
                  msg.role === "user"
                    ? "bg-blue-50 text-blue-900 ml-auto"
                    : "bg-white text-gray-800 border border-gray-100"
                }`}
              >
                {msg.content}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Loader2 size={14} className="animate-spin" /> Drafting response…
              </div>
            )}
          </div>
        </section>

        <form
          className="px-5 pt-3 pb-4 border-t border-gray-200 bg-white shadow-[0_-12px_24px_-20px_rgba(15,23,42,0.35)]"
          onSubmit={(event) => {
            event.preventDefault();
            if (!loading && input.trim()) {
              sendMessage(input);
              setInput("");
            }
          }}
        >
          <div className="flex gap-2 rounded-2xl border border-gray-200 bg-white px-4 py-2.5">
            <input
              className="flex-1 text-sm bg-transparent outline-none"
              placeholder="Ask anything about the playbook…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button
              type="submit"
              className="bg-primary text-white px-4 py-2 rounded-xl text-sm font-semibold disabled:bg-gray-300"
              disabled={loading}
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </aside>
  );
};

function Chip({ label, selected, onToggle }: { label: string; selected?: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`px-3 py-1.5 rounded-lg border text-sm ${selected ? "border-primary bg-blue-50 text-primary" : "border-gray-200 hover:bg-gray-50"}`}
    >
      {label}
    </button>
  );
}

