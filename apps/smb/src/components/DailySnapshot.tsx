import { Card, Group, Stack, Text } from '@mantine/core'

interface MetricCardProps {
    value: string
    label: string
    trend?: number
    trendLabel?: string
}

function MetricCard({ value, label, trend, trendLabel }: MetricCardProps) {
    const trendIcon = trend && trend > 0 ? '↑' : trend && trend < 0 ? '↓' : null
    const trendColor = trend && trend > 0 ? 'teal.6' : trend && trend < 0 ? 'red.6' : 'gray.6'

    return (
        <Card radius="lg" withBorder p="md" className="flex-1">
            <Stack gap="xs" align="center">
                <Text size="xl" fw={700} c="gray.9">
                    {value}
                </Text>
                <Text size="xs" c="gray.6" fw={500} ta="center">
                    {label}
                </Text>
                {trend !== undefined && (
                    <Text size="xs" c={trendColor} fw={600}>
                        {trendIcon} {Math.abs(trend)}% {trendLabel || 'vs yesterday'}
                    </Text>
                )}
            </Stack>
        </Card>
    )
}

interface DailySnapshotProps {
    metrics: {
        revenue: { value: string; trend?: number }
        orders: { value: string; trend?: number }
        fillRate: { value: string; trend?: number }
        rating: { value: string; trend?: number }
    }
}

export default function DailySnapshot({ metrics }: DailySnapshotProps) {
    return (
        <Stack gap="sm">
            <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                Today's Snapshot
            </Text>
            <Group gap="sm" className="flex-wrap md:flex-nowrap">
                <MetricCard value={metrics.revenue.value} label="Revenue" trend={metrics.revenue.trend} />
                <MetricCard value={metrics.orders.value} label="Orders" trend={metrics.orders.trend} />
                <MetricCard value={metrics.fillRate.value} label="Fill Rate" trend={metrics.fillRate.trend} />
                <MetricCard value={metrics.rating.value} label="★ Rating" trend={metrics.rating.trend} />
            </Group>
        </Stack>
    )
}
