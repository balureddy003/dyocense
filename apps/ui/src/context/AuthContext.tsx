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

export interface AuthUser {
  id: string;
  fullName: string;
  email?: string;
  username?: string;
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
  logout: () => Promise<void>;
  updateProfile: (profile: BusinessProfile) => Promise<void>;
  refreshProfile: () => Promise<void>;
  keycloak?: KeycloakInstance;
  usingMock?: boolean;
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

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const usingMock = !isKeycloakConfigured();
  const keycloakConfig = useMemo<KeycloakConfig | null>(() => {
    if (usingMock) return null;
    const env = getKeycloakConfig();
    return {
      url: env.url!,
      realm: env.realm!,
      clientId: env.clientId!,
    };
  }, [usingMock]);

  const keycloakRef = useRef<KeycloakInstance | null>(null);

  const [ready, setReady] = useState(usingMock);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<BusinessProfile | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);

  useEffect(() => {
    if (usingMock) {
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
  }, [keycloakConfig, usingMock]);

  const login = useCallback(
    async (redirectTo?: string) => {
      if (usingMock) {
        const mockUser: AuthUser = {
          id: "demo-user",
          fullName: "Demo User",
          email: "demo@dyocense.dev",
          username: "demo",
        };
        setAuthenticated(true);
        setUser(mockUser);
        setToken("mock-token");
        setAuthToken("mock-token");
        setProfile(readStoredProfile(mockUser.id));
        return;
      }

      if (keycloakRef.current) {
        await keycloakRef.current.login({
          redirectUri: redirectTo ?? window.location.href,
        });
      }
    },
    [usingMock]
  );

  const logout = useCallback(async () => {
    if (usingMock) {
      if (user?.id) {
        clearStoredProfile(user.id);
      }
      setAuthenticated(false);
      setUser(null);
      setToken(null);
      setAuthToken(null);
      setProfile(null);
      return;
    }

    if (keycloakRef.current) {
      const redirectUri = window.location.origin;
      await keycloakRef.current.logout({ redirectUri });
    }
  }, [usingMock, user]);

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
    logout,
    updateProfile,
    refreshProfile,
    keycloak: keycloakRef.current ?? undefined,
    usingMock,
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
