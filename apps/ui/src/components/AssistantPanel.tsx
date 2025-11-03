import { Loader2, MessageSquareMore, Send, Sparkles, Star } from "lucide-react";
import { Playbook } from "../hooks/usePlaybook";
import { useChat } from "../hooks/useChat";
import { useState } from "react";

interface AssistantPanelProps {
  playbook: Playbook;
}

export const AssistantPanel = ({ playbook }: AssistantPanelProps) => {
  const { messages, sendMessage, loading } = useChat();
  const [input, setInput] = useState("");
  const suggestionPrompts =
    playbook.whatIfs.map((scenario) => scenario.title) ||
    playbook.plan.map((stage) => stage.title.slice(0, 60)) ||
    [];

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

      <section className="flex-1 overflow-y-auto px-5 py-4 space-y-3 bg-gray-50">
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
        className="px-5 py-4 border-t bg-white flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (!loading && input.trim()) {
            sendMessage(input);
            setInput("");
          }
        }}
      >
        <input
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm"
          placeholder="Ask anything about the playbook…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:bg-gray-300"
          disabled={loading}
        >
          Send
        </button>
      </form>
    </aside>
  );
};
