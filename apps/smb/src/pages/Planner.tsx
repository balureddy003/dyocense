import { ActionIcon, Alert, Badge, Button, Card, Group, Loader, Modal, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconCheck, IconCircle, IconRefresh, IconSparkles, IconX } from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { get, post } from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { useTemplateStore } from '../stores/template'

type Task = {
    id?: string
    label: string
    owner?: string
    status?: string
    priority?: 'high' | 'medium' | 'low'
}

type Plan = {
    id: string
    title: string
    tasks: Task[]
}

export default function Planner() {
    const tenantId = useAuthStore((s: any) => s.tenantId)
    const apiToken = useAuthStore((s: any) => s.apiToken)
    const { selectedTemplate } = useTemplateStore()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [searchParams] = useSearchParams()

    // Deep linking support for taskId
    const taskIdParam = searchParams.get('taskId')
    const [selectedTaskIndex, setSelectedTaskIndex] = useState<number | null>(null)
    const [taskDetailOpen, setTaskDetailOpen] = useState(false)

    // Check if coming from coach page
    const [showWelcomeBanner, setShowWelcomeBanner] = React.useState(() => {
        const fromCoach = sessionStorage.getItem('fromCoachPage')
        if (fromCoach === 'true') {
            sessionStorage.removeItem('fromCoachPage')
            return true
        }
        return false
    })

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

    // Handle deep linking to specific task
    useEffect(() => {
        if (taskIdParam && plan?.tasks) {
            const taskIndex = plan.tasks.findIndex((t: Task) => t.id === taskIdParam || t.label.includes(taskIdParam))
            if (taskIndex !== -1) {
                setSelectedTaskIndex(taskIndex)
                setTaskDetailOpen(true)
            }
        }
    }, [taskIdParam, plan]);

    const taskStats = React.useMemo(() => {
        if (!plan?.tasks?.length) return { total: 0, completed: 0, inProgress: 0, pending: 0 }
        const total = plan.tasks.length
        const completed = plan.tasks.filter((t) => (t.status ?? '').toLowerCase().includes('done') || (t.status ?? '').toLowerCase().includes('complete')).length
        const inProgress = plan.tasks.filter((t) => (t.status ?? '').toLowerCase().includes('progress') || (t.status ?? '').toLowerCase().includes('doing')).length
        const pending = total - completed - inProgress
        return { total, completed, inProgress, pending }
    }, [plan])

    const completionRate = plan?.tasks?.length ? Math.round((taskStats.completed / plan.tasks.length) * 100) : 0

    const regenerateMutation = useMutation({
        mutationFn: async () => {
            let latestGoalId: string | undefined
            try {
                latestGoalId = sessionStorage.getItem('latestGoalId') || undefined
            } catch { }

            return await post<Plan>(
                `/v1/tenants/${encodeURIComponent(tenantId!)}/plans`,
                {
                    archetype_id: selectedTemplate?.archetypeId,
                    regenerate: true,
                    goal_id: latestGoalId,
                },
                apiToken,
            )
        },
        onSuccess: (plan) => {
            queryClient.setQueryData(['plan', tenantId], plan)
        },
    })

    if (!tenantId) {
        return (
            <div style={{ padding: '40px', textAlign: 'center' }}>
                <Title order={2}>Action Plan</Title>
                <Text c="dimmed" mt="md">
                    Sign in to view your action plan
                </Text>
            </div>
        )
    }

    return (
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
            {/* Header */}
            <Group justify="space-between" mb="xl">
                <div>
                    <Title order={1}>Action Plan</Title>
                    <Text c="dimmed" size="sm">
                        Your tasks and priorities
                    </Text>
                </div>
                <Group>
                    <Button
                        variant="light"
                        leftSection={<IconSparkles size={16} />}
                        onClick={() => navigate('/coach')}
                    >
                        AI Coach
                    </Button>
                    <Button
                        variant="outline"
                        leftSection={<IconRefresh size={16} />}
                        onClick={() => regenerateMutation.mutate()}
                        loading={regenerateMutation.isPending}
                    >
                        Regenerate
                    </Button>
                </Group>
            </Group>

            {/* Welcome Banner */}
            {showWelcomeBanner && !plan && (
                <Alert
                    variant="light"
                    color="blue"
                    title="Ready to create your action plan!"
                    withCloseButton
                    onClose={() => setShowWelcomeBanner(false)}
                    icon={<IconSparkles size={20} />}
                    mb="lg"
                >
                    <Text size="sm" mb="sm">
                        Your coach helped refine your goal. Now let's turn it into a weekly action plan.
                    </Text>
                    <Button
                        size="sm"
                        variant="light"
                        onClick={() => {
                            regenerateMutation.mutate()
                            setShowWelcomeBanner(false)
                        }}
                        loading={regenerateMutation.isPending}
                    >
                        Generate Action Plan
                    </Button>
                </Alert>
            )}

            {/* Fitness Tracker Style Stats */}
            {plan && (
                <>
                    <Card withBorder radius="lg" p="xl" mb="lg" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                        <Group justify="space-between" align="flex-start" mb="xl">
                            <div>
                                <Text size="sm" c="white" opacity={0.9} mb={4}>
                                    WEEKLY PLAN
                                </Text>
                                <Title order={3} c="white">
                                    {plan.title}
                                </Title>
                            </div>
                            <Badge size="lg" color="white" variant="filled" style={{ color: '#667eea' }}>
                                {completionRate}% Complete
                            </Badge>
                        </Group>

                        {/* Ring Progress */}
                        <div style={{ position: 'relative', height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
                            <svg width="200" height="200" style={{ transform: 'rotate(-90deg)' }}>
                                {/* Background ring */}
                                <circle
                                    cx="100"
                                    cy="100"
                                    r="85"
                                    fill="none"
                                    stroke="rgba(255,255,255,0.2)"
                                    strokeWidth="20"
                                />
                                {/* Progress ring */}
                                <circle
                                    cx="100"
                                    cy="100"
                                    r="85"
                                    fill="none"
                                    stroke="white"
                                    strokeWidth="20"
                                    strokeLinecap="round"
                                    strokeDasharray={`${(completionRate / 100) * 534} 534`}
                                    style={{ transition: 'stroke-dasharray 0.6s ease' }}
                                />
                            </svg>
                            <div style={{ position: 'absolute', textAlign: 'center' }}>
                                <Text size="48px" fw={700} c="white" style={{ lineHeight: 1 }}>
                                    {taskStats.completed}
                                </Text>
                                <Text size="sm" c="white" opacity={0.9}>
                                    of {taskStats.total} tasks
                                </Text>
                            </div>
                        </div>

                        {/* Mini Stats */}
                        <Group justify="center" gap="xl">
                            <div style={{ textAlign: 'center' }}>
                                <Text size="xl" fw={700} c="white">
                                    {taskStats.inProgress}
                                </Text>
                                <Text size="xs" c="white" opacity={0.8}>
                                    In Progress
                                </Text>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                                <Text size="xl" fw={700} c="white">
                                    {taskStats.pending}
                                </Text>
                                <Text size="xs" c="white" opacity={0.8}>
                                    To Do
                                </Text>
                            </div>
                        </Group>
                    </Card>

                    {/* Tasks List - Simplified */}
                    <Stack gap="md">
                        <Group justify="space-between">
                            <Title order={4}>Your Tasks</Title>
                            <Text size="sm" c="dimmed">
                                {taskStats.total} total
                            </Text>
                        </Group>

                        {isLoading ? (
                            <Card withBorder p="xl">
                                <Loader />
                            </Card>
                        ) : (
                            plan.tasks?.map((task, idx) => {
                                const isDone = (task.status ?? '').toLowerCase().includes('done') || (task.status ?? '').toLowerCase().includes('complete')
                                const isProgress = (task.status ?? '').toLowerCase().includes('progress') || (task.status ?? '').toLowerCase().includes('doing')

                                return (
                                    <Card
                                        key={`${task.label}-${idx}`}
                                        withBorder
                                        radius="md"
                                        p="md"
                                        style={{
                                            background: isDone ? '#f0fff4' : 'white',
                                            borderLeft: isDone ? '4px solid #51cf66' : isProgress ? '4px solid #ffd43b' : '4px solid #e9ecef',
                                        }}
                                    >
                                        <Group justify="space-between" wrap="nowrap">
                                            <Group gap="md" style={{ flex: 1 }}>
                                                <ActionIcon
                                                    size="lg"
                                                    radius="xl"
                                                    variant={isDone ? 'filled' : 'light'}
                                                    color={isDone ? 'green' : isProgress ? 'yellow' : 'gray'}
                                                >
                                                    {isDone ? <IconCheck size={18} /> : <IconCircle size={18} />}
                                                </ActionIcon>
                                                <div style={{ flex: 1 }}>
                                                    <Text fw={500} style={{ textDecoration: isDone ? 'line-through' : 'none', opacity: isDone ? 0.7 : 1 }}>
                                                        {task.label}
                                                    </Text>
                                                    {task.owner && (
                                                        <Text size="xs" c="dimmed">
                                                            {task.owner}
                                                        </Text>
                                                    )}
                                                </div>
                                            </Group>
                                            <Badge
                                                color={isDone ? 'green' : isProgress ? 'yellow' : 'gray'}
                                                variant="light"
                                            >
                                                {task.status ?? 'Pending'}
                                            </Badge>
                                        </Group>
                                    </Card>
                                )
                            })
                        )}
                    </Stack>

                    {/* Quick Actions */}
                    <Card withBorder radius="lg" p="lg" mt="xl" style={{ background: '#f8f9fa' }}>
                        <Text size="sm" fw={600} c="dimmed" mb="md">
                            QUICK ACTIONS
                        </Text>
                        <Group>
                            <Button
                                variant="light"
                                leftSection={<IconSparkles size={16} />}
                                onClick={() => navigate('/coach')}
                            >
                                Refine with AI Coach
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => navigate('/goals')}
                            >
                                View Goals
                            </Button>
                        </Group>
                    </Card>

                    {/* Task Detail Modal - New */}
                    <Modal
                        opened={taskDetailOpen}
                        onClose={() => setTaskDetailOpen(false)}
                        title="Task Details"
                        size="lg"
                    >
                        {selectedTaskIndex !== null && plan.tasks && (
                            <TaskDetailView
                                task={plan.tasks[selectedTaskIndex]}
                                onClose={() => setTaskDetailOpen(false)}
                            />
                        )}
                    </Modal>
                </>
            )}

            {/* No Plan State */}
            {!plan && !isLoading && (
                <Card withBorder radius="lg" p="xl" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 64, marginBottom: 16 }}>📋</div>
                    <Title order={3} mb="sm">
                        No action plan yet
                    </Title>
                    <Text c="dimmed" mb="xl" maw={500} mx="auto">
                        Create an action plan to break your goals into weekly tasks and track your progress.
                    </Text>
                    <Button
                        size="lg"
                        onClick={() => regenerateMutation.mutate()}
                        loading={regenerateMutation.isPending}
                        leftSection={<IconSparkles size={20} />}
                    >
                        Generate Action Plan
                    </Button>
                </Card>
            )}

            {isError && (
                <Alert color="red" title="Unable to load plan" mb="lg">
                    Please try refreshing the page or contact support.
                </Alert>
            )}
        </div>
    )
}

