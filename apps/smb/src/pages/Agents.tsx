import { Alert, Badge, Button, Card, Grid, Group, Loader, Stack, Text, Title } from '@mantine/core'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import ChatShell from '../components/ChatShell'
import { fetchCatalog, listRuns, triggerRun, type CatalogItem, type RunRecord } from '../lib/api'
import { useConnectorsQuery } from '../hooks/useConnectors'
import { useAuthStore } from '../stores/auth'
import { useTemplateStore } from '../stores/template'

export default function Agents() {
    const tenantId = useAuthStore((s: any) => s.tenantId)
    const apiToken = useAuthStore((s: any) => s.apiToken)
    const { selectedTemplate } = useTemplateStore()
    const queryClient = useQueryClient()
    const connectorsQuery = useConnectorsQuery(apiToken, tenantId)

    const {
        data: catalogData,
        isLoading: catalogLoading,
        isError: catalogError,
    } = useQuery({
        queryKey: ['catalog'],
        enabled: Boolean(apiToken),
        queryFn: () => fetchCatalog(apiToken),
    })

    const {
        data: runsData,
        isLoading: runsLoading,
        isError: runsError,
    } = useQuery({
        queryKey: ['runs'],
        enabled: Boolean(apiToken),
        queryFn: () => listRuns(apiToken, 5),
    })

    const displayedCatalog = catalogData ?? []
    const erpnextConnected = (connectorsQuery.data ?? []).some((connector) => connector.connector_type === 'erpnext')

    const erpAgents = [
        {
            key: 'fulfillment-pulse',
            title: 'Fulfillment Pulse',
            description: 'Use ERP-driven orders to spot shipping delays, flagged SKUs, and staffing needs during peak demand.',
            templateId: 'inventory_basic',
            requiresErpnext: true,
        },
        {
            key: 'accessory-bundler',
            title: 'Accessory Bundler',
            description: 'Analyze bundle attach rates and draft promos that pair base products with high-margin accessories.',
            templateId: 'inventory_basic',
            requiresErpnext: true,
        },
        {
            key: 'parts-forecaster',
            title: 'Replacement Parts Forecaster',
            description: 'Forecast spare-part demand from ERP sales history and push restock tasks into Planner.',
            templateId: 'inventory_basic',
            requiresErpnext: true,
        },
    ]

    const launchMutation = useMutation({
        mutationFn: async ({ templateId, name }: { templateId: string; name: string }) => {
            if (!apiToken) throw new Error('Missing token')
            const payload = {
                template_id: templateId,
                goal: `Execute ${name} playbook`,
                project_id: `demo-${templateId}-${Date.now().toString(36)}`,
                mode: 'plan',
            }
            return await triggerRun(payload, apiToken)
        },
        onSuccess: (response, variables) => {
            if (!response) return
            queryClient.setQueryData<RunRecord[]>(['runs'], (prev = []) => [{ run_id: response.run_id, status: response.status, goal: `Execute ${variables.name} playbook` }, ...prev].slice(0, 5))
        },
    })

    const runs = runsData ?? []

    const automationPrompts = selectedTemplate.prompts.agents

    return (
        <Card radius="xl" withBorder className="mx-auto w-full max-w-6xl bg-night-800/80 px-4 py-8 shadow-card md:px-8">
            <Grid gutter="xl">
                <Grid.Col span={{ base: 12, md: 7 }}>
                    <Stack gap="lg">
                        <div>
                            <Text size="xs" fw={600} tt="uppercase" c="blue.3" style={{ letterSpacing: '0.25em' }}>
                                Automation agents
                            </Text>
                            <Title order={2} c="white">
                                Run playbooks through chat + action cards
                            </Title>
                            <Text c="gray.4">
                                Assign Dyocense agents to execute templates from the catalog. Each run hits the kernel’s /v1/runs endpoint so planners, evidence, and audits stay in sync. The{' '}
                                <strong>{selectedTemplate.name}</strong> workspace highlights the goals below.
                            </Text>
                        </div>
                        <Card radius="lg" withBorder className="bg-night-900/30">
                            <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.4em' }}>
                                {selectedTemplate.industry} goals
                            </Text>
                            <Stack gap="xs" mt="sm">
                                {selectedTemplate.goals.map((goal) => (
                                    <Group key={goal.id} justify="space-between" align="flex-start">
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
                                ))}
                            </Stack>
                        </Card>
                        {catalogError && <Alert color="red">Unable to load catalog.</Alert>}
                        {catalogLoading ? (
                            <Loader />
                        ) : displayedCatalog.length ? (
                            <Grid gutter="md">
                                {displayedCatalog.map((item) => (
                                    <Grid.Col span={{ base: 12, md: 4 }} key={item.id}>
                                        <Card radius="lg" withBorder className="bg-white/5 h-full">
                                            <Title order={4}>{item.name}</Title>
                                            <Text size="sm" c="gray.4" mt="xs">
                                                {item.description}
                                            </Text>
                                            <Button
                                                fullWidth
                                                radius="xl"
                                                mt="md"
                                                loading={launchMutation.isPending && launchMutation.variables?.templateId === item.id}
                                                onClick={() => launchMutation.mutate({ templateId: item.id, name: item.name ?? item.id })}
                                            >
                                                Launch agent
                                            </Button>
                                        </Card>
                                    </Grid.Col>
                                ))}
                            </Grid>
                        ) : (
                            <Card radius="lg" withBorder className="bg-night-900/50">
                                <Title order={4}>No catalog entries yet</Title>
                                <Text size="sm" c="gray.4" mt="xs">
                                    Connect your POS, ERP, or storefront so Dyocense can recommend the right playbooks.
                                </Text>
                                <Button component={Link} to="/connectors" radius="xl" mt="md" variant="light">
                                    Connect data sources
                                </Button>
                            </Card>
                        )}
                        <Card radius="lg" withBorder className="bg-night-900/40">
                            <Group justify="space-between" align="center" mb="sm">
                                <Title order={4}>ERP commerce agents</Title>
                                {!erpnextConnected && (
                                    <Badge variant="light" color="red">
                                        Connect ERP to unlock
                                    </Badge>
                                )}
                            </Group>
                            <Grid gutter="md">
                                {erpAgents.map((agent) => (
                                    <Grid.Col span={{ base: 12, md: 4 }} key={agent.key}>
                                        <Card radius="lg" withBorder className="bg-night-900/60 h-full">
                                            <Title order={4}>{agent.title}</Title>
                                            <Text size="sm" c="gray.4" mt="xs">
                                                {agent.description}
                                            </Text>
                                            {agent.requiresErpnext && !erpnextConnected ? (
                                                <Button component={Link} to="/connectors" fullWidth radius="xl" mt="md" variant="light">
                                                    Connect ERP source
                                                </Button>
                                            ) : (
                                                <Button
                                                    fullWidth
                                                    radius="xl"
                                                    mt="md"
                                                    loading={launchMutation.isPending && launchMutation.variables?.templateId === agent.templateId}
                                                    onClick={() => launchMutation.mutate({ templateId: agent.templateId, name: agent.title })}
                                                >
                                                    Run agent
                                                </Button>
                                            )}
                                        </Card>
                                    </Grid.Col>
                                ))}
                            </Grid>
                        </Card>
                        <Card radius="lg" withBorder className="bg-night-900/40">
                            <Group justify="space-between" align="center">
                                <Title order={4}>Recent agent runs</Title>
                                <Button variant="light" radius="xl" onClick={() => queryClient.invalidateQueries({ queryKey: ['runs'] })}>
                                    Refresh
                                </Button>
                            </Group>
                            {runsError && <Alert color="red" mt="md">Unable to load runs.</Alert>}
                            {runsLoading ? (
                                <Loader mt="md" />
                            ) : runs.length ? (
                                <Stack gap="sm" mt="md">
                                    {runs.map((run) => (
                                        <Card key={run.run_id} radius="lg" withBorder className="bg-white/5">
                                            <Group justify="space-between">
                                                <div>
                                                    <Text fw={600}>{run.goal}</Text>
                                                    <Text size="xs" c="gray.4">
                                                        Run ID: {run.run_id}
                                                    </Text>
                                                </div>
                                                <Button size="xs" variant="outline" radius="xl">
                                                    {run.status}
                                                </Button>
                                            </Group>
                                        </Card>
                                    ))}
                                </Stack>
                            ) : (
                                <Text mt="md" size="sm" c="gray.4">
                                    No runs yet. Launch an agent to see activity.
                                </Text>
                            )}
                        </Card>
                        <Card radius="lg" withBorder className="bg-night-900/20">
                            <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.4em' }}>
                                Suggested sessions
                            </Text>
                            <Stack gap="xs" mt="sm">
                                {selectedTemplate.sessions.map((session) => (
                                    <AgentActionCard
                                        key={session.id}
                                        label={`${session.title} · ${session.duration}`}
                                        description={session.description}
                                        badge="Session"
                                        cta={session.cta}
                                        onSelect={() => launchMutation.mutate({ templateId: selectedTemplate.archetypeId, name: session.title })}
                                    />
                                ))}
                            </Stack>
                        </Card>
                        <Text size="xs" c="gray.4">
                            Tenant: <span className="font-mono text-white">{tenantId}</span>
                        </Text>
                    </Stack>
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 5 }}>
                    <ChatShell
                        title="Automation copilot"
                        description="Ask for messages, workflows, or connectors. I’ll show cards to run the right playbook."
                        prompts={automationPrompts}
                        templateId={selectedTemplate.archetypeId}
                    />
                </Grid.Col>
            </Grid>
        </Card>
    )
}
