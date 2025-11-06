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
    throw error;
  }
}

export async function listRuns<T = any>(opts?: { project_id?: string; limit?: number }): Promise<T> {
  const params = new URLSearchParams();
  params.set("limit", String(opts?.limit ?? 10));
  if (opts?.project_id) params.set("project_id", opts.project_id);
  const qs = params.toString();
  return fetchJSON<T>(`/v1/runs${qs ? `?${qs}` : ""}`);
}

export async function getRun<T = any>(runId: string): Promise<T> {
  return fetchJSON<T>(`/v1/runs/${runId}`);
}

export async function listEvidence<T = any>(): Promise<T> {
  return fetchJSON<T>("/v1/evidence?limit=20");
}

export async function getEvidence<T = any>(runId: string): Promise<T> {
  return fetchJSON<T>(`/v1/evidence/${runId}`);
}

export async function getTemplates<T = any>(): Promise<T> {
  return fetchJSON<T>("/v1/templates");
}

// Backward compatibility
export async function getArchetypes<T = any>(): Promise<T> {
  return getTemplates<T>();
}

export async function postChat<T = any>(body: unknown): Promise<T> {
  return fetchJSON<T>("/v1/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// OpenAI-compatible Chat Completions API
export type OAIRole = "system" | "user" | "assistant";

export interface OAIMessage {
  role: OAIRole;
  content: string;
}

export interface OAIChatRequest {
  model?: string;
  messages: OAIMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  user?: string;
  // vendor extension for context passthrough (optional)
  context?: Record<string, unknown>;
}

export interface OAIChatResponse {
  id: string;
  object: string; // "chat.completion"
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: { role: "assistant"; content: string };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export async function postOpenAIChat(body: OAIChatRequest): Promise<OAIChatResponse> {
  return fetchJSON<OAIChatResponse>("/v1/chat/completions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function createRun<T = any>(body: unknown): Promise<T> {
  return fetchJSON<T>("/v1/runs", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export interface SubscriptionPlan {
  tier: string;
  name: string;
  price_per_month: number;
  description: string;
  limits: {
    max_projects: number;
    max_playbooks: number;
    max_members: number;
    support_level: string;
  };
  features: string[];
}

export interface TenantRegistrationPayload {
  name: string;
  owner_email: string;
  plan_tier: string;
  metadata?: Record<string, unknown>;
}

export interface TenantRegistrationResponse {
  tenant_id: string;
  api_token: string;
  plan: SubscriptionPlan;
  already_exists?: boolean;
  message?: string;
}

export interface TenantProfile {
  tenant_id: string;
  name: string;
  owner_email: string;
  plan: SubscriptionPlan;
  status: string;
  usage: {
    projects: number;
    playbooks: number;
    members: number;
    cycle_started_at: string;
  };
}

export interface UserProfile {
  user_id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  roles: string[];
}

export interface ProjectSummary {
  project_id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserLoginPayload {
  tenant_id: string;
  email: string;
  password: string;
}

export interface UserLoginResponse {
  token: string;
  user_id: string;
  tenant_id: string;
  expires_in: number;
}

export interface UserRegistrationPayload {
  tenant_id: string;
  email: string;
  full_name: string;
  password: string;
  temporary_password: string;
}

export interface ApiTokenSummary {
  token_id: string;
  name: string;
  created_at: string;
}

export interface ApiTokenCreateResponse extends ApiTokenSummary {
  secret: string;
}

export async function listPlans(): Promise<SubscriptionPlan[]> {
  return fetchJSON<SubscriptionPlan[]>("/v1/plans");
}

export async function registerTenant(payload: TenantRegistrationPayload): Promise<TenantRegistrationResponse> {
  return fetchJSON<TenantRegistrationResponse>("/v1/tenants/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface OnboardingDetails {
  tenant_id: string;
  keycloak_realm: string | null;
  keycloak_url: string | null;
  temporary_password: string | null;
  username: string | null;
  email: string;
  login_url: string | null;
  status: "ready" | "pending_keycloak_setup";
  message?: string;
}

export async function getOnboardingDetails(): Promise<OnboardingDetails> {
  return fetchJSON<OnboardingDetails>("/v1/tenants/me/onboarding");
}

export async function cancelSubscription(): Promise<{ status: string; message: string }> {
  return fetchJSON<{ status: string; message: string }>("/v1/tenants/me/cancel", {
    method: "POST",
  });
}

export async function getTenantProfile(): Promise<TenantProfile> {
  return fetchJSON<TenantProfile>("/v1/tenants/me");
}

export async function updateTenantBusinessProfile(profile: {
  industry?: string;
  company_size?: string;
  team_size?: string;
  primary_goal?: string;
  business_type?: string;
}): Promise<{ message: string; profile: any }> {
  return fetchJSON<{ message: string; profile: any }>("/v1/tenants/me/profile", {
    method: "PUT",
    body: JSON.stringify(profile),
  });
}

export interface PlaybookRecommendation {
  id: string;
  title: string;
  description: string;
  template_id: string;
  archetype_id?: string;  // Backward compatibility
  icon: string;
  estimated_time: string;
  tags: string[];
}

export async function getPlaybookRecommendations(): Promise<{
  recommendations: PlaybookRecommendation[];
  industry: string;
  message: string;
}> {
  return fetchJSON<{
    recommendations: PlaybookRecommendation[];
    industry: string;
    message: string;
  }>("/v1/goals/recommendations");
}

export async function listProjects(): Promise<ProjectSummary[]> {
  return fetchJSON<ProjectSummary[]>("/v1/projects");
}

export async function createProject(name: string, description?: string | null): Promise<ProjectSummary> {
  return fetchJSON<ProjectSummary>("/v1/projects", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
}

export async function loginUser(payload: UserLoginPayload): Promise<UserLoginResponse> {
  return fetchJSON<UserLoginResponse>("/v1/users/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface TenantOption {
  tenant_id: string;
  name: string;
}

export async function getUserTenants(email: string): Promise<TenantOption[]> {
  const response = await fetchJSON<{ tenants: TenantOption[] }>(`/v1/users/tenants?email=${encodeURIComponent(email)}`);
  return response.tenants;
}

export async function registerUser(payload: UserRegistrationPayload): Promise<UserProfile> {
  return fetchJSON<UserProfile>("/v1/users/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchUserProfile(): Promise<UserProfile> {
  return fetchJSON<UserProfile>("/v1/users/me");
}

export async function listUserApiTokens(): Promise<ApiTokenSummary[]> {
  return fetchJSON<ApiTokenSummary[]>("/v1/users/api-tokens");
}

export async function createUserApiToken(name: string): Promise<ApiTokenCreateResponse> {
  return fetchJSON<ApiTokenCreateResponse>("/v1/users/api-tokens", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function deleteUserApiToken(tokenId: string): Promise<void> {
  await fetchJSON<void>(`/v1/users/api-tokens/${tokenId}`, {
    method: "DELETE",
  });
}

// Invitations
export interface InvitationSummary {
  invite_id: string;
  tenant_id: string;
  inviter_user_id: string;
  invitee_email: string;
  status: string;
  created_at: string;
  expires_at: string;
}

export async function createInvitation(invitee_email: string): Promise<InvitationSummary> {
  return fetchJSON<InvitationSummary>("/v1/invitations", {
    method: "POST",
    body: JSON.stringify({ invitee_email }),
  });
}

export async function listInvitations(): Promise<InvitationSummary[]> {
  return fetchJSON<InvitationSummary[]>("/v1/invitations");
}

export async function revokeInvitation(inviteId: string): Promise<void> {
  await fetchJSON<void>(`/v1/invitations/${inviteId}`, {
    method: "DELETE",
  });
}

export async function resendInvitation(inviteId: string): Promise<{ message: string; invite_id: string }> {
  return fetchJSON<{ message: string; invite_id: string }>(`/v1/invitations/${inviteId}/resend`, {
    method: "POST",
  });
}

// ==================== Connector Management ====================

export interface ConnectorMetadata {
  total_records?: number;
  last_sync_duration?: number;
  error_message?: string;
  last_error_at?: string;
}

export interface Connector {
  connector_id: string;
  tenant_id: string;
  connector_type: string;
  connector_name: string;
  display_name: string;
  category: string;
  icon: string;
  data_types: string[];
  status: "active" | "inactive" | "error" | "syncing" | "testing";
  last_sync?: string;
  sync_frequency: "realtime" | "hourly" | "daily" | "weekly" | "manual";
  metadata: ConnectorMetadata;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface CreateConnectorPayload {
  connector_type: string;
  display_name: string;
  config: Record<string, any>;
  sync_frequency?: "realtime" | "hourly" | "daily" | "weekly" | "manual";
}

export interface TestConnectorPayload {
  connector_type: string;
  config: Record<string, any>;
}

export interface TestConnectorResult {
  success: boolean;
  message: string;
  details?: Record<string, any>;
  error_code?: string;
}

/**
 * Get the connector marketplace catalog
 */
export async function getConnectorCatalog(): Promise<any> {
  return fetchJSON<any>("/v1/catalog", {
    fallback: { connectors: [], total: 0 }
  });
}

/**
 * Create a new connector for the authenticated tenant
 */
export async function createConnector(payload: CreateConnectorPayload): Promise<Connector> {
  return fetchJSON<Connector>("/v1/connectors", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * List all connectors for the authenticated tenant
 */
export async function listConnectors(statusFilter?: string): Promise<Connector[]> {
  const params = statusFilter ? `?status=${statusFilter}` : "";
  return fetchJSON<Connector[]>(`/v1/connectors${params}`, {
    fallback: []
  });
}

/**
 * Get a specific connector by ID
 */
export async function getConnector(connectorId: string): Promise<Connector> {
  return fetchJSON<Connector>(`/v1/connectors/${connectorId}`);
}

/**
 * Delete a connector
 */
export async function deleteConnector(connectorId: string): Promise<void> {
  await fetchJSON<void>(`/v1/connectors/${connectorId}`, {
    method: "DELETE",
  });
}

/**
 * Test an existing connector's configuration
 */
export async function testConnector(connectorId: string): Promise<TestConnectorResult> {
  return fetchJSON<TestConnectorResult>(`/v1/connectors/${connectorId}/test`, {
    method: "POST",
  });
}

/**
 * Test a connector configuration without saving it
 */
export async function testConnectorConfig(payload: TestConnectorPayload): Promise<TestConnectorResult> {
  return fetchJSON<TestConnectorResult>("/v1/connectors/test", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
