import { ActionIcon, Badge, Button, Card, Checkbox, Group, Progress, Stack, Tabs, Text } from '@mantine/core'
import { IconCalendar, IconCalendarStats, IconCalendarTime, IconCalendarWeek, IconPlus, IconSparkles, IconTarget, IconTrendingUp } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { celebrateTaskCompletion } from '../utils/celebrations'
import { updateStreak } from './StreakCounter'
import TaskDetailModal from './TaskDetailModal'

interface Task {
    id: string
    title: string
    category: string
    completed: boolean
    due_date?: string
    priority?: 'low' | 'medium' | 'high' | 'urgent'
}

interface PlanHorizon {
    id: string
    label: string
    icon: React.ComponentType<any>
    description: string
}

interface MultiHorizonPlannerProps {
    dailyTasks?: Task[]
    weeklyTasks?: Task[]
    quarterlyTasks?: Task[]
    yearlyTasks?: Task[]
    onToggle?: (taskId: string, horizon: string) => void
    defaultHorizon?: string
}

const HORIZONS: PlanHorizon[] = [
    { id: 'daily', label: 'Today', icon: IconCalendar, description: 'Focus for today' },
    { id: 'weekly', label: 'This Week', icon: IconCalendarWeek, description: 'Week\'s priorities' },
    { id: 'quarterly', label: 'This Quarter', icon: IconCalendarStats, description: '90-day goals' },
    { id: 'yearly', label: 'This Year', icon: IconCalendarTime, description: 'Annual objectives' },
]