// New TaskDetailView component for modal
function TaskDetailView({ task, onClose }: { task: Task, onClose: () => void }) {
    const [taskData, setTaskData] = useState<Task>(task)

    const updateTaskMutation = useMutation({
        mutationFn: async (updatedTask: Task) => {
            if (!updatedTask.id) throw new Error('Task ID is required')
            return await post<Task>(
                `/v1/tenants/${encodeURIComponent(taskData.tenantId!)}/tasks/${encodeURIComponent(updatedTask.id)}`,
                updatedTask,
                taskData.apiToken,
            )
        },
        onSuccess: (data) => {
            setTaskData(data)
        },
    })

    return (
        <div>
            <Text size="lg" fw={500} mb="md">
                {taskData.label}
            </Text>
            <Textarea
                value={taskData.description}
                onChange={(e) => setTaskData({ ...taskData, description: e.target.value })}
                placeholder="Task description"
                label="Description"
                minRows={2}
                mb="md"
            />
            <Group position="apart" mt="md">
                <Button
                    variant="light"
                    onClick={() => {
                        onClose()
                        updateTaskMutation.mutate(taskData)
                    }}
                    loading={updateTaskMutation.isPending}
                >
                    Save Changes
                </Button>
                <Button
                    variant="outline"
                    color="red"
                    onClick={() => {
                        onClose()
                        // Optionally, add task deletion logic here
                    }}
                >
                    <IconX size={16} /> Delete Task
                </Button>
            </Group>
        </div>
    )
}
