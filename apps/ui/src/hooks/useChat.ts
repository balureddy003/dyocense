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
  const history: ChatMessage[] = [...messages, { role: "user", content: msg } as ChatMessage];
  setMessages(history);
    setLoading(true);
    try {
      const response = await postChat<{ reply: string }>({ messages: history } as any, undefined as any);
      setMessages((m) => [...m, { role: "assistant", content: response.reply }]);
    } catch (error) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: "Sorry, I couldn't process that right now. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, sendMessage, loading };
}
