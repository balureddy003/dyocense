import { useState } from "react";
import {
  CalendarRange,
  ChevronDown,
  ChevronUp,
  Database,
  Layers,
  Settings2,
  Sparkles,
} from "lucide-react";
import { CreatePlaybookPayload } from "../hooks/usePlaybook";

interface CreatePlaybookProps {
  onSubmit: (payload: CreatePlaybookPayload) => Promise<void>;
  submitting: boolean;
}

const archetypeOptions = [
  { label: "Inventory optimization", id: "inventory_basic" },
  { label: "Demand forecasting", id: "forecasting_basic" },
  { label: "Assortment rationalization", id: "assortment_optimizer" },
];

const quickStarts = [
  {
    title: "Holiday surge readiness",
    description: "Model peak demand, supplier flex, and store allocation in one run.",
    archetype: "inventory_basic",
  },
  {
    title: "Express lane pilot rollout",
    description: "Balance safety stock and cycle time for high-velocity SKUs across DCs.",
    archetype: "inventory_basic",
  },
  {
    title: "Markdown recovery plan",
    description: "Blend demand forecasts with pricing levers to clear overstock.",
    archetype: "markdown_planner",
  },
];

const preferenceGroups = [
  {
    label: "Decision scope",
    options: ["Network-wide", "Regional", "Store cluster", "Supplier-specific"],
  },
  {
    label: "Primary KPI",
    options: ["Holding cost", "Service level", "Margin", "Turns"],
  },
  {
    label: "Planning cadence",
    options: ["Weekly", "Bi-weekly", "Monthly", "Ad hoc"],
  },
];

const SAMPLE_DATA_INPUTS = {
  demand: [
    { sku: "widget", quantity: 120 },
    { sku: "gadget", quantity: 95 },
  ],
  holding_cost: [
    { sku: "widget", cost: 2.5 },
    { sku: "gadget", cost: 1.75 },
  ],
};

