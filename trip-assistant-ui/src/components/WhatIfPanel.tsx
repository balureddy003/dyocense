import { WhatIfScenario } from "../hooks/useItinerary";
import { BarChart3 } from "lucide-react";

export const WhatIfPanel = ({ scenarios }: { scenarios: WhatIfScenario[] }) => {
  if (!scenarios.length) {
    return (
      <section className="bg-white rounded-xl shadow-card p-5">
        <h3 className="text-lg font-semibold text-gray-900">What-if analysis</h3>
        <p className="text-sm text-gray-600 mt-2">
          Run a scenario to compare how key KPIs change under different assumptions.
        </p>
      </section>
    );
  }
  return (
    <section className="bg-white rounded-xl shadow-card p-5 space-y-4">
      <header className="flex items-center gap-2">
        <BarChart3 size={18} className="text-primary" />
        <h3 className="text-lg font-semibold text-gray-900">What-if analysis</h3>
      </header>
      <p className="text-sm text-gray-600">
        Explore how the plan adapts when demand, supply, or cost drivers change.
      </p>
      <ul className="grid gap-4 md:grid-cols-2">
        {scenarios.map((scenario) => (
          <li key={scenario.title} className="border border-gray-100 rounded-lg p-4 bg-gray-50 space-y-3">
            <h4 className="font-medium text-gray-800">{scenario.title}</h4>
            <p className="text-sm text-gray-600">{scenario.summary}</p>
            <dl className="text-xs text-gray-500 grid grid-cols-2 gap-2">
              {Object.entries(scenario.delta).map(([k, v]) => (
                <div key={k}>
                  <dt className="uppercase tracking-wide text-gray-400">{k}</dt>
                  <dd className="text-gray-700 font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
    </section>
  );
};
