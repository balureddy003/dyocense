import type { GoalPlan } from "../lib/goalPlanner";

export function PlanPreview({ plan }: { plan: GoalPlan | null }) {
  if (!plan) return (
    <div className="bg-white border rounded-xl p-4">
      <h2 className="text-sm font-semibold mb-2">Plan preview</h2>
      <div className="text-sm text-gray-500">Your plan will appear here as you progress.</div>
    </div>
  );

  return (
    <div className="bg-white border rounded-xl p-4">
      <h2 className="text-sm font-semibold mb-2">Plan preview</h2>
      <p className="text-sm text-gray-700">{plan.summary}</p>
      <h3 className="text-sm font-semibold mt-4 mb-1">Actions</h3>
      <ul className="list-disc ml-5 text-sm text-gray-700">
        {plan.actions.map((a) => (
          <li key={a.id}>
            <span className="font-medium">{a.type}</span> on {a.entity} {a.delta ? JSON.stringify(a.delta) : ""}
          </li>
        ))}
      </ul>
      <div className="mt-4">
        <div className="text-xs text-gray-500 mb-1">Supplier map (placeholder)</div>
        <div className="h-32 bg-gray-100 border rounded-md flex items-center justify-center text-xs text-gray-500">Map coming soon</div>
      </div>
    </div>
  );
}

export default PlanPreview;
