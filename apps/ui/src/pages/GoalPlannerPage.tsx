import { useEffect, useMemo, useState } from "react";
import { analyzeGoal, GoalPlan, GoalRequest, refineGoal, PlanDelta } from "../lib/goalPlanner";
import { BusinessMetrics } from "../components/BusinessMetrics";
import { ChatPanel } from "../components/ChatPanel";
import { PlanPreview } from "../components/PlanPreview";
import { deletePlan, listSavedPlans, savePlanSnapshot, type SavedPlan } from "../lib/goalPlannerStore";

export const GoalPlannerPage = () => {
  type Step = "define" | "analyze" | "review" | "refine" | "save";
  const [goalText, setGoalText] = useState("Improve service level while lowering holding cost");
  const [businessUnit, setBusinessUnit] = useState("Default BU");
  const [markets, setMarkets] = useState<string[]>(["EU"]);
  const [horizonUnit, setHorizonUnit] = useState<"weeks" | "months">("weeks");
  const [horizonValue, setHorizonValue] = useState(12);
  const [costWeight, setCostWeight] = useState(0.6);
  const [serviceWeight, setServiceWeight] = useState(0.3);
  const [carbonWeight, setCarbonWeight] = useState(0.1);
  const [planning, setPlanning] = useState(false);
  const [plan, setPlan] = useState<GoalPlan | null>(null);
  const [refining, setRefining] = useState(false);
  const [step, setStep] = useState<Step>("define");
  const [variants, setVariants] = useState<GoalPlan[]>([]);
  const [history, setHistory] = useState<Array<{ label: string; time: number; snapshot: GoalPlan }>>([]);
  const [saved, setSaved] = useState<SavedPlan[]>([]);

  useEffect(() => {
    setSaved(listSavedPlans());
  }, []);

  const metricsFromPlan = (p: GoalPlan | null) => {
    if (!p) return undefined;
    const fmt = (n?: number, pct = false) => (n === undefined ? "-" : pct ? `${Math.round(n * 100)}%` : new Intl.NumberFormat().format(n));
    return [
      { label: "Projected Cost", value: `£${fmt(p.kpis.projected.cost_total)}`, change: Math.round(((p.kpis.baseline.cost_total ?? 0) - (p.kpis.projected.cost_total ?? 0)) / (p.kpis.baseline.cost_total || 1) * 100), trend: "up" as const, icon: "money" as const, status: "good" as const },
      { label: "Projected Revenue", value: `£${fmt(p.kpis.projected.revenue_total)}`, trend: "up" as const, icon: "money" as const, status: "good" as const },
      { label: "Service Level", value: fmt(p.kpis.projected.service_level, true), trend: "up" as const, icon: "service" as const, status: "good" as const },
      { label: "Carbon", value: fmt(p.kpis.projected.carbon), trend: "down" as const, icon: "risk" as const, status: "warning" as const },
    ];
  };

  const onPlan = async () => {
    setStep("analyze");
    setPlanning(true);
    try {
      const req: GoalRequest = {
        goal_text: goalText,
        business_context: { business_unit_id: businessUnit, markets },
        horizon: { unit: horizonUnit, value: horizonValue },
        objectives: { cost: costWeight, service_level: serviceWeight, carbon: carbonWeight },
      };
      const result = await analyzeGoal(req);
      // Generate A/B/C variants by invoking real refine calls with tweaked objective weights
      const deltaA: PlanDelta = {
        change_objective_weights: {
          cost: Math.min(1, (req.objectives?.cost ?? 0.5) + 0.1),
        },
      };
      const deltaB: PlanDelta = {
        change_objective_weights: {
          service_level: Math.min(1, (req.objectives?.service_level ?? 0.3) + 0.1),
        },
      };
      const deltaC: PlanDelta = {
        change_objective_weights: {
          carbon: Math.min(1, (req.objectives?.carbon ?? 0.1) + 0.1),
        },
      };

      const [vA, vB, vC] = await Promise.all([
        refineGoal(result.id, deltaA),
        refineGoal(result.id, deltaB),
        refineGoal(result.id, deltaC),
      ]);
      setVariants([vA, vB, vC]);
      setPlan(vA); // Auto-select first variant so KPIs render immediately
      setStep("review");
      setHistory([{ label: "Analyze", time: Date.now(), snapshot: result }]);
    } finally {
      setPlanning(false);
    }
  };

  const applyDelta = async (delta: PlanDelta) => {
    if (!plan) return;
    setRefining(true);
    try {
      const updated = await refineGoal(plan.id, delta);
      setPlan(updated);
      const label = describeDelta(delta);
      setHistory((h) => [...h, { label, time: Date.now(), snapshot: updated }]);
      setStep("refine");
    } finally {
      setRefining(false);
    }
  };

  const describeDelta = (d: PlanDelta) => {
    if (d.adjust_horizon) return `Adjust horizon → ${d.adjust_horizon.value} ${d.adjust_horizon.unit}`;
    if (d.change_objective_weights) return `Change weights`;
    if (d.add_constraints?.length) return `Add constraints (${d.add_constraints.length})`;
    if (d.relax_constraints?.length) return `Relax constraints (${d.relax_constraints.length})`;
    if (d.lock_action_ids?.length) return `Lock actions (${d.lock_action_ids.length})`;
    return "Refine";
  };

  const saveCurrent = () => {
    if (!plan) return;
    const savedItem = savePlanSnapshot(plan, {
      goal_text: goalText,
      business_context: { business_unit_id: businessUnit, markets },
      horizon: { unit: horizonUnit, value: horizonValue },
      objectives: { cost: costWeight, service_level: serviceWeight, carbon: carbonWeight },
    });
    setSaved((s) => [savedItem, ...s.filter((i) => i.id !== savedItem.id)]);
  };

  const restoreSaved = (item: SavedPlan) => {
    setPlan(item.plan);
    setHistory([{ label: `Restore ${item.version ?? ""}`.trim(), time: Date.now(), snapshot: item.plan }]);
    setStep("refine");
  };

  const deleteSaved = (id: string) => {
    deletePlan(id);
    setSaved((s) => s.filter((i) => i.id !== id));
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-semibold mb-2">Goal Planner</h1>
      <p className="text-sm text-gray-600 mb-4">Get smart recommendations in 3 steps: Define → Review → Refine</p>

      {/* Stepper */}
      <div className="flex items-center gap-3 mb-6 text-sm">
        {(["define","analyze","review","refine","save"] as Step[]).map((s, idx) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-semibold ${step===s?"bg-indigo-600":"bg-gray-300"}`}>{idx+1}</div>
            <div className={`${step===s?"font-medium":"text-gray-500"}`}>{s.charAt(0).toUpperCase()+s.slice(1)}</div>
            {idx<4 && <div className="w-8 h-[2px] bg-gray-200 mx-1"/>}
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <ChatPanel
            onContext={(ctx) => {
              if (ctx.goalText !== undefined) setGoalText(ctx.goalText);
              if (ctx.businessUnit !== undefined) setBusinessUnit(ctx.businessUnit);
              if (ctx.markets !== undefined) setMarkets(ctx.markets);
              if (ctx.horizon !== undefined && "value" in ctx.horizon) {
                setHorizonUnit(ctx.horizon.unit);
                setHorizonValue(ctx.horizon.value);
              }
              if (ctx.objectives?.cost !== undefined) setCostWeight(ctx.objectives.cost);
              if (ctx.objectives?.service_level !== undefined) setServiceWeight(ctx.objectives.service_level);
              if (ctx.objectives?.carbon !== undefined) setCarbonWeight(ctx.objectives.carbon);
            }}
            onPlanRequest={onPlan}
          />
          <div className="bg-white border rounded-xl p-5 space-y-4">
            {step === "analyze" && (
              <div className="text-sm text-gray-600">Planning… please wait</div>
            )}
            <div>
              <label className="text-sm font-medium">Goal</label>
              <textarea className="mt-1 w-full border rounded-md p-2 focus:outline-none" rows={3} value={goalText} onChange={(e) => setGoalText(e.target.value)} />
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Business Unit</label>
                <input className="mt-1 w-full border rounded-md p-2" value={businessUnit} onChange={(e) => setBusinessUnit(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium">Markets (comma separated)</label>
                <input className="mt-1 w-full border rounded-md p-2" value={markets.join(", ")} onChange={(e) => setMarkets(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))} />
              </div>
            </div>

            <div className="grid sm:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium">Horizon Value</label>
                <input type="number" min={1} max={60} className="mt-1 w-full border rounded-md p-2" value={horizonValue} onChange={(e) => setHorizonValue(parseInt(e.target.value || "1", 10))} />
              </div>
              <div>
                <label className="text-sm font-medium">Horizon Unit</label>
                <select className="mt-1 w-full border rounded-md p-2" value={horizonUnit} onChange={(e) => setHorizonUnit(e.target.value as any)}>
                  <option value="weeks">Weeks</option>
                  <option value="months">Months</option>
                </select>
              </div>
              <div className="flex items-end">
                <button disabled={planning} onClick={onPlan} className="w-full bg-indigo-600 text-white rounded-md px-4 py-2 disabled:opacity-50">{planning ? "Planning…" : "Plan with AI"}</button>
              </div>
            </div>

            <div className="grid sm:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium">Cost Weight</label>
                <input type="range" min={0} max={1} step={0.05} value={costWeight} onChange={(e) => setCostWeight(parseFloat(e.target.value))} className="w-full" />
                <div className="text-xs text-gray-500">{costWeight}</div>
              </div>
              <div>
                <label className="text-sm font-medium">Service Level Weight</label>
                <input type="range" min={0} max={1} step={0.05} value={serviceWeight} onChange={(e) => setServiceWeight(parseFloat(e.target.value))} className="w-full" />
                <div className="text-xs text-gray-500">{serviceWeight}</div>
              </div>
              <div>
                <label className="text-sm font-medium">Carbon Weight</label>
                <input type="range" min={0} max={1} step={0.05} value={carbonWeight} onChange={(e) => setCarbonWeight(parseFloat(e.target.value))} className="w-full" />
                <div className="text-xs text-gray-500">{carbonWeight}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <PlanPreview plan={plan} />
          {/* Variant review cards */}
          {step === "review" && variants.length > 0 && (
            <div className="bg-white border rounded-xl p-4">
              <h2 className="text-sm font-semibold mb-2">Choose a plan variant</h2>
              <div className="grid sm:grid-cols-3 gap-3">
                {variants.map((v) => (
                  <button key={v.id} onClick={() => { setPlan(v); setStep("refine"); }} className={`text-left border rounded-lg p-3 hover:shadow-sm ${plan?.id===v.id?"border-indigo-500":"border-gray-200"}`}>
                    <div className="font-medium mb-1">{v.summary}</div>
                    <div className="text-xs text-gray-500">Cost: £{new Intl.NumberFormat().format(v.kpis.projected.cost_total ?? 0)}</div>
                    <div className="text-xs text-gray-500">Service: {Math.round((v.kpis.projected.service_level ?? 0)*100)}%</div>
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="bg-white border rounded-xl p-4">
            <h2 className="text-sm font-semibold mb-3">Projected KPIs</h2>
            <BusinessMetrics metrics={metricsFromPlan(plan)} />
            <div className="mt-3 flex justify-end">
              <button
                disabled={!plan}
                onClick={saveCurrent}
                className="px-3 py-1.5 rounded-md border text-sm hover:bg-gray-50 disabled:opacity-50"
              >
                Save version
              </button>
            </div>
          </div>
          {/* Quick refinement chips */}
          <div className="bg-white border rounded-xl p-4">
            <h2 className="text-sm font-semibold mb-2">Quick refinements</h2>
            <div className="flex flex-wrap gap-2">
              <button
                disabled={!plan || refining}
                onClick={() => applyDelta({ adjust_horizon: { unit: horizonUnit, value: Math.min(60, horizonValue + 4) } })}
                className="px-3 py-1.5 rounded-full border text-sm hover:bg-gray-50 disabled:opacity-50"
                title="Extend horizon by 4"
              >
                +4 {horizonUnit}
              </button>
              <button
                disabled={!plan || refining}
                onClick={() => applyDelta({ change_objective_weights: { cost: Math.min(1, costWeight + 0.1) } })}
                className="px-3 py-1.5 rounded-full border text-sm hover:bg-gray-50 disabled:opacity-50"
                title="Increase cost focus"
              >
                Cost ↑
              </button>
              <button
                disabled={!plan || refining}
                onClick={() => applyDelta({ change_objective_weights: { service_level: Math.min(1, serviceWeight + 0.1) } })}
                className="px-3 py-1.5 rounded-full border text-sm hover:bg-gray-50 disabled:opacity-50"
                title="Increase service level focus"
              >
                Service ↑
              </button>
              <button
                disabled={!plan || refining}
                onClick={() => applyDelta({ change_objective_weights: { carbon: Math.min(1, carbonWeight + 0.1) } })}
                className="px-3 py-1.5 rounded-full border text-sm hover:bg-gray-50 disabled:opacity-50"
                title="Tighten carbon target"
              >
                Carbon ↓
              </button>
            </div>
            {refining && <div className="text-xs text-gray-500 mt-2">Applying…</div>}
          </div>
          {plan && (
            <div className="bg-white border rounded-xl p-4">
              <h2 className="text-sm font-semibold mb-2">Baseline vs Projected</h2>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-500">Cost</div>
                <div>
                  £{new Intl.NumberFormat().format(plan.kpis.baseline.cost_total ?? 0)} → <span className="font-semibold">£{new Intl.NumberFormat().format(plan.kpis.projected.cost_total ?? 0)}</span>
                </div>
                <div className="text-gray-500">Revenue</div>
                <div>
                  £{new Intl.NumberFormat().format(plan.kpis.baseline.revenue_total ?? 0)} → <span className="font-semibold">£{new Intl.NumberFormat().format(plan.kpis.projected.revenue_total ?? 0)}</span>
                </div>
                <div className="text-gray-500">Service level</div>
                <div>
                  {Math.round((plan.kpis.baseline.service_level ?? 0) * 100)}% → <span className="font-semibold">{Math.round((plan.kpis.projected.service_level ?? 0) * 100)}%</span>
                </div>
                <div className="text-gray-500">Carbon</div>
                <div>
                  {Math.round(plan.kpis.baseline.carbon ?? 0)} → <span className="font-semibold">{Math.round(plan.kpis.projected.carbon ?? 0)}</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Refinement history */}
          {history.length > 0 && (
            <div className="bg-white border rounded-xl p-4">
              <h2 className="text-sm font-semibold mb-2">Refinement history</h2>
              <ul className="text-sm space-y-2">
                {history.map((h, idx) => (
                  <li key={idx} className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{h.label}</div>
                      <div className="text-xs text-gray-500">{new Date(h.time).toLocaleString()}</div>
                    </div>
                    <button
                      className="px-2 py-1 border rounded-md text-xs hover:bg-gray-50"
                      onClick={() => setPlan(h.snapshot)}
                    >
                      View
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {/* Save & Run */}
          {plan && (
            <div className="bg-white border rounded-xl p-4">
              <h2 className="text-sm font-semibold mb-2">Save & Run</h2>
              <div className="flex gap-2">
                <button onClick={saveCurrent} className="px-3 py-1.5 rounded-md border text-sm hover:bg-gray-50">Save</button>
                <button disabled className="px-3 py-1.5 rounded-md border text-sm bg-gray-100 text-gray-500" title="Coming soon">Run Scenario</button>
              </div>
            </div>
          )}
          {/* Saved versions */}
          <div className="bg-white border rounded-xl p-4">
            <h2 className="text-sm font-semibold mb-2">Saved versions (local)</h2>
            {saved.length === 0 ? (
              <div className="text-sm text-gray-500">No saved versions yet.</div>
            ) : (
              <ul className="text-sm space-y-2">
                {saved.map((s) => (
                  <li key={`${s.id}-${s.savedAt}`} className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{s.version ?? "draft"} • {s.summary}</div>
                      <div className="text-xs text-gray-500">{new Date(s.savedAt).toLocaleString()} • {s.meta.horizon ?? ""}</div>
                    </div>
                    <div className="flex gap-2">
                      <button className="px-2 py-1 border rounded-md text-xs hover:bg-gray-50" onClick={() => restoreSaved(s)}>Restore</button>
                      <button className="px-2 py-1 border rounded-md text-xs hover:bg-red-50 text-red-600" onClick={() => deleteSaved(s.id)}>Delete</button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoalPlannerPage;
