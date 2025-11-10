import { Group, RingProgress, Stack, Text } from '@mantine/core'

interface BusinessHealthScoreProps {
    score: number // 0-100
    trend?: number // +/- change from last period
    size?: number
}

export default function BusinessHealthScore({ score, trend = 0, size = 180 }: BusinessHealthScoreProps) {
    const getStatus = (score: number) => {
        if (score >= 90) return { label: 'Excellent', icon: '💪', color: 'teal' }
        if (score >= 75) return { label: 'Strong', icon: '👍', color: 'green' }
        if (score >= 60) return { label: 'Good', icon: '✓', color: 'blue' }
        if (score >= 40) return { label: 'Needs Attention', icon: '⚠️', color: 'yellow' }
        return { label: 'Critical', icon: '🚨', color: 'red' }
    }

    const status = getStatus(score)
    const trendIcon = trend > 0 ? '↑' : trend < 0 ? '↓' : '→'
    const trendColor = trend > 0 ? 'teal' : trend < 0 ? 'red' : 'gray'

    return (
        <Stack gap="md" align="center">
            <RingProgress
                size={size}
                thickness={16}
                roundCaps
                sections={[{ value: score, color: status.color }]}
                label={
                    <Stack gap={4} align="center">
                        <Text size="xl" fw={700} c="gray.9">
                            {score}
                        </Text>
                        <Text size="xs" c="gray.6" fw={500}>
                            /100
                        </Text>
                    </Stack>
                }
            />

            <Stack gap={4} align="center">
                <Group gap={6}>
                    <Text size="lg" fw={600} c="gray.9">
                        {status.icon} {status.label}
                    </Text>
                    {trend !== 0 && (
                        <Text size="sm" fw={600} c={trendColor}>
                            {trendIcon} {Math.abs(trend)}
                        </Text>
                    )}
                </Group>
                <Text size="xs" c="gray.6">
                    Business Health Score
                </Text>
            </Stack>
        </Stack>
    )
}
