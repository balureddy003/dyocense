import { SavedPlan } from "../components/PlanSelector";

const STORAGE_KEY_PREFIX = "dyocense-plans";

function scopedKey(tenantId: string, projectId?: string | null): string {
  return `${STORAGE_KEY_PREFIX}-${tenantId}${projectId ? `-${projectId}` : ""}`;
}

export function getSavedPlans(tenantId: string, projectId?: string | null): SavedPlan[] {
  try {
    const key = scopedKey(tenantId, projectId);
    const stored = localStorage.getItem(key);
    if (!stored) return [];
    return JSON.parse(stored);
  } catch (error) {
    console.error("Error loading saved plans:", error);
    return [];
  }
}

export function savePlan(tenantId: string, plan: SavedPlan, projectId?: string | null): void {
  try {
    const key = scopedKey(tenantId, projectId ?? plan.projectId);
    const plans = getSavedPlans(tenantId, projectId ?? plan.projectId);
    
    // Check if plan exists, update or add
    const existingIndex = plans.findIndex((p) => p.id === plan.id);
    if (existingIndex >= 0) {
      plans[existingIndex] = { ...plan, updatedAt: new Date().toISOString() };
    } else {
      plans.push(plan);
    }
    
    localStorage.setItem(key, JSON.stringify(plans));
  } catch (error) {
    console.error("Error saving plan:", error);
  }
}

export function deletePlan(tenantId: string, planId: string, projectId?: string | null): void {
  try {
    const key = scopedKey(tenantId, projectId);
    const plans = getSavedPlans(tenantId, projectId);
    const filtered = plans.filter((p) => p.id !== planId);
    localStorage.setItem(key, JSON.stringify(filtered));
  } catch (error) {
    console.error("Error deleting plan:", error);
  }
}

export function getActivePlanId(tenantId: string, projectId?: string | null): string | null {
  try {
    const key = `${STORAGE_KEY_PREFIX}-active-${tenantId}${projectId ? `-${projectId}` : ""}`;
    return localStorage.getItem(key);
  } catch (error) {
    console.error("Error getting active plan:", error);
    return null;
  }
}

export function setActivePlanId(tenantId: string, planId: string, projectId?: string | null): void {
  try {
    const key = `${STORAGE_KEY_PREFIX}-active-${tenantId}${projectId ? `-${projectId}` : ""}`;
    localStorage.setItem(key, planId);
  } catch (error) {
    console.error("Error setting active plan:", error);
  }
}

export function clearActivePlan(tenantId: string, projectId?: string | null): void {
  try {
    const key = `${STORAGE_KEY_PREFIX}-active-${tenantId}${projectId ? `-${projectId}` : ""}`;
    localStorage.removeItem(key);
  } catch (error) {
    console.error("Error clearing active plan:", error);
  }
}
