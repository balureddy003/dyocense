import { useQuery } from '@tanstack/react-query'
import { ConnectorStatus, listConnectors, TenantConnector } from '../lib/api'

type Options = {
    status?: ConnectorStatus
    enabled?: boolean
}

export function useConnectorsQuery(apiToken?: string, tenantId?: string, options: Options = {}) {
    const { status, enabled = true } = options
    return useQuery<TenantConnector[]>({
        queryKey: ['connectors', tenantId, status],
        enabled: Boolean(apiToken && tenantId && enabled),
        queryFn: () => listConnectors(apiToken, status),
    })
}
