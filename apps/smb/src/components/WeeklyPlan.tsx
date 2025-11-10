import { Card, Checkbox, Group, Stack, Text } from '@mantine/core'
import { useEffect, useState } from 'react'
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
    const [localTasks, setLocalTasks] = useState(tasks)
    const [lastCompletedCount, setLastCompletedCount] = useState(0)
    const [selectedTask, setSelectedTask] = useState<Task | null>(null)

    const completedCount = localTasks.filter((t) => t.completed).length
    const completionPercentage = localTasks.length > 0 ? (completedCount / localTasks.length) * 100 : 0

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

    return (
        <Stack gap="sm">
            <Group justify="space-between" align="center">
                <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                    This Week's Plan
                </Text>
                <Text size="xs" c="gray.6" fw={500}>
                    {completedCount}/{localTasks.length} completed
                </Text>
            </Group>
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
