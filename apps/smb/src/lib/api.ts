export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'
const PROXY_API_KEY = import.meta.env.VITE_PROXY_API_KEY

const buildHeaders = (token?: string) => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(PROXY_API_KEY ? { 'x-api-key': PROXY_API_KEY } : {}),
})

const readBody = async (res: Response) => {
    const text = await res.text()
    if (!text) return null
    try {
        return JSON.parse(text)
    } catch {
        return text
    }
}

export async function post<T = any>(path: string, body: any = {}, token?: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: buildHeaders(token),
        body: JSON.stringify(body),
    })
    if (!res.ok) {
        const error: any = new Error(`POST ${path} failed with ${res.status}`)
        error.status = res.status
        error.statusText = res.statusText
        try {
            error.body = await readBody(res)
        } catch {
            // Ignore if response body is not JSON
        }
        throw error
    }
    return readBody(res)
}

export async function get<T = any>(path: string, token?: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(PROXY_API_KEY ? { 'x-api-key': PROXY_API_KEY } : {}),
        }
    })
    if (!res.ok) throw new Error(`GET ${path} failed with ${res.status}`)
    return readBody(res)
}

export async function del(path: string, token?: string): Promise<void> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'DELETE',
        headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(PROXY_API_KEY ? { 'x-api-key': PROXY_API_KEY } : {}),
        },
    })
    if (!res.ok) throw new Error(`DELETE ${path} failed with ${res.status}`)
}

export async function put<T = any>(path: string, body: any = {}, token?: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'PUT',
        headers: buildHeaders(token),
        body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`PUT ${path} failed with ${res.status}`)
    return readBody(res)
}

export async function tryGet<T = any>(path: string, token?: string): Promise<T | null> {
    try {
        return await get<T>(path, token)
    } catch (_err) {
        return null
    }
}

export async function tryPost<T = any>(path: string, body: any = {}, token?: string): Promise<T | null> {
    try {
        return await post<T>(path, body, token)
    } catch (_err) {
        return null
    }
}

export async function tryDelete(path: string, token?: string): Promise<boolean> {
    try {
        await del(path, token)
        return true
    } catch (_err) {
        return false
    }
}

export async function requestPasswordReset(email: string): Promise<{ message: string }> {
    return post('/v1/auth/request-password-reset', { email })
}

export async function resetPassword(token: string, password: string): Promise<{ message: string }> {
    return post('/v1/auth/reset-password', { token, password })
}

export type CatalogItem = {
    id: string
    name: string
    description?: string
    data_inputs?: Record<string, unknown>
}

export type RunRecord = {
    run_id: string
    status: string
    goal: string
    template_id?: string
    result?: any
    error?: string
}

export type EvidenceRecord = {
    run_id: string
    stored_at?: string
    goal_pack?: Record<string, unknown>
    solution?: Record<string, unknown>
    explanation?: Record<string, unknown>
}

export type ConnectorStatus = 'active' | 'inactive' | 'error' | 'syncing' | 'testing'

export type TenantConnector = {
    connector_id: string
    connector_type: string
    connector_name: string
    display_name: string
    category: string
    icon?: string
    data_types: string[]
    status: ConnectorStatus
    sync_frequency: string
    last_sync?: string
    created_at?: string
    updated_at?: string
    created_by?: string
    metadata?: {
        total_records?: number
        last_sync_duration?: number
        error_message?: string
        mcp_enabled?: boolean
    }
}

export type ConnectorTestResponse = {
    success: boolean
    message: string
    details?: Record<string, unknown>
    error_code?: string
}

export type UpdateConnectorPayload = {
    display_name?: string
    config?: Record<string, unknown>
    sync_frequency?: string
    status?: ConnectorStatus
    enable_mcp?: boolean
}

export async function fetchCatalog(token?: string): Promise<CatalogItem[]> {
    const data = await tryGet<{ items?: CatalogItem[] }>('/v1/catalog', token)
    return data?.items ?? []
}

export async function listRuns(token?: string, limit = 10): Promise<RunRecord[]> {
    const data = await tryGet<{ runs?: RunRecord[] }>('/v1/runs', token)
    const runs = data?.runs ?? []
    return runs.slice(0, limit)
}

export async function triggerRun(payload: Record<string, unknown>, token?: string) {
    return tryPost<{ run_id: string; status: string }>('/v1/runs', payload, token)
}

export async function listEvidence(token?: string, limit = 5): Promise<EvidenceRecord[]> {
    const data = await tryGet<{ items?: EvidenceRecord[] }>(`/v1/evidence?limit=${limit}`, token)
    return data?.items ?? []
}

export async function logEvidence(payload: Record<string, unknown>, token?: string) {
    return tryPost('/v1/evidence/log', payload, token)
}

const CONNECTORS_API_BASE = '/api/dyocense_connectors'

export type ConnectorCatalogItem = {
    id: string
    displayName: string
    category: string
    icon: string
    dataTypes: string[]
    authType: string
    description?: string
}

const connectorsPath = (path: string) => `${CONNECTORS_API_BASE}${path}`

