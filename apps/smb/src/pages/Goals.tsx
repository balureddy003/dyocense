import { ActionIcon, Alert, Badge, Button, Card, Container, Drawer, Group, Progress, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconArrowRight, IconSparkles, IconTrash } from '@tabler/icons-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StreakCounter from '../components/StreakCounter'
import { del, get, post, put } from '../lib/api'
import { celebrateGoalMilestone } from '../utils/celebrations'

interface Goal {
    id: string
    tenant_id: string
    title: string
    description: string
    current: number
    target: number
    unit: string
    category: 'revenue' | 'operations' | 'customer' | 'growth' | 'custom'
    status: 'active' | 'completed' | 'archived'
    deadline: string
    created_at: string
    updated_at: string
    auto_tracked: boolean
    connector_source?: string
    last_celebrated_milestone?: number // Track which milestones we've already celebrated
}

interface GoalVersionSnapshot {
    timestamp: number
    goal: Goal
}

function recordGoalVersion(goal: Goal) {
    try {
        const key = `goalVersions:${goal.id}`
        const existing: GoalVersionSnapshot[] = JSON.parse(localStorage.getItem(key) || '[]')
        existing.push({ timestamp: Date.now(), goal })
        localStorage.setItem(key, JSON.stringify(existing))
    } catch (e) {
        // swallow – localStorage may be unavailable
        console.warn('Failed to record goal version', e)
    }
}

