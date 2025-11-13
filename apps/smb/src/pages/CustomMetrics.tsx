import {
    ActionIcon,
    Alert,
    Badge,
    Button,
    Card,
    Code,
    Container,
    Divider,
    Grid,
    Group,
    List,
    Modal,
    MultiSelect,
    Paper,
    Select,
    Stack,
    Switch,
    Table,
    Tabs,
    Text,
    TextInput,
    Textarea,
    Title,
    Tooltip
} from '@mantine/core';
import {
    IconAlertCircle,
    IconCalculator,
    IconCheck,
    IconMath,
    IconPlus,
    IconTemplate,
    IconTrash
} from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

const apiUrl = (import.meta as any).env?.VITE_API_URL || '';

interface CustomMetric {
    id: string;
    name: string;
    description: string;
    metric_type: string;
    formula: string;
    unit: string;
    data_sources: string[];
    thresholds_count: number;
    enabled: boolean;
    created_at: string;
    created_by: string;
}

interface MetricTemplate {
    id: string;
    name: string;
    description: string;
    category: string;
    formula: string;
    unit: string;
    data_sources: string[];
    recommended_thresholds: any[];
    industry: string | null;
}

interface DataSource {
    id: string;
    name: string;
    unit: string;
}

interface CalculationResult {
    metric_id: string;
    metric_name: string;
    value: number;
    unit: string;
    calculated_at: string;
    triggered_thresholds: any[];
    data_points: any[];
}

const metricTypeOptions = [
    { value: 'calculated', label: 'Calculated (Formula-based)' },
    { value: 'ratio', label: 'Ratio' },
    { value: 'percentage', label: 'Percentage' },
];

const categoryOptions = [
    { value: 'financial', label: 'Financial' },
    { value: 'operational', label: 'Operational' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'sales', label: 'Sales' },
];

const severityOptions = [
    { value: 'info', label: 'Info' },
    { value: 'warning', label: 'Warning' },
    { value: 'critical', label: 'Critical' },
];

const comparisonOptions = [
    { value: '>', label: 'Greater than (>)' },
    { value: '<', label: 'Less than (<)' },
    { value: '>=', label: 'Greater or equal (>=)' },
    { value: '<=', label: 'Less or equal (<=)' },
    { value: '==', label: 'Equal (==)' },
    { value: '!=', label: 'Not equal (!=)' },
];

