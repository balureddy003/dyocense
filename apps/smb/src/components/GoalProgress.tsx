import { Card, Group, Progress, Stack, Text } from '@mantine/core'

interface Goal {
    id: string
    title: string
    current: number
    target: number
    unit: string
    daysRemaining: number
}

interface GoalProgressProps {
    goals: Goal[]
}

export default function GoalProgress({ goals }: GoalProgressProps) {
    return (
        <Stack gap="sm">
            <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                Active Goals
            </Text>
            <Stack gap="xs">
                {goals.map((goal) => {
                    const percentage = Math.min((goal.current / goal.target) * 100, 100)
                    const color = percentage >= 90 ? 'teal' : percentage >= 70 ? 'green' : percentage >= 50 ? 'blue' : 'yellow'

                    return (
                        <Card key={goal.id} radius="md" withBorder p="md">
                            <Stack gap="xs">
                                <Group justify="space-between" align="flex-start">
                                    <div>
                                        <Text size="sm" fw={600} c="gray.9">
                                            {goal.title}
                                        </Text>
                                        <Text size="xs" c="gray.6" mt={4}>
                                            {goal.current.toLocaleString()} / {goal.target.toLocaleString()} {goal.unit}
                                        </Text>
                                    </div>
                                    <Text size="xs" c="gray.5" fw={500}>
                                        {goal.daysRemaining} days left
                                    </Text>
                                </Group>
                                <Progress value={percentage} color={color} size="md" radius="xl" />
                                <Text size="xs" c={`${color}.6`} fw={600} ta="right">
                                    {percentage.toFixed(0)}% complete
                                </Text>
                            </Stack>
                        </Card>
                    )
                })}
            </Stack>
        </Stack>
    )
}
