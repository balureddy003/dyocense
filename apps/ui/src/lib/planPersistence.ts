import { SavedPlan } from "../components/PlanSelector";

const STORAGE_KEY_PREFIX = "dyocense-plans";

function scopedKey(tenantId: string, projectId?: string | null): string {
  return `${STORAGE_KEY_PREFIX}-${tenantId}${projectId ? `-${projectId}` : ""}`;
}

export function getSavedPlans(tenantId: string, projectId?: string | null): SavedPlan[] {
  try {
    // Primary: scoped to tenant + project
    const key = scopedKey(tenantId, projectId);
    const stored = localStorage.getItem(key);
    if (stored) {
      return JSON.parse(stored);
    }

    // Backward-compat: if no project-scoped plans are found, try legacy unscoped key (tenant only)
    // This covers older saves made before projects were introduced.
    const legacyKey = scopedKey(tenantId, undefined);
    const legacyStored = localStorage.getItem(legacyKey);
    if (legacyStored) {
      const legacyPlans: SavedPlan[] = JSON.parse(legacyStored);

      // If a projectId is provided now, migrate legacy plans into the scoped key for future fast loads
      // without mutating the original set unintentionally.
      if (projectId) {
        const targetProjectId = projectId ?? undefined;
        const migrated = legacyPlans.map((p) => ({ ...p, projectId: p.projectId ?? targetProjectId }));
        localStorage.setItem(key, JSON.stringify(migrated));
        return migrated;
      }

      return legacyPlans;
    }

    // Optional resilience: scan for any project-scoped keys for this tenant and merge
    // Useful if projectId is unknown or missing but plans exist under other projects.
    try {
      const prefix = `${STORAGE_KEY_PREFIX}-${tenantId}-`;
      const aggregated: SavedPlan[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (!k || !k.startsWith(prefix)) continue;
        const raw = localStorage.getItem(k);
        if (!raw) continue;
        try {
          const parsed: SavedPlan[] = JSON.parse(raw);
          aggregated.push(...parsed);
        } catch {
          // ignore bad entries and continue
        }
      }
      if (aggregated.length > 0) return aggregated;
    } catch {
      // ignore scanning errors
    }

    return [];
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
