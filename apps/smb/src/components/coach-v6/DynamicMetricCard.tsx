/**
 * Dynamic Metric Card Component
 * 
 * Displays an industry-specific metric with:
 * - Current value and trend
 * - Status indicator (good/warning/critical)
 * - Benchmark comparison
 * - Optional sparkline
 * - Tooltip with description
 */

import { useEffect, useState } from 'react';
import {
    Card,
    Group,
    Stack,
    Text,
    RingProgress,
    Tooltip,
    Badge,
    useMantineTheme,
} from '@mantine/core';
import {
    IconArrowUp,
    IconArrowDown,
    IconMinus,
    IconInfoCircle,
} from '@tabler/icons-react';
import type { DashboardWidget } from './IndustryDashboard';

interface MetricData {
    id: string;
    name: string;
    value: number;
    formatted_value: string;
    unit: string;
    category: string;
    trend?: 'up' | 'down' | 'stable' | null;
    trend_value?: number | null;
    benchmark?: number | null;
    status?: 'good' | 'warning' | 'critical' | null;
    tooltip?: string | null;
}

interface DynamicMetricCardProps {
    widget: DashboardWidget;
    tenantId: string;
    token: string;
}

export function DynamicMetricCard({ widget, tenantId, token }: DynamicMetricCardProps) {
    const theme = useMantineTheme();
    const [metric, setMetric] = useState<MetricData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (widget.metric_id) {
            fetchMetricData();
        }
    }, [widget.metric_id, tenantId]);

    const fetchMetricData = async () => {
        try {
            setLoading(true);

            const response = await fetch(
                `/v1/tenants/${tenantId}/metrics/industry`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error('Failed to fetch metrics');
            }

            const data = await response.json();
            
            // Find the metric matching this widget's metric_id
            const matchedMetric = data.metrics.find(
                (m: MetricData) => m.id === widget.metric_id
            );

            if (matchedMetric) {
                setMetric(matchedMetric);
            }
        } catch (err) {
            console.error('Error fetching metric:', err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status?: string | null) => {
        switch (status) {
            case 'good':
                return 'green';
            case 'warning':
                return 'yellow';
            case 'critical':
                return 'red';
            default:
                return 'gray';
        }
    };

    const getTrendIcon = (trend?: 'up' | 'down' | 'stable' | null) => {
        switch (trend) {
            case 'up':
                return <IconArrowUp size={16} color={theme.colors.green[6]} />;
            case 'down':
                return <IconArrowDown size={16} color={theme.colors.red[6]} />;
            case 'stable':
                return <IconMinus size={16} color={theme.colors.gray[5]} />;
            default:
                return null;
        }
    };

    const getColorFromScheme = (scheme?: string) => {
        return scheme || 'blue';
    };

    if (loading) {
        return (
            <Card withBorder padding="lg" radius="md" h="100%">
                <Stack gap="xs">
                    <Text size="sm" c="dimmed">
                        {widget.title}
                    </Text>
                    <Text size="xl" fw={700}>
                        --
                    </Text>
                </Stack>
            </Card>
        );
    }

    if (!metric) {
        return (
            <Card withBorder padding="lg" radius="md" h="100%">
                <Stack gap="xs">
                    <Text size="sm" c="dimmed">
                        {widget.title}
                    </Text>
                    <Text size="sm" c="red">
                        No data
                    </Text>
                </Stack>
            </Card>
        );
    }

    const color = getColorFromScheme(widget.color_scheme);
    const statusColor = getStatusColor(metric.status);

    return (
        <Card
            withBorder
            padding="lg"
            radius="md"
            h="100%"
            style={{
                borderColor: metric.status === 'critical' 
                    ? theme.colors.red[3] 
                    : metric.status === 'warning'
                    ? theme.colors.yellow[3]
                    : undefined,
                borderWidth: metric.status ? 2 : 1,
            }}
        >
            <Stack gap="xs" h="100%">
                {/* Header */}
                <Group justify="space-between" align="flex-start">
                    <Group gap="xs">
                        <Text size="sm" c="dimmed" fw={500}>
                            {widget.title}
                        </Text>
                        {metric.tooltip && (
                            <Tooltip label={metric.tooltip} multiline w={250}>
                                <IconInfoCircle size={16} color={theme.colors.gray[5]} />
                            </Tooltip>
                        )}
                    </Group>
                    {metric.status && (
                        <Badge size="xs" color={statusColor} variant="dot">
                            {metric.status}
                        </Badge>
                    )}
                </Group>

                {/* Value */}
                <Group align="baseline" gap="xs">
                    <Text size="2rem" fw={700} c={color}>
                        {metric.formatted_value}
                    </Text>
                    {widget.show_trend && metric.trend && getTrendIcon(metric.trend)}
                </Group>

                {/* Benchmark Comparison */}
                {metric.benchmark !== null && metric.benchmark !== undefined && (
                    <Group gap="xs" mt="auto">
                        <Text size="xs" c="dimmed">
                            vs target: {widget.config.target || metric.benchmark}
                            {widget.config.format === 'percentage' ? '%' : ''}
                        </Text>
                        {metric.value !== null && (
                            <RingProgress
                                size={40}
                                thickness={4}
                                sections={[
                                    {
                                        value: Math.min(
                                            100,
                                            (metric.value / (metric.benchmark || 1)) * 100
                                        ),
                                        color: statusColor,
                                    },
                                ]}
                            />
                        )}
                    </Group>
                )}

                {/* Trend Value */}
                {widget.show_trend && metric.trend_value !== null && metric.trend_value !== undefined && (
                    <Text size="xs" c="dimmed">
                        {metric.trend_value > 0 ? '+' : ''}
                        {metric.trend_value.toFixed(1)}
                        {widget.config.format === 'percentage' ? '%' : ''} from last period
                    </Text>
                )}
            </Stack>
        </Card>
    );
}
