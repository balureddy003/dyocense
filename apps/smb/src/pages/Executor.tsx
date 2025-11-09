import { Alert, Badge, Button, Card, Grid, Group, Loader, Stack, Text, Title } from '@mantine/core'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import React from 'react'
import ChatShell from '../components/ChatShell'
import { type EvidenceRecord, listEvidence, listRuns, logEvidence, type RunRecord } from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { useTemplateStore } from '../stores/template'

export default function Executor() {
    const tenantId = useAuthStore((s: any) => s.tenantId)
    const apiToken = useAuthStore((s: any) => s.apiToken)
    const { selectedTemplate } = useTemplateStore()
    const queryClient = useQueryClient()
    const [statusMessage, setStatusMessage] = React.useState<string | null>(null)

    const runsQuery = useQuery({
        queryKey: ['runs'],
        enabled: Boolean(apiToken),
        queryFn: () => listRuns(apiToken, 5),
    })

    const evidenceQuery = useQuery({
        queryKey: ['evidence'],
        enabled: Boolean(apiToken),
        queryFn: () => listEvidence(apiToken, 5),
    })

    const runs = runsQuery.data ?? []
    const evidence = evidenceQuery.data ?? []

    const logMutation = useMutation({
        mutationFn: async ({ run }: { run: RunRecord }) => {
            if (!apiToken) return null
            const payload = {
                run_id: run.run_id,
                ops: { summary: run.goal },
                solution: run.result ?? { status: run.status },
                explanation: run.result?.explanation ?? { summary: 'SMB console note' },
            }
            return await logEvidence(payload, apiToken)
        },
        onSuccess: (_response, variables) => {
            setStatusMessage(`Evidence logged for ${variables.run.run_id}`)
            queryClient.invalidateQueries({ queryKey: ['evidence'] })
        },
        onError: () => {
            setStatusMessage('Unable to log evidence—check connectivity.')
        },
    })

    const prompts = selectedTemplate.prompts.executor

    const planHint = runs[0] ? `Latest run ${runs[0].run_id} status: ${runs[0].status}` : undefined

    return (
        <Card radius="xl" withBorder className="mx-auto w-full max-w-6xl bg-night-800/80 px-4 py-8 shadow-card md:px-8">
            <Grid gutter="xl">
                <Grid.Col span={{ base: 12, md: 7 }}>
                    <Stack gap="lg">
                        <div>
                            <Text size="xs" fw={600} tt="uppercase" c="blue.3" style={{ letterSpacing: '0.25em' }}>
                                Execution console
                            </Text>
                            <Title order={2} c="white">
                                Prove progress, unblock owners, log evidence
                            </Title>
                            <Text c="gray.4">
                                Every kernel run emits evidence so you can export decisions, share status digests, and hand compliance a clean audit path.
                            </Text>
                        </div>
                        <Card radius="lg" withBorder className="bg-night-900/40">
                            {statusMessage && (
                                <Stack gap="xs" mb="md">
                                    <Text data-testid="log-status" size="sm" c="gray.2">
                                        {statusMessage}
                                    </Text>
                                </Stack>
                            )}
                            <Group justify="space-between" align="center">
                                <Title order={4}>Recent runs</Title>
                                <Button variant="light" radius="xl" onClick={() => queryClient.invalidateQueries({ queryKey: ['runs'] })}>
                                    Refresh
                                </Button>
                            </Group>
                            {runsQuery.isError && <Alert color="red" mt="md">Unable to load runs.</Alert>}
                            {runsQuery.isLoading ? (
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
                                                <Button size="xs" radius="xl" variant="outline">
                                                    {run.status}
                                                </Button>
                                            </Group>
                                        </Card>
                                    ))}
                                </Stack>
                            ) : (
                                <Text mt="md" size="sm" c="gray.4">
                                    No runs to display.
                                </Text>
                            )}
                        </Card>

                        <Card radius="lg" withBorder className="bg-night-900/40">
                            <Title order={4}>Evidence log</Title>
                            {evidenceQuery.isError && <Alert color="red" mt="md">Unable to load evidence.</Alert>}
                            {evidenceQuery.isLoading ? (
                                <Loader mt="md" />
                            ) : evidence.length ? (
                                <Stack gap="sm" mt="md">
                                    {evidence.map((item) => (
                                        <Card key={item.run_id} radius="lg" withBorder className="bg-white/5">
                                            <Group justify="space-between">
                                                <div>
                                                    <Text fw={600}>Run {item.run_id}</Text>
                                                    <Text size="xs" c="gray.4">
                                                        Stored: {item.stored_at ?? 'local cache'}
                                                    </Text>
                                                </div>
                                                <Text size="xs" c="gray.4">
                                                    {(item.explanation?.summary as unknown as string) ?? 'Explanation available in kernel'}
                                                </Text>
                                            </Group>
                                        </Card>
                                    ))}
                                </Stack>
                            ) : (
                                <Text mt="md" size="sm" c="gray.4">
                                    No evidence records yet. They appear as soon as agents finish.
                                </Text>
                            )}
                        </Card>

                        {runs.length ? (
                            <Group>
                                <Button
                                    radius="xl"
                                    loading={logMutation.isPending}
                                    onClick={() => {
                                        setStatusMessage(`Evidence logged for ${runs[0].run_id}`)
                                        logMutation.mutate({ run: runs[0] })
                                    }}
                                >
                                    {logMutation.isPending ? 'Logging…' : 'Log decision evidence'}
                                </Button>
                                <Button variant="outline" radius="xl">
                                    Send digest
                                </Button>
                            </Group>
                        ) : (
                            <Text size="sm" c="gray.4">
                                Load a run to enable evidence logging.
                            </Text>
                        )}

                        <Card radius="lg" withBorder className="bg-night-900/20">
                            <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.4em' }}>
                                Template signals
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
                        <Text size="xs" c="gray.4">
                            Tenant: <span className="font-mono text-white">{tenantId}</span>
                        </Text>
                    </Stack>
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 5 }}>
                    <ChatShell
                        title="Evidence copilot"
                        description="Ask for summaries, explanations, or auto-generated digests. I’ll show action cards to jump into Executors."
                        prompts={prompts}
                        templateId={selectedTemplate.archetypeId}
                        planHint={planHint}
                    />
                </Grid.Col>
            </Grid>
        </Card>
    )
}
