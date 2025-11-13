import {
    Alert,
    Badge,
    Button,
    Card,
    Container,
    Divider,
    Grid,
    Group,
    Loader,
    Select,
    Stack,
    Table,
    Text,
    Title,
} from '@mantine/core';
import { IconAlertTriangle, IconDownload, IconMinus, IconTrendingDown, IconTrendingUp } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { get } from '../lib/api';
import { useAuthStore } from '../stores/auth';

export function AdvancedAnalytics() {
    const { tenantId, apiToken } = useAuthStore();

    const [selectedMetric, setSelectedMetric] = useState('revenue');
    const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
    const [endDate, setEndDate] = useState(new Date());
    const [granularity, setGranularity] = useState('daily');
    const [comparisonType, setComparisonType] = useState('previous_period');

    // Available metrics
    const metrics = [
        { value: 'revenue', label: 'Revenue' },
        { value: 'health_score', label: 'Health Score' },
        { value: 'task_completion', label: 'Tasks Completed' },
        { value: 'profit_margin', label: 'Profit Margin' },
    ];

    // Fetch trend data
    const { data: trendData, isLoading: trendLoading } = useQuery({
        queryKey: ['analytics-trend', tenantId, selectedMetric, startDate, endDate, granularity],
        queryFn: async () => {
            if (!startDate || !endDate) return null;

            const params = new URLSearchParams({
                metric: selectedMetric,
                start_date: startDate.toISOString(),
                end_date: endDate.toISOString(),
                granularity: granularity,
            });

            return get(`/v1/tenants/${tenantId}/analytics/trends?${params}`, apiToken);
        },
        enabled: !!tenantId && !!apiToken && !!startDate && !!endDate,
    });

    // Fetch comparison data
    const { data: comparisonData } = useQuery({
        queryKey: ['analytics-comparison', tenantId, selectedMetric, startDate, endDate, comparisonType],
        queryFn: async () => {
            if (!startDate || !endDate) return null;

            const params = new URLSearchParams({
                metric: selectedMetric,
                current_start: startDate.toISOString(),
                current_end: endDate.toISOString(),
                comparison_type: comparisonType,
            });

            return get(`/v1/tenants/${tenantId}/analytics/compare?${params}`, apiToken);
        },
        enabled: !!tenantId && !!apiToken && !!startDate && !!endDate,
    });    // Fetch anomalies
    const { data: anomaliesData } = useQuery({
        queryKey: ['analytics-anomalies', tenantId, selectedMetric],
        queryFn: () => {
            const params = new URLSearchParams({
                metric: selectedMetric,
                threshold: '2.0',
            });
            return get(`/v1/tenants/${tenantId}/analytics/anomalies?${params}`, apiToken);
        },
        enabled: !!tenantId && !!apiToken,
    });

    // Export to CSV
    const handleExportCSV = async () => {
        if (!startDate || !endDate) return;

        const params = new URLSearchParams({
            metrics: metrics.map(m => m.value).join(','),
            start_date: startDate.toISOString(),
            end_date: endDate.toISOString(),
        });

        const url = `/v1/tenants/${tenantId}/analytics/export/csv?${params}`;
        // Trigger download
        const apiUrl = (import.meta as any).env?.VITE_API_URL || '';
        window.open(`${apiUrl}${url}`, '_blank');
    }; const getTrendIcon = (direction: string) => {
        if (direction === 'up') return <IconTrendingUp size={20} color="green" />;
        if (direction === 'down') return <IconTrendingDown size={20} color="red" />;
        return <IconMinus size={20} color="gray" />;
    };

    const getTrendColor = (direction: string) => {
        if (direction === 'up') return 'green';
        if (direction === 'down') return 'red';
        return 'gray';
    };

    return (
        <Container size="xl" py="xl">
            {/* Header */}
            <Group justify="space-between" mb="xl">
                <div>
                    <Title order={1} size="h2">🔬 Advanced Analytics</Title>
                    <Text c="dimmed" mt="xs">Deep insights with forecasting and anomaly detection</Text>
                </div>
                <Button leftSection={<IconDownload size={16} />} onClick={handleExportCSV}>
                    Export CSV
                </Button>
            </Group>

            {/* Filters */}
            <Card shadow="sm" padding="lg" radius="md" withBorder mb="xl">
                <Text fw={600} size="lg" mb="md">Analysis Configuration</Text>
                <Grid>
                    <Grid.Col span={{ base: 12, md: 3 }}>
                        <Select
                            label="Metric"
                            value={selectedMetric}
                            onChange={(value) => setSelectedMetric(value || 'revenue')}
                            data={metrics}
                        />
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 3 }}>
                        <Select
                            label="Granularity"
                            value={granularity}
                            onChange={(value) => setGranularity(value || 'daily')}
                            data={[
                                { value: 'hourly', label: 'Hourly' },
                                { value: 'daily', label: 'Daily' },
                                { value: 'weekly', label: 'Weekly' },
                                { value: 'monthly', label: 'Monthly' },
                            ]}
                        />
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 3 }}>
                        <Stack gap="xs">
                            <Text size="sm" fw={500}>Date Range</Text>
                            <Group gap="xs">
                                <Text size="xs" c="dimmed">
                                    {startDate.toLocaleDateString()} - {endDate.toLocaleDateString()}
                                </Text>
                            </Group>
                        </Stack>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 3 }}>
                        <Select
                            label="Compare To"
                            value={comparisonType}
                            onChange={(value) => setComparisonType(value || 'previous_period')}
                            data={[
                                { value: 'previous_period', label: 'Previous Period' },
                                { value: 'previous_year', label: 'Same Period Last Year' },
                                { value: 'average', label: '90-Day Average' },
                            ]}
                        />
                    </Grid.Col>
                </Grid>
            </Card>

            {trendLoading && (
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Group justify="center" p="xl">
                        <Loader />
                        <Text>Loading analytics data...</Text>
                    </Group>
                </Card>
            )}

            {!trendLoading && trendData && (
                <Stack gap="xl">
                    {/* Trend Summary */}
                    <Card shadow="sm" padding="lg" radius="md" withBorder>
                        <Group justify="space-between" mb="md">
                            <Text fw={600} size="lg">Trend Analysis</Text>
                            <Group gap="xs">
                                {getTrendIcon(trendData.trend_direction)}
                                <Badge color={getTrendColor(trendData.trend_direction)} size="lg">
                                    {trendData.change_percentage > 0 ? '+' : ''}{trendData.change_percentage}%
                                </Badge>
                            </Group>
                        </Group>

                        <Grid mb="md">
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">7-Day Moving Avg</Text>
                                <Text size="xl" fw={600}>
                                    {trendData.moving_average_7d?.toFixed(2) || 'N/A'}
                                </Text>
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">30-Day Moving Avg</Text>
                                <Text size="xl" fw={600}>
                                    {trendData.moving_average_30d?.toFixed(2) || 'N/A'}
                                </Text>
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <Text size="sm" c="dimmed">Next Period Forecast</Text>
                                <Text size="xl" fw={600}>
                                    {trendData.forecast_next_period?.toFixed(2) || 'N/A'}
                                </Text>
                            </Grid.Col>
                        </Grid>

                        {trendData.seasonality_detected && (
                            <Alert color="blue" title="Seasonality Detected" mb="md">
                                This metric shows seasonal patterns. Forecasts account for these cycles.
                            </Alert>
                        )}

                        <ResponsiveContainer width="100%" height={350}>
                            <AreaChart data={trendData.data_points}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="label" />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                <Area
                                    type="monotone"
                                    dataKey="value"
                                    stroke="#4F46E5"
                                    fill="#4F46E5"
                                    fillOpacity={0.3}
                                    name={selectedMetric}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </Card>

                    {/* Period Comparison */}
                    {comparisonData && (
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Period Comparison</Text>
                            <Text c="dimmed" mb="lg">{comparisonData.context}</Text>

                            <Grid>
                                <Grid.Col span={6}>
                                    <Card padding="md" withBorder>
                                        <Text size="sm" c="dimmed" mb="xs">Current Period</Text>
                                        <Text size="xl" fw={700}>{comparisonData.current_period.value}</Text>
                                        <Text size="xs" c="dimmed" mt="xs">
                                            {new Date(comparisonData.current_period.start_date).toLocaleDateString()} - {' '}
                                            {new Date(comparisonData.current_period.end_date).toLocaleDateString()}
                                        </Text>
                                    </Card>
                                </Grid.Col>
                                <Grid.Col span={6}>
                                    <Card padding="md" withBorder>
                                        <Text size="sm" c="dimmed" mb="xs">Comparison Period</Text>
                                        <Text size="xl" fw={700}>{comparisonData.comparison_period.value}</Text>
                                        <Text size="xs" c="dimmed" mt="xs">
                                            {new Date(comparisonData.comparison_period.start_date).toLocaleDateString()} - {' '}
                                            {new Date(comparisonData.comparison_period.end_date).toLocaleDateString()}
                                        </Text>
                                    </Card>
                                </Grid.Col>
                            </Grid>

                            <Divider my="md" />

                            <Group justify="center">
                                <div style={{ textAlign: 'center' }}>
                                    <Text size="sm" c="dimmed">Change</Text>
                                    <Group gap="xs" mt="xs">
                                        <Badge
                                            size="xl"
                                            color={comparisonData.is_improvement ? 'green' : 'red'}
                                        >
                                            {comparisonData.percentage_change > 0 ? '+' : ''}
                                            {comparisonData.percentage_change}%
                                        </Badge>
                                        <Text size="sm" c="dimmed">
                                            ({comparisonData.absolute_change > 0 ? '+' : ''}
                                            {comparisonData.absolute_change})
                                        </Text>
                                    </Group>
                                </div>
                            </Group>
                        </Card>
                    )}

                    {/* Anomalies */}
                    {anomaliesData && anomaliesData.anomalies_count > 0 && (
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group justify="space-between" mb="md">
                                <Text fw={600} size="lg">Detected Anomalies</Text>
                                <Badge color="orange" leftSection={<IconAlertTriangle size={14} />}>
                                    {anomaliesData.anomalies_count} Found
                                </Badge>
                            </Group>

                            <Table>
                                <Table.Thead>
                                    <Table.Tr>
                                        <Table.Th>Date</Table.Th>
                                        <Table.Th>Value</Table.Th>
                                        <Table.Th>Expected</Table.Th>
                                        <Table.Th>Deviation</Table.Th>
                                        <Table.Th>Severity</Table.Th>
                                        <Table.Th>Explanation</Table.Th>
                                    </Table.Tr>
                                </Table.Thead>
                                <Table.Tbody>
                                    {anomaliesData.anomalies.map((anomaly: any, index: number) => (
                                        <Table.Tr key={index}>
                                            <Table.Td>
                                                {new Date(anomaly.detected_at).toLocaleDateString()}
                                            </Table.Td>
                                            <Table.Td fw={600}>{anomaly.value.toFixed(2)}</Table.Td>
                                            <Table.Td c="dimmed">{anomaly.expected_value.toFixed(2)}</Table.Td>
                                            <Table.Td>
                                                <Badge color={anomaly.severity === 'high' ? 'red' : anomaly.severity === 'medium' ? 'orange' : 'yellow'}>
                                                    {anomaly.deviation_pct > 0 ? '+' : ''}{anomaly.deviation_pct}%
                                                </Badge>
                                            </Table.Td>
                                            <Table.Td>
                                                <Badge color={anomaly.severity === 'high' ? 'red' : anomaly.severity === 'medium' ? 'orange' : 'yellow'}>
                                                    {anomaly.severity}
                                                </Badge>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text size="sm">{anomaly.explanation}</Text>
                                            </Table.Td>
                                        </Table.Tr>
                                    ))}
                                </Table.Tbody>
                            </Table>
                        </Card>
                    )}

                    {anomaliesData && anomaliesData.anomalies_count === 0 && (
                        <Alert color="green" title="No Anomalies Detected">
                            All data points are within normal range. No unusual spikes or drops detected.
                        </Alert>
                    )}
                </Stack>
            )}
        </Container>
    );
}