export default function Goals() {
    const tenantId = localStorage.getItem('tenantId') || 'tenant-demo'
    const apiToken = localStorage.getItem('api_token') || ''
    const queryClient = useQueryClient()
    const navigate = useNavigate()

    // Fetch goals from API
    const { data: goals = [], isLoading } = useQuery({
        queryKey: ['goals', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/goals?status=active`, apiToken),
        staleTime: 30 * 1000, // 30 seconds
    })

    // Create goal mutation
    const createGoalMutation = useMutation({
        mutationFn: (goalData: any) => post(`/v1/tenants/${tenantId}/goals`, goalData, apiToken),
        onSuccess: (created: any) => {
            if (created) recordGoalVersion(created)
            // Persist latest goal context for Coach & Planner flows
            try {
                if (created?.id) sessionStorage.setItem('latestGoalId', created.id)
                sessionStorage.setItem('latestGoal', JSON.stringify(created))
            } catch (e) {
                console.warn('Unable to persist latest goal context', e)
            }
            queryClient.invalidateQueries({ queryKey: ['goals', tenantId] })
            // Show success banner
            setShowSuccessBanner(true)
            setTimeout(() => setShowSuccessBanner(false), 10000) // Auto-dismiss after 10s
        },
    })

    // Update goal mutation
    const updateGoalMutation = useMutation({
        mutationFn: ({ goalId, data }: { goalId: string; data: any }) =>
            put(`/v1/tenants/${tenantId}/goals/${goalId}`, data, apiToken),
        onSuccess: (updated: any) => {
            if (updated) recordGoalVersion(updated)
            queryClient.invalidateQueries({ queryKey: ['goals', tenantId] })
        },
    })

    // Delete goal mutation
    const deleteGoalMutation = useMutation({
        mutationFn: (goalId: string) => del(`/v1/tenants/${tenantId}/goals/${goalId}`, apiToken),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['goals', tenantId] })
        },
    })

    // Inline wizard state instead of modal
    const [showInlineWizard, setShowInlineWizard] = useState(false)
    const [goalInput, setGoalInput] = useState('')
    const [aiSuggestion, setAiSuggestion] = useState<Partial<Goal> | null>(null)
    const [isGenerating, setIsGenerating] = useState(false)
    const [historyGoal, setHistoryGoal] = useState<Goal | null>(null)
    const [showSuccessBanner, setShowSuccessBanner] = useState(false)

    const wizardActive = showInlineWizard && !aiSuggestion
    const wizardPreview = showInlineWizard && !!aiSuggestion

    // Monitor goals for milestone achievements
    useEffect(() => {
        if (!goals) return

        goals.forEach((goal: Goal) => {
            const progress = calculateProgress(goal)
            const milestones = [25, 50, 75, 100]

            milestones.forEach((milestone) => {
                // Check if we've crossed this milestone and haven't celebrated it yet
                if (
                    progress >= milestone &&
                    (!goal.last_celebrated_milestone || goal.last_celebrated_milestone < milestone)
                ) {
                    // Celebrate milestone
                    celebrateGoalMilestone(goal.title, milestone)

                    // Update the goal to track this milestone
                    updateGoalMutation.mutate({
                        goalId: goal.id,
                        data: { last_celebrated_milestone: milestone },
                    })
                }
            })
        })
    }, [goals])

    const handleGenerateGoal = async () => {
        if (!goalInput.trim()) return

        setIsGenerating(true)
        // Simulate AI processing
        await new Promise((resolve) => setTimeout(resolve, 1500))

        // Mock AI suggestion based on input
        const suggestion: Partial<Goal> = {
            title: extractTitle(goalInput),
            description: enhanceDescription(goalInput),
            target: extractTarget(goalInput),
            unit: extractUnit(goalInput),
            category: detectCategory(goalInput),
            deadline: suggestDeadline(goalInput),
            auto_tracked: canAutoTrack(goalInput),
        }

        setAiSuggestion(suggestion)
        setIsGenerating(false)
    }

    // Mock AI helpers
    const extractTitle = (input: string): string => {
        if (input.toLowerCase().includes('revenue')) return 'Revenue Growth Target'
        if (input.toLowerCase().includes('customer')) return 'Customer Acquisition Goal'
        if (input.toLowerCase().includes('inventory')) return 'Inventory Optimization'
        return 'Custom Business Goal'
    }

    const enhanceDescription = (input: string): string => {
        return `${input}\n\nAI-enhanced: This goal aligns with your business growth strategy and can be tracked automatically through your connected data sources.`
    }

    const extractTarget = (input: string): number => {
        const numbers = input.match(/\d+/g)
        return numbers ? parseInt(numbers[numbers.length - 1]) : 100
    }

    const extractUnit = (input: string): string => {
        if (input.includes('$') || input.toLowerCase().includes('revenue')) return 'USD'
        if (input.toLowerCase().includes('customer')) return 'Customers'
        if (input.toLowerCase().includes('%')) return '%'
        return 'Units'
    }

    const detectCategory = (input: string): Goal['category'] => {
        if (input.toLowerCase().includes('revenue') || input.includes('$')) return 'revenue'
        if (input.toLowerCase().includes('customer')) return 'customer'
        if (input.toLowerCase().includes('inventory') || input.toLowerCase().includes('stock')) return 'operations'
        if (input.toLowerCase().includes('grow')) return 'growth'
        return 'custom'
    }

    const suggestDeadline = (input: string): string => {
        const thirtyDaysFromNow = new Date()
        thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30)
        return thirtyDaysFromNow.toISOString().split('T')[0]
    }

    const canAutoTrack = (input: string): boolean => {
        return (
            input.toLowerCase().includes('revenue') ||
            input.toLowerCase().includes('customer') ||
            input.toLowerCase().includes('inventory') ||
            input.toLowerCase().includes('sales')
        )
    }

    const handleCreateGoal = () => {
        if (!aiSuggestion) return

        const newGoalData = {
            title: aiSuggestion.title!,
            description: aiSuggestion.description!,
            current: 0,
            target: aiSuggestion.target!,
            unit: aiSuggestion.unit!,
            category: aiSuggestion.category!,
            deadline: aiSuggestion.deadline!,
            auto_tracked: aiSuggestion.auto_tracked!,
            connector_source: aiSuggestion.auto_tracked ? 'Auto-detected' : undefined,
        }

        createGoalMutation.mutate(newGoalData)
        setShowInlineWizard(false)
        setGoalInput('')
        setAiSuggestion(null)
    }

    const handleDeleteGoal = (goalId: string) => {
        deleteGoalMutation.mutate(goalId)
    }

    const getCategoryColor = (category: Goal['category']) => {
        switch (category) {
            case 'revenue':
                return 'teal'
            case 'customer':
                return 'blue'
            case 'operations':
                return 'green'
            case 'growth':
                return 'violet'
            default:
                return 'gray'
        }
    }

    const calculateProgress = (goal: Goal) => {
        return Math.min((goal.current / goal.target) * 100, 100)
    }

    const getDaysRemaining = (deadline: string) => {
        const today = new Date()
        const end = new Date(deadline)
        const diff = Math.ceil((end.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
        return diff
    }

    const activeGoals = goals.filter((g: Goal) => g.status === 'active')
    const completedGoals = goals.filter((g: Goal) => g.status === 'completed')

    if (isLoading) {
        return (
            <Container size="xl" className="py-6">
                <Text>Loading goals...</Text>
            </Container>
        )
    }

    return (
        <Container size="xl" className="py-6">
            <Stack gap="xl">
                {/* Success Banner - Contextual */}
                {showSuccessBanner && (
                    <Alert
                        variant="light"
                        color="green"
                        title="Goal created! 🎉"
                        withCloseButton
                        onClose={() => setShowSuccessBanner(false)}
                        icon={<IconSparkles size={20} />}
                    >
                        <Text size="sm" mb="sm">
                            Next step: Talk to your AI Coach to refine this goal and create an action plan.
                        </Text>
                        <Button
                            size="sm"
                            variant="light"
                            color="green"
                            rightSection={<IconArrowRight size={16} />}
                            onClick={() => {
                                sessionStorage.setItem('fromGoalsPage', 'true')
                                navigate('/coach')
                            }}
                        >
                            Talk to AI Coach
                        </Button>
                    </Alert>
                )}

                {/* Header - Simplified */}
                <Group justify="space-between" align="flex-start">
                    <div>
                        <Title order={1} size="h2" c="gray.9" mb={4}>
                            Your Business Goals 🎯
                        </Title>
                        <Text size="md" c="gray.7" maw={700}>
                            Set what you want to achieve (like "Increase revenue by $50k"). Your <strong>AI Coach</strong> will help refine it and create an action plan with weekly tasks.
                        </Text>
                    </div>
                    {activeGoals.length > 0 && !showInlineWizard && (
                        <Button
                            leftSection={<IconSparkles size={18} />}
                            onClick={() => {
                                setShowInlineWizard(true)
                                window.scrollTo({ top: 0, behavior: 'smooth' })
                            }}
                            variant="light"
                        >
                            + Create Goal
                        </Button>
                    )}
                </Group>

                {/* Empty State - No Goals */}
                {activeGoals.length === 0 && completedGoals.length === 0 ? (
                    <div className="rounded-3xl border-2 border-dashed border-brand-200 bg-gradient-to-br from-brand-50/30 to-violet-50/30 p-12 text-center">
                        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brand-100">
                            <span className="text-4xl">🎯</span>
                        </div>
                        <Title order={2} mb="md" c="gray.9">
                            What do you want to achieve?
                        </Title>
                        <Text size="md" c="gray.6" mb="xl" maw={560} mx="auto">
                            Describe your goal in simple words—like "Increase revenue by $50,000 in Q1"—and we'll structure it into a trackable goal with deadlines and metrics.
                        </Text>
                        <div className="mb-8">
                            <Text size="sm" c="gray.7" fw={600} mb="sm">Example goals:</Text>
                            <div className="flex flex-wrap justify-center gap-2">
                                <Badge size="lg" variant="light" color="teal">💰 Grow revenue by 25%</Badge>
                                <Badge size="lg" variant="light" color="blue">🎯 Get 100 new customers</Badge>
                                <Badge size="lg" variant="light" color="green">⚙️ Reduce waste by 15%</Badge>
                            </div>
                        </div>
                        {!showInlineWizard && (
                            <Button
                                size="lg"
                                leftSection={<IconSparkles size={20} />}
                                onClick={() => setShowInlineWizard(true)}
                                variant="gradient"
                                gradient={{ from: 'brand', to: 'violet', deg: 90 }}
                            >
                                Set your first goal
                            </Button>
                        )}

                        {showInlineWizard && (
                            <Card withBorder radius="lg" mt="xl" p="xl" style={{ maxWidth: 600, margin: '0 auto' }}>
                                <Stack gap="md">
                                    {!aiSuggestion && (
                                        <>
                                            <Group gap="xs">
                                                <IconSparkles size={20} color="var(--mantine-color-brand-6)" />
                                                <Text fw={600}>Step 1: Describe your goal</Text>
                                            </Group>
                                            <Text size="sm" c="gray.6">
                                                In your own words, what do you want to achieve? Include what success looks like and a rough timeframe.
                                            </Text>
                                            <Textarea
                                                placeholder="Example: Grow monthly revenue by $10,000 in next 90 days"
                                                value={goalInput}
                                                onChange={(e) => setGoalInput(e.currentTarget.value)}
                                                autosize
                                                minRows={3}
                                                maxRows={6}
                                            />
                                            <Group justify="space-between">
                                                <Button variant="subtle" onClick={() => { setShowInlineWizard(false); setGoalInput(''); setAiSuggestion(null) }}>Cancel</Button>
                                                <Button leftSection={<IconSparkles size={18} />} onClick={handleGenerateGoal} loading={isGenerating} disabled={!goalInput.trim()}>
                                                    Next: Structure my goal
                                                </Button>
                                            </Group>
                                        </>
                                    )}
                                    {aiSuggestion && (
                                        <>
                                            <Group gap="xs" mb="sm">
                                                <IconSparkles size={20} color="var(--mantine-color-brand-6)" />
                                                <Text fw={600}>Step 2: Review structured goal</Text>
                                            </Group>
                                            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                                                <Group gap="xs" mb="xs">
                                                    <IconSparkles size={16} color="var(--mantine-color-blue-6)" />
                                                    <Text size="sm" fw={600} c="blue.7">Structured Goal</Text>
                                                </Group>
                                                <Stack gap="sm">
                                                    <div>
                                                        <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>Title</Text>
                                                        <Text size="md" fw={600} c="gray.9" mt={4}>{aiSuggestion.title}</Text>
                                                    </div>
                                                    <div>
                                                        <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>Description</Text>
                                                        <Text size="sm" c="gray.7" mt={4}>{aiSuggestion.description}</Text>
                                                    </div>
                                                    <Group>
                                                        <div>
                                                            <Text size="xs" c="gray.6" fw={500}>Target</Text>
                                                            <Text size="sm" fw={600} c="gray.9" mt={2}>{aiSuggestion.target} {aiSuggestion.unit}</Text>
                                                        </div>
                                                        <div>
                                                            <Text size="xs" c="gray.6" fw={500}>Deadline</Text>
                                                            <Text size="sm" fw={600} c="gray.9" mt={2}>{aiSuggestion.deadline}</Text>
                                                        </div>
                                                        <div>
                                                            <Text size="xs" c="gray.6" fw={500}>Category</Text>
                                                            <Badge size="sm" color={getCategoryColor(aiSuggestion.category!)} variant="light" mt={2}>{aiSuggestion.category}</Badge>
                                                        </div>
                                                    </Group>
                                                    {aiSuggestion.auto_tracked && (
                                                        <div className="rounded-md bg-teal-50 p-3">
                                                            <Text size="xs" c="teal.7" fw={500}>✨ This goal can be auto-tracked using your connected data sources!</Text>
                                                        </div>
                                                    )}
                                                </Stack>
                                            </div>
                                            <Text size="sm" c="gray.6" mb="sm">
                                                This is how your goal will be tracked. Click "Create Goal" to save it, then we'll help you build an action plan.
                                            </Text>
                                            <Group justify="space-between">
                                                <Button variant="subtle" onClick={() => { setAiSuggestion(null); setGoalInput('') }}>Back</Button>
                                                <Button onClick={handleCreateGoal} leftSection={<IconSparkles size={16} />}>Create Goal → Get Action Plan</Button>
                                            </Group>
                                        </>
                                    )}
                                </Stack>
                            </Card>
                        )}
                    </div>
                ) : (
                    <>
                        {/* Inline Wizard - For Adding Another Goal */}
                        {showInlineWizard && (
                            <Card withBorder radius="lg" p="xl" mb="xl" style={{ maxWidth: 800, margin: '0 auto 2rem' }}>
                                <Stack gap="md">
                                    {!aiSuggestion && (
                                        <>
                                            <Group gap="xs">
                                                <IconSparkles size={20} color="var(--mantine-color-brand-6)" />
                                                <Text fw={600}>Step 1: Describe your goal</Text>
                                            </Group>
                                            <Text size="sm" c="gray.6">
                                                In your own words, what do you want to achieve? Include what success looks like and a rough timeframe.
                                            </Text>
                                            <Textarea
                                                value={goalInput}
                                                onChange={(e) => setGoalInput(e.target.value)}
                                                placeholder="e.g., Increase revenue by $50,000 in the next 3 months"
                                                autosize
                                                minRows={3}
                                            />
                                            <Group justify="space-between">
                                                <Button variant="subtle" onClick={() => setShowInlineWizard(false)}>Cancel</Button>
                                                <Button onClick={handleGenerateGoal} loading={isGenerating} disabled={!goalInput.trim()}>
                                                    Next: AI Structures It
                                                </Button>
                                            </Group>
                                        </>
                                    )}
                                    {aiSuggestion && (
                                        <>
                                            <Group gap="xs">
                                                <IconSparkles size={20} color="var(--mantine-color-brand-6)" />
                                                <Text fw={600}>Step 2: Review structured goal</Text>
                                            </Group>
                                            <Card withBorder p="md">
                                                <Text fw={600} size="lg">{aiSuggestion.title}</Text>
                                                <Text size="sm" c="gray.6" mt="xs">{aiSuggestion.description}</Text>
                                                <Group gap="md" mt="md">
                                                    <Badge color={getCategoryColor(aiSuggestion.category!)} size="lg">
                                                        {aiSuggestion.category}
                                                    </Badge>
                                                    <Text size="sm">
                                                        Target: <strong>{aiSuggestion.target} {aiSuggestion.unit}</strong>
                                                    </Text>
                                                    <Text size="sm">
                                                        Deadline: <strong>{aiSuggestion.deadline ? new Date(aiSuggestion.deadline).toLocaleDateString() : 'Not set'}</strong>
                                                    </Text>
                                                </Group>
                                            </Card>
                                            <Text size="sm" c="gray.6" mb="sm">
                                                This is how your goal will be tracked. Click "Create Goal" to save it, then we'll help you build an action plan.
                                            </Text>
                                            <Group justify="space-between">
                                                <Button variant="subtle" onClick={() => { setAiSuggestion(null); setGoalInput('') }}>Back</Button>
                                                <Button onClick={handleCreateGoal} leftSection={<IconSparkles size={16} />}>Create Goal → Get Action Plan</Button>
                                            </Group>
                                        </>
                                    )}
                                </Stack>
                            </Card>
                        )}

                        {/* Stats Summary */}
                        <div className="grid gap-4 sm:grid-cols-4">
                            <Card withBorder radius="md" p="md">
                                <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                    Active Goals
                                </Text>
                                <Text size="xl" fw={700} c="gray.9" mt="xs">
                                    {activeGoals.length}
                                </Text>
                            </Card>
                            <Card withBorder radius="md" p="md">
                                <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                    Completed
                                </Text>
                                <Text size="xl" fw={700} c="teal.6" mt="xs">
                                    {completedGoals.length}
                                </Text>
                            </Card>
                            <Card withBorder radius="md" p="md">
                                <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                    Auto-Tracked
                                </Text>
                                <Text size="xl" fw={700} c="blue.6" mt="xs">
                                    {activeGoals.filter((g: Goal) => g.auto_tracked).length}
                                </Text>
                            </Card>
                            <div>
                                <StreakCounter variant="compact" />
                            </div>
                        </div>

                        {/* Active Goals */}
                        <Stack gap="md">
                            <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                Active Goals ({activeGoals.length})
                            </Text>

                            {activeGoals.map((goal: Goal) => {
                                const progress = calculateProgress(goal)
                                const daysLeft = getDaysRemaining(goal.deadline)
                                const isUrgent = daysLeft < 7
                                const progressColor = progress >= 90 ? 'teal' : progress >= 70 ? 'green' : progress >= 50 ? 'blue' : 'yellow'

                                return (
                                    <Card key={goal.id} radius="md" withBorder p="lg">
                                        <Group justify="space-between" align="flex-start" mb="md">
                                            <div style={{ flex: 1 }}>
                                                <Group gap="xs" mb="xs">
                                                    <Badge size="sm" color={getCategoryColor(goal.category)} variant="light">
                                                        {goal.category}
                                                    </Badge>
                                                    {goal.auto_tracked && (
                                                        <Badge size="sm" color="blue" variant="outline" leftSection={<IconSparkles size={12} />}>
                                                            Auto-tracked
                                                        </Badge>
                                                    )}
                                                </Group>
                                                <Title order={3} size="h4" c="gray.9">
                                                    {goal.title}
                                                </Title>
                                                <Text size="sm" c="gray.6" mt="xs">
                                                    {goal.description}
                                                </Text>
                                            </div>
                                            <Group gap={4}>
                                                <Badge size="sm" variant="outline" color="gray">
                                                    v{(JSON.parse(localStorage.getItem(`goalVersions:${goal.id}`) || '[]') as GoalVersionSnapshot[]).length || 1}
                                                </Badge>
                                                <ActionIcon variant="subtle" color="grape" onClick={() => setHistoryGoal(goal)}>
                                                    <IconSparkles size={18} />
                                                </ActionIcon>
                                                <ActionIcon variant="subtle" color="red" onClick={() => handleDeleteGoal(goal.id)}>
                                                    <IconTrash size={18} />
                                                </ActionIcon>
                                            </Group>
                                        </Group>

                                        <Stack gap="xs">
                                            <Group justify="space-between">
                                                <Text size="sm" c="gray.7" fw={500}>
                                                    {goal.current.toLocaleString()} / {goal.target.toLocaleString()} {goal.unit}
                                                </Text>
                                                <Text size="sm" c={isUrgent ? 'red.6' : 'gray.'} fw={500}>
                                                    {daysLeft} days left {isUrgent && '⚠️'}
                                                </Text>
                                            </Group>
                                            <Progress value={progress} color={progressColor} size="lg" radius="xl" />
                                            <Group justify="space-between">
                                                <Text size="xs" c={`${progressColor}.6`} fw={600}>
                                                    {progress.toFixed(0)}% complete
                                                </Text>
                                                {goal.connector_source && (
                                                    <Text size="xs" c="gray.5">
                                                        Data from {goal.connector_source}
                                                    </Text>
                                                )}
                                            </Group>
                                        </Stack>
                                    </Card>
                                )
                            })}

                            {activeGoals.length === 0 && completedGoals.length > 0 && (
                                <Card withBorder radius="md" p="xl" className="text-center">
                                    <Text size="lg" c="gray.6" mb="sm">No active goals yet</Text>
                                    <Text size="sm" c="gray.5" mb="md">Use AI to create your next goal and keep momentum.</Text>
                                    {!showInlineWizard && (
                                        <Button leftSection={<IconSparkles size={18} />} onClick={() => setShowInlineWizard(true)}>Create Goal with AI</Button>
                                    )}
                                    {showInlineWizard && (
                                        <Stack mt="md" gap="sm">
                                            {!aiSuggestion && (
                                                <>
                                                    <Textarea value={goalInput} onChange={(e) => setGoalInput(e.currentTarget.value)} placeholder="Describe your next goal..." autosize minRows={3} />
                                                    <Group justify="center" gap="sm">
                                                        <Button variant="subtle" onClick={() => { setShowInlineWizard(false); setGoalInput(''); setAiSuggestion(null) }}>Cancel</Button>
                                                        <Button leftSection={<IconSparkles size={16} />} onClick={handleGenerateGoal} loading={isGenerating} disabled={!goalInput.trim()}>Generate</Button>
                                                    </Group>
                                                </>
                                            )}
                                            {aiSuggestion && (
                                                <>
                                                    <Text size="sm" fw={600}>{aiSuggestion.title}</Text>
                                                    <Text size="xs" c="gray.6">Target: {aiSuggestion.target} {aiSuggestion.unit} • Deadline: {aiSuggestion.deadline}</Text>
                                                    <Group justify="center" gap="sm">
                                                        <Button variant="subtle" onClick={() => { setAiSuggestion(null); setGoalInput('') }}>Start Over</Button>
                                                        <Button size="sm" onClick={handleCreateGoal}>Create Goal</Button>
                                                    </Group>
                                                </>
                                            )}
                                        </Stack>
                                    )}
                                </Card>
                            )}
                        </Stack>
                    </>
                )}
            </Stack>
            {/* Version History Drawer */}
            <Drawer
                opened={!!historyGoal}
                onClose={() => setHistoryGoal(null)}
                position="right"
                size="md"
                title={historyGoal ? `Goal History – ${historyGoal.title}` : 'Goal History'}
            >
                {historyGoal && (
                    <Stack gap="sm">
                        {(() => {
                            const snapshots: GoalVersionSnapshot[] = JSON.parse(
                                localStorage.getItem(`goalVersions:${historyGoal.id}`) || '[]'
                            )
                            if (snapshots.length === 0) return <Text size="sm">No versions recorded yet.</Text>
                            return snapshots
                                .slice()
                                .reverse()
                                .map((s, idx) => (
                                    <Card key={s.timestamp} withBorder radius="md" p="md">
                                        <Group justify="space-between" mb="xs">
                                            <Text size="sm" fw={600}>Version {snapshots.length - idx}</Text>
                                            <Text size="xs" c="gray.6">{new Date(s.timestamp).toLocaleString()}</Text>
                                        </Group>
                                        <Text size="sm" fw={500}>{s.goal.title}</Text>
                                        <Text size="xs" c="gray.6" mt={4}>{s.goal.description}</Text>
                                        <Group gap="md" mt="xs">
                                            <Badge size="sm" color={getCategoryColor(s.goal.category)}>{s.goal.category}</Badge>
                                            <Text size="xs" c="gray.6">Target: {s.goal.target} {s.goal.unit}</Text>
                                            <Text size="xs" c="gray.6">Deadline: {s.goal.deadline}</Text>
                                        </Group>
                                    </Card>
                                ))
                        })()}
                    </Stack>
                )}
            </Drawer>
        </Container>
    )
}
