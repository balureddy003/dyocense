import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import Executor from '../../pages/Executor'
import { server, createMockHandlers } from '../mocks/server'
import { renderWithProviders } from '../utils/renderWithProviders'
import { useAuthStore } from '../../stores/auth'

const hydrateAuth = () => {
    useAuthStore.setState({ apiToken: 'demo-token', tenantId: 'tenant-123', user: { name: 'Tester' } })
}

describe('Executor page', () => {
    beforeAll(() => server.listen())
    afterEach(() => server.resetHandlers())
    afterAll(() => server.close())

    it('renders run telemetry and evidence', async () => {
        server.use(
            ...createMockHandlers({
                runs: [{ run_id: 'run-01', goal: 'Increase sales', status: 'complete' }],
                evidence: [{ run_id: 'run-01', stored_at: '2024-01-01T00:00:00Z', explanation: { summary: 'Done' } }],
            })
        )
        hydrateAuth()
        renderWithProviders(<Executor />)
        await waitFor(() => {
            expect(screen.getByText('Increase sales')).toBeInTheDocument()
            const runBadges = screen.getAllByText(/run-01/i)
            expect(runBadges.length).toBeGreaterThan(0)
        })
    })

    it('logs evidence using the latest run', async () => {
        server.use(
            ...createMockHandlers({
                runs: [{ run_id: 'run-02', goal: 'Optimize staffing', status: 'running' }],
                evidence: [],
                runResponse: { run_id: 'run-02', status: 'running' },
            })
        )
        hydrateAuth()
        renderWithProviders(<Executor />)
        const logButton = await screen.findByRole('button', { name: /log decision evidence/i })
        fireEvent.click(logButton)
        await waitFor(() => {
            expect(screen.getByText(/Evidence logged for run-02/i)).toBeInTheDocument()
        })
    })
})
