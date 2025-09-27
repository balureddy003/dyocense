import { useCallback, useState } from 'react';
import { ChatHistory } from '../components/ChatHistory';
import { Composer } from '../components/Composer';
import { PlanInsights } from '../components/PlanInsights';
import { ProviderSwitcher } from '../components/ProviderSwitcher';
import { ToolPanel } from '../components/ToolPanel';
import { Provider } from '../services/api';
import { useChatStore } from '../store/chatStore';

export function ChatPage() {
  const { messages } = useChatStore();
  const [context, setContext] = useState('SKU1, SKU2 across Q3 2025');
  const [providers, setProviders] = useState<Provider[]>([]);
  const [refreshSignal, setRefreshSignal] = useState(0);
  const refreshPlans = useCallback(() => setRefreshSignal((value) => value + 1), []);

  return (
    <div className="layout">
      <header>
        <h1>Dyocense Planning Copilot</h1>
        <p>LibreChat-inspired interface for orchestrating the Dyocense kernel via conversational commands.</p>
      </header>

      <main>
        <div className="left-column">
          <ChatHistory messages={messages} />
          <ToolPanel />
        </div>
        <div className="right-column">
          <ProviderSwitcher providers={providers} setProviders={setProviders} />
          <PlanInsights refreshSignal={refreshSignal} />
          <Composer context={context} onContextChange={setContext} onPlanningComplete={refreshPlans} />
        </div>
      </main>

      <footer>
        <small>Kernel :8080 • API :8000 • Client :3000 • Powered by Dyocense + LLM router</small>
      </footer>
    </div>
  );
}
