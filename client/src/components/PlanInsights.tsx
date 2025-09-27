import { useEffect, useState } from 'react';
import { fetchPlans, PlanListItem } from '../services/api';
import { useChatStore, createAssistantMessage } from '../store/chatStore';

interface PlanInsightsProps {
  refreshSignal: number;
}

export function PlanInsights({ refreshSignal }: PlanInsightsProps) {
  const [plans, setPlans] = useState<PlanListItem[]>([]);
  const { addMessage } = useChatStore();

  useEffect(() => {
    fetchPlans()
      .then(setPlans)
      .catch(() => setPlans([]));
  }, [refreshSignal]);

  function handleDiagnose(plan: PlanListItem) {
    addMessage(
      createAssistantMessage(
        `Diagnostics for plan ${plan.plan_id}: evidence ${plan.evidence_ref}. (Detailed insights TBD as kernel exposes diagnostics API.)`
      )
    );
  }

  return (
    <section className="insights">
      <header>
        <h3>Recent Plans</h3>
        <p>Snapshot of runs for the active tenant. Select a plan to request diagnostics.</p>
      </header>
      <ul>
        {plans.map((plan) => (
          <li key={plan.plan_id}>
            <div>
              <strong>{plan.plan_id}</strong>
              <span>{new Date(plan.created_at).toLocaleString()}</span>
              {plan.goal_id && <span className="pill">goal: {plan.goal_id}</span>}
              {plan.variant && <span className="pill">variant: {plan.variant}</span>}
            </div>
            <button type="button" onClick={() => handleDiagnose(plan)}>
              Diagnose
            </button>
          </li>
        ))}
        {plans.length === 0 && <li className="empty">No plans yet. Submit a goal to generate diagnostics.</li>}
      </ul>
    </section>
  );
}
