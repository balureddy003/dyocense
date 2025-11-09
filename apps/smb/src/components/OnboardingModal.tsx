import { Alert, Button, Group, Modal, Stack, Text } from '@mantine/core'
import { useQueryClient } from '@tanstack/react-query'
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { tryPost } from '../lib/api'
import { useAuthStore } from '../stores/auth'

type Props = {
    open: boolean
    onClose: () => void
}

export default function OnboardingModal({ open, onClose }: Props) {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [status, setStatus] = React.useState<'idle' | 'working'>('idle')
    const [error, setError] = React.useState<string | null>(null)

    const createSampleWorkspaceAndPlan = async () => {
        if (!tenantId) return
        setStatus('working')
        setError(null)
        try {
            const data = await tryPost<{
                workspace: any
                plan: any
            }>(`/v1/onboarding/${encodeURIComponent(tenantId)}`, {
                workspace_name: 'Sample Workspace',
                plan_title: 'Sample Launch Plan',
                archetype_id: 'inventory_basic',
            }, apiToken)

            if (!data) throw new Error('no data returned')
            queryClient.invalidateQueries({ queryKey: ['plan', tenantId] })
            onClose()
            navigate('/planner')
        } catch (err) {
            setError('We could not reach the onboarding service. Please try again.')
        } finally {
            setStatus('idle')
        }
    }

    return (
        <Modal opened={open} onClose={onClose} title="Welcome to Dyocense" centered>
            <Stack gap="sm">
                <Text c="gray.6">Spin up a sample workspace and launch plan so you can see Dyocense agents, automations, and reporting in action.</Text>
                {error && <Alert color="red">{error}</Alert>}
                <Group>
                    <Button loading={status === 'working'} onClick={createSampleWorkspaceAndPlan}>
                        {status === 'working' ? 'Creating…' : 'Create sample workspace & plan'}
                    </Button>
                    <Button variant="outline" onClick={onClose}>
                        Maybe later
                    </Button>
                </Group>
            </Stack>
        </Modal>
    )
}
