
import { ApiOptions } from "./config";

export type ObjectiveWeights = {
  cost?: number;
  revenue?: number;
  service_level?: number;
  carbon?: number;
};

export type GoalRequest = {
  tenant_id?: string;
  project_id?: string;
  business_context?: {
    business_unit_id?: string;
    markets?: string[];
    products?: string[];
  };
  goal_text: string;
  horizon:
    | { unit: "weeks" | "months"; value: number }
    | { start_date: string; end_date: string };
  objectives?: ObjectiveWeights;
  policies?: string[];
  constraints?: Array<{ name: string; type: string; value: any }>;
};

export type KPIBlock = {
  cost_total?: number;
  revenue_total?: number;
  service_level?: number;
  carbon?: number;
};

export type GoalPlan = {
  id: string;
  summary: string;
  version?: string;
  kpis: { baseline: KPIBlock; projected: KPIBlock };
  actions: Array<{ id: string; type: string; entity: string; delta?: any; rationale?: string }>;
  schedule?: Array<Record<string, any>>;
};

export type PlanDelta = {
  adjust_horizon?: { unit: "weeks" | "months"; value: number };
  change_objective_weights?: ObjectiveWeights;
  add_constraints?: Array<{ name: string; type: string; value: any }>;
  remove_constraint_names?: string[];
  relax_constraints?: Array<{ name: string; type: string; value: any }>;
  lock_action_ids?: string[];
  scenario_tags?: string[];
};

async function fetchJSON<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { API_BASE_URL, DEFAULT_HEADERS, getAuthHeaders } = await import("./config");
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
  const resp = await fetch(url, {
    ...options,
    headers: { ...DEFAULT_HEADERS, ...getAuthHeaders(), ...(options.headers || {}) },
  });
  if (!resp.ok) throw new Error(`Request failed ${resp.status}`);
  if (resp.status === 204) return {} as T;
  return (await resp.json()) as T;
}

export async function analyzeGoal(req: GoalRequest): Promise<GoalPlan> {
  return fetchJSON<GoalPlan>("/v1/goal-planner/analyze", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function refineGoal(planId: string, delta: PlanDelta): Promise<GoalPlan> {
  return fetchJSON<GoalPlan>(`/v1/goal-planner/refine/${planId}`, {
    method: "POST",
    body: JSON.stringify(delta),
  });
}
