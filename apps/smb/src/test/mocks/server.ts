import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

type MockConfig = Partial<{
    catalog: any[]
    runs: any[]
    evidence: any[]
    runResponse: any
}>

export const createMockHandlers = (config: MockConfig = {}) => [
    http.get('http://localhost:8002/v1/catalog', () => {
        return HttpResponse.json({ items: config.catalog ?? [] })
    }),
    http.get('http://localhost:8002/v1/runs', () => {
        return HttpResponse.json({ runs: config.runs ?? [] })
    }),
    http.post('http://localhost:8002/v1/runs', () => {
        return HttpResponse.json(config.runResponse ?? { run_id: 'run-123', status: 'pending' })
    }),
    http.get('http://localhost:8002/v1/evidence', () => {
        return HttpResponse.json({ items: config.evidence ?? [] })
    }),
    http.post('http://localhost:8002/v1/evidence/log', () => {
        return HttpResponse.json({ run_id: config.runResponse?.run_id ?? 'run-123', stored_at: new Date().toISOString() })
    }),
]

export const server = setupServer(...createMockHandlers())