export async function listConnectors(token?: string, statusFilter?: ConnectorStatus, tenantId?: string): Promise<TenantConnector[]> {
    if (!tenantId) return []
    const query = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''
    const response = await tryGet<{ connectors: TenantConnector[]; total: number }>(`/v1/tenants/${tenantId}/connectors${query}`, token)
    return response?.connectors ?? []
}

export async function fetchConnectorCatalog(token?: string): Promise<ConnectorCatalogItem[]> {
    const data = await tryGet<{ connectors?: ConnectorCatalogItem[] }>('/v1/marketplace/connectors', token)
    return data?.connectors ?? []
}

export async function createConnector(payload: { connector_type: string; display_name: string; config: Record<string, unknown>; sync_frequency?: string; enable_mcp?: boolean }, token?: string, tenantId?: string) {
    if (!tenantId) throw new Error('Tenant ID required')
    return post(`/v1/tenants/${tenantId}/connectors`, payload, token)
}

export async function deleteConnector(connectorId: string, token?: string, tenantId?: string) {
    if (!tenantId) throw new Error('Tenant ID required')
    return del(`/v1/tenants/${tenantId}/connectors/${connectorId}`, token)
}

export async function testConnector(connectorId: string, token?: string, tenantId?: string): Promise<ConnectorTestResponse> {
    if (!tenantId) throw new Error('Tenant ID required')
    return post(`/v1/tenants/${tenantId}/connectors/${connectorId}/test`, {}, token)
}

export async function testConnectorConfig(payload: { connector_type: string; config: Record<string, unknown> }, token?: string, tenantId?: string) {
    if (!tenantId) throw new Error('Tenant ID required')
    return post(`/v1/tenants/${tenantId}/connectors/test`, payload, token)
}

export async function updateConnector(connectorId: string, payload: UpdateConnectorPayload, token?: string, tenantId?: string) {
    if (!tenantId) throw new Error('Tenant ID required')
    return put(`/v1/tenants/${tenantId}/connectors/${connectorId}`, payload, token)
}

export async function uploadCSV(file: File, connectorId: string, token?: string, tenantId?: string) {
    if (!tenantId) throw new Error('Tenant ID required')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('connector_id', connectorId)
    formData.append('tenant_id', tenantId)

    const res = await fetch(`${API_BASE}/api/connectors/upload_csv`, {
        method: 'POST',
        headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(PROXY_API_KEY ? { 'x-api-key': PROXY_API_KEY } : {}),
            // Don't set Content-Type - let browser set it with boundary for multipart/form-data
        },
        body: formData,
    })

    if (!res.ok) {
        const error: any = new Error(`CSV upload failed with ${res.status}`)
        error.status = res.status
        error.statusText = res.statusText
        try {
            error.body = await res.json()
        } catch {
            // Ignore if response body is not JSON
        }
        throw error
    }

    return readBody(res)
}

export type ConnectorRecommendation = {
    id: string
    label: string
    description: string
    icon: string
    category: string
    priority: number
    reason: string
    fields: Array<{
        name: string
        label: string
        type?: 'text' | 'textarea' | 'file'
        placeholder?: string
        helper?: string
        accept?: string
    }>
}

export type ConnectorRecommendationsResponse = {
    recommendations: ConnectorRecommendation[]
    business_profile: {
        industry?: string | null
        business_type?: string | null
        team_size?: string | null
    }
    data_status: {
        has_orders: boolean
        has_inventory: boolean
        has_customers: boolean
        has_products: boolean
    }
    existing_connectors: string[]
    message: string
}

export async function getConnectorRecommendations(token?: string, tenantId?: string): Promise<ConnectorRecommendationsResponse> {
    if (!tenantId) throw new Error('Tenant ID required')
    return get(`/v1/tenants/${tenantId}/connectors/recommendations`, token)
}

// ===================================
// Coach V6 API Functions
// ===================================

export type CoachRecommendation = {
    id: string
    priority: 'critical' | 'important' | 'suggestion'
    title: string
    description: string
    reasoning?: string
    actions: Array<{
        id: string
        label: string
        description?: string
        buttonText: string
        variant?: string
        completed?: boolean
    }>
    dismissible: boolean
    dismissed: boolean
    createdAt: string
    generatedAt: string
    expiresAt?: string
    metadata?: Record<string, any>
}

export type Alert = {
    id: string
    type: string
    title: string
    description: string
    metric?: string
    value?: any
    threshold?: any
}

export type Signal = {
    id: string
    type: string
    title: string
    description: string
    metric?: string
    value?: any
}

export type MetricSnapshot = {
    id: string
    label: string
    value: string
    change: number
    changeType: 'percentage' | 'absolute'
    trend: 'up' | 'down' | 'stable'
    sparklineData?: number[]
    period?: string
    format?: string
}

export async function getCoachRecommendations(tenantId: string, token?: string): Promise<CoachRecommendation[]> {
    return get(`/v1/tenants/${tenantId}/coach/recommendations`, token)
}