export default function MultiHorizonPlanner({
    dailyTasks = [],
    weeklyTasks = [],
    quarterlyTasks = [],
    yearlyTasks = [],
    onToggle,
    defaultHorizon = 'weekly'
}: MultiHorizonPlannerProps) {
    const navigate = useNavigate()
    const [activeHorizon, setActiveHorizon] = useState(defaultHorizon)
    const [selectedTask, setSelectedTask] = useState<Task | null>(null)

    const getTasksForHorizon = (horizon: string): Task[] => {
        switch (horizon) {
            case 'daily': return dailyTasks
            case 'weekly': return weeklyTasks
            case 'quarterly': return quarterlyTasks
            case 'yearly': return yearlyTasks
            default: return []
        }
    }

    const [localTasks, setLocalTasks] = useState(getTasksForHorizon(activeHorizon))
    const [lastCompletedCount, setLastCompletedCount] = useState(0)

    const currentTasks = getTasksForHorizon(activeHorizon)
    const completedCount = currentTasks.filter((t) => t.completed).length
    const totalCount = currentTasks.length
    const completionPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0

    // Update local tasks when horizon changes
    useEffect(() => {
        setLocalTasks(getTasksForHorizon(activeHorizon))
    }, [activeHorizon, dailyTasks, weeklyTasks, quarterlyTasks, yearlyTasks])

    // Celebrate when tasks are completed
    useEffect(() => {
        if (completedCount > lastCompletedCount && completedCount > 0) {
            celebrateTaskCompletion(completedCount, totalCount)
            if (completedCount === totalCount && activeHorizon === 'weekly') {
                updateStreak(completedCount, totalCount)
            }
        }
        setLastCompletedCount(completedCount)
    }, [completedCount, totalCount, activeHorizon])

    const handleToggle = (taskId: string) => {
        onToggle?.(taskId, activeHorizon)
    }

    const handleTaskClick = (task: Task) => {
        setSelectedTask(task)
    }

    const getPriorityColor = (priority?: string) => {
        switch (priority) {
            case 'urgent': return 'red'
            case 'high': return 'orange'
            case 'medium': return 'blue'
            case 'low': return 'gray'
            default: return 'gray'
        }
    }

    const getSuggestedTasksForHorizon = (horizon: string) => {
        const suggestions: Record<string, any[]> = {
            daily: [
                { title: 'Review and respond to customer emails', category: 'Customer Service', icon: IconTarget, reason: 'Daily engagement' },
                { title: 'Check inventory levels for best sellers', category: 'Operations', icon: IconTrendingUp, reason: 'Stock management' },
                { title: 'Review today\'s sales and metrics', category: 'Analytics', icon: IconTrendingUp, reason: 'Daily performance' },
            ],
            weekly: [
                { title: 'Review low-stock inventory items', category: 'Operations', icon: IconTrendingUp, reason: 'Based on your inventory data' },
                { title: 'Follow up with top 5 VIP customers', category: 'Sales', icon: IconTarget, reason: 'Customer retention focus' },
                { title: 'Analyze weekend vs weekday sales patterns', category: 'Analytics', icon: IconTrendingUp, reason: 'Revenue optimization' },
            ],
            quarterly: [
                { title: 'Review Q4 revenue goals and adjust strategy', category: 'Strategy', icon: IconTarget, reason: 'Quarterly planning' },
                { title: 'Optimize top 10 product listings', category: 'Marketing', icon: IconTrendingUp, reason: 'Revenue growth' },
                { title: 'Implement new customer retention program', category: 'Customer Success', icon: IconTarget, reason: 'Long-term growth' },
            ],
            yearly: [
                { title: 'Define annual revenue and growth targets', category: 'Strategy', icon: IconTarget, reason: 'Annual planning' },
                { title: 'Evaluate and optimize supplier relationships', category: 'Operations', icon: IconTrendingUp, reason: 'Cost optimization' },
                { title: 'Expand product line or enter new market', category: 'Growth', icon: IconTarget, reason: 'Business expansion' },
            ]
        }
        return suggestions[horizon] || []
    }

    const renderEmptyState = () => {
        const suggestions = getSuggestedTasksForHorizon(activeHorizon)
        const currentHorizon = HORIZONS.find(h => h.id === activeHorizon)

        return (
            <Card radius="md" withBorder p="lg" bg="gray.0">
                <Stack gap="md" align="center" py="md">
                    <IconSparkles size={40} stroke={1.5} color="var(--mantine-color-blue-6)" />
                    <div style={{ textAlign: 'center' }}>
                        <Text size="md" fw={600} c="gray.8" mb={4}>
                            No {currentHorizon?.label.toLowerCase()} plan yet
                        </Text>
                        <Text size="sm" c="gray.6" mb="lg">
                            Let the AI Coach create your personalized {currentHorizon?.label.toLowerCase()} action plan
                        </Text>
                    </div>

                    <Button
                        variant="filled"
                        color="blue"
                        leftSection={<IconSparkles size={16} />}
                        onClick={() => navigate('/coach')}
                        size="md"
                    >
                        Get AI-Powered {currentHorizon?.label} Plan
                    </Button>

                    <div style={{ width: '100%', marginTop: '1rem' }}>
                        <Text size="xs" c="gray.6" fw={600} mb="sm" tt="uppercase">
                            Or try these {currentHorizon?.label.toLowerCase()} suggestions:
                        </Text>
                        <Stack gap="xs">
                            {suggestions.map((task, idx) => (
                                <Card key={idx} padding="sm" withBorder radius="sm" bg="white">
                                    <Group gap="xs" wrap="nowrap">
                                        <task.icon size={18} stroke={1.5} color="var(--mantine-color-gray-6)" />
                                        <div style={{ flex: 1 }}>
                                            <Text size="sm" fw={500} c="gray.8">
                                                {task.title}
                                            </Text>
                                            <Group gap={6} mt={2}>
                                                <Badge size="xs" variant="light" color="gray">
                                                    {task.category}
                                                </Badge>
                                                <Text size="xs" c="gray.5">
                                                    {task.reason}
                                                </Text>
                                            </Group>
                                        </div>
                                    </Group>
                                </Card>
                            ))}
                        </Stack>
                    </div>
                </Stack>
            </Card>
        )
    }

    const renderTaskList = () => {
        if (currentTasks.length === 0) {
            return renderEmptyState()
        }

        return (
            <>
                <Group justify="space-between" mb="sm">
                    <Text size="sm" c="gray.6">
                        {completedCount} of {totalCount} completed
                    </Text>
                    <ActionIcon variant="subtle" color="blue" onClick={() => navigate('/coach')}>
                        <IconPlus size={18} />
                    </ActionIcon>
                </Group>

                <Progress value={completionPercentage} color="teal" size="sm" mb="md" />

                <Card radius="md" withBorder p="md">
                    <Stack gap="md">
                        {currentTasks.map((task) => (
                            <Group key={task.id} gap="sm" align="flex-start">
                                <Checkbox
                                    checked={task.completed}
                                    onChange={() => handleToggle(task.id)}
                                    size="md"
                                    color="teal"
                                    styles={{ input: { cursor: 'pointer' } }}
                                />
                                <div
                                    style={{ flex: 1, cursor: 'pointer' }}
                                    onClick={() => handleTaskClick(task)}
                                    role="button"
                                    tabIndex={0}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter' || e.key === ' ') handleTaskClick(task)
                                    }}
                                >
                                    <Group gap="xs" mb={4}>
                                        <Text
                                            size="sm"
                                            fw={500}
                                            c={task.completed ? 'neutral.5' : 'neutral.9'}
                                            style={{
                                                textDecoration: task.completed ? 'line-through' : 'none',
                                            }}
                                        >
                                            {task.title}
                                        </Text>
                                        {task.priority && (
                                            <Badge size="xs" color={getPriorityColor(task.priority)} variant="dot">
                                                {task.priority}
                                            </Badge>
                                        )}
                                    </Group>
                                    <Text size="xs" c="gray.5">
                                        {task.category}
                                        {task.due_date && ` • Due: ${new Date(task.due_date).toLocaleDateString()}`}
                                    </Text>
                                </div>
                            </Group>
                        ))}
                    </Stack>
                </Card>

                {completionPercentage === 100 && totalCount > 0 && (
                    <Text size="xs" c="teal.6" fw={600} ta="center" mt="sm">
                        🎉 {HORIZONS.find(h => h.id === activeHorizon)?.label} complete! Great work!
                    </Text>
                )}
            </>
        )
    }

    return (
        <Stack gap="sm">
            <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                Action Plans
            </Text>

            <Tabs value={activeHorizon} onChange={(value) => setActiveHorizon(value || 'weekly')}>
                <Tabs.List grow>
                    {HORIZONS.map((horizon) => (
                        <Tabs.Tab
                            key={horizon.id}
                            value={horizon.id}
                            leftSection={<horizon.icon size={16} />}
                        >
                            <div>
                                <Text size="sm" fw={500}>{horizon.label}</Text>
                                <Text size="xs" c="dimmed">{horizon.description}</Text>
                            </div>
                        </Tabs.Tab>
                    ))}
                </Tabs.List>

                {HORIZONS.map((horizon) => (
                    <Tabs.Panel key={horizon.id} value={horizon.id} pt="md">
                        {renderTaskList()}
                    </Tabs.Panel>
                ))}
            </Tabs>

            {/* Task Detail Modal */}
            {selectedTask && (
                <TaskDetailModal
                    opened={!!selectedTask}
                    onClose={() => setSelectedTask(null)}
                    task={selectedTask}
                />
            )}
        </Stack>
    )
}
