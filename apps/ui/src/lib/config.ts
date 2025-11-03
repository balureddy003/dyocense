export const API_BASE_URL = import.meta.env.VITE_DYOCENSE_BASE_URL?.replace(/\/$/, "") || "http://localhost:8001";

export const DEFAULT_HEADERS: HeadersInit = {
  "Content-Type": "application/json",
};

export interface ApiOptions extends RequestInit {
  fallback?: unknown;
}

let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
};

export const getAuthHeaders = (): HeadersInit => {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
};
