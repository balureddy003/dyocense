import { createAssistantMessage, useChatStore } from '../store/chatStore';

export function ToolPanel() {
  const { addMessage, providerId, loading } = useChatStore();

  function pushMessage(text: string) {
    addMessage(createAssistantMessage(text));
  }

  return (
    <section className="tools">
      <h3>Kernel Tools</h3>
      <p>Trigger common Dyocense actions for the selected provider ({providerId}).</p>
      <div className="tool-buttons">
        <button type="button" disabled={loading} onClick={() => pushMessage('Forecast tool invoked (mock).')}>
          Run Forecast
        </button>
        <button type="button" disabled={loading} onClick={() => pushMessage('OptiGuide compile triggered (mock).')}>
          Compile Model
        </button>
        <button type="button" disabled={loading} onClick={() => pushMessage('Optimizer solve executed (mock).')}>
          Solve Plan
        </button>
        <button type="button" disabled={loading} onClick={() => pushMessage('Policy feedback check queued (mock).')}>
          Policy Feedback
        </button>
      </div>
    </section>
  );
}
