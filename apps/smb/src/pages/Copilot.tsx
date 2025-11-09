import { Alert, Badge, Button, Card, Grid, Group, Loader, RingProgress, SegmentedControl, Stack, Text, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AgentActionCard from '../components/AgentActionCard'
import ChatShell from '../components/ChatShell'
import { get, listEvidence, listRuns } from '../lib/api'
import { templates } from '../data/templates'
import { useConnectorsQuery } from '../hooks/useConnectors'
import { useAuthStore } from '../stores/auth'
import { useTemplateStore } from '../stores/template'

export default function Copilot() {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)
    const { selectedTemplate, setTemplate } = useTemplateStore()
    const navigate = useNavigate()

    const { data: planSummary } = useQuery({
        queryKey: ['plan-summary', tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            if (!tenantId) return []
            const res = await get<{ items?: any[] } | any[]>(`/v1/tenants/${encodeURIComponent(tenantId)}/plans`)
            return Array.isArray(res) ? res : res?.items ?? []
        },
    })
    const connectorsQuery = useConnectorsQuery(apiToken, tenantId)
    const runsQuery = useQuery({
        queryKey: ['runs', tenantId, 'copilot'],
        enabled: Boolean(apiToken),
        queryFn: () => listRuns(apiToken, 5),
    })
    const evidenceQuery = useQuery({
        queryKey: ['evidence', tenantId, 'copilot'],
        enabled: Boolean(apiToken),
        queryFn: () => listEvidence(apiToken, 5),
    })

    const goalScore = React.useMemo(() => {
        if (!selectedTemplate.goals.length) return 0
        const weights: Record<typeof selectedTemplate.goals[number]['status'], number> = {
            on_track: 1,
            at_risk: 0.6,
            not_started: 0.2,
        }
        const total = selectedTemplate.goals.reduce((sum, goal) => sum + weights[goal.status], 0)
        return Math.round((total / selectedTemplate.goals.length) * 100)
    }, [selectedTemplate.goals])

    const connectorCards = React.useMemo(
        () =>
            connectorsQuery.data?.length
                ? connectorsQuery.data.map((connector) => ({
                      id: connector.connector_id,
                      name: connector.display_name ?? connector.connector_name,
                      description: connector.data_types?.join(', ') || connector.category,
                      status: connector.status,
                      lastSync: connector.last_sync,
                      source: 'api' as const,
                  }))
                : selectedTemplate.connectors.map((connector) => ({
                      id: connector.id,
                      name: connector.name,
                      description: connector.description,
                      status: connector.status,
                      source: 'template' as const,
                  })),
        [connectorsQuery.data, selectedTemplate],
    )

    const connectorColor = (status: string, source: 'api' | 'template') => {
        if (source === 'api') {
            if (status === 'active') return 'green'
            if (status === 'syncing' || status === 'testing') return 'yellow'
            if (status === 'error') return 'red'
            return 'gray'
        }
        if (status === 'connected') return 'green'
        if (status === 'required') return 'red'
        return 'yellow'
    }

    const connectorLabel = (status: string, source: 'api' | 'template') => {
        if (source === 'api') {
            return status === 'active'
                ? 'Connected'
                : status === 'syncing'
                  ? 'Syncing'
                  : status === 'testing'
                    ? 'Testing'
                    : status === 'error'
                      ? 'Check connection'
                      : 'Paused'
        }
        if (status === 'connected') return 'Connected'
        if (status === 'required') return 'Needed'
        return 'Optional'
    }

    return (
        <Card radius="xl" withBorder className="mx-auto grid w-full max-w-6xl gap-6 bg-night-800/80 px-4 py-8 shadow-card md:grid-cols-[1.15fr_0.85fr] md:px-8">
            <Stack gap="lg">
                <SegmentedControl
                    value={selectedTemplate.id}
                    onChange={setTemplate}
                    data={templates.map((template) => ({ label: template.industry, value: template.id }))}
                />
                <div>
                    <Text size="xs" fw={600} tt="uppercase" c="blue.3" style={{ letterSpacing: '0.25em' }}>
                        Goals Copilot
                    </Text>
                    <Title order={2} c="white">
                        {selectedTemplate.name}
                    </Title>
                    <Text c="gray.4">{selectedTemplate.summary}</Text>
                </div>

                <Grid gutter="lg">
                    <Grid.Col span={{ base: 12, md: 5 }}>
                        <Card radius="lg" withBorder className="bg-night-900/40 h-full">
                            <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.25em' }}>
                                Goal fitness
                            </Text>
                            <RingProgress
                                mt="md"
                                size={160}
                                thickness={12}
                                sections={[
                                    {
                                        value: goalScore,
                                        color: goalScore >= 66 ? 'green' : goalScore >= 40 ? 'yellow' : 'red',
                                    },
                                    { value: Math.max(0, 100 - goalScore), color: 'gray' },
                                ]}
                                label={
                                    <Stack gap={0} align="center">
                                        <Text size="sm" c="gray.4">
                                            Score
                                        </Text>
                                        <Text size="xl" fw={700}>
                                            {goalScore}%
                                        </Text>
                                    </Stack>
                                }
                            />
                            <Text size="xs" c="gray.5" mt="sm">
                                {planSummary?.length ? `${planSummary.length} live plan${planSummary.length > 1 ? 's' : ''} linked.` : 'Run onboarding to create your first plan.'}
                            </Text>
                        </Card>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 7 }}>
                        <Card radius="lg" withBorder className="bg-night-900/30 h-full">
                            <Group justify="space-between" align="center">
                                <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.25em' }}>
                                    Goal feed
                                </Text>
                                <Button component={Link} to="/planner" radius="xl" size="xs" variant="light">
                                    Open Planner
                                </Button>
                            </Group>
                            <Stack gap="sm" mt="md">
                                {selectedTemplate.goals.map((goal) => (
                                    <Card key={goal.id} radius="md" withBorder className="bg-night-900/50">
                                        <Group justify="space-between" align="flex-start">
                                            <div>
                                                <Text fw={600}>{goal.title}</Text>
                                                <Text size="xs" c="gray.4">
                                                    {goal.description}
                                                </Text>
                                            </div>
                                            <Badge color={goal.status === 'on_track' ? 'green' : goal.status === 'at_risk' ? 'yellow' : 'gray'} variant="light">
                                                {goal.target}
                                            </Badge>
                                        </Group>
                                    </Card>
                                ))}
                            </Stack>
                        </Card>
                    </Grid.Col>
                </Grid>

                <Card radius="lg" withBorder className="bg-night-900/40">
                    <Group justify="space-between" align="center">
                        <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.25em' }}>
                            Connectors
                        </Text>
                        <Button component={Link} to="/tools?tool=planner" variant="light" radius="xl" size="xs">
                            Manage
                        </Button>
                    </Group>
                    <Stack gap="xs" mt="md">
                        {connectorsQuery.isLoading && <Loader size="sm" />}
                        {connectorsQuery.isError && (
                            <Text size="xs" c="red.4">
                                Unable to load live connectors—showing template defaults.
                            </Text>
                        )}
                        {connectorCards.map((connector) => (
                            <Group key={connector.id} justify="space-between" align="flex-start">
                                <div>
                                    <Text fw={600}>{connector.name}</Text>
                                    <Text size="xs" c="gray.4">
                                        {connector.description}
                                    </Text>
                                    {connector.lastSync && (
                                        <Text size="xs" c="gray.6">
                                            Last sync: {new Date(connector.lastSync).toLocaleString()}
                                        </Text>
                                    )}
                                </div>
                                <Badge color={connectorColor(connector.status, connector.source)} variant="light">
                                    {connectorLabel(connector.status, connector.source)}
                                </Badge>
                            </Group>
                        ))}
                        {!connectorCards.length && (
                            <Text size="sm" c="gray.5">
                                No connectors yet. Use the button above to link POS, ERP, or marketing tools.
                            </Text>
                        )}
                    </Stack>
                </Card>

                <Card radius="lg" withBorder className="bg-night-900/20">
                    <Group justify="space-between" align="center">
                        <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.25em' }}>
                            Coaching sessions
                        </Text>
                        <Button component={Link} to="/agents" variant="subtle" size="xs">
                            Delegate
                        </Button>
                    </Group>
                    <Stack gap="sm" mt="md">
                        {selectedTemplate.sessions.map((session) => (
                            <AgentActionCard
                                key={session.id}
                                label={`${session.title} · ${session.duration}`}
                                description={session.description}
                                badge="Session"
                                cta={session.cta}
                                onSelect={() => navigate('/agents')}
                            />
                        ))}
                    </Stack>
                </Card>

                <Card radius="lg" withBorder className="bg-night-900/30">
                    <Group justify="space-between" align="center">
                        <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.25em' }}>
                            Data playground
                        </Text>
                        <Button component={Link} to="/executor" variant="light" size="xs" radius="xl">
                            Open executor
                        </Button>
                    </Group>
                    <Grid gutter="lg" mt="md">
                        <Grid.Col span={{ base: 12, md: 6 }}>
                            <Stack gap="sm">
                                <Group justify="space-between">
                                    <Title order={5}>Recent runs</Title>
                                    <Text size="xs" c="gray.5">
                                        {runsQuery.isLoading ? 'Loading…' : `${runsQuery.data?.length ?? 0} entries`}
                                    </Text>
                                </Group>
                                {runsQuery.isError && <Alert color="red">Unable to load runs.</Alert>}
                                {runsQuery.isLoading ? (
                                    <Loader size="sm" />
                                ) : (runsQuery.data ?? []).length ? (
                                    (runsQuery.data ?? []).map((run) => (
                                        <Card key={run.run_id} radius="md" withBorder className="bg-night-900/50">
                                            <Text fw={600}>{run.goal}</Text>
                                            <Text size="xs" c="gray.4">
                                                {run.run_id} · {run.status}
                                            </Text>
                                        </Card>
                                    ))
                                ) : (
                                    <Text size="sm" c="gray.5">
                                        Launch an agent to see runs here.
                                    </Text>
                                )}
                            </Stack>
                        </Grid.Col>
                        <Grid.Col span={{ base: 12, md: 6 }}>
                            <Stack gap="sm">
                                <Group justify="space-between">
                                    <Title order={5}>Evidence</Title>
                                    <Text size="xs" c="gray.5">
                                        {evidenceQuery.isLoading ? 'Loading…' : `${evidenceQuery.data?.length ?? 0} notes`}
                                    </Text>
                                </Group>
                                {evidenceQuery.isError && <Alert color="red">Unable to load evidence.</Alert>}
                                {evidenceQuery.isLoading ? (
                                    <Loader size="sm" />
                                ) : (evidenceQuery.data ?? []).length ? (
                                    (evidenceQuery.data ?? []).map((item) => (
                                        <Card key={item.run_id} radius="md" withBorder className="bg-night-900/50">
                                            <Text fw={600}>Run {item.run_id}</Text>
                                            <Text size="xs" c="gray.4">
                                                {(item.explanation?.summary as unknown as string) ?? 'Explanation stored in kernel'}
                                            </Text>
                                        </Card>
                                    ))
                                ) : (
                                    <Text size="sm" c="gray.5">
                                        Log evidence from the executor to see it here.
                                    </Text>
                                )}
                            </Stack>
                        </Grid.Col>
                    </Grid>
                </Card>
            </Stack>
            <Stack>
                <Text size="xs" fw={600} tt="uppercase" c="blue.3" style={{ letterSpacing: '0.25em' }}>
                    Copilot chat
                </Text>
                <Title order={3} c="white">
                    Conversational coach
                </Title>
                <Text size="sm" c="gray.4">
                    Ask about goals, connector health, or next best actions. Responses come with action cards that jump into Planner, Agents, or the Executor.
                </Text>
                <ChatShell prompts={selectedTemplate.prompts.copilot} templateId={selectedTemplate.archetypeId} />
            </Stack>
        </Card>
    )
}