export const CreatePlaybook = ({ onSubmit, submitting }: CreatePlaybookProps) => {
  const [preferencesOpen, setPreferencesOpen] = useState(true);
  const [selectedArchetype, setSelectedArchetype] = useState(archetypeOptions[0]);
  const [showArchetypeList, setShowArchetypeList] = useState(false);
  const [goal, setGoal] = useState("Reduce holding cost while maintaining 95% service level.");
  const [horizon, setHorizon] = useState<number>(4);
  const [projectId, setProjectId] = useState<string>(`ui-${Date.now()}`);
  const [dataSource, setDataSource] = useState<string>("ERP snapshot, weekly feed");

  const handleSubmit = async (archetypeOverride?: string) => {
    const archetypeId = archetypeOverride ?? selectedArchetype.id;
    const effectiveHorizon = Number.isFinite(horizon) && horizon > 0 ? horizon : 4;
    await onSubmit({
      goal,
      horizon: effectiveHorizon,
      archetype_id: archetypeId,
      project_id: projectId,
      data_inputs: {
        source: dataSource,
        ...SAMPLE_DATA_INPUTS,
      },
    });
  };

  return (
    <div className="min-h-full bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col gap-10">
        <header className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-primary uppercase tracking-wide">
            <Sparkles size={16} /> Dyocense Playbook Builder
          </div>
          <h1 className="text-3xl font-semibold text-gray-900">Launch a new scenario in minutes.</h1>
          <p className="text-gray-600 text-base max-w-3xl">
            Describe the business objective, choose an archetype, and Dyocense will compile data, simulate what-ifs,
            and deliver a sharing-ready playbook.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px] items-start">
          <section className="bg-white shadow-card rounded-3xl border border-gray-100 p-6 space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Goal statement
                <input
                  className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="e.g. Reduce holding cost while keeping 95% service level"
                  value={goal}
                  onChange={(event) => setGoal(event.target.value)}
                />
              </label>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Planning horizon (weeks)
                <div className="flex items-center gap-2">
                  <CalendarRange size={16} className="text-gray-400" />
                  <input
                    type="number"
                    min={1}
                    className="flex-1 px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                    value={horizon}
                    onChange={(event) => setHorizon(Number(event.target.value))}
                  />
                </div>
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Archetype
                <div className="relative">
                  <button
                    type="button"
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-gray-200 hover:border-primary"
                    onClick={() => setShowArchetypeList((prev) => !prev)}
                  >
                    <span className="flex items-center gap-2">
                      <Layers size={16} className="text-gray-400" /> {selectedArchetype.label}
                    </span>
                    <ChevronDown size={16} className="text-gray-400" />
                  </button>
                  {showArchetypeList && (
                    <div className="absolute z-10 mt-2 w-full rounded-xl border border-gray-200 bg-white shadow-lg">
                      {archetypeOptions.map((option) => (
                        <button
                          key={option.id}
                          className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 ${
                            option.id === selectedArchetype.id ? "text-primary" : "text-gray-700"
                          }`}
                          onClick={() => {
                            setSelectedArchetype(option);
                            setShowArchetypeList(false);
                          }}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </label>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                Data source (optional)
                <div className="flex items-center gap-2">
                  <Database size={16} className="text-gray-400" />
                  <input
                    className="flex-1 px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                    value={dataSource}
                    onChange={(event) => setDataSource(event.target.value)}
                  />
                </div>
              </label>
            </div>

            <label className="flex flex-col gap-2 text-sm text-gray-700">
              Project identifier
              <input
                className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
              />
            </label>

            <div className="border border-gray-100 rounded-2xl">
              <button
                type="button"
                className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-gray-800"
                onClick={() => setPreferencesOpen((prev) => !prev)}
              >
                <span className="flex items-center gap-2">
                  <Settings2 size={16} className="text-primary" /> Preferences
                </span>
                {preferencesOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              {preferencesOpen && (
                <div className="px-4 pb-4 pt-2 space-y-4">
                  {preferenceGroups.map((group) => (
                    <div key={group.label} className="space-y-2">
                      <p className="text-xs font-semibold uppercase text-gray-500">{group.label}</p>
                      <div className="flex flex-wrap gap-2">
                        {group.options.map((option) => (
                          <button
                            key={option}
                            className="px-3 py-1.5 rounded-full border border-gray-200 text-sm text-gray-700 hover:border-primary"
                          >
                            {option}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                  <textarea
                    className="w-full min-h-[100px] rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-primary focus:ring-2 focus:ring-primary/10"
                    placeholder="Note any constraints, change approvals, or stakeholder needs"
                  />
                  <div className="flex justify-end gap-3 text-sm">
                    <button className="px-4 py-2 rounded-lg border border-gray-200 text-gray-500">Clear</button>
                    <button className="px-4 py-2 rounded-lg bg-primary text-white font-semibold">Confirm</button>
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                className="px-5 py-3 rounded-full bg-primary text-white text-sm font-semibold shadow-card disabled:bg-blue-200"
                onClick={() => handleSubmit()}
                disabled={submitting}
              >
                <span className="flex items-center gap-2">
                  <Sparkles size={16} /> Plan with Copilot
                </span>
              </button>
            </div>
          </section>

          <aside className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Suggested playbooks</h3>
            <div className="space-y-3">
              {quickStarts.map((item) => (
                <article key={item.title} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm space-y-2">
                  <p className="text-xs text-primary uppercase tracking-wide">{item.archetype}</p>
                  <h4 className="text-sm font-semibold text-gray-900">{item.title}</h4>
                  <p className="text-sm text-gray-600">{item.description}</p>
                  <button
                    className="text-sm text-primary font-medium"
                    onClick={() => handleSubmit(item.archetype)}
                    disabled={submitting}
                  >
                    Use template
                  </button>
                </article>
              ))}
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};
