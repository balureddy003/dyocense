import { useRef, useState } from "react";
// Minimal context type retained for prop compatibility; no client stub usage.
type AgentContext = Record<string, unknown>;
import { useChat } from "../hooks/useChat";

export type ChatPanelProps = {
  onContext: (ctx: AgentContext) => void;
  onPlanRequest: () => void;
};

export function ChatPanel({ onContext, onPlanRequest }: ChatPanelProps) {
  // Keep prop shape but stop using client stubs; use real chat API.
  const { messages, sendMessage, loading } = useChat();
  const [input, setInput] = useState("");
  const fileRef = useRef<HTMLInputElement | null>(null);

  const send = async (text: string, files?: FileList | null) => {
    if (!text && (!files || files.length === 0)) return;
    await sendMessage(text);
    setInput("");
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="bg-white border rounded-xl p-4">
      <h2 className="text-sm font-semibold mb-2">Assistant</h2>
      <div className="h-60 overflow-y-auto border rounded-md p-3 bg-gray-50 text-sm space-y-2">
        {messages.map((m, idx) => (
          <div key={idx} className={m.role === "assistant" ? "text-gray-800" : "text-gray-700"}>
            <span className="font-medium">{m.role === "assistant" ? "Assistant" : "You"}:</span> {m.content}
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-2">
        <input
          className="flex-1 border rounded-md p-2 text-sm"
          placeholder="Type your answer…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
        />
        <input ref={fileRef} type="file" className="hidden" multiple onChange={(e) => send(input, e.target.files)} />
        <button className="px-3 py-1.5 rounded-md border text-sm hover:bg-gray-50" onClick={() => fileRef.current?.click()}>Attach</button>
        <button disabled={loading} className="px-3 py-1.5 rounded-md bg-indigo-600 text-white text-sm disabled:opacity-50" onClick={() => send(input)}>
          {loading ? "Thinking…" : "Send"}
        </button>
      </div>
      {/* Removed client-side context extraction to avoid stubs. */}
      <div className="mt-3 flex justify-end">
        <button
          onClick={onPlanRequest}
          className="px-3 py-1.5 rounded-md border text-sm hover:bg-gray-50 disabled:opacity-50"
          title="Generate plan variants"
          disabled
        >
          Analyze with AI
        </button>
      </div>
    </div>
  );
}

export default ChatPanel;
