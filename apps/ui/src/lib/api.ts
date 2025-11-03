import { API_BASE_URL, DEFAULT_HEADERS, ApiOptions, getAuthHeaders } from "./config";

async function fetchJSON<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...DEFAULT_HEADERS,
        ...getAuthHeaders(),
        ...(options.headers || {}),
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    if (response.status === 204) {
      return {} as T;
    }
    return (await response.json()) as T;
  } catch (error) {
    if ("fallback" in options && options.fallback !== undefined) {
      console.warn(`Falling back to mock for ${path}:`, error);
      return options.fallback as T;
    }
    throw error;
  }
}

export async function listRuns<T>(fallback: T): Promise<T> {
  return fetchJSON<T>("/v1/runs?limit=10", { fallback });
}

export async function getRun<T>(runId: string, fallback: T): Promise<T> {
  return fetchJSON<T>(`/v1/runs/${runId}`, { fallback });
}

export async function listEvidence<T>(fallback: T): Promise<T> {
  return fetchJSON<T>("/v1/evidence?limit=20", { fallback });
}

export async function getEvidence<T>(runId: string, fallback: T): Promise<T> {
  return fetchJSON<T>(`/v1/evidence/${runId}`, { fallback });
}

export async function getArchetypes<T>(fallback: T): Promise<T> {
  return fetchJSON<T>("/v1/archetypes", { fallback });
}

export async function postChat<T>(body: unknown, fallback: T): Promise<T> {
  return fetchJSON<T>("/v1/chat", {
    method: "POST",
    body: JSON.stringify(body),
    fallback,
  });
}

export async function createRun<T>(body: unknown, fallback: T): Promise<T> {
  return fetchJSON<T>("/v1/runs", {
    method: "POST",
    body: JSON.stringify(body),
    fallback,
  });
}
