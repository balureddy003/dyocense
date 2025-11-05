import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  TenantProfile,
  listPlans,
  listProjects,
  createProject as apiCreateProject,
  getTenantProfile,
  ProjectSummary,
  SubscriptionPlan,
  listUserApiTokens,
  createUserApiToken,
  ApiTokenSummary,
} from "../lib/api";

interface UseAccountState {
  plans: SubscriptionPlan[];
  profile: TenantProfile | null;
  projects: ProjectSummary[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  ensureLoaded: () => Promise<void>;
  createProject: (name: string, description?: string | null) => Promise<ProjectSummary | null>;
  apiTokens: ApiTokenSummary[];
  createApiToken: (name: string) => Promise<string | null>;
  refreshApiTokens: () => Promise<void>;
}

export const useAccount = (): UseAccountState => {
  const { authenticated, ready } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [profile, setProfile] = useState<TenantProfile | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [apiTokens, setApiTokens] = useState<ApiTokenSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialised, setInitialised] = useState(false);

  const loadAccount = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [planData, profileData] = await Promise.allSettled([listPlans(), getTenantProfile()]);
      if (planData.status === "fulfilled") {
        setPlans(planData.value);
      }
      if (profileData.status === "fulfilled") {
        setProfile(profileData.value);
        try {
          const projectData = await listProjects();
          setProjects(projectData);
        } catch (err) {
          console.warn("Failed to load projects", err);
        }
        try {
          const tokens = await listUserApiTokens();
          setApiTokens(tokens);
        } catch (err) {
          console.warn("Failed to load API tokens", err);
        }
      } else if (profileData.status === "rejected") {
        setProfile(null);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load subscription data.");
    } finally {
      setLoading(false);
      setInitialised(true);
    }
  }, []);

  useEffect(() => {
    // Only load account data if user is authenticated
    if (ready && authenticated) {
      loadAccount().catch((err) => {
        console.warn("Failed to load account context", err);
      });
    }
  }, [loadAccount, ready, authenticated]);

  const ensureLoaded = useCallback(async () => {
    if (!initialised && !loading) {
      await loadAccount();
    }
  }, [initialised, loading, loadAccount]);

  const handleCreateProject = useCallback(
    async (name: string, description?: string | null) => {
      try {
        const project = await apiCreateProject(name, description);
        setProjects((prev) => [...prev, project]);
        return project;
      } catch (err: any) {
        setError(err?.message || "Failed to create project.");
        return null;
      }
    },
    []
  );

  const refreshApiTokens = useCallback(async () => {
    try {
      const tokens = await listUserApiTokens();
      setApiTokens(tokens);
    } catch (err) {
      console.warn("Failed to refresh API tokens", err);
    }
  }, []);

  const handleCreateToken = useCallback(
    async (name: string) => {
      try {
        const response = await createUserApiToken(name);
        setApiTokens((prev) => [...prev, { token_id: response.token_id, name: response.name, created_at: response.created_at }]);
        return response.secret;
      } catch (err: any) {
        setError(err?.message || "Failed to create API token.");
        return null;
      }
    },
    []
  );

  return {
    plans,
    profile,
    projects,
    loading,
    error,
    refresh: loadAccount,
    ensureLoaded,
    createProject: handleCreateProject,
    apiTokens,
    createApiToken: handleCreateToken,
    refreshApiTokens,
  };
};
