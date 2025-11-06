import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  CheckCircle2, 
  Loader2, 
  MessageSquare, 
  RefreshCw, 
  Send, 
  Sparkles, 
  TrendingUp,
  Eye,
  Edit3,
  Zap
} from "lucide-react";
import { Playbook, CreatePlaybookPayload } from "../hooks/usePlaybook";
import { TopNav } from "../components/TopNav";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface PlaybookResultsPageProps {
  playbook: Playbook;
  originalPayload: CreatePlaybookPayload;
  onRegenerate: (payload: CreatePlaybookPayload) => Promise<void>;
  onViewFullPlan: () => void;
  loading?: boolean;
}

export const PlaybookResultsPage = ({ 
  playbook, 
  originalPayload, 
  onRegenerate, 
  onViewFullPlan,
  loading = false 
}: PlaybookResultsPageProps) => {
  const navigate = useNavigate();
  // Track a pending action so short confirmations like "yes" can apply it deterministically
  type PendingAction =
    | { kind: "extend_horizon"; weeks: number }
    | { kind: "focus_cost" }
    | { kind: "run_scenario"; index: number; title: string }
    | null;

  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [chatMessages, setChatMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `Great! I've created your ${playbook.title}. I analyzed your data and generated recommendations to help you ${playbook.goal.toLowerCase()}. What would you like to explore or adjust?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Smart suggestion prompts based on playbook type
  const getSuggestions = () => {
    const baseGoal = playbook.goal.toLowerCase();
    const suggestions = [];

    if (baseGoal.includes("inventory") || baseGoal.includes("stock")) {
      suggestions.push(
        "What if I reduce holding costs by 15%?",
        "Show me options to minimize stockouts",
        "How can I optimize reorder points?"
      );
    } else if (baseGoal.includes("demand") || baseGoal.includes("forecast")) {
      suggestions.push(
        "What if demand increases by 20%?",
        "Show seasonal trends in more detail",
        "How accurate is this forecast?"
      );
    } else if (baseGoal.includes("cost") || baseGoal.includes("reduce")) {
      suggestions.push(
        "What are the biggest cost-saving opportunities?",
        "Show me quick wins I can implement today",
        "Compare current vs. optimized costs"
      );
    }

    // Universal suggestions
    suggestions.push(
      "Extend planning horizon to 8 weeks",
      "Explain the top recommendation",
      "What are the risks I should consider?"
    );

    return suggestions.slice(0, 6);
  };

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim() || chatLoading) return;

    const userMessage: Message = {
      role: "user",
      content: messageText,
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setInput("");
    setChatLoading(true);

    // If the user confirms and we have a pending action, apply it deterministically
    const lower = messageText.trim().toLowerCase();
    const isAffirmation = ["yes", "yep", "yeah", "ok", "okay", "sure", "do it", "go ahead", "apply", "confirm"].some(
      (w) => lower === w || lower.includes(w)
    );

    if (isAffirmation && pendingAction) {
      await applyPendingAction(pendingAction);
      setPendingAction(null);
      setChatLoading(false);
      return;
    }

    // Simulate AI response (in real implementation, call your AI API)
    setTimeout(() => {
      const response = generateAIResponse(messageText, playbook, originalPayload);
      const assistantMessage: Message = {
        role: "assistant",
        content: response.text,
        timestamp: new Date()
      };
      // Store pending action (if any) so a simple "yes" can apply it
      setPendingAction(response.pendingAction ?? null);
      setChatMessages((prev) => [...prev, assistantMessage]);
      setChatLoading(false);
    }, 600);
  };

  // Apply a previously proposed action by regenerating with structured parameter changes
  const applyPendingAction = async (action: NonNullable<PendingAction>) => {
    // Announce the application
    setChatMessages((prev) => [
      ...prev,
      { role: "assistant", content: "Applying your request…", timestamp: new Date() },
    ]);

    const base: CreatePlaybookPayload = { ...originalPayload };
    const mergedInputs: Record<string, unknown> = { ...(base.data_inputs || {}) };

    if (action.kind === "extend_horizon") {
      base.horizon = action.weeks; // deterministic change
      mergedInputs.applied_change = `extend_horizon:${action.weeks}w`;
    } else if (action.kind === "focus_cost") {
      mergedInputs.objective = "min_cost";
      mergedInputs.applied_change = "focus_cost";
    } else if (action.kind === "run_scenario") {
      const scenario = playbook.whatIfs[action.index];
      mergedInputs.scenario = {
        title: scenario?.title || action.title,
        delta: scenario?.delta || {},
      };
      mergedInputs.applied_change = `scenario:${action.index}`;
    }

    base.data_inputs = mergedInputs;

    try {
      await onRegenerate(base);
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            action.kind === "extend_horizon"
              ? `Done. I regenerated the plan with an ${action.weeks}-week horizon. What would you like to explore next?`
              : action.kind === "focus_cost"
              ? "Done. I prioritised cost minimisation and updated the plan accordingly. Want to compare before vs after?"
              : `Scenario applied ("${action.title}"). I've updated the plan.
You can ask for a comparison or apply another change.`,
          timestamp: new Date(),
        },
      ]);
    } catch (e) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn't update the plan right now. Please try again, or adjust parameters manually.",
          timestamp: new Date(),
        },
      ]);
    }
  };

  const generateAIResponse = (
    userInput: string, 
    playbook: Playbook, 
    payload: CreatePlaybookPayload
  ): { text: string; pendingAction?: PendingAction } => {
    const input = userInput.toLowerCase();

    // Intent detection for regeneration
    if (input.includes("increase") && input.includes("horizon")) {
      return {
        text:
          "I can extend the planning horizon to 8 weeks for better long‑term visibility. Say 'apply' to proceed.",
        pendingAction: { kind: "extend_horizon", weeks: 8 },
      };
    }

    if (input.includes("reduce") && input.includes("cost")) {
      return {
        text:
          "I can prioritise cost minimisation and regenerate the plan. Say 'apply' to proceed.",
        pendingAction: { kind: "focus_cost" },
      };
    }

    if (input.includes("what if") || input.includes("scenario")) {
      const first = playbook.whatIfs[0];
      const second = playbook.whatIfs[1];
      const list = [first, second].filter(Boolean)
        .map((s, i) => `• ${s!.title}: ${s!.summary}`)
        .join("\n\n");
      return {
        text:
          `Here are scenarios you can apply right away:\n\n${list}\n\nSay 'apply scenario 1' or 'apply scenario 2'.`,
        pendingAction: first ? { kind: "run_scenario", index: 0, title: first.title } : undefined,
      };
    }

    if (input.includes("explain") || input.includes("why")) {
      return {
        text: `Let me explain the key recommendations:\n\n${playbook.plan
          .slice(0, 2)
          .map(
            (stage, i) =>
              `${i + 1}. **${stage.title}**: ${stage.description}\n   - ${stage.activities
                .slice(0, 2)
                .map((a) => a.name)
                .join("\n   - ")}`
          )
          .join("\n\n")}\n\nThe approach is designed to ${playbook.goal.toLowerCase()} while balancing risk and cost.`,
      };
    }

    if (input.includes("quick win") || input.includes("implement")) {
      return {
        text: `Here are the quick wins you can implement immediately:\n\n${playbook.summary.quickWins
          .map((win, i) => `${i + 1}. ${win}`)
          .join("\n")}\n\nSay 'explain 1' or 'apply scenario 1' to proceed.`,
      };
    }

    if (input.includes("risk") || input.includes("concern")) {
      return {
        text:
          "Key risks: 1) data quality, 2) demand volatility, 3) execution capacity. I can propose mitigations or run a sensitivity scenario. Say 'apply scenario 1' or 'suggest mitigations'.",
      };
    }

    // Parse explicit apply commands, e.g., "apply scenario 2" or "apply horizon 8w"
    const applyScenarioMatch = input.match(/apply\s+scenario\s+(\d+)/);
    if (applyScenarioMatch) {
      const idx = Math.max(0, Math.min(playbook.whatIfs.length - 1, parseInt(applyScenarioMatch[1], 10) - 1));
      const s = playbook.whatIfs[idx];
      return {
        text: `I'll apply: ${s?.title}. Say 'apply' to confirm.`,
        pendingAction: { kind: "run_scenario", index: idx, title: s?.title || `Scenario ${idx + 1}` },
      };
    }

    const applyHorizon = input.match(/horizon\s*(to|=)?\s*(\d+)\s*(w|wk|wks|week|weeks)/);
    if (applyHorizon) {
      const weeks = parseInt(applyHorizon[2], 10);
      return {
        text: `I can set the planning horizon to ${weeks} weeks. Say 'apply' to proceed.`,
        pendingAction: { kind: "extend_horizon", weeks },
      };
    }

    // Default deterministic response (avoid repeating if already sent)
    return {
      text:
        `Here are a few things I can do now:\n\n• Apply a scenario (e.g., 'apply scenario 1')\n• Extend horizon (e.g., 'horizon 8 weeks')\n• Focus on cost (say 'reduce cost')\n• Explain recommendations (say 'explain')\n\nReply with one of the options or say 'apply' after I propose a change.`,
    };
  };

  const suggestions = getSuggestions();

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <TopNav />
      
      <div className="flex-1 flex flex-col lg:flex-row max-w-7xl mx-auto w-full gap-6 p-6">
        {/* Left: Results Summary */}
        <div className="flex-1 space-y-6">
          {/* Header */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
            <button
              onClick={() => navigate("/home")}
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-primary transition"
            >
              <ArrowLeft size={16} />
              Back to home
            </button>

            <div className="flex items-start gap-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-green-100 shrink-0">
                <CheckCircle2 size={24} className="text-green-600" />
              </div>
              <div className="flex-1 space-y-2">
                <h1 className="text-2xl font-bold text-gray-900">{playbook.title}</h1>
                <p className="text-gray-600">{playbook.summary.context}</p>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Sparkles size={14} className="text-primary" />
                  <span>AI-generated • Ready to refine</span>
                </div>
              </div>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
              {playbook.summary.primaryKpis.map((kpi, idx) => (
                <div key={idx} className="space-y-1">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">{kpi.label}</p>
                  <p className="text-xl font-bold text-gray-900">{kpi.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Wins */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Zap size={20} className="text-amber-500" />
              <h2 className="text-lg font-semibold text-gray-900">Quick Wins</h2>
            </div>
            <p className="text-sm text-gray-600">
              High-impact actions you can take immediately
            </p>
            <ul className="space-y-3">
              {playbook.summary.quickWins.map((win, idx) => (
                <li key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-amber-50 border border-amber-100">
                  <CheckCircle2 size={18} className="text-amber-600 shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">{win}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Top Recommendations Preview */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
            <div className="flex items-center gap-2">
              <TrendingUp size={20} className="text-primary" />
              <h2 className="text-lg font-semibold text-gray-900">Top Recommendations</h2>
            </div>
            <div className="space-y-3">
              {playbook.plan.slice(0, 3).map((stage, idx) => (
                <div key={idx} className="p-4 rounded-lg border border-gray-100 hover:border-primary/30 transition">
                  <h3 className="font-semibold text-gray-900 mb-2">{stage.title}</h3>
                  <p className="text-sm text-gray-600 mb-3">{stage.description}</p>
                  <ul className="space-y-1">
                    {stage.activities.slice(0, 2).map((activity, actIdx) => (
                      <li key={actIdx} className="text-sm text-gray-700 flex items-start gap-2">
                        <span className="text-primary">•</span>
                        <span>{activity.name}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={onViewFullPlan}
              className="flex items-center gap-2 px-6 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition"
            >
              <Eye size={18} />
              View Full Plan
            </button>
            <button
              onClick={() => handleSendMessage("I want to adjust the parameters and regenerate")}
              className="flex items-center gap-2 px-6 py-3 rounded-full border-2 border-primary text-primary font-semibold hover:bg-blue-50 transition"
            >
              <Edit3 size={18} />
              Adjust Parameters
            </button>
            <button
              onClick={() => {
                if (window.confirm("Regenerate with current settings?")) {
                  void onRegenerate(originalPayload);
                }
              }}
              className="flex items-center gap-2 px-6 py-3 rounded-full border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 transition"
              disabled={loading}
            >
              <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
              Regenerate
            </button>
          </div>
        </div>

        {/* Right: AI Chat Interface */}
        <div className="lg:w-[420px] flex flex-col bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b bg-gradient-to-b from-blue-50/60 to-white">
            <div className="flex items-center gap-2 text-primary font-semibold text-sm uppercase tracking-wide mb-2">
              <Sparkles size={16} /> Dyocense Copilot
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Refine Your Plan</h2>
            <p className="text-sm text-gray-600 mt-1">
              Ask questions, run scenarios, or adjust parameters
            </p>
          </div>

          {/* Suggestions */}
          <div className="px-6 py-4 border-b space-y-3">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Try asking</h3>
            <div className="grid grid-cols-1 gap-2">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(suggestion)}
                  className="flex items-center justify-between gap-2 rounded-lg border border-gray-200 px-3 py-2.5 text-left text-sm text-gray-700 hover:border-primary hover:bg-blue-50/50 transition"
                >
                  <span className="line-clamp-1">{suggestion}</span>
                  <Send size={14} className="text-primary shrink-0" />
                </button>
              ))}
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-gray-50">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "bg-primary text-white rounded-tr-sm"
                      : "bg-white text-gray-800 border border-gray-100 rounded-tl-sm"
                  }`}
                >
                  {msg.content.split('\n').map((line, i) => (
                    <p key={i} className={i > 0 ? "mt-2" : ""}>
                      {line.startsWith('•') || line.match(/^\d+\./) ? (
                        <span className="block">{line}</span>
                      ) : line.startsWith('**') ? (
                        <strong>{line.replace(/\*\*/g, '')}</strong>
                      ) : (
                        line
                      )}
                    </p>
                  ))}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Loader2 size={16} className="animate-spin" />
                <span>Analyzing your request...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(input);
            }}
            className="px-6 py-4 border-t bg-white"
          >
            <div className="flex gap-2 items-center rounded-full border-2 border-gray-200 bg-gray-50 px-4 py-2 focus-within:border-primary focus-within:bg-white transition">
              <MessageSquare size={18} className="text-gray-400" />
              <input
                type="text"
                className="flex-1 text-sm bg-transparent outline-none placeholder:text-gray-400"
                placeholder="Ask about your plan..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={chatLoading}
              />
              <button
                type="submit"
                className="bg-primary text-white p-2 rounded-full disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition"
                disabled={chatLoading || !input.trim()}
              >
                <Send size={16} />
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              AI can make mistakes. Verify important decisions.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};
