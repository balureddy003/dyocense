import {
    Alert,
    Badge,
    Button,
    Card,
    Container,
    Divider,
    Grid,
    Group,
    List,
    NumberInput,
    Paper,
    Select,
    Stack,
    Table,
    Tabs,
    Text,
    Textarea,
    Title,
} from '@mantine/core';
import {
    IconAlertTriangle,
    IconCalculator,
    IconCalendarEvent,
    IconChartLine,
    IconTrendingUp
} from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { Area, AreaChart, CartesianGrid, Legend, Line, LineChart, Tooltip as RechartsTooltip, ResponsiveContainer, XAxis, YAxis } from 'recharts';

const apiUrl = (import.meta as any).env?.VITE_API_URL || '';

const metricOptions = [
    { value: 'revenue', label: 'Revenue' },
    { value: 'profit', label: 'Profit' },
    { value: 'customers', label: 'Customers' },
    { value: 'orders', label: 'Orders' },
];

const forecastMethodOptions = [
    { value: 'auto', label: 'Auto-Select Best Method' },
    { value: 'linear', label: 'Linear Trend' },
    { value: 'exponential_smoothing', label: 'Exponential Smoothing' },
    { value: 'moving_average', label: 'Moving Average' },
    { value: 'seasonal', label: 'Seasonal' },
];

const anomalyMethodOptions = [
    { value: 'zscore', label: 'Z-Score (Statistical)' },
    { value: 'iqr', label: 'IQR (Interquartile Range)' },
];

