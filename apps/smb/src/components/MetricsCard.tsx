import { Card, Grid, Group, Stack, Text } from '@mantine/core'
import { IconArrowDown, IconArrowUp, IconTrendingUp } from '@tabler/icons-react'

interface Metric {
    label: string
    value: string
    trend?: string
    color?: string
}

interface MetricsCardProps {
    metrics: Metric[]
    chart?: {
        type: string
        data: Array<{ day: string; revenue: number }>
    }
}

export default function MetricsCard({ metrics, chart }: MetricsCardProps) {
    const getColor = (color?: string) => {
        switch (color) {
            case 'green': return '#10b981'
            case 'blue': return '#3b82f6'
            case 'orange': return '#f59e0b'
            case 'purple': return '#a855f7'
            default: return '#6b7280'
        }
    }

    const getTrendIcon = (trend?: string) => {
        if (!trend) return null
        const isPositive = trend.startsWith('+')
        return isPositive ? (
            <IconArrowUp size={14} color="#10b981" />
        ) : (
            <IconArrowDown size={14} color="#ef4444" />
        )
    }

    const maxRevenue = chart ? Math.max(...chart.data.map(d => d.revenue)) : 0

    return (
        <Card
            withBorder
            radius="md"
            p="md"
            style={{
                backgroundColor: '#f9fafb',
                borderColor: '#e5e7eb'
            }}
        >
            <Stack gap="md">
                {/* Metrics Grid */}
                <Grid>
                    {metrics.map((metric, i) => (
                        <Grid.Col span={{ base: 6, sm: 3 }} key={i}>
                            <Stack gap={4}>
                                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                                    {metric.label}
                                </Text>
                                <Group gap={4} align="baseline">
                                    <Text size="xl" fw={700} style={{ color: getColor(metric.color) }}>
                                        {metric.value}
                                    </Text>
                                    {metric.trend && (
                                        <Group gap={2} style={{ marginLeft: 4 }}>
                                            {getTrendIcon(metric.trend)}
                                            <Text
                                                size="xs"
                                                fw={600}
                                                c={metric.trend.startsWith('+') ? 'green' : 'red'}
                                            >
                                                {metric.trend}
                                            </Text>
                                        </Group>
                                    )}
                                </Group>
                            </Stack>
                        </Grid.Col>
                    ))}
                </Grid>

                {/* Mini Chart */}
                {chart && chart.type === 'revenue_trend' && (
                    <Stack gap={4}>
                        <Group gap={4} align="center">
                            <IconTrendingUp size={14} color="#6b7280" />
                            <Text size="xs" c="dimmed" fw={600}>
                                Revenue Trend (Last 7 Days)
                            </Text>
                        </Group>
                        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 60 }}>
                            {chart.data.map((point, i) => {
                                const height = (point.revenue / maxRevenue) * 50
                                return (
                                    <div
                                        key={i}
                                        style={{
                                            flex: 1,
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'center',
                                            gap: 4
                                        }}
                                    >
                                        <div
                                            style={{
                                                width: '100%',
                                                height: `${height}px`,
                                                backgroundColor: i === chart.data.length - 1 ? '#3b82f6' : '#93c5fd',
                                                borderRadius: '4px 4px 0 0',
                                                transition: 'all 0.3s ease'
                                            }}
                                            title={`${point.day}: $${point.revenue.toLocaleString()}`}
                                        />
                                        <Text size="9px" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
                                            {point.day.replace(' ago', '').replace('Today', 'Now')}
                                        </Text>
                                    </div>
                                )
                            })}
                        </div>
                    </Stack>
                )}
            </Stack>
        </Card>
    )
}
