import { ActionIcon, Badge, Button, Card, Container, Group, Modal, Progress, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconPlus, IconSparkles, IconTrash } from '@tabler/icons-react'
import { useState } from 'react'

interface Goal {
    id: string
    title: string
    description: string
    current: number
    target: number
    unit: string
    category: 'revenue' | 'operations' | 'customer' | 'growth' | 'custom'
    status: 'active' | 'completed' | 'archived'
    deadline: string
    createdAt: string
    autoTracked: boolean
    connectorSource?: string
}

export default function Goals() {
    const [goals, setGoals] = useState<Goal[]>([
        {
            id: '1',
            title: 'Seasonal Revenue Boost',
            description: 'Increase Q4 revenue by 25% through holiday promotions and new product launches',
            current: 78500,
            target: 100000,
            unit: 'USD',
            category: 'revenue',
            status: 'active',
            deadline: '2025-12-01',
            createdAt: '2025-11-01',
            autoTracked: true,
            connectorSource: 'GrandNode',
        },
        {
            id: '2',
            title: 'Inventory Optimization',
            description: 'Improve inventory turnover rate to reduce holding costs and prevent stockouts',
            current: 87,
            target: 95,
            unit: '% Turnover',
            category: 'operations',
            status: 'active',
            deadline: '2025-12-10',
            createdAt: '2025-11-01',
            autoTracked: true,
            connectorSource: 'Salesforce Kennedy ERP',
        },
        {
            id: '3',
            title: 'Customer Retention',
            description: 'Build loyalty program to increase repeat customer rate from 28% to 35%',
            current: 142,
            target: 200,
            unit: 'Repeat Customers',
            category: 'customer',
            status: 'active',
            deadline: '2025-11-24',
            createdAt: '2025-11-01',
            autoTracked: true,
            connectorSource: 'GrandNode',
        },
    ])

    const [showCreateModal, setShowCreateModal] = useState(false)
    const [goalInput, setGoalInput] = useState('')
    const [aiSuggestion, setAiSuggestion] = useState<Partial<Goal> | null>(null)
    const [isGenerating, setIsGenerating] = useState(false)

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
            autoTracked: canAutoTrack(goalInput),
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

        const newGoal: Goal = {
            id: Date.now().toString(),
            title: aiSuggestion.title!,
            description: aiSuggestion.description!,
            current: 0,
            target: aiSuggestion.target!,
            unit: aiSuggestion.unit!,
            category: aiSuggestion.category!,
            status: 'active',
            deadline: aiSuggestion.deadline!,
            createdAt: new Date().toISOString().split('T')[0],
            autoTracked: aiSuggestion.autoTracked!,
            connectorSource: aiSuggestion.autoTracked ? 'Auto-detected' : undefined,
        }

        setGoals([newGoal, ...goals])
        setShowCreateModal(false)
        setGoalInput('')
        setAiSuggestion(null)
    }

    const handleDeleteGoal = (goalId: string) => {
        setGoals(goals.filter((g) => g.id !== goalId))
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

    const activeGoals = goals.filter((g) => g.status === 'active')
    const completedGoals = goals.filter((g) => g.status === 'completed')

    return (
        <Container size="xl" className="py-6">
            <Stack gap="xl">
                {/* Header */}
                <Group justify="space-between" align="center">
                    <div>
                        <Title order={1} size="h2" c="neutral.900">
                            Your Goals 🎯
                        </Title>
                        <Text size="sm" c="neutral.600" mt={4}>
                            Set ambitious goals and let AI help you achieve them
                        </Text>
                    </div>
                    <Button leftSection={<IconPlus size={18} />} size="md" onClick={() => setShowCreateModal(true)}>
                        Create Goal
                    </Button>
                </Group>

                {/* Stats Summary */}
                <div className="grid gap-4 sm:grid-cols-3">
                    <Card withBorder radius="md" p="md">
                        <Text size="xs" c="neutral.600" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                            Active Goals
                        </Text>
                        <Text size="xl" fw={700} c="neutral.900" mt="xs">
                            {activeGoals.length}
                        </Text>
                    </Card>
                    <Card withBorder radius="md" p="md">
                        <Text size="xs" c="neutral.600" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                            Completed
                        </Text>
                        <Text size="xl" fw={700} c="teal.6" mt="xs">
                            {completedGoals.length}
                        </Text>
                    </Card>
                    <Card withBorder radius="md" p="md">
                        <Text size="xs" c="neutral.600" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                            Auto-Tracked
                        </Text>
                        <Text size="xl" fw={700} c="blue.6" mt="xs">
                            {activeGoals.filter((g) => g.autoTracked).length}
                        </Text>
                    </Card>
                </div>

                {/* Active Goals */}
                <Stack gap="md">
                    <Text size="sm" fw={600} c="neutral.700" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                        Active Goals ({activeGoals.length})
                    </Text>

                    {activeGoals.map((goal) => {
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
                                            {goal.autoTracked && (
                                                <Badge size="sm" color="blue" variant="outline" leftSection={<IconSparkles size={12} />}>
                                                    Auto-tracked
                                                </Badge>
                                            )}
                                        </Group>
                                        <Title order={3} size="h4" c="neutral.900">
                                            {goal.title}
                                        </Title>
                                        <Text size="sm" c="neutral.600" mt="xs">
                                            {goal.description}
                                        </Text>
                                    </div>
                                    <ActionIcon variant="subtle" color="red" onClick={() => handleDeleteGoal(goal.id)}>
                                        <IconTrash size={18} />
                                    </ActionIcon>
                                </Group>

                                <Stack gap="xs">
                                    <Group justify="space-between">
                                        <Text size="sm" c="neutral.700" fw={500}>
                                            {goal.current.toLocaleString()} / {goal.target.toLocaleString()} {goal.unit}
                                        </Text>
                                        <Text size="sm" c={isUrgent ? 'red.6' : 'neutral.600'} fw={500}>
                                            {daysLeft} days left {isUrgent && '⚠️'}
                                        </Text>
                                    </Group>
                                    <Progress value={progress} color={progressColor} size="lg" radius="xl" />
                                    <Group justify="space-between">
                                        <Text size="xs" c={`${progressColor}.6`} fw={600}>
                                            {progress.toFixed(0)}% complete
                                        </Text>
                                        {goal.connectorSource && (
                                            <Text size="xs" c="neutral.500">
                                                Data from {goal.connectorSource}
                                            </Text>
                                        )}
                                    </Group>
                                </Stack>
                            </Card>
                        )
                    })}

                    {activeGoals.length === 0 && (
                        <Card withBorder radius="md" p="xl" className="text-center">
                            <Text size="lg" c="neutral.600" mb="sm">
                                No active goals yet
                            </Text>
                            <Text size="sm" c="neutral.500" mb="md">
                                Create your first goal using AI to get personalized recommendations
                            </Text>
                            <Button leftSection={<IconSparkles size={18} />} onClick={() => setShowCreateModal(true)}>
                                Create Goal with AI
                            </Button>
                        </Card>
                    )}
                </Stack>
            </Stack>

            {/* Create Goal Modal */}
            <Modal
                opened={showCreateModal}
                onClose={() => {
                    setShowCreateModal(false)
                    setGoalInput('')
                    setAiSuggestion(null)
                }}
                title={
                    <Group gap="xs">
                        <IconSparkles size={20} color="var(--mantine-color-brand-6)" />
                        <Text fw={600}>Create Goal with AI</Text>
                    </Group>
                }
                size="lg"
            >
                <Stack gap="md">
                    {!aiSuggestion ? (
                        <>
                            <Text size="sm" c="neutral.600">
                                Describe your goal in natural language. AI will help structure it into a trackable, achievable goal.
                            </Text>

                            <Textarea
                                placeholder="Example: I want to increase my revenue by $50,000 in the next 30 days by launching a new product line and running holiday promotions"
                                value={goalInput}
                                onChange={(e) => setGoalInput(e.currentTarget.value)}
                                autosize
                                minRows={4}
                                maxRows={8}
                                styles={{
                                    input: { fontSize: '14px' },
                                }}
                            />

                            <Group justify="flex-end" gap="sm">
                                <Button variant="subtle" onClick={() => setShowCreateModal(false)}>
                                    Cancel
                                </Button>
                                <Button
                                    leftSection={<IconSparkles size={18} />}
                                    onClick={handleGenerateGoal}
                                    loading={isGenerating}
                                    disabled={!goalInput.trim()}
                                >
                                    Generate Goal
                                </Button>
                            </Group>
                        </>
                    ) : (
                        <>
                            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                                <Group gap="xs" mb="xs">
                                    <IconSparkles size={16} color="var(--mantine-color-blue-6)" />
                                    <Text size="sm" fw={600} c="blue.7">
                                        AI-Generated Goal
                                    </Text>
                                </Group>
                                <Stack gap="sm">
                                    <div>
                                        <Text size="xs" c="neutral.600" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                            Title
                                        </Text>
                                        <Text size="md" fw={600} c="neutral.900" mt={4}>
                                            {aiSuggestion.title}
                                        </Text>
                                    </div>
                                    <div>
                                        <Text size="xs" c="neutral.600" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                            Description
                                        </Text>
                                        <Text size="sm" c="neutral.700" mt={4}>
                                            {aiSuggestion.description}
                                        </Text>
                                    </div>
                                    <Group>
                                        <div>
                                            <Text size="xs" c="neutral.600" fw={500}>
                                                Target
                                            </Text>
                                            <Text size="sm" fw={600} c="neutral.900" mt={2}>
                                                {aiSuggestion.target} {aiSuggestion.unit}
                                            </Text>
                                        </div>
                                        <div>
                                            <Text size="xs" c="neutral.600" fw={500}>
                                                Deadline
                                            </Text>
                                            <Text size="sm" fw={600} c="neutral.900" mt={2}>
                                                {aiSuggestion.deadline}
                                            </Text>
                                        </div>
                                        <div>
                                            <Text size="xs" c="neutral.600" fw={500}>
                                                Category
                                            </Text>
                                            <Badge size="sm" color={getCategoryColor(aiSuggestion.category!)} variant="light" mt={2}>
                                                {aiSuggestion.category}
                                            </Badge>
                                        </div>
                                    </Group>
                                    {aiSuggestion.autoTracked && (
                                        <div className="rounded-md bg-teal-50 p-3">
                                            <Text size="xs" c="teal.7" fw={500}>
                                                ✨ This goal can be auto-tracked using your connected data sources!
                                            </Text>
                                        </div>
                                    )}
                                </Stack>
                            </div>

                            <Text size="sm" c="neutral.600">
                                Review the AI-generated goal. You can edit it later or regenerate with different input.
                            </Text>

                            <Group justify="flex-end" gap="sm">
                                <Button
                                    variant="subtle"
                                    onClick={() => {
                                        setAiSuggestion(null)
                                        setGoalInput('')
                                    }}
                                >
                                    Start Over
                                </Button>
                                <Button onClick={handleCreateGoal}>Create Goal</Button>
                            </Group>
                        </>
                    )}
                </Stack>
            </Modal>
        </Container>
    )
}