export function Forecasting() {
    const [activeTab, setActiveTab] = useState<string | null>('forecast');

    // Forecast state
    const [forecastMetric, setForecastMetric] = useState('revenue');
    const [forecastPeriods, setForecastPeriods] = useState(14);
    const [forecastMethod, setForecastMethod] = useState('auto');
    const [forecastData, setForecastData] = useState<any>(null);

    // Seasonality state
    const [seasonalityMetric, setSeasonalityMetric] = useState('revenue');
    const [seasonalityData, setSeasonalityData] = useState<any>(null);

    // Anomaly state
    const [anomalyMetric, setAnomalyMetric] = useState('revenue');
    const [anomalyMethod, setAnomalyMethod] = useState('zscore');
    const [anomalySensitivity, setAnomalySensitivity] = useState(3);
    const [anomalyData, setAnomalyData] = useState<any>(null);

    // Scenario state
    const [scenarioName, setScenarioName] = useState('Revenue Growth Scenario');
    const [revenueGrowth, setRevenueGrowth] = useState(15);
    const [customerChange, setCustomerChange] = useState(100);
    const [avgOrderGrowth, setAvgOrderGrowth] = useState(10);
    const [scenarioData, setScenarioData] = useState<any>(null);

    // Forecast mutation
    const forecastMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                periods: forecastPeriods.toString(),
                method: forecastMethod,
                confidence_level: '0.95',
            });

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/forecast/${forecastMetric}?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to generate forecast');
            return response.json();
        },
        onSuccess: (data) => {
            setForecastData(data);
        },
    });

    // Seasonality mutation
    const seasonalityMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/seasonality/${seasonalityMetric}`
            );

            if (!response.ok) throw new Error('Failed to detect seasonality');
            return response.json();
        },
        onSuccess: (data) => {
            setSeasonalityData(data);
        },
    });

    // Anomaly mutation
    const anomalyMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                method: anomalyMethod,
                sensitivity: anomalySensitivity.toString(),
            });

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/anomalies/${anomalyMetric}?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to detect anomalies');
            return response.json();
        },
        onSuccess: (data) => {
            setAnomalyData(data);
        },
    });

    // Scenario mutation
    const scenarioMutation = useMutation({
        mutationFn: async () => {
            const assumptions = JSON.stringify({
                revenue_growth: revenueGrowth / 100,
                customers_change: customerChange,
                avg_order_value_growth: avgOrderGrowth / 100,
            });

            const params = new URLSearchParams({
                scenario_name: scenarioName,
                assumptions: assumptions,
            });

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/scenarios?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to run scenario');
            return response.json();
        },
        onSuccess: (data) => {
            setScenarioData(data);
        },
    });

    const formatDate = (dateString: string): string => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const getSeverityColor = (severity: string): string => {
        const colors: Record<string, string> = {
            high: 'red',
            medium: 'orange',
            low: 'yellow',
        };
        return colors[severity] || 'gray';
    };

    return (
        <Container size="xl" py="xl">
            <Stack gap="xl">
                <Group justify="space-between">
                    <Title order={1}>📈 Forecasting & Predictive Analytics</Title>
                </Group>

                <Tabs value={activeTab} onChange={setActiveTab}>
                    <Tabs.List>
                        <Tabs.Tab value="forecast" leftSection={<IconTrendingUp size={16} />}>
                            Forecasting
                        </Tabs.Tab>
                        <Tabs.Tab value="seasonality" leftSection={<IconCalendarEvent size={16} />}>
                            Seasonality
                        </Tabs.Tab>
                        <Tabs.Tab value="anomalies" leftSection={<IconAlertTriangle size={16} />}>
                            Anomaly Detection
                        </Tabs.Tab>
                        <Tabs.Tab value="scenarios" leftSection={<IconCalculator size={16} />}>
                            What-If Scenarios
                        </Tabs.Tab>
                    </Tabs.List>

                    {/* Forecasting Tab */}
                    <Tabs.Panel value="forecast" pt="md">
                        <Grid>
                            <Grid.Col span={{ base: 12, md: 4 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack>
                                        <Text fw={600} size="lg">Generate Forecast</Text>

                                        <Select
                                            label="Metric"
                                            data={metricOptions}
                                            value={forecastMetric}
                                            onChange={(value) => setForecastMetric(value || 'revenue')}
                                        />

                                        <NumberInput
                                            label="Forecast Periods (days)"
                                            value={forecastPeriods}
                                            onChange={(value) => setForecastPeriods(Number(value) || 14)}
                                            min={1}
                                            max={90}
                                        />

                                        <Select
                                            label="Method"
                                            data={forecastMethodOptions}
                                            value={forecastMethod}
                                            onChange={(value) => setForecastMethod(value || 'auto')}
                                        />

                                        <Button
                                            fullWidth
                                            onClick={() => forecastMutation.mutate()}
                                            loading={forecastMutation.isPending}
                                            leftSection={<IconChartLine size={16} />}
                                        >
                                            Generate Forecast
                                        </Button>

                                        {forecastMutation.isError && (
                                            <Alert color="red" title="Error">
                                                {(forecastMutation.error as Error)?.message}
                                            </Alert>
                                        )}
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 8 }}>
                                {forecastData ? (
                                    <Stack>
                                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                                            <Stack gap="xs">
                                                <Group justify="space-between">
                                                    <Text fw={600} size="lg">
                                                        {forecastData.metric_name} Forecast
                                                    </Text>
                                                    <Badge>{forecastData.method}</Badge>
                                                </Group>

                                                <Text size="sm" c="dimmed">
                                                    {forecastData.forecast_periods} day forecast •
                                                    MAPE: {forecastData.accuracy_metrics.mape}% •
                                                    RMSE: {forecastData.accuracy_metrics.rmse.toFixed(2)}
                                                </Text>
                                            </Stack>

                                            <Divider my="md" />

                                            <ResponsiveContainer width="100%" height={400}>
                                                <AreaChart
                                                    data={forecastData.forecasted_values.map((point: any, idx: number) => ({
                                                        date: formatDate(point.date),
                                                        forecast: point.value,
                                                        lower: forecastData.confidence_intervals[idx].lower_bound,
                                                        upper: forecastData.confidence_intervals[idx].upper_bound,
                                                    }))}
                                                >
                                                    <CartesianGrid strokeDasharray="3 3" />
                                                    <XAxis dataKey="date" />
                                                    <YAxis />
                                                    <RechartsTooltip />
                                                    <Legend />
                                                    <Area
                                                        type="monotone"
                                                        dataKey="upper"
                                                        stackId="1"
                                                        stroke="#82ca9d"
                                                        fill="#82ca9d"
                                                        fillOpacity={0.2}
                                                        name="Upper Bound"
                                                    />
                                                    <Area
                                                        type="monotone"
                                                        dataKey="forecast"
                                                        stackId="2"
                                                        stroke="#8884d8"
                                                        fill="#8884d8"
                                                        name="Forecast"
                                                    />
                                                    <Area
                                                        type="monotone"
                                                        dataKey="lower"
                                                        stackId="1"
                                                        stroke="#82ca9d"
                                                        fill="#82ca9d"
                                                        fillOpacity={0.2}
                                                        name="Lower Bound"
                                                    />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </Card>

                                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                                            <Text fw={600} mb="md">Forecasted Values</Text>
                                            <Table>
                                                <Table.Thead>
                                                    <Table.Tr>
                                                        <Table.Th>Date</Table.Th>
                                                        <Table.Th>Forecast</Table.Th>
                                                        <Table.Th>Range (95% CI)</Table.Th>
                                                    </Table.Tr>
                                                </Table.Thead>
                                                <Table.Tbody>
                                                    {forecastData.forecasted_values.slice(0, 7).map((point: any, idx: number) => (
                                                        <Table.Tr key={idx}>
                                                            <Table.Td>{formatDate(point.date)}</Table.Td>
                                                            <Table.Td>
                                                                <Text fw={600}>{point.value.toFixed(2)}</Text>
                                                            </Table.Td>
                                                            <Table.Td>
                                                                <Text size="sm" c="dimmed">
                                                                    {forecastData.confidence_intervals[idx].lower_bound.toFixed(2)} - {forecastData.confidence_intervals[idx].upper_bound.toFixed(2)}
                                                                </Text>
                                                            </Table.Td>
                                                        </Table.Tr>
                                                    ))}
                                                </Table.Tbody>
                                            </Table>
                                        </Card>
                                    </Stack>
                                ) : (
                                    <Card shadow="sm" padding="xl" radius="md" withBorder>
                                        <Stack align="center" gap="md">
                                            <IconChartLine size={48} stroke={1.5} color="#aaa" />
                                            <Text c="dimmed">Select a metric and click "Generate Forecast" to see predictions</Text>
                                        </Stack>
                                    </Card>
                                )}
                            </Grid.Col>
                        </Grid>
                    </Tabs.Panel>

                    {/* Seasonality Tab */}
                    <Tabs.Panel value="seasonality" pt="md">
                        <Grid>
                            <Grid.Col span={{ base: 12, md: 4 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack>
                                        <Text fw={600} size="lg">Detect Seasonality</Text>

                                        <Select
                                            label="Metric"
                                            data={metricOptions}
                                            value={seasonalityMetric}
                                            onChange={(value) => setSeasonalityMetric(value || 'revenue')}
                                        />

                                        <Button
                                            fullWidth
                                            onClick={() => seasonalityMutation.mutate()}
                                            loading={seasonalityMutation.isPending}
                                            leftSection={<IconCalendarEvent size={16} />}
                                        >
                                            Analyze Seasonality
                                        </Button>

                                        {seasonalityMutation.isError && (
                                            <Alert color="red" title="Error">
                                                {(seasonalityMutation.error as Error)?.message}
                                            </Alert>
                                        )}
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 8 }}>
                                {seasonalityData ? (
                                    <Stack>
                                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                                            <Stack gap="md">
                                                <Group justify="space-between">
                                                    <Text fw={600} size="lg">Seasonality Analysis</Text>
                                                    <Badge color={seasonalityData.has_seasonality ? 'green' : 'gray'}>
                                                        {seasonalityData.has_seasonality ? 'Seasonal Pattern Detected' : 'No Seasonality'}
                                                    </Badge>
                                                </Group>

                                                {seasonalityData.has_seasonality ? (
                                                    <>
                                                        <Paper p="md" withBorder>
                                                            <Group>
                                                                <Stack gap={4} style={{ flex: 1 }}>
                                                                    <Text size="sm" c="dimmed">Period</Text>
                                                                    <Text fw={600} tt="capitalize">{seasonalityData.period}</Text>
                                                                </Stack>
                                                                <Stack gap={4} style={{ flex: 1 }}>
                                                                    <Text size="sm" c="dimmed">Strength</Text>
                                                                    <Text fw={600}>{(seasonalityData.strength * 100).toFixed(1)}%</Text>
                                                                </Stack>
                                                            </Group>
                                                        </Paper>

                                                        <Text size="sm">
                                                            Your {seasonalityData.metric_name} shows a {seasonalityData.period} seasonal pattern
                                                            with {seasonalityData.strength > 0.6 ? 'strong' : 'moderate'} regularity.
                                                            This means values tend to repeat in a predictable cycle every {seasonalityData.period === 'weekly' ? '7 days' : '30 days'}.
                                                        </Text>

                                                        <ResponsiveContainer width="100%" height={300}>
                                                            <LineChart
                                                                data={seasonalityData.trend_components.map((val: number, idx: number) => ({
                                                                    index: idx,
                                                                    trend: val,
                                                                    seasonal: seasonalityData.seasonal_components[idx],
                                                                }))}
                                                            >
                                                                <CartesianGrid strokeDasharray="3 3" />
                                                                <XAxis dataKey="index" label={{ value: 'Days', position: 'insideBottom', offset: -5 }} />
                                                                <YAxis />
                                                                <RechartsTooltip />
                                                                <Legend />
                                                                <Line type="monotone" dataKey="trend" stroke="#8884d8" name="Trend" />
                                                                <Line type="monotone" dataKey="seasonal" stroke="#82ca9d" name="Seasonal" />
                                                            </LineChart>
                                                        </ResponsiveContainer>
                                                    </>
                                                ) : (
                                                    <Alert color="blue" title="No Significant Pattern">
                                                        No clear seasonal pattern was detected in your {seasonalityData.metric_name} data.
                                                        This could mean your metric is more influenced by other factors or has irregular patterns.
                                                    </Alert>
                                                )}
                                            </Stack>
                                        </Card>
                                    </Stack>
                                ) : (
                                    <Card shadow="sm" padding="xl" radius="md" withBorder>
                                        <Stack align="center" gap="md">
                                            <IconCalendarEvent size={48} stroke={1.5} color="#aaa" />
                                            <Text c="dimmed">Select a metric and click "Analyze Seasonality" to detect patterns</Text>
                                        </Stack>
                                    </Card>
                                )}
                            </Grid.Col>
                        </Grid>
                    </Tabs.Panel>

                    {/* Anomalies Tab */}
                    <Tabs.Panel value="anomalies" pt="md">
                        <Grid>
                            <Grid.Col span={{ base: 12, md: 4 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack>
                                        <Text fw={600} size="lg">Detect Anomalies</Text>

                                        <Select
                                            label="Metric"
                                            data={metricOptions}
                                            value={anomalyMetric}
                                            onChange={(value) => setAnomalyMetric(value || 'revenue')}
                                        />

                                        <Select
                                            label="Detection Method"
                                            data={anomalyMethodOptions}
                                            value={anomalyMethod}
                                            onChange={(value) => setAnomalyMethod(value || 'zscore')}
                                        />

                                        <NumberInput
                                            label="Sensitivity"
                                            description="Higher = fewer anomalies"
                                            value={anomalySensitivity}
                                            onChange={(value) => setAnomalySensitivity(Number(value) || 3)}
                                            min={1}
                                            max={5}
                                            step={0.5}
                                        />

                                        <Button
                                            fullWidth
                                            onClick={() => anomalyMutation.mutate()}
                                            loading={anomalyMutation.isPending}
                                            leftSection={<IconAlertTriangle size={16} />}
                                        >
                                            Detect Anomalies
                                        </Button>

                                        {anomalyMutation.isError && (
                                            <Alert color="red" title="Error">
                                                {(anomalyMutation.error as Error)?.message}
                                            </Alert>
                                        )}
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 8 }}>
                                {anomalyData ? (
                                    <Stack>
                                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                                            <Stack gap="md">
                                                <Group justify="space-between">
                                                    <Text fw={600} size="lg">Anomaly Detection Results</Text>
                                                    <Group>
                                                        <Badge color={anomalyData.anomaly_count > 0 ? 'orange' : 'green'}>
                                                            {anomalyData.anomaly_count} Anomalies
                                                        </Badge>
                                                        <Badge variant="light">
                                                            {anomalyData.anomaly_percentage.toFixed(1)}% of data
                                                        </Badge>
                                                    </Group>
                                                </Group>

                                                {anomalyData.anomaly_count > 0 ? (
                                                    <>
                                                        <Alert color="orange" title="Unusual Values Detected">
                                                            Found {anomalyData.anomaly_count} data points that significantly deviate
                                                            from normal patterns in your {anomalyData.metric_name}.
                                                        </Alert>

                                                        <Table>
                                                            <Table.Thead>
                                                                <Table.Tr>
                                                                    <Table.Th>Date</Table.Th>
                                                                    <Table.Th>Value</Table.Th>
                                                                    <Table.Th>Deviation</Table.Th>
                                                                    <Table.Th>Severity</Table.Th>
                                                                </Table.Tr>
                                                            </Table.Thead>
                                                            <Table.Tbody>
                                                                {anomalyData.anomalies.map((anomaly: any, idx: number) => (
                                                                    <Table.Tr key={idx}>
                                                                        <Table.Td>{formatDate(anomaly.date)}</Table.Td>
                                                                        <Table.Td>
                                                                            <Text fw={600}>{anomaly.value.toFixed(2)}</Text>
                                                                        </Table.Td>
                                                                        <Table.Td>
                                                                            <Text size="sm" c="dimmed">
                                                                                {anomaly.z_score ? `Z-score: ${anomaly.z_score}` :
                                                                                    `Range: ${anomaly.expected_range}`}
                                                                            </Text>
                                                                        </Table.Td>
                                                                        <Table.Td>
                                                                            <Badge color={getSeverityColor(anomaly.severity)}>
                                                                                {anomaly.severity}
                                                                            </Badge>
                                                                        </Table.Td>
                                                                    </Table.Tr>
                                                                ))}
                                                            </Table.Tbody>
                                                        </Table>
                                                    </>
                                                ) : (
                                                    <Alert color="green" title="No Anomalies Detected">
                                                        Your {anomalyData.metric_name} data looks normal with no unusual spikes or drops.
                                                    </Alert>
                                                )}
                                            </Stack>
                                        </Card>
                                    </Stack>
                                ) : (
                                    <Card shadow="sm" padding="xl" radius="md" withBorder>
                                        <Stack align="center" gap="md">
                                            <IconAlertTriangle size={48} stroke={1.5} color="#aaa" />
                                            <Text c="dimmed">Select a metric and click "Detect Anomalies" to find unusual values</Text>
                                        </Stack>
                                    </Card>
                                )}
                            </Grid.Col>
                        </Grid>
                    </Tabs.Panel>

                    {/* Scenarios Tab */}
                    <Tabs.Panel value="scenarios" pt="md">
                        <Grid>
                            <Grid.Col span={{ base: 12, md: 4 }}>
                                <Card shadow="sm" padding="lg" radius="md" withBorder>
                                    <Stack>
                                        <Text fw={600} size="lg">What-If Scenario</Text>

                                        <Textarea
                                            label="Scenario Name"
                                            value={scenarioName}
                                            onChange={(e) => setScenarioName(e.currentTarget.value)}
                                            rows={2}
                                        />

                                        <Divider label="Assumptions" />

                                        <NumberInput
                                            label="Revenue Growth (%)"
                                            value={revenueGrowth}
                                            onChange={(value) => setRevenueGrowth(Number(value) || 0)}
                                            suffix="%"
                                        />

                                        <NumberInput
                                            label="Customer Change"
                                            value={customerChange}
                                            onChange={(value) => setCustomerChange(Number(value) || 0)}
                                        />

                                        <NumberInput
                                            label="Avg Order Value Growth (%)"
                                            value={avgOrderGrowth}
                                            onChange={(value) => setAvgOrderGrowth(Number(value) || 0)}
                                            suffix="%"
                                        />

                                        <Button
                                            fullWidth
                                            onClick={() => scenarioMutation.mutate()}
                                            loading={scenarioMutation.isPending}
                                            leftSection={<IconCalculator size={16} />}
                                        >
                                            Run Scenario
                                        </Button>

                                        {scenarioMutation.isError && (
                                            <Alert color="red" title="Error">
                                                {(scenarioMutation.error as Error)?.message}
                                            </Alert>
                                        )}
                                    </Stack>
                                </Card>
                            </Grid.Col>

                            <Grid.Col span={{ base: 12, md: 8 }}>
                                {scenarioData ? (
                                    <Stack>
                                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                                            <Stack gap="md">
                                                <Group justify="space-between">
                                                    <Text fw={600} size="lg">{scenarioData.scenario_name}</Text>
                                                    <Badge>Confidence: {(scenarioData.confidence_level * 100).toFixed(0)}%</Badge>
                                                </Group>

                                                <Paper p="md" withBorder>
                                                    <Text size="sm" fw={500} mb="xs">Assumptions:</Text>
                                                    <List size="sm" spacing="xs">
                                                        {Object.entries(scenarioData.assumptions).map(([key, value]: [string, any]) => (
                                                            <List.Item key={key}>
                                                                {key.replace(/_/g, ' ')}: {typeof value === 'number' && value < 1 ?
                                                                    `${(value * 100).toFixed(1)}%` : value}
                                                            </List.Item>
                                                        ))}
                                                    </List>
                                                </Paper>

                                                <Text fw={500}>Predicted Outcomes:</Text>

                                                <Grid>
                                                    {Object.entries(scenarioData.predicted_outcomes).map(([metric, value]: [string, any]) => {
                                                        const change = scenarioData.comparison_to_baseline[metric];
                                                        const isPositive = change > 0;

                                                        return (
                                                            <Grid.Col key={metric} span={6}>
                                                                <Paper p="md" withBorder>
                                                                    <Stack gap={4}>
                                                                        <Text size="sm" c="dimmed" tt="capitalize">
                                                                            {metric.replace(/_/g, ' ')}
                                                                        </Text>
                                                                        <Text size="xl" fw={700}>{value.toFixed(2)}</Text>
                                                                        <Badge
                                                                            color={isPositive ? 'green' : 'red'}
                                                                            variant="light"
                                                                            leftSection={isPositive ? '↑' : '↓'}
                                                                        >
                                                                            {Math.abs(change).toFixed(2)}
                                                                        </Badge>
                                                                    </Stack>
                                                                </Paper>
                                                            </Grid.Col>
                                                        );
                                                    })}
                                                </Grid>
                                            </Stack>
                                        </Card>
                                    </Stack>
                                ) : (
                                    <Card shadow="sm" padding="xl" radius="md" withBorder>
                                        <Stack align="center" gap="md">
                                            <IconCalculator size={48} stroke={1.5} color="#aaa" />
                                            <Text c="dimmed">Configure assumptions and click "Run Scenario" to see predicted outcomes</Text>
                                        </Stack>
                                    </Card>
                                )}
                            </Grid.Col>
                        </Grid>
                    </Tabs.Panel>
                </Tabs>
            </Stack>
        </Container>
    );
}
