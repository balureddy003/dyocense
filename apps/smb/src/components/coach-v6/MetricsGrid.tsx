import { Card, Group, SimpleGrid, Stack, Text, useMantineTheme } from '@mantine/core';
import { IconArrowDown, IconArrowUp, IconMinus } from '@tabler/icons-react';
import type { MetricsGridProps } from './types';

/**
 * Metrics Grid Component
 * 
 * Displays 4 key business metrics with sparklines and trend indicators.
 * Clickable for drill-down to detailed reports.
 */
export function MetricsGrid({ metrics, loading = false, onMetricClick }: MetricsGridProps) {
    const theme = useMantineTheme();

    const renderSparkline = (data: number[]) => {
        if (!data || data.length === 0) return null;

        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min;
        const height = 40;
        const width = 80;
        const padding = 2;

        // Normalize data to 0-1 range
        const normalized = data.map((value) => (value - min) / (range || 1));

        // Create SVG path
        const step = (width - padding * 2) / (data.length - 1);
        const points = normalized.map((value, index) => {
            const x = padding + index * step;
            const y = height - padding - value * (height - padding * 2);
            return `${x},${y}`;
        });

        return (
            <svg width={width} height={height} style={{ display: 'block' }}>
                <polyline
                    points={points.join(' ')}
                    fill="none"
                    stroke={theme.colors.blue[5]}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </svg>
        );
    };

    const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
        switch (trend) {
            case 'up':
                return <IconArrowUp size={16} color={theme.colors.green[6]} />;
            case 'down':
                return <IconArrowDown size={16} color={theme.colors.red[6]} />;
            case 'stable':
                return <IconMinus size={16} color={theme.colors.gray[5]} />;
        }
    };

    const getTrendColor = (trend: 'up' | 'down' | 'stable') => {
        switch (trend) {
            case 'up':
                return theme.colors.green[6];
            case 'down':
                return theme.colors.red[6];
            case 'stable':
                return theme.colors.gray[5];
        }
    };

    const formatChange = (change: number, changeType: 'percentage' | 'absolute') => {
        if (changeType === 'percentage') {
            return `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
        }
        return `${change > 0 ? '+' : ''}${change.toLocaleString()}`;
    };

    return (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md">
            {metrics.map((metric) => (
                <Card
                    key={metric.id}
                    shadow="sm"
                    padding="lg"
                    radius="md"
                    withBorder
                    onClick={() => onMetricClick?.(metric.id)}
                    style={{
                        cursor: onMetricClick ? 'pointer' : 'default',
                        transition: 'transform 0.2s, box-shadow 0.2s',
                    }}
                    onMouseEnter={(e) => {
                        if (onMetricClick) {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                            e.currentTarget.style.boxShadow = theme.shadows.md;
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (onMetricClick) {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = theme.shadows.sm;
                        }
                    }}
                >
                    <Stack gap="sm">
                        {/* Label */}
                        <Text size="xs" tt="uppercase" c="dimmed" fw={600} style={{ letterSpacing: '0.5px' }}>
                            {metric.label}
                        </Text>

                        {/* Value */}
                        <Group justify="space-between" align="flex-end">
                            <div>
                                <Text size="xl" fw={700} style={{ lineHeight: 1 }}>
                                    {loading ? '--' : metric.value}
                                </Text>
                                <Group gap={4} mt={4}>
                                    {getTrendIcon(metric.trend)}
                                    <Text size="sm" c={getTrendColor(metric.trend)} fw={500}>
                                        {formatChange(metric.change, metric.changeType)}
                                    </Text>
                                </Group>
                            </div>

                            {/* Sparkline */}
                            {metric.sparklineData && metric.sparklineData.length > 0 && (
                                <div>{renderSparkline(metric.sparklineData)}</div>
                            )}
                        </Group>

                        {/* Period */}
                        {metric.period && (
                            <Text size="xs" c="dimmed">
                                {metric.period}
                            </Text>
                        )}
                    </Stack>
                </Card>
            ))}
        </SimpleGrid>
    );
}
