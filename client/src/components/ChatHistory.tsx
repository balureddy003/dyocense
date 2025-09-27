import { ChatMessage } from '../store/chatStore';

interface ChatHistoryProps {
  messages: ChatMessage[];
}

export function ChatHistory({ messages }: ChatHistoryProps) {
  return (
    <section className="conversation">
      {messages.map((message) => (
        <article key={message.id} className={`message ${message.role}`}>
          <header>
            <span>{message.role === 'assistant' ? 'Assistant' : message.role === 'user' ? 'You' : 'System'}</span>
            <time>
              {message.createdAt instanceof Date
                ? message.createdAt.toLocaleTimeString()
                : new Date(message.createdAt).toLocaleTimeString()}
            </time>
          </header>
          <p>{message.text}</p>
        </article>
      ))}
    </section>
  );
}
