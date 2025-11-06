// Local persistence for Goal Planner plans and history (UI-only fallback)

import type { GoalPlan, GoalRequest } from "./goalPlanner";

export type SavedPlan = {
  id: string; // plan id
  version?: string;
  summary: string;
  savedAt: number; // epoch ms
  meta: {
    goalText: string;
    businessUnit?: string;
    markets?: string[];
    horizon?: string; // e.g. "12 weeks"
  };
  plan: GoalPlan;
};

const STORAGE_KEY = "goalPlanner:plans";

function readAll(): SavedPlan[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedPlan[]) : [];
  } catch {
    return [];
  }
}

function writeAll(items: SavedPlan[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // no-op
  }
}

export function savePlanSnapshot(plan: GoalPlan, req?: GoalRequest): SavedPlan {
  const items = readAll();
  const saved: SavedPlan = {
    id: plan.id,
    version: plan.version,
    summary: plan.summary,
    savedAt: Date.now(),
    meta: {
      goalText: req?.goal_text ?? "",
      businessUnit: req?.business_context?.business_unit_id,
      markets: req?.business_context?.markets,
      horizon: (() => {
        if (!req?.horizon) return undefined;
        if ("value" in req.horizon) return `${req.horizon.value} ${req.horizon.unit}`;
        return `${req.horizon.start_date} → ${req.horizon.end_date}`;
      })(),
    },
    plan,
  };
  // If same id exists, replace; else append
  const idx = items.findIndex((i) => i.id === plan.id);
  if (idx >= 0) items[idx] = saved; else items.push(saved);
  // Keep latest 20
  items.sort((a, b) => b.savedAt - a.savedAt);
  writeAll(items.slice(0, 20));
  return saved;
}

export function listSavedPlans(): SavedPlan[] {
  return readAll().sort((a, b) => b.savedAt - a.savedAt);
}

export function loadPlan(id: string): SavedPlan | undefined {
  return readAll().find((p) => p.id === id);
}

export function deletePlan(id: string) {
  const remaining = readAll().filter((p) => p.id !== id);
  writeAll(remaining);
}
