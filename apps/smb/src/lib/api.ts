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
    if (!res.ok) throw new Error(`POST ${path} failed with ${res.status}`)
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
    data_types: string[]
    status: ConnectorStatus
    sync_frequency: string
    last_sync?: string
    metadata?: {
        total_records?: number
        last_sync_duration?: number
        error_message?: string
    }
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

export async function listConnectors(token?: string, statusFilter?: ConnectorStatus): Promise<TenantConnector[]> {
    const query = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''
    const data = await tryGet<TenantConnector[]>(connectorsPath(`/v1/connectors${query}`), token)
    return data ?? []
}

export async function fetchConnectorCatalog(token?: string): Promise<ConnectorCatalogItem[]> {
    const data = await tryGet<{ connectors?: ConnectorCatalogItem[] }>(connectorsPath('/v1/catalog'), token)
    return data?.connectors ?? []
}

export async function createConnector(payload: { connector_type: string; display_name: string; config: Record<string, unknown>; sync_frequency?: string }, token?: string) {
    return post(connectorsPath('/v1/connectors'), payload, token)
}

export async function deleteConnector(connectorId: string, token?: string) {
    return del(connectorsPath(`/v1/connectors/${connectorId}`), token)
}

export async function testConnector(connectorId: string, token?: string) {
    return post(connectorsPath(`/v1/connectors/${connectorId}/test`), {}, token)
}

export async function testConnectorConfig(payload: { connector_type: string; config: Record<string, unknown> }, token?: string) {
    return post(connectorsPath('/v1/connectors/test'), payload, token)
}
