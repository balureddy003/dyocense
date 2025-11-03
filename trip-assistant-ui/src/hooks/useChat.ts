import { useState } from "react";
import { postChat } from "../lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hi! I can help you shape inventory scenarios, compare what-ifs, or summarize outcomes.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (msg: string) => {
    if (!msg.trim()) return;
    const history = [...messages, { role: "user", content: msg }];
    setMessages(history);
    setLoading(true);
    try {
      const response = await postChat<{ reply: string }>(
        { messages: history },
        { reply: "Here's a mock response while chat is being wired up." }
      );
      setMessages((m) => [...m, { role: "assistant", content: response.reply }]);
    } catch (error) {
      console.warn("Falling back to simulated chat", error);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: "Here's a quick idea—try running the 'Demand spike scenario' to see how safety stock shifts.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, sendMessage, loading };
}
