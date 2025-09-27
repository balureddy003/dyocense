const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer tenant_demo',
      ...(options?.headers ?? {})
    },
    ...options
  });
  if (!response.ok) {
    throw new Error(`API error ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export interface Provider {
  provider_id: string;
  name: string;
  model: string;
  streaming: boolean;
}

export interface PlanListItem {
  plan_id: string;
  goal_id?: string | null;
  variant?: string | null;
  evidence_ref: string;
  created_at: string;
  allow?: boolean | null;
}

export async function fetchProviders(): Promise<Provider[]> {
  return request<Provider[]>(`/llm/providers`, { method: 'GET' });
}

export interface PlanChatResponse {
  summary: string;
  status: string;
  provider_id?: string;
  conversation_id: string;
  llm_response?: string;
}

export async function postPlanChat(goal: string, context: string, providerId: string): Promise<PlanChatResponse> {
  return request(`/chat/plan`, {
    method: 'POST',
    body: JSON.stringify({ goal, context, tenant_id: 'tenant_demo', provider_id: providerId })
  });
}

export async function fetchPlans(): Promise<PlanListItem[]> {
  return request(`/plans`, { method: 'GET' });
}