export function CustomMetrics() {
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<string | null>('metrics');

    // Create metric state
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [metricName, setMetricName] = useState('');
    const [metricDescription, setMetricDescription] = useState('');
    const [metricType, setMetricType] = useState('calculated');
    const [formula, setFormula] = useState('');
    const [unit, setUnit] = useState('');
    const [selectedDataSources, setSelectedDataSources] = useState<string[]>([]);

    // Template state
    const [selectedTemplate, setSelectedTemplate] = useState<MetricTemplate | null>(null);
    const [templateModalOpen, setTemplateModalOpen] = useState(false);
    const [customTemplateName, setCustomTemplateName] = useState('');

    // Calculate state
    const [calculateModalOpen, setCalculateModalOpen] = useState(false);
    const [calculateMetricId, setCalculateMetricId] = useState<string | null>(null);
    const [calculationResult, setCalculationResult] = useState<CalculationResult | null>(null);

    // Filter state
    const [categoryFilter, setCategoryFilter] = useState<string | null>(null);

    // Fetch custom metrics
    const { data: metricsData, isLoading: metricsLoading } = useQuery({
        queryKey: ['custom-metrics'],
        queryFn: async () => {
            const response = await fetch(`${apiUrl}/v1/tenants/test-tenant/metrics/custom`);
            if (!response.ok) throw new Error('Failed to fetch metrics');
            return response.json();
        },
        refetchInterval: 30000,
    });

    // Fetch templates
    const { data: templatesData, isLoading: templatesLoading } = useQuery({
        queryKey: ['metric-templates', categoryFilter],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (categoryFilter) params.append('category', categoryFilter);

            const response = await fetch(`${apiUrl}/v1/tenants/test-tenant/metrics/templates?${params}`);
            if (!response.ok) throw new Error('Failed to fetch templates');
            return response.json();
        },
        refetchInterval: 60000,
    });

    // Fetch data sources
    const { data: dataSourcesData } = useQuery({
        queryKey: ['data-sources'],
        queryFn: async () => {
            const response = await fetch(`${apiUrl}/v1/tenants/test-tenant/metrics/data-sources`);
            if (!response.ok) throw new Error('Failed to fetch data sources');
            return response.json();
        },
    });

    // Create metric mutation
    const createMetricMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                name: metricName,
                description: metricDescription,
                metric_type: metricType,
                formula: formula,
                unit: unit,
                data_sources: selectedDataSources.join(','),
            });

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/metrics/custom?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create metric');
            }
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['custom-metrics'] });
            setCreateModalOpen(false);
            resetCreateForm();
        },
    });

    // Create from template mutation
    const createFromTemplateMutation = useMutation({
        mutationFn: async (templateId: string) => {
            const params = new URLSearchParams();
            if (customTemplateName) {
                params.append('custom_name', customTemplateName);
            }

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/metrics/templates/${templateId}/create?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to create from template');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['custom-metrics'] });
            setTemplateModalOpen(false);
            setSelectedTemplate(null);
            setCustomTemplateName('');
        },
    });

    // Delete metric mutation
    const deleteMetricMutation = useMutation({
        mutationFn: async (metricId: string) => {
            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/metrics/custom/${metricId}`,
                { method: 'DELETE' }
            );

            if (!response.ok) throw new Error('Failed to delete metric');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['custom-metrics'] });
        },
    });

    // Toggle metric mutation
    const toggleMetricMutation = useMutation({
        mutationFn: async ({ metricId, enabled }: { metricId: string; enabled: boolean }) => {
            const params = new URLSearchParams({
                enabled: enabled.toString(),
            });

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/metrics/custom/${metricId}?${params}`,
                { method: 'PUT' }
            );

            if (!response.ok) throw new Error('Failed to update metric');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['custom-metrics'] });
        },
    });

    // Calculate metric mutation
    const calculateMetricMutation = useMutation({
        mutationFn: async (metricId: string) => {
            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/metrics/custom/${metricId}/calculate`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to calculate metric');
            return response.json();
        },
        onSuccess: (data) => {
            setCalculationResult(data);
        },
    });

    const resetCreateForm = () => {
        setMetricName('');
        setMetricDescription('');
        setMetricType('calculated');
        setFormula('');
        setUnit('');
        setSelectedDataSources([]);
    };

    const handleCreateMetric = () => {
        createMetricMutation.mutate();
    };

    const handleUseTemplate = (template: MetricTemplate) => {
        setSelectedTemplate(template);
        setCustomTemplateName(template.name);
        setTemplateModalOpen(true);
    };

    const handleCalculateMetric = (metricId: string) => {
        setCalculateMetricId(metricId);
        setCalculationResult(null);
        setCalculateModalOpen(true);
        calculateMetricMutation.mutate(metricId);
    };

    const formatDate = (dateString: string): string => {
        return new Date(dateString).toLocaleDateString();
    };

    const getCategoryColor = (category: string): string => {
        const colors: Record<string, string> = {
            financial: 'blue',
            operational: 'green',
            marketing: 'orange',
            sales: 'purple',
        };
        return colors[category] || 'gray';
    };

    const getSeverityColor = (severity: string): string => {
        const colors: Record<string, string> = {
            info: 'blue',
            warning: 'orange',
            critical: 'red',
        };
        return colors[severity] || 'gray';
    };

    const metrics: CustomMetric[] = metricsData?.metrics || [];
    const templates: MetricTemplate[] = templatesData?.templates || [];
    const dataSources: DataSource[] = dataSourcesData?.data_sources || [];

    const dataSourceOptions = dataSources.map(ds => ({
        value: ds.id,
        label: `${ds.name} (${ds.unit})`
    }));

    return (
        <Container size="xl" py="xl">
            <Group justify="space-between" mb="xl">
                <Title order={1}>📊 Custom Metrics & KPIs</Title>
                <Group>
                    <Button
                        leftSection={<IconTemplate size={16} />}
                        variant="light"
                        onClick={() => setActiveTab('templates')}
                    >
                        Browse Templates
                    </Button>
                    <Button
                        leftSection={<IconPlus size={16} />}
                        onClick={() => setCreateModalOpen(true)}
                    >
                        Create Custom Metric
                    </Button>
                </Group>
            </Group>

            <Tabs value={activeTab} onChange={setActiveTab}>
                <Tabs.List>
                    <Tabs.Tab value="metrics" leftSection={<IconMath size={16} />}>
                        My Metrics
                    </Tabs.Tab>
                    <Tabs.Tab value="templates" leftSection={<IconTemplate size={16} />}>
                        KPI Templates
                    </Tabs.Tab>
                </Tabs.List>

                <Tabs.Panel value="metrics" pt="md">
                    <Card shadow="sm" padding="lg" radius="md" withBorder>
                        {metricsLoading ? (
                            <Text>Loading metrics...</Text>
                        ) : metrics.length === 0 ? (
                            <Alert color="blue" title="No custom metrics yet">
                                Create your first custom metric or use a template to get started!
                            </Alert>
                        ) : (
                            <Table highlightOnHover>
                                <Table.Thead>
                                    <Table.Tr>
                                        <Table.Th>Name</Table.Th>
                                        <Table.Th>Formula</Table.Th>
                                        <Table.Th>Unit</Table.Th>
                                        <Table.Th>Data Sources</Table.Th>
                                        <Table.Th>Status</Table.Th>
                                        <Table.Th>Actions</Table.Th>
                                    </Table.Tr>
                                </Table.Thead>
                                <Table.Tbody>
                                    {metrics.map((metric) => (
                                        <Table.Tr key={metric.id}>
                                            <Table.Td>
                                                <Stack gap={4}>
                                                    <Text fw={500}>{metric.name}</Text>
                                                    <Text size="xs" c="dimmed">{metric.description}</Text>
                                                </Stack>
                                            </Table.Td>
                                            <Table.Td>
                                                <Code>{metric.formula}</Code>
                                            </Table.Td>
                                            <Table.Td>
                                                <Badge variant="light">{metric.unit}</Badge>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text size="sm">{metric.data_sources.length} source(s)</Text>
                                            </Table.Td>
                                            <Table.Td>
                                                <Switch
                                                    checked={metric.enabled}
                                                    onChange={(e) =>
                                                        toggleMetricMutation.mutate({
                                                            metricId: metric.id,
                                                            enabled: e.currentTarget.checked,
                                                        })
                                                    }
                                                />
                                            </Table.Td>
                                            <Table.Td>
                                                <Group gap="xs">
                                                    <Tooltip label="Calculate">
                                                        <ActionIcon
                                                            variant="light"
                                                            color="blue"
                                                            onClick={() => handleCalculateMetric(metric.id)}
                                                        >
                                                            <IconCalculator size={16} />
                                                        </ActionIcon>
                                                    </Tooltip>
                                                    <Tooltip label="Delete">
                                                        <ActionIcon
                                                            variant="light"
                                                            color="red"
                                                            onClick={() => deleteMetricMutation.mutate(metric.id)}
                                                        >
                                                            <IconTrash size={16} />
                                                        </ActionIcon>
                                                    </Tooltip>
                                                </Group>
                                            </Table.Td>
                                        </Table.Tr>
                                    ))}
                                </Table.Tbody>
                            </Table>
                        )}
                    </Card>
                </Tabs.Panel>

                <Tabs.Panel value="templates" pt="md">
                    <Stack>
                        <Group>
                            <Select
                                placeholder="Filter by category"
                                data={[
                                    { value: '', label: 'All Categories' },
                                    ...categoryOptions
                                ]}
                                value={categoryFilter || ''}
                                onChange={(value) => setCategoryFilter(value || null)}
                                clearable
                            />
                        </Group>

                        {templatesLoading ? (
                            <Text>Loading templates...</Text>
                        ) : (
                            <Grid>
                                {templates.map((template) => (
                                    <Grid.Col key={template.id} span={{ base: 12, md: 6, lg: 4 }}>
                                        <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
                                            <Stack gap="md">
                                                <Group justify="space-between">
                                                    <Badge color={getCategoryColor(template.category)}>
                                                        {template.category}
                                                    </Badge>
                                                    {template.industry && (
                                                        <Badge variant="outline">{template.industry}</Badge>
                                                    )}
                                                </Group>

                                                <Stack gap={4}>
                                                    <Text fw={600} size="lg">{template.name}</Text>
                                                    <Text size="sm" c="dimmed">{template.description}</Text>
                                                </Stack>

                                                <Divider />

                                                <Stack gap="xs">
                                                    <Text size="sm" fw={500}>Formula:</Text>
                                                    <Code block>{template.formula}</Code>
                                                </Stack>

                                                <Stack gap="xs">
                                                    <Text size="sm" fw={500}>Data Sources:</Text>
                                                    <Text size="sm" c="dimmed">
                                                        {template.data_sources.join(', ')}
                                                    </Text>
                                                </Stack>

                                                <Stack gap="xs">
                                                    <Text size="sm" fw={500}>Unit:</Text>
                                                    <Badge variant="light">{template.unit}</Badge>
                                                </Stack>

                                                {template.recommended_thresholds.length > 0 && (
                                                    <Stack gap="xs">
                                                        <Text size="sm" fw={500}>Recommended Thresholds:</Text>
                                                        <List size="sm" spacing="xs">
                                                            {template.recommended_thresholds.map((threshold, idx) => (
                                                                <List.Item key={idx}>
                                                                    <Badge
                                                                        size="sm"
                                                                        color={getSeverityColor(threshold.severity)}
                                                                    >
                                                                        {threshold.severity}
                                                                    </Badge>
                                                                    {' '}
                                                                    {threshold.comparison} {threshold.value}
                                                                </List.Item>
                                                            ))}
                                                        </List>
                                                    </Stack>
                                                )}

                                                <Button
                                                    fullWidth
                                                    leftSection={<IconPlus size={16} />}
                                                    onClick={() => handleUseTemplate(template)}
                                                >
                                                    Use This Template
                                                </Button>
                                            </Stack>
                                        </Card>
                                    </Grid.Col>
                                ))}
                            </Grid>
                        )}
                    </Stack>
                </Tabs.Panel>
            </Tabs>

            {/* Create Metric Modal */}
            <Modal
                opened={createModalOpen}
                onClose={() => setCreateModalOpen(false)}
                title="Create Custom Metric"
                size="lg"
            >
                <Stack>
                    <TextInput
                        label="Metric Name"
                        placeholder="e.g., Profit Margin"
                        value={metricName}
                        onChange={(e) => setMetricName(e.currentTarget.value)}
                        required
                    />

                    <Textarea
                        label="Description"
                        placeholder="What does this metric measure?"
                        value={metricDescription}
                        onChange={(e) => setMetricDescription(e.currentTarget.value)}
                        rows={2}
                        required
                    />

                    <Select
                        label="Metric Type"
                        data={metricTypeOptions}
                        value={metricType}
                        onChange={(value) => setMetricType(value || 'calculated')}
                        required
                    />

                    <MultiSelect
                        label="Data Sources"
                        description="Select the metrics used in your formula"
                        data={dataSourceOptions}
                        value={selectedDataSources}
                        onChange={setSelectedDataSources}
                        searchable
                        required
                    />

                    <Textarea
                        label="Formula"
                        description="Use +, -, *, /, () and data source names"
                        placeholder="e.g., (revenue - cogs) / revenue * 100"
                        value={formula}
                        onChange={(e) => setFormula(e.currentTarget.value)}
                        rows={3}
                        required
                    />

                    <TextInput
                        label="Unit"
                        placeholder="e.g., %, $, items"
                        value={unit}
                        onChange={(e) => setUnit(e.currentTarget.value)}
                        required
                    />

                    {createMetricMutation.isError && (
                        <Alert color="red" title="Error" icon={<IconAlertCircle size={16} />}>
                            {(createMetricMutation.error as Error)?.message || 'Failed to create metric'}
                        </Alert>
                    )}

                    <Button
                        fullWidth
                        onClick={handleCreateMetric}
                        loading={createMetricMutation.isPending}
                        leftSection={<IconPlus size={16} />}
                    >
                        Create Metric
                    </Button>
                </Stack>
            </Modal>

            {/* Template Modal */}
            <Modal
                opened={templateModalOpen}
                onClose={() => setTemplateModalOpen(false)}
                title="Create from Template"
                size="md"
            >
                {selectedTemplate && (
                    <Stack>
                        <Paper p="md" withBorder>
                            <Stack gap="xs">
                                <Text fw={600}>{selectedTemplate.name}</Text>
                                <Text size="sm" c="dimmed">{selectedTemplate.description}</Text>
                                <Code block>{selectedTemplate.formula}</Code>
                            </Stack>
                        </Paper>

                        <TextInput
                            label="Custom Name (optional)"
                            placeholder={selectedTemplate.name}
                            value={customTemplateName}
                            onChange={(e) => setCustomTemplateName(e.currentTarget.value)}
                        />

                        <Button
                            fullWidth
                            onClick={() => createFromTemplateMutation.mutate(selectedTemplate.id)}
                            loading={createFromTemplateMutation.isPending}
                            leftSection={<IconCheck size={16} />}
                        >
                            Create Metric
                        </Button>
                    </Stack>
                )}
            </Modal>

            {/* Calculate Modal */}
            <Modal
                opened={calculateModalOpen}
                onClose={() => setCalculateModalOpen(false)}
                title="Metric Calculation Result"
                size="md"
            >
                <Stack>
                    {calculateMetricMutation.isPending ? (
                        <Text>Calculating...</Text>
                    ) : calculationResult ? (
                        <>
                            <Paper p="md" withBorder>
                                <Stack gap="xs" align="center">
                                    <Text size="sm" c="dimmed">{calculationResult.metric_name}</Text>
                                    <Group gap="xs">
                                        <Text size="48px" fw={700} c="blue">
                                            {calculationResult.value.toFixed(2)}
                                        </Text>
                                        <Text size="xl" c="dimmed">{calculationResult.unit}</Text>
                                    </Group>
                                    <Text size="xs" c="dimmed">
                                        Calculated at {new Date(calculationResult.calculated_at).toLocaleString()}
                                    </Text>
                                </Stack>
                            </Paper>

                            {calculationResult.triggered_thresholds.length > 0 && (
                                <Stack gap="xs">
                                    <Text fw={500}>Triggered Alerts:</Text>
                                    {calculationResult.triggered_thresholds.map((threshold, idx) => (
                                        <Alert
                                            key={idx}
                                            color={getSeverityColor(threshold.severity)}
                                            icon={<IconAlertCircle size={16} />}
                                        >
                                            <Text fw={500}>{threshold.message}</Text>
                                            <Text size="sm">
                                                {threshold.comparison} {threshold.threshold_value} (actual: {threshold.actual_value})
                                            </Text>
                                        </Alert>
                                    ))}
                                </Stack>
                            )}

                            <Stack gap="xs">
                                <Text fw={500}>Data Points:</Text>
                                <Table>
                                    <Table.Thead>
                                        <Table.Tr>
                                            <Table.Th>Source</Table.Th>
                                            <Table.Th>Value</Table.Th>
                                        </Table.Tr>
                                    </Table.Thead>
                                    <Table.Tbody>
                                        {calculationResult.data_points.map((point, idx) => (
                                            <Table.Tr key={idx}>
                                                <Table.Td>{point.data_source}</Table.Td>
                                                <Table.Td>{point.value}</Table.Td>
                                            </Table.Tr>
                                        ))}
                                    </Table.Tbody>
                                </Table>
                            </Stack>
                        </>
                    ) : calculateMetricMutation.isError ? (
                        <Alert color="red" title="Calculation Error">
                            {(calculateMetricMutation.error as Error)?.message || 'Failed to calculate metric'}
                        </Alert>
                    ) : null}
                </Stack>
            </Modal>
        </Container>
    );
}
