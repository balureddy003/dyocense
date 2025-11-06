import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Keycloak, { KeycloakConfig, KeycloakInstance } from "keycloak-js";
import { getKeycloakConfig, isKeycloakConfigured } from "../lib/auth";
import { setAuthToken } from "../lib/config";
import { getTenantProfile, loginUser, registerUser, fetchUserProfile } from "../lib/api";

export interface AuthUser {
  id: string;
  fullName: string;
  email?: string;
  username?: string;
  tenantId?: string;
}

export interface BusinessProfile {
  companyName: string;
  industry: string;
  teamSize?: string;
  primaryGoal?: string;
  timezone?: string;
}

interface AuthContextValue {
  ready: boolean;
  authenticated: boolean;
  user: AuthUser | null;
  token: string | null;
  profile: BusinessProfile | null;
  loadingProfile: boolean;
  login: (redirectTo?: string) => Promise<void>;
  loginWithToken: (options: TokenLoginOptions) => Promise<void>;
  loginWithCredentials: (tenantId: string, email: string, password: string) => Promise<void>;
  registerUserAccount: (tenantId: string, email: string, fullName: string, password: string, temporaryPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (profile: BusinessProfile) => Promise<void>;
  refreshProfile: () => Promise<void>;
  keycloak?: KeycloakInstance;
  supportsKeycloak: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const PROFILE_STORAGE_PREFIX = "dyocense-profile";

const buildProfileKey = (userId: string) => `${PROFILE_STORAGE_PREFIX}:${userId}`;

const readStoredProfile = (userId: string): BusinessProfile | null => {
  if (!userId) return null;
  try {
    const raw = window.localStorage.getItem(buildProfileKey(userId));
    if (!raw) return null;
    return JSON.parse(raw) as BusinessProfile;
  } catch (error) {
    console.warn("Failed to read stored profile", error);
    return null;
  }
};

const persistProfile = (userId: string, profile: BusinessProfile) => {
  try {
    window.localStorage.setItem(buildProfileKey(userId), JSON.stringify(profile));
  } catch (error) {
    console.warn("Failed to persist profile", error);
  }
};

const clearStoredProfile = (userId: string) => {
  try {
    window.localStorage.removeItem(buildProfileKey(userId));
  } catch (error) {
    console.warn("Failed to clear profile", error);
  }
};

interface AuthProviderProps {
  children: ReactNode;
}

interface TokenLoginOptions {
  apiToken: string;
  tenantId?: string;
  displayName?: string;
  email?: string;
  remember?: boolean;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const supportsKeycloak = isKeycloakConfigured();
  const keycloakConfig = useMemo<KeycloakConfig | null>(() => {
    if (!supportsKeycloak) return null;
    const env = getKeycloakConfig();
    return {
      url: env.url!,
      realm: env.realm!,
      clientId: env.clientId!,
    };
  }, [supportsKeycloak]);

  const keycloakRef = useRef<KeycloakInstance | null>(null);

  const [ready, setReady] = useState(!supportsKeycloak);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<BusinessProfile | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [hydratedFromStorage, setHydratedFromStorage] = useState(false);

  useEffect(() => {
    if (!supportsKeycloak) {
      setReady(true);
      return;
    }

    if (keycloakConfig) {
      const instance = new Keycloak(keycloakConfig);
      keycloakRef.current = instance;

      instance
        .init({
          onLoad: "check-sso",
          pkceMethod: "S256",
          silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
        })
        .then((auth) => {
          setAuthenticated(auth);
          if (auth) {
            const parsed = instance.tokenParsed;
            const newUser: AuthUser = {
              id: parsed?.sub || parsed?.email || "",
              fullName: parsed?.name || parsed?.preferred_username || "Dyocense User",
              email: parsed?.email,
              username: parsed?.preferred_username,
            };
            setUser(newUser);
            setToken(instance.token ?? null);
            setAuthToken(instance.token ?? null);
            setProfile(readStoredProfile(newUser.id));
          } else {
            setUser(null);
            setToken(null);
            setAuthToken(null);
            setProfile(null);
          }
        })
        .catch((error) => {
          console.error("Keycloak init failed", error);
        })
        .finally(() => {
          setReady(true);
        });

      instance.onTokenExpired = () => {
        instance
          .updateToken(30)
          .then((refreshed) => {
            if (refreshed) {
              setToken(instance.token ?? null);
              setAuthToken(instance.token ?? null);
            }
          })
          .catch((error) => {
            console.warn("Failed to refresh token", error);
            setAuthenticated(false);
            setUser(null);
            setToken(null);
            setAuthToken(null);
            setProfile(null);
          });
      };
    }
  }, [keycloakConfig, supportsKeycloak]);


  const loginWithToken = useCallback(
    async ({ apiToken, tenantId, displayName, email, remember = true }: TokenLoginOptions) => {
      const trimmedToken = apiToken.trim();
      if (!trimmedToken) {
        throw new Error("API token is required.");
      }

      const provisionalUser: AuthUser = {
        id: tenantId?.trim() || "manual-tenant",
        fullName: displayName?.trim() || tenantId?.trim() || "Dyocense Customer",
        email: email?.trim() || undefined,
        username: tenantId?.trim() || "customer",
      };

      setAuthToken(trimmedToken);
      setToken(trimmedToken);
      setAuthenticated(true);
  setUser(provisionalUser);

      try {
        const tenantProfile = await getTenantProfile();
        const enrichedUser: AuthUser = {
          id: tenantProfile.tenant_id,
          fullName: tenantProfile.name || provisionalUser.fullName,
          email: tenantProfile.owner_email || provisionalUser.email,
          username: tenantProfile.tenant_id,
        };
        setUser(enrichedUser);
        setProfile({
          companyName: tenantProfile.name || "",
          industry: "",
          teamSize: String(tenantProfile.usage?.members ?? ""),
          primaryGoal: "",
          timezone: "",
        });
        try {
          const profile = await fetchUserProfile();
          setUser({
            id: profile.user_id,
            fullName: profile.full_name,
            email: profile.email,
            username: profile.email,
          });
        } catch (userErr) {
          console.warn("User profile unavailable for API token", userErr);
        }
      } catch (err: any) {
        console.warn("Failed to load tenant profile", err);
        if (err?.message?.includes("401") || err?.message?.includes("403")) {
          setAuthenticated(false);
          setUser(null);
          setToken(null);
          setAuthToken(null);
          setProfile(null);
          throw new Error("Invalid or expired API token.");
        }
      }

      if (remember && typeof window !== "undefined") {
        window.localStorage.setItem("dyocense-api-token", trimmedToken);
        if (tenantId?.trim()) {
          window.localStorage.setItem("dyocense-tenant-id", tenantId.trim());
        }
        if (displayName?.trim()) {
          window.localStorage.setItem("dyocense-user-name", displayName.trim());
        }
        if (email?.trim()) {
          window.localStorage.setItem("dyocense-user-email", email.trim());
        }
      } else if (typeof window !== "undefined") {
        window.localStorage.removeItem("dyocense-api-token");
        window.localStorage.removeItem("dyocense-tenant-id");
        window.localStorage.removeItem("dyocense-user-name");
        window.localStorage.removeItem("dyocense-user-email");
      }
    },
    []
  );

  const loginWithCredentials = useCallback(
    async (tenantId: string, email: string, password: string) => {
      const response = await loginUser({ tenant_id: tenantId, email, password });
      setAuthToken(response.token);
      setToken(response.token);
  setAuthenticated(true);

      if (typeof window !== "undefined") {
        window.localStorage.setItem("dyocense-api-token", response.token);
        window.localStorage.setItem("dyocense-tenant-id", tenantId);
        window.localStorage.setItem("dyocense-user-email", email);
      }

      try {
        const userProfile = await fetchUserProfile();
        setUser({
          id: userProfile.user_id,
          fullName: userProfile.full_name,
          email: userProfile.email,
          username: userProfile.email,
        });
      } catch (err) {
        console.warn("Failed to fetch user profile", err);
        setUser({ id: response.user_id, fullName: email, email, username: email });
      }

      try {
        const tenantProfile = await getTenantProfile();
        setProfile({
          companyName: tenantProfile.name,
          industry: "",
          teamSize: String(tenantProfile.usage?.members ?? ""),
          primaryGoal: "",
          timezone: "",
        });
      } catch (err) {
        console.warn("Failed to fetch tenant profile", err);
      }
    },
    []
  );

  const registerUserAccount = useCallback(
    async (tenantId: string, email: string, fullName: string, password: string, temporaryPassword: string) => {
      await registerUser({ tenant_id: tenantId, email, full_name: fullName, password, temporary_password: temporaryPassword });
    },
    []
  );

  useEffect(() => {
    if (hydratedFromStorage || authenticated) return;
    if (typeof window === "undefined") return;
    const storedToken = window.localStorage.getItem("dyocense-api-token");
    if (storedToken) {
      loginWithToken({
        apiToken: storedToken,
        tenantId: window.localStorage.getItem("dyocense-tenant-id") || undefined,
        displayName: window.localStorage.getItem("dyocense-user-name") || undefined,
        email: window.localStorage.getItem("dyocense-user-email") || undefined,
        remember: true,
      })
        .catch((err) => {
          console.warn("Stored token login failed", err);
          window.localStorage.removeItem("dyocense-api-token");
          window.localStorage.removeItem("dyocense-tenant-id");
          window.localStorage.removeItem("dyocense-user-name");
          window.localStorage.removeItem("dyocense-user-email");
        })
        .finally(() => {
          setHydratedFromStorage(true);
        });
    } else {
      setHydratedFromStorage(true);
    }
  }, [authenticated, hydratedFromStorage, loginWithToken]);

  const login = useCallback(
    async (redirectTo?: string) => {
      if (!supportsKeycloak) {
        throw new Error("Authentication is not supported: Keycloak is not configured.");
      }

      if (keycloakRef.current) {
        await keycloakRef.current.login({
          redirectUri: redirectTo ?? window.location.href,
        });
      }
    },
  [supportsKeycloak]
  );

  const logout = useCallback(async () => {
  if (!supportsKeycloak) {
      if (user?.id) {
        clearStoredProfile(user.id);
      }
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("dyocense-api-token");
        window.localStorage.removeItem("dyocense-tenant-id");
        window.localStorage.removeItem("dyocense-user-name");
        window.localStorage.removeItem("dyocense-user-email");
      }
      setAuthenticated(false);
      setUser(null);
      setToken(null);
      setAuthToken(null);
      setProfile(null);
      return;
    }

    if (keycloakRef.current) {
      // Proactively clear local state and storage before redirecting to IdP logout,
      // to avoid any stale Authorization headers or user state after redirect.
      if (user?.id) {
        clearStoredProfile(user.id);
      }
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("dyocense-api-token");
        window.localStorage.removeItem("dyocense-tenant-id");
        window.localStorage.removeItem("dyocense-user-name");
        window.localStorage.removeItem("dyocense-user-email");
      }
      setAuthenticated(false);
      setUser(null);
      setToken(null);
      setAuthToken(null);
      setProfile(null);
      const redirectUri = window.location.origin;
      await keycloakRef.current.logout({ redirectUri });
    }
  }, [supportsKeycloak, user]);

  const refreshProfile = useCallback(async () => {
    if (!user?.id) return;
    setLoadingProfile(true);
    try {
      // Placeholder for future API integration. Currently relies on local storage.
      const stored = readStoredProfile(user.id);
      setProfile(stored);
    } finally {
      setLoadingProfile(false);
    }
  }, [user]);

  const updateProfile = useCallback(
    async (nextProfile: BusinessProfile) => {
      if (!user?.id) return;
      setProfile(nextProfile);
      persistProfile(user.id, nextProfile);
    },
    [user]
  );

  const value: AuthContextValue = {
    ready,
    authenticated,
    user,
    token,
    profile,
    loadingProfile,
  login,
    loginWithToken,
    loginWithCredentials,
    registerUserAccount,
    logout,
    updateProfile,
    refreshProfile,
    keycloak: keycloakRef.current ?? undefined,
    supportsKeycloak,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
};