export async function dismissRecommendation(tenantId: string, recId: string, token?: string): Promise<{ success: boolean }> {
    return post(`/v1/tenants/${tenantId}/coach/recommendations/${recId}/dismiss`, {}, token)
}

export interface RecommendationFeedback {
    helpful: boolean
    reason?: string
    comment?: string
}

export async function submitRecommendationFeedback(
    tenantId: string,
    recId: string,
    feedback: RecommendationFeedback,
    token?: string
): Promise<{ success: boolean; feedback_id: string }> {
    return post(`/v1/tenants/${tenantId}/coach/recommendations/${recId}/feedback`, feedback, token)
}

export async function getHealthAlerts(tenantId: string, token?: string): Promise<Alert[]> {
    return get(`/v1/tenants/${tenantId}/health-score/alerts`, token)
}

export async function getHealthSignals(tenantId: string, token?: string): Promise<Signal[]> {
    return get(`/v1/tenants/${tenantId}/health-score/signals`, token)
}

export async function getMetricsSnapshot(tenantId: string, token?: string): Promise<MetricSnapshot[]> {
    return get(`/v1/tenants/${tenantId}/metrics/snapshot`, token)
}

export type HealthScore = {
    score: number
    trend: number
    breakdown: {
        revenue?: number
        operations?: number
        customer?: number
        revenue_available: boolean
        operations_available: boolean
        customer_available: boolean
    }
    last_updated: string
    period_days: number
}

export async function getHealthScore(tenantId: string, token?: string): Promise<HealthScore> {
    return get(`/v1/tenants/${tenantId}/health-score`, token)
}

export async function getGoals(tenantId: string, token?: string): Promise<any[]> {
    return get(`/v1/tenants/${tenantId}/goals`, token)
}

export async function getTasks(tenantId: string, token?: string, horizon?: string): Promise<any[]> {
    const params = horizon ? `?horizon=${horizon}` : '';
    return get(`/v1/tenants/${tenantId}/tasks${params}`, token)
}

// ===================================
// OptiGuide API Functions
// ===================================

export type OptimizationRecommendation = {
    sku: string
    action: string
    current_stock?: number
    optimal_stock?: number
    potential_saving?: number
    change_pct?: number
}

export type OptimizationResult = {
    solver_status: string
    objective_value: number
    recommendations: OptimizationRecommendation[]
    total_potential_savings: number
    _modified?: boolean
    _modifications?: Record<string, any>
}

export type WhatIfAnalysisResponse = {
    success: boolean
    question: string
    original_result: OptimizationResult
    modified_result: OptimizationResult
    modifications_applied: Record<string, any>
    analysis: string
    narrative: string
    timestamp: string
}

export type WhyAnalysisResponse = {
    success: boolean
    question: string
    narrative: string
    supporting_data?: {
        recommendations?: OptimizationRecommendation[]
        metrics?: Record<string, any>
    }
    timestamp: string
}

export type OptiGuideChatResponse = {
    success: boolean
    question: string
    intent: 'forecast' | 'optimize' | 'what_if' | 'why' | 'overview'
    narrative: string
    supporting_data?: Record<string, any>
    timestamp: string
}

export type OptiGuideCapabilities = {
    conversational_ai: {
        narrative_generation: boolean
        what_if_analysis: boolean
        langgraph_orchestration: boolean
        multi_agent: boolean
    }
    advanced_features: {
        prophet_installed: boolean
        ortools_installed: boolean
        langgraph_installed: boolean
        autogen_installed: boolean
        optiguide_available: boolean
    }
    endpoints?: {
        basic?: string[]
        optiguide?: string[]
        langgraph?: string[]
    }
}

/**
 * Ask a what-if question about inventory optimization scenarios
 * Examples: "What if order costs increase 20%?", "What if holding costs double?"
 */
export async function askWhatIf(
    tenantId: string,
    question: string,
    llmConfig?: Record<string, any>,
    token?: string
): Promise<WhatIfAnalysisResponse> {
    return post(`/v1/tenants/${tenantId}/what-if`, { question, llm_config: llmConfig }, token)
}

/**
 * Ask a "why" question for root cause analysis
 * Examples: "Why are inventory costs high?", "Why is SKU X overstocked?"
 */
export async function askWhy(
    tenantId: string,
    question: string,
    llmConfig?: Record<string, any>,
    token?: string
): Promise<WhyAnalysisResponse> {
    return post(`/v1/tenants/${tenantId}/why`, { question, llm_config: llmConfig }, token)
}

/**
 * Chat with OptiGuide using LangGraph orchestration
 * Supports forecast, optimize, what_if, why, and overview intents
 */
export async function chatWithOptiGuide(
    tenantId: string,
    question: string,
    llmConfig?: Record<string, any>,
    token?: string
): Promise<OptiGuideChatResponse> {
    return post(`/v1/tenants/${tenantId}/chat`, { question, llm_config: llmConfig }, token)
}

/**
 * Get OptiGuide capabilities (AutoGen, LangGraph, etc.)
 */
export async function getOptiGuideCapabilities(): Promise<OptiGuideCapabilities> {
    return get('/v1/capabilities')
}
