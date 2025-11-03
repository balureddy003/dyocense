import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { useChat } from "../hooks/useChat";

export const SidebarAI = () => {
  const { messages, sendMessage, loading } = useChat();
  const [input, setInput] = useState("");

  return (
    <aside className="w-full lg:w-[320px] bg-white border-r flex flex-col">
      <div className="p-4 font-semibold border-b text-primary flex items-center gap-2">
        <Sparkles size={18} />
        AI Copilot
      </div>
      <div className="flex-1 p-4 space-y-3 overflow-y-auto">
        {messages.map((msg, idx) => (
          <div
            key={`${msg.role}-${idx}`}
            className={`p-3 rounded-lg text-sm leading-5 shadow-sm max-w-[90%] ${
              msg.role === "user"
                ? "bg-blue-50 text-blue-900 self-end ml-auto"
                : "bg-gray-100 text-gray-800"
            }`}
          >
            {msg.content}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Loader2 size={16} className="animate-spin" />
            Thinking...
          </div>
        )}
      </div>
      <div className="p-3 border-t flex gap-2">
        <input
          className="border rounded w-full px-3 py-2 text-sm"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about scenarios, metrics, or actions"
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              if (!loading) {
                sendMessage(input);
                setInput("");
              }
            }
          }}
        />
        <button
          className="bg-primary text-white px-3 py-2 rounded text-sm disabled:bg-gray-300"
          onClick={() => {
            if (!loading) {
              sendMessage(input);
              setInput("");
            }
          }}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </aside>
  );
};
