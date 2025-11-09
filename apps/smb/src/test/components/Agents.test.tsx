import { beforeAll, afterAll, afterEach, describe, expect, it, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import Agents from '../../pages/Agents'
import { server, createMockHandlers } from '../mocks/server'
import { renderWithProviders } from '../utils/renderWithProviders'
import { useAuthStore } from '../../stores/auth'

const setupAuth = () => {
    useAuthStore.setState({ apiToken: 'demo-token', tenantId: 'tenant-123', user: { name: 'Tester' } })
}

describe('Agents page', () => {
    beforeAll(() => {
        server.listen()
    })

    afterEach(() => {
        server.resetHandlers()
    })

    afterAll(() => {
        server.close()
    })

    it('shows catalog items from the API', async () => {
        server.use(
            ...createMockHandlers({
                catalog: [
                    { id: 'inventory_basic', name: 'Inventory Planner', description: 'Plan inventory with AI' },
                    { id: 'staffing_pro', name: 'Staffing Pro', description: 'Automate staffing' },
                ],
            })
        )
        setupAuth()
        renderWithProviders(<Agents />)
        await waitFor(() => {
            expect(screen.getByText('Inventory Planner')).toBeInTheDocument()
            expect(screen.getByText('Staffing Pro')).toBeInTheDocument()
        })
    })

    it('launches an agent and surfaces the new run', async () => {
        const runSpy = vi.fn().mockResolvedValue({ run_id: 'run-abc', status: 'pending' })
        server.use(
            ...createMockHandlers({
                catalog: [{ id: 'inventory_basic', name: 'Inventory Planner', description: 'Plan inventory' }],
                runs: [],
                runResponse: { run_id: 'run-abc', status: 'pending' },
            })
        )
        setupAuth()
        renderWithProviders(<Agents />)
        const launchButton = await screen.findByRole('button', { name: /launch agent/i })
        fireEvent.click(launchButton)
        await waitFor(() => {
            expect(screen.getByText(/run-abc/i)).toBeInTheDocument()
        })
    })
})
