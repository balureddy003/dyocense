import { useEffect, useMemo, useState } from "react";
import { CalendarRange, ChevronDown, Layers, Sparkles } from "lucide-react";
import { CreatePlaybookPayload } from "../hooks/usePlaybook";
import { DataIngestionPanel } from "./DataIngestionPanel";
import { Tooltip } from "./Tooltip";
import { getArchetypes } from "../lib/api";

interface CreatePlaybookProps {
  onSubmit: (payload: CreatePlaybookPayload) => Promise<void>;
  submitting: boolean;
  projects?: Array<{ project_id: string; name: string }>;
  initialArchetypeId?: string;
}

const FALLBACK_ARCHETYPES = [
  { label: "Inventory optimization", id: "inventory_basic", description: "Balance stock levels to avoid stockouts and reduce costs" },
  { label: "Demand forecasting", id: "forecasting_basic", description: "Predict future sales to plan better" },
  { label: "Assortment planning", id: "assortment_optimizer", description: "Choose the right products for each location" },
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

export const CreatePlaybook = ({ onSubmit, submitting, projects = [], initialArchetypeId }: CreatePlaybookProps) => {
  const [archetypes, setArchetypes] = useState(FALLBACK_ARCHETYPES);
  const [selectedArchetype, setSelectedArchetype] = useState(FALLBACK_ARCHETYPES[0]);
  const [showArchetypeList, setShowArchetypeList] = useState(false);
  const [goal, setGoal] = useState("Keep enough stock on hand while minimizing storage costs.");
  const [horizon, setHorizon] = useState<number>(4);
  const [projectId, setProjectId] = useState<string>(`ui-${Date.now()}`);
  const [dataInputs, setDataInputs] = useState<Record<string, unknown>>(SAMPLE_DATA_INPUTS);

  const projectOptions = useMemo(
    () => projects.map((project) => ({ id: project.project_id, name: project.name })),
    [projects]
  );

  useEffect(() => {
    if (!projectOptions.length) return;
    if (!projectOptions.find((option) => option.id === projectId)) {
      setProjectId(projectOptions[0].id);
    }
  }, [projectOptions, projectId]);

  // Update selected archetype when initialArchetypeId changes
  useEffect(() => {
    if (initialArchetypeId && archetypes.length) {
      const matchingArchetype = archetypes.find((arch) => arch.id === initialArchetypeId);
      if (matchingArchetype) {
        setSelectedArchetype(matchingArchetype);
      }
    }
  }, [initialArchetypeId, archetypes]);

  useEffect(() => {
    let cancelled = false;
    async function loadArchetypes() {
      try {
        const response = await getArchetypes<{
          items?: Array<{ id: string; name?: string; description?: string }>;
          archetypes?: Array<{ id: string; name?: string; description?: string }>;
        }>({ items: [] });
        const collection = response.items ?? (response as any).archetypes ?? [];
        if (!cancelled && collection.length) {
          const mapped = collection.map((item: any) => ({
            id: item.id,
            label: item.name || item.id,
            description: item.description,
          }));
          setArchetypes(mapped);
          setSelectedArchetype((prev) => mapped.find((entry: any) => entry.id === prev.id) ?? mapped[0]);
        }
      } catch (err) {
        console.warn("Using fallback archetypes", err);
        if (!cancelled) {
          setArchetypes(FALLBACK_ARCHETYPES);
          setSelectedArchetype((prev) => prev ?? FALLBACK_ARCHETYPES[0]);
        }
      }
    }
    loadArchetypes();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async () => {
    const effectiveHorizon = Number.isFinite(horizon) && horizon > 0 ? horizon : 4;
    
    // Backend expects data_inputs to be Dict[str, List[Dict]] - only data arrays, no strings
    const cleanedDataInputs = Object.keys(dataInputs).reduce((acc, key) => {
      const value = dataInputs[key];
      // Only include if it's an array (filter out non-array values)
      if (Array.isArray(value)) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, unknown>);

    await onSubmit({
      goal,
      horizon: effectiveHorizon,
      archetype_id: selectedArchetype.id,
      project_id: projectId,
      data_inputs: Object.keys(cleanedDataInputs).length > 0 ? cleanedDataInputs : undefined,
    });
  };

  return (
    <div className="min-h-full bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <header className="space-y-3 mb-8">
          <div className="flex items-center gap-2 text-sm font-semibold text-primary uppercase tracking-wide">
            <Sparkles size={16} /> Create Your AI Plan
          </div>
          <h1 className="text-3xl font-semibold text-gray-900">Get smart recommendations in 3 steps</h1>
          <p className="text-gray-600 text-base max-w-2xl">
            Choose a template, upload your data, and let AI create a customized plan for your business.
          </p>
        </header>

        <div className="bg-white shadow-card rounded-3xl border border-gray-100 p-8 space-y-6">
          {/* Step 1: Choose Template */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-primary text-white text-sm font-bold">1</span>
              <h2 className="text-lg font-semibold text-gray-900">Choose a template</h2>
            </div>
            
            <div className="grid gap-3 md:grid-cols-3">
              {archetypes.map((archetype) => (
                <button
                  key={archetype.id}
                  className={`p-4 rounded-xl border-2 text-left transition ${
                    selectedArchetype.id === archetype.id
                      ? "border-primary bg-blue-50"
                      : "border-gray-200 hover:border-primary"
                  }`}
                  onClick={() => setSelectedArchetype(archetype)}
                >
                  <div className="flex items-start gap-2 mb-2">
                    <Layers size={18} className={selectedArchetype.id === archetype.id ? "text-primary" : "text-gray-400"} />
                    <h3 className="text-sm font-semibold text-gray-900">{archetype.label}</h3>
                  </div>
                  {archetype.description && (
                    <p className="text-xs text-gray-600">{archetype.description}</p>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Step 2: Set Your Goal */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-primary text-white text-sm font-bold">2</span>
              <h2 className="text-lg font-semibold text-gray-900">What do you want to achieve?</h2>
              <Tooltip content="Describe your business goal in simple terms. The AI will use this to customize recommendations." />
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                <span>Your goal</span>
                <input
                  className="px-4 py-3 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="e.g. Keep enough stock while lowering costs"
                  value={goal}
                  onChange={(event) => setGoal(event.target.value)}
                />
              </label>
              <label className="flex flex-col gap-2 text-sm text-gray-700">
                <span className="flex items-center gap-2">
                  Planning horizon
                  <Tooltip content="How many weeks ahead do you want to plan? Most businesses use 4-8 weeks." />
                </span>
                <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-gray-200 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/10">
                  <CalendarRange size={16} className="text-gray-400" />
                  <input
                    type="number"
                    min={1}
                    max={52}
                    className="flex-1 outline-none"
                    value={horizon}
                    onChange={(event) => setHorizon(Number(event.target.value))}
                  />
                  <span className="text-sm text-gray-500">weeks</span>
                </div>
              </label>
            </div>
          </div>

          {/* Step 3: Upload Data */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-primary text-white text-sm font-bold">3</span>
              <h2 className="text-lg font-semibold text-gray-900">Upload your data</h2>
              <Tooltip content="Upload CSV files with your sales, inventory, or cost data. Sample files are available in the examples folder." />
            </div>
            
            <DataIngestionPanel value={dataInputs} onChange={setDataInputs} />
          </div>

          {/* Submit Button */}
          <div className="flex justify-center pt-4">
            <button
              className="px-8 py-4 rounded-full bg-gradient-to-r from-primary to-blue-600 text-white text-base font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleSubmit}
              disabled={submitting}
            >
              <span className="flex items-center gap-2">
                <Sparkles size={18} />
                {submitting ? "Creating your plan..." : "Get AI Recommendations"}
              </span>
            </button>
          </div>
        </div>

        {/* Help Text */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Need help? Check the <code className="px-2 py-1 bg-gray-100 rounded">examples/</code> folder for sample data files.</p>
        </div>
      </div>
    </div>
  );
};
