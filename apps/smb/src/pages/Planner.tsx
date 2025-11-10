import { Alert, Badge, Button, Card, Divider, Group, Loader, Progress, SimpleGrid, Stack, Text, Title } from '@mantine/core'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import React from 'react'
import { useNavigate } from 'react-router-dom'
import AgentActionCard from '../components/AgentActionCard'
import ChatShell from '../components/ChatShell'
import { get, tryPost } from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { useTemplateStore } from '../stores/template'

type Plan = {
    id: string
    title: string
    tasks: { label: string; owner?: string; status?: string }[]
}

export default function Planner() {
    const tenantId = useAuthStore((s: any) => s.tenantId)
    const apiToken = useAuthStore((s: any) => s.apiToken)
    const { selectedTemplate } = useTemplateStore()
    const navigate = useNavigate()
    const queryClient = useQueryClient()

    const { data: planData, isLoading, isError } = useQuery({
        queryKey: ['plan', tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const res = await get<{ items?: Plan[] } | Plan[]>(`/v1/tenants/${encodeURIComponent(tenantId!)}/plans`, apiToken)
            const items = Array.isArray(res) ? res : res?.items ?? []
            return items[0] ?? null
        },
        retry: 1,
    })

    const plan = planData

    const taskStats = React.useMemo(() => {
        if (!plan?.tasks?.length) return { total: 0, assigned: 0, inMotion: 0 }
        const total = plan.tasks.length
        const assigned = plan.tasks.filter((task) => Boolean(task.owner)).length
        const inMotion = plan.tasks.filter((task) => (task.status ?? '').toLowerCase() !== 'planned').length
        return { total, assigned, inMotion }
    }, [plan])

    const statusColor = (status?: string) => {
        const normalized = (status ?? 'planned').toLowerCase()
        if (normalized.includes('done') || normalized.includes('complete')) return 'green'
        if (normalized.includes('risk') || normalized.includes('block')) return 'red'
        if (normalized.includes('progress') || normalized.includes('doing')) return 'yellow'
        return 'gray'
    }

    const regenerateMutation = useMutation({
        mutationFn: async () => {
            return await tryPost<Plan | null>(
                `/v1/tenants/${encodeURIComponent(tenantId!)}/plans`,
                { archetype_id: selectedTemplate.archetypeId, regenerate: true },
                apiToken,
            )
        },
        onSuccess: (plan) => {
            if (!plan) return
            queryClient.setQueryData(['plan', tenantId], plan)
        },
    })

    if (!tenantId) {
        return (
            <div className="mx-auto max-w-3xl rounded-3xl border border-white/10 bg-night-800/80 px-6 py-10 text-center shadow-card">
                <h1 className="text-3xl font-semibold text-white">Planner</h1>
                <p className="mt-2 text-slate-300">Complete signup and verification to unlock the Planner.</p>
            </div>
        )
    }

    const planHintText = plan
        ? `Current plan "${plan.title}" with ${plan.tasks?.length ?? 0} tasks.`
        : `Template: ${selectedTemplate.name} focuses on ${selectedTemplate.goals[0]?.title}.`
    const planPrompts = plan
        ? [
            `Rewrite the "${plan.tasks[0]?.label ?? 'first'}" task with more detail`,
            ...selectedTemplate.prompts.planner,
        ]
        : selectedTemplate.prompts.planner

    const focusTasks = plan?.tasks.slice(0, 2) ?? []
    const backlogTasks = plan?.tasks.slice(2) ?? []
    const suggestionPrompts = selectedTemplate.prompts.planner.slice(0, 3)
    const flowGuide = [
        { label: 'Plan', description: 'Use the copilot to clarify goals, owners, and blockers.' },
        { label: 'Agents', description: 'Delegate execution steps (messages, schedules, promos).' },
        { label: 'Executor', description: 'Track runs, log evidence, export digests.' },
    ]

    return (
        <div className="mx-auto w-full max-w-6xl rounded-3xl border border-white/10 bg-night-800/80 px-4 py-8 shadow-card md:px-8">
            <div className="grid gap-6 md:grid-cols-[1.1fr_0.9fr]">
                <div className="space-y-6">
                    <Stack gap="xs">
                        <Text size="xs" fw={600} tt="uppercase" ls={4} c="blue.3">
                            Planner
                        </Text>
                        <Title order={2} c="white">
                            Tenant: {tenantId}
                        </Title>
                        <Text c="gray.4">Plans stay in sync with automations and the execution console.</Text>
                    </Stack>
                    {isError && <Alert color="red">Unable to fetch plan. Showing template guidance instead.</Alert>}
                    {plan ? (
                        <Stack gap="lg">
                            <Card radius="xl" withBorder className="bg-white/5">
                                <Group justify="space-between" align="flex-start">
                                    <div>
                                        <Title order={3}>{plan.title}</Title>
                                        <Text size="sm" c="gray.4">
                                            ID: {plan.id}
                                        </Text>
                                    </div>
                                    <Group>
                                        <Button
                                            onClick={() => regenerateMutation.mutate()}
                                            loading={regenerateMutation.isPending}
                                            radius="xl"
                                            variant="light"
                                        >
                                            Regenerate with AI
                                        </Button>
                                        <Button radius="xl" variant="outline" onClick={() => navigate('/executor')}>
                                            Share status
                                        </Button>
                                    </Group>
                                </Group>
                                <Text size="sm" c="gray.4" mt="sm">
                                    This plan follows the <strong>{selectedTemplate.name}</strong> template. Finish the actions below, then hand off to Agents and the Executor.
                                </Text>
                                <SimpleGrid cols={{ base: 1, sm: 3 }} mt="lg">
                                    <div>
                                        <Text size="xs" c="gray.5">
                                            Total tasks
                                        </Text>
                                        <Title order={3}>{taskStats.total}</Title>
                                    </div>
                                    <div>
                                        <Text size="xs" c="gray.5">
                                            Assigned
                                        </Text>
                                        <Title order={3}>{taskStats.assigned}</Title>
                                    </div>
                                    <div>
                                        <Text size="xs" c="gray.5">
                                            In motion
                                        </Text>
                                        <Title order={3}>{taskStats.inMotion}</Title>
                                    </div>
                                </SimpleGrid>
                                <Stack gap={4} mt="lg">
                                    <Group justify="space-between">
                                        <Text size="xs" c="gray.5">
                                            Plan progress
                                        </Text>
                                        <Text size="xs" c="gray.4">
                                            {taskStats.total ? Math.round((taskStats.inMotion / taskStats.total) * 100) : 0}%
                                        </Text>
                                    </Group>
                                    <Progress value={taskStats.total ? (taskStats.inMotion / taskStats.total) * 100 : 0} />
                                </Stack>
                            </Card>

                            <Card radius="xl" withBorder className="bg-night-900/40">
                                <Group justify="space-between" align="center" mb="sm">
                                    <Title order={4}>Today&apos;s focus</Title>
                                    <Button size="xs" variant="subtle" onClick={() => navigate('/agents')}>
                                        Hand off to agents
                                    </Button>
                                </Group>
                                {isLoading ? (
                                    <Loader />
                                ) : (
                                    <Stack gap="sm">
                                        {focusTasks.map((task, idx) => (
                                            <Card key={`${task.label}-${idx}`} radius="lg" withBorder className="bg-night-900/40">
                                                <Group justify="space-between" align="flex-start">
                                                    <Group gap="xs">
                                                        <Badge color="blue" variant="light">
                                                            {String(idx + 1).padStart(2, '0')}
                                                        </Badge>
                                                        <div>
                                                            <Text fw={500}>{task.label}</Text>
                                                            <Text size="xs" c="gray.5">
                                                                Owner: {task.owner ?? 'Unassigned'}
                                                            </Text>
                                                        </div>
                                                    </Group>
                                                    <Badge color={statusColor(task.status)} variant="outline">
                                                        {task.status ?? 'Planned'}
                                                    </Badge>
                                                </Group>
                                            </Card>
                                        ))}
                                        {!focusTasks.length && (
                                            <Text size="sm" c="gray.4">
                                                No prioritized tasks yet—use the chat to generate clarifying steps.
                                            </Text>
                                        )}
                                    </Stack>
                                )}
                            </Card>

                            {backlogTasks.length > 0 && (
                                <Card radius="xl" withBorder className="bg-night-900/30">
                                    <Title order={4}>Backlog</Title>
                                    <Text size="sm" c="gray.5" mb="sm">
                                        These steps sit behind the focus list. Reorder via Planner chat or assign owners before moving to Agents.
                                    </Text>
                                    <Stack gap="sm">
                                        {backlogTasks.map((task, idx) => (
                                            <Card key={`${task.label}-${idx}`} radius="md" withBorder className="bg-night-900/50">
                                                <Group justify="space-between" align="flex-start">
                                                    <div>
                                                        <Text fw={500}>{task.label}</Text>
                                                        <Text size="xs" c="gray.5">
                                                            Owner: {task.owner ?? 'Unassigned'}
                                                        </Text>
                                                    </div>
                                                    <Badge color={statusColor(task.status)} variant="light">
                                                        {task.status ?? 'Planned'}
                                                    </Badge>
                                                </Group>
                                            </Card>
                                        ))}
                                    </Stack>
                                </Card>
                            )}
                        </Stack>
                    ) : (
                        <Card radius="xl" withBorder className="bg-night-900/40">
                            {isLoading ? (
                                <Loader />
                            ) : (
                                <Stack gap="sm">
                                    <Text c="gray.4">No plan found for this tenant. Run onboarding to create a starter plan.</Text>
                                    <Button radius="xl" onClick={() => navigate('/home')}>
                                        Open onboarding
                                    </Button>
                                </Stack>
                            )}
                        </Card>
                    )}

                    <Card radius="xl" withBorder className="bg-night-900/30">
                        <p className="text-sm font-semibold uppercase tracking-[0.4em] text-slate-400">Copilot jumpstart</p>
                        <div className="mt-3 space-y-3">
                            {suggestionPrompts.map((prompt) => (
                                <AgentActionCard
                                    key={prompt}
                                    label={prompt}
                                    description="Send this to the Planner chat to convert it into steps, owners, and risks."
                                    badge="Prompt"
                                    cta="Ask copilot"
                                    onSelect={() => {
                                        const chatEl = document.getElementById('planner-chat')
                                        if (chatEl) chatEl.scrollIntoView({ behavior: 'smooth' })
                                    }}
                                />
                            ))}
                            <AgentActionCard
                                label="Summarize plan"
                                description="Generate an explainable digest and log it as evidence."
                                badge="Digest"
                                cta="View"
                                onSelect={() => navigate('/executor')}
                            />
                        </div>
                    </Card>
                    <Card radius="xl" withBorder className="bg-night-900/20">
                        <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.4em' }}>
                            Flow guide
                        </Text>
                        <Stack gap="sm" mt="md">
                            {flowGuide.map((step, idx) => (
                                <div key={step.label}>
                                    {idx > 0 && <Divider my="xs" color="white" opacity={0.1} />}
                                    <Group align="flex-start" gap="sm">
                                        <Badge radius="xl" variant="light">
                                            {String(idx + 1)}
                                        </Badge>
                                        <div>
                                            <Text fw={600}>{step.label}</Text>
                                            <Text size="sm" c="gray.4">
                                                {step.description}
                                            </Text>
                                        </div>
                                    </Group>
                                </div>
                            ))}
                        </Stack>
                    </Card>
                    <Card radius="xl" withBorder className="bg-night-900/20">
                        <Text size="xs" fw={600} tt="uppercase" c="gray.4" style={{ letterSpacing: '0.4em' }}>
                            Template sessions
                        </Text>
                        <Stack gap="sm" mt="md">
                            {selectedTemplate.sessions.map((session) => (
                                <AgentActionCard
                                    key={session.id}
                                    label={`${session.title} · ${session.duration}`}
                                    description={session.description}
                                    badge={selectedTemplate.industry}
                                    cta={session.cta}
                                    onSelect={() => navigate('/agents')}
                                />
                            ))}
                        </Stack>
                    </Card>
                </div>
                <div id="planner-chat">
                    <ChatShell
                        title="AI Coach"
                        description="Ask for refinements, risk analysis, or follow-ups. Responses include one-click cards."
                        prompts={planPrompts}
                        templateId={selectedTemplate.archetypeId}
                        planHint={planHintText}
                    />
                </div>
            </div>
        </div>
    )
}
