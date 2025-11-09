import { Card, Checkbox, Group, Stack, Text } from '@mantine/core'
import { useState } from 'react'

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

    const handleToggle = (taskId: string) => {
        setLocalTasks((prev) =>
            prev.map((task) => (task.id === taskId ? { ...task, completed: !task.completed } : task))
        )
        onToggle?.(taskId)
    }

    const completedCount = localTasks.filter((t) => t.completed).length
    const completionPercentage = localTasks.length > 0 ? (completedCount / localTasks.length) * 100 : 0

    return (
        <Stack gap="sm">
            <Group justify="space-between" align="center">
                <Text size="sm" fw={600} c="neutral.700" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                    This Week's Plan
                </Text>
                <Text size="xs" c="neutral.600" fw={500}>
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
                            <div style={{ flex: 1 }}>
                                <Text
                                    size="sm"
                                    fw={500}
                                    c={task.completed ? 'neutral.500' : 'neutral.900'}
                                    style={{
                                        textDecoration: task.completed ? 'line-through' : 'none',
                                    }}
                                >
                                    {task.title}
                                </Text>
                                <Text size="xs" c="neutral.500" mt={2}>
                                    {task.category}
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
        </Stack>
    )
}
