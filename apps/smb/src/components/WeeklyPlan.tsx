import { Badge, Button, Card, Checkbox, Group, Stack, Text } from '@mantine/core'
import { IconSparkles, IconTarget, IconTrendingUp } from '@tabler/icons-react'
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
}

interface WeeklyPlanProps {
    tasks: Task[]
    onToggle?: (taskId: string) => void
}

export default function WeeklyPlan({ tasks, onToggle }: WeeklyPlanProps) {
    const navigate = useNavigate()
    const [localTasks, setLocalTasks] = useState(tasks)
    const [lastCompletedCount, setLastCompletedCount] = useState(0)
    const [selectedTask, setSelectedTask] = useState<Task | null>(null)

    const completedCount = localTasks.filter((t) => t.completed).length
    const completionPercentage = localTasks.length > 0 ? (completedCount / localTasks.length) * 100 : 0

    // Update local tasks when props change
    useEffect(() => {
        setLocalTasks(tasks)
    }, [tasks])

    // Celebrate when tasks are completed
    useEffect(() => {
        if (completedCount > lastCompletedCount && completedCount > 0) {
            celebrateTaskCompletion(completedCount, localTasks.length)

            // Update streak if all tasks completed
            if (completedCount === localTasks.length) {
                updateStreak(completedCount, localTasks.length)
            }
        }
        setLastCompletedCount(completedCount)
    }, [completedCount, localTasks.length])

    const handleToggle = (taskId: string) => {
        setLocalTasks((prev) =>
            prev.map((task) => (task.id === taskId ? { ...task, completed: !task.completed } : task))
        )
        onToggle?.(taskId)
    }

    const handleTaskClick = (task: Task) => {
        setSelectedTask(task)
    }

    const suggestedTasks = [
        {
            title: 'Review low-stock inventory items',
            category: 'Operations',
            icon: IconTrendingUp,
            reason: 'Based on your inventory data',
        },
        {
            title: 'Follow up with top 5 VIP customers',
            category: 'Sales',
            icon: IconTarget,
            reason: 'Customer retention focus',
        },
        {
            title: 'Analyze weekend vs weekday sales patterns',
            category: 'Analytics',
            icon: IconTrendingUp,
            reason: 'Revenue optimization',
        },
    ]

    return (
        <Stack gap="sm">
            <Group justify="space-between" align="center">
                <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                    This Week's Plan
                </Text>
                {localTasks.length > 0 && (
                    <Text size="xs" c="gray.6" fw={500}>
                        {completedCount}/{localTasks.length} completed
                    </Text>
                )}
            </Group>

            {localTasks.length === 0 ? (
                <Card radius="md" withBorder p="lg" bg="gray.0">
                    <Stack gap="md" align="center" py="md">
                        <IconSparkles size={40} stroke={1.5} color="var(--mantine-color-blue-6)" />
                        <div style={{ textAlign: 'center' }}>
                            <Text size="md" fw={600} c="gray.8" mb={4}>
                                No tasks planned yet
                            </Text>
                            <Text size="sm" c="gray.6" mb="lg">
                                Let the AI Coach create your personalized weekly action plan based on your business data
                            </Text>
                        </div>

                        <Button
                            variant="filled"
                            color="blue"
                            leftSection={<IconSparkles size={16} />}
                            onClick={() => navigate('/coach')}
                            size="md"
                        >
                            Get AI-Powered Plan
                        </Button>

                        <div style={{ width: '100%', marginTop: '1rem' }}>
                            <Text size="xs" c="gray.6" fw={600} mb="sm" tt="uppercase">
                                Or try these suggestions:
                            </Text>
                            <Stack gap="xs">
                                {suggestedTasks.map((task, idx) => (
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
            ) : (
                <Card radius="md" withBorder p="md">
                    <Stack gap="md">
                        {localTasks.map((task) => (
                            <Group key={task.id} gap="sm" align="flex-start">
                                <Checkbox
                                    checked={task.completed}
                                    onChange={() => handleToggle(task.id)}
                                    size="md"
                                    color="teal"
                                    styles={{
                                        input: { cursor: 'pointer' },
                                    }}
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
                                    <Text size="xs" c="gray.5" mt={2}>
                                        {task.category} • Click for details
                                    </Text>
                                </div>
                            </Group>
                        ))}
                    </Stack>
                </Card>
            )}

            {completionPercentage === 100 && localTasks.length > 0 && (
                <Text size="xs" c="teal.6" fw={600} ta="center">
                    🎉 Week complete! Great work!
                </Text>
            )}

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
