// In development, use relative URLs to leverage Vite's proxy
// In production, use the environment variable or fallback to localhost:8001
export const API_BASE_URL = import.meta.env.DEV
  ? "" // Use Vite proxy in development
  : (import.meta.env.VITE_DYOCENSE_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8001");

export const ADMIN_TENANT_ID = import.meta.env.VITE_ADMIN_TENANT_ID || "admin";

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
