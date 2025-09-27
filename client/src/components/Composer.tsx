import { FormEvent, useState } from 'react';
import { createAssistantMessage, createUserMessage, useChatStore } from '../store/chatStore';
import { postPlanChat } from '../services/api';

interface ComposerProps {
  context: string;
  onContextChange: (context: string) => void;
  onPlanningComplete?: () => void;
}

export function Composer({ context, onContextChange, onPlanningComplete }: ComposerProps) {
  const { addMessage, providerId, loading, setLoading } = useChatStore();
  const [goal, setGoal] = useState('Reduce inventory cost by 5% without lowering service level.');

  const disabled = goal.trim().length === 0 || loading;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled) return;

    const userMessage = createUserMessage(goal);
    addMessage(userMessage);
    setLoading(true);

    try {
      const planResponse = await postPlanChat(goal, context, providerId);
      addMessage(createAssistantMessage(planResponse.summary));
      if (planResponse.llm_response) {
        addMessage(createAssistantMessage(planResponse.llm_response));
      }
      if (onPlanningComplete) {
        onPlanningComplete();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unexpected error contacting Dyocense API';
      addMessage(createAssistantMessage(message));
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="composer">
      <form onSubmit={handleSubmit}>
        <label>
          Desired outcome
          <textarea value={goal} onChange={(event) => setGoal(event.target.value)} rows={4} />
        </label>
        <label>
          Context / constraints
          <textarea value={context} onChange={(event) => onContextChange(event.target.value)} rows={3} />
        </label>
        <button type="submit" disabled={disabled}>
          {loading ? 'Submitting…' : 'Plan with Dyocense'}
        </button>
      </form>
    </aside>
  );
}
