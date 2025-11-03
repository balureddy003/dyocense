export const API_BASE_URL = import.meta.env.VITE_DYOCENSE_BASE_URL?.replace(/\/$/, "") || "http://localhost:8001";

export const DEFAULT_HEADERS: HeadersInit = {
  "Content-Type": "application/json",
};

export interface ApiOptions extends RequestInit {
  fallback?: unknown;
}
