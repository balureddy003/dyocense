/**
 * Multi-Agent Visualization Components for Coach
 * 
 * Redesigned for SMB users:
 * - Clear visual hierarchy
 * - Consistent spacing (8px grid)
 * - Plain language
 * - Mobile-friendly
 */
import {
    Alert,
    Badge,
    Box,
    Card,
    Grid,
    Group,
    Paper,
    Progress,
    RingProgress,
    Stack,
    Table,
    Text,
    ThemeIcon,
    Title
} from '@mantine/core';
import {
    IconAlertTriangle,
    IconCircleCheck,
    IconInfoCircle,
    IconMinus,
    IconTrendingDown,
    IconTrendingUp
} from '@tabler/icons-react';
import React from 'react';
import {
    CriticalActionCard,
    SimplifiedHealthScore,
    SPACING
} from './SimplifiedCoachLayout';

// ============================================================================
// Type Definitions
// ============================================================================

interface VisualResponse {
    summary: string;
    kpis: KPI[];
    charts: Chart[];
    tables: DataTable[];
    actions: ActionCard[];
    insights: Insight[];
    metadata?: {
        health_score: number;
        alert_count: number;
        signal_count: number;
    };
}

interface KPI {
    label: string;
    value: string | number;
    unit?: string;
    trend?: 'up' | 'down' | 'stable' | 'critical';
    change?: string;
    color?: string;
    icon?: string;
}

interface Chart {
    type: 'bar' | 'line' | 'radialBar' | 'pie';
    title: string;
    data: any[];
    config?: {
        height?: number;
        showGrid?: boolean;
        showLabels?: boolean;
        horizontal?: boolean;
        showValues?: boolean;
        xAxis?: string;
        yAxis?: string;
    };
}

interface DataTable {
    title: string;
    headers: string[];
    rows: any[];
}

interface ActionCard {
    priority: 'critical' | 'high' | 'medium' | 'low';
    title: string;
    deadline: string;
    why: string;
    metric: string;
    icon?: string;
}

interface Insight {
    icon: string;
    type: 'warning' | 'info' | 'positive' | 'critical';
    title: string;
    description: string;
    metric: string;
    action?: string;
}

// ============================================================================
// Main Component
// ============================================================================

interface CoachVisualizationProps {
    visualResponse: VisualResponse;
}

export const CoachVisualization: React.FC<CoachVisualizationProps> = ({ visualResponse }) => {
    return (
        <Stack gap={SPACING.lg} mt={SPACING.md}>
            {/* Health Score - If Available */}
            {visualResponse.metadata?.health_score !== undefined && (
                <SimplifiedHealthScore score={visualResponse.metadata.health_score} />
            )}

            {/* Summary */}
            {visualResponse.summary && (
                <Paper p={SPACING.md} radius="lg" bg="blue.0">
                    <Text size="sm" fw={600} c="blue.9">
                        {visualResponse.summary}
                    </Text>
                </Paper>
            )}

            {/* KPIs */}
            {visualResponse.kpis && visualResponse.kpis.length > 0 && (
                <Grid gutter={SPACING.md}>
                    {visualResponse.kpis.map((kpi, idx) => (
                        <Grid.Col key={idx} span={{ base: 12, sm: 6, md: 3 }}>
                            <KPIWidget kpi={kpi} />
                        </Grid.Col>
                    ))}
                </Grid>
            )}

            {/* Critical Actions - Plain Language */}
            {visualResponse.actions && visualResponse.actions.length > 0 && (
                <Stack gap={SPACING.md}>
                    <Text size="md" fw={700}>What needs your attention:</Text>
                    {visualResponse.actions.map((action, idx) => (
                        <ActionCardWidget key={idx} action={action} />
                    ))}
                </Stack>
            )}

            {/* Insights - Plain Language */}
            {visualResponse.insights && visualResponse.insights.length > 0 && (
                <Stack gap={SPACING.sm}>
                    <Text size="md" fw={700}>Key insights:</Text>
                    <Grid gutter={SPACING.sm}>
                        {visualResponse.insights.map((insight, idx) => (
                            <Grid.Col key={idx} span={{ base: 12, md: 6 }}>
                                <InsightCard insight={insight} />
                            </Grid.Col>
                        ))}
                    </Grid>
                </Stack>
            )}

            {/* Charts */}
            {visualResponse.charts && visualResponse.charts.length > 0 && (
                <Grid gutter={SPACING.md}>
                    {visualResponse.charts.map((chart, idx) => (
                        <Grid.Col key={idx} span={{ base: 12, md: 6 }}>
                            <ChartWidget chart={chart} />
                        </Grid.Col>
                    ))}
                </Grid>
            )}

            {/* Evidence Tables - Plain Language */}
            {visualResponse.tables && visualResponse.tables.length > 0 && (
                <Stack gap={SPACING.md}>
                    <Text size="md" fw={700}>Evidence:</Text>
                    {visualResponse.tables.map((table, idx) => (
                        <TableWidget key={idx} table={table} />
                    ))}
                </Stack>
            )}
        </Stack>
    );
};

// ============================================================================
// Sub-Components
// ============================================================================

const KPIWidget: React.FC<{ kpi: KPI }> = ({ kpi }) => {
    const getTrendIcon = () => {
        switch (kpi.trend) {
            case 'up':
                return <IconTrendingUp size={16} />;
            case 'down':
                return <IconTrendingDown size={16} />;
            case 'critical':
                return <IconAlertTriangle size={16} />;
            default:
                return <IconMinus size={16} />;
        }
    };

    const getColor = () => {
        if (kpi.color) return kpi.color;
        switch (kpi.trend) {
            case 'up':
                return 'green';
            case 'down':
            case 'critical':
                return 'red';
            default:
                return 'blue';
        }
    };

    return (
        <Card shadow="sm" padding={SPACING.md} radius="lg" withBorder>
            <Stack gap={SPACING.xs}>
                <Group gap={SPACING.xs}>
                    {kpi.icon && <Text size="xl">{kpi.icon}</Text>}
                    <Text size="xs" c="dimmed" fw={600} tt="uppercase">
                        {kpi.label}
                    </Text>
                </Group>
                <Group justify="apart" align="baseline">
                    <Text size="28px" fw={700} lh={1}>
                        {kpi.value}{kpi.unit || ''}
                    </Text>
                    {kpi.trend && kpi.change && (
                        <Group gap={4}>
                            <ThemeIcon size="sm" variant="light" color={getColor()}>
                                {getTrendIcon()}
                            </ThemeIcon>
                            <Text size="sm" fw={600} c={getColor()}>
                                {kpi.change}
                            </Text>
                        </Group>
                    )}
                </Group>
            </Stack>
        </Card>
    );
};

const ChartWidget: React.FC<{ chart: Chart }> = ({ chart }) => {
    // For now, render simple bar charts using Mantine Progress
    // In production, integrate Recharts or Chart.js
    const renderSimpleBarChart = () => {
        if (chart.type === 'radialBar' && Array.isArray(chart.data)) {
            // Render radial bar as ring progress
            return (
                <Group justify="center" gap="lg">
                    {chart.data.map((item: any, idx: number) => (
                        <Stack key={idx} align="center" gap="xs">
                            <RingProgress
                                size={100}
                                thickness={12}
                                sections={[{ value: item.value || 0, color: item.color || 'blue' }]}
                                label={
                                    <Text size="sm" ta="center" fw={700}>
                                        {item.value}%
                                    </Text>
                                }
                            />
                            <Text size="xs" c="dimmed">
                                {item.category}
                            </Text>
                        </Stack>
                    ))}
                </Group>
            );
        }

        if (chart.type === 'bar' && Array.isArray(chart.data)) {
            // Render horizontal bars
            return (
                <Stack gap="xs">
                    {chart.data.map((item: any, idx: number) => (
                        <Box key={idx}>
                            <Group justify="apart" mb={4}>
                                <Text size="sm">{item.name}</Text>
                                <Text size="sm" fw={600}>
                                    {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
                                </Text>
                            </Group>
                            <Progress
                                value={(item.value / Math.max(...chart.data.map((d: any) => d.value || 0))) * 100}
                                color="violet"
                                size="md"
                            />
                        </Box>
                    ))}
                </Stack>
            );
        }

        // Fallback for other chart types
        return (
            <Text size="sm" c="dimmed">
                Chart visualization ({chart.type}) - Install chart library for full rendering
            </Text>
        );
    };

    return (
        <Card shadow="sm" padding="md" radius="md" withBorder>
            <Stack gap="md">
                <Title order={5}>{chart.title}</Title>
                <Box style={{ minHeight: chart.config?.height || 200 }}>
                    {renderSimpleBarChart()}
                </Box>
            </Stack>
        </Card>
    );
};

const InsightCard: React.FC<{ insight: Insight }> = ({ insight }) => {
    const getAlertColor = () => {
        switch (insight.type) {
            case 'critical':
            case 'warning':
                return 'red';
            case 'positive':
                return 'green';
            default:
                return 'blue';
        }
    };

    const getIcon = () => {
        switch (insight.type) {
            case 'critical':
            case 'warning':
                return <IconAlertTriangle size={20} />;
            case 'positive':
                return <IconCircleCheck size={20} />;
            default:
                return <IconInfoCircle size={20} />;
        }
    };

    return (
        <Alert
            color={getAlertColor()}
            variant="light"
            icon={getIcon()}
            title={
                <Group gap="xs">
                    <Text>{insight.icon}</Text>
                    <Text fw={600}>{insight.title}</Text>
                </Group>
            }
        >
            <Stack gap="xs">
                <Text size="sm">{insight.description}</Text>
                {insight.metric && (
                    <Badge variant="filled" color={getAlertColor()}>
                        {insight.metric}
                    </Badge>
                )}
                {insight.action && (
                    <Text size="xs" c="dimmed" fw={500}>
                        → {insight.action}
                    </Text>
                )}
            </Stack>
        </Alert>
    );
};

const ActionCardWidget: React.FC<{ action: ActionCard }> = ({ action }) => {
    // Use new simplified component for critical/high priority actions
    if (action.priority === 'critical' || action.priority === 'high') {
        return (
            <CriticalActionCard
                icon={action.icon || '⚠️'}
                title={action.title}
                deadline={action.deadline}
                why={action.why}
                clients={(action as any).clients}
                products={(action as any).products}
            />
        );
    }

    // Simple card for lower priority
    const getPriorityColor = () => {
        if (action.priority === 'medium') return 'orange';
        return 'blue';
    };

    return (
        <Card shadow="sm" padding={SPACING.md} radius="lg" withBorder>
            <Stack gap={SPACING.sm}>
                <Group gap={SPACING.xs}>
                    {action.icon && <Text size="lg">{action.icon}</Text>}
                    <Badge variant="light" color={getPriorityColor()} size="sm">
                        {action.priority === 'medium' ? 'Soon' : 'Optional'}
                    </Badge>
                    <Badge variant="outline" color="gray" size="sm">
                        {action.deadline}
                    </Badge>
                </Group>
                <Text size="md" fw={600}>{action.title}</Text>
                <Text size="sm" c="dimmed">{action.why}</Text>
            </Stack>
        </Card>
    );
}; const TableWidget: React.FC<{ table: DataTable }> = ({ table }) => {
    return (
        <Card shadow="sm" padding="md" radius="md" withBorder>
            <Stack gap="md">
                <Title order={5}>{table.title}</Title>
                <Table striped highlightOnHover>
                    <Table.Thead>
                        <Table.Tr>
                            {table.headers.map((header, idx) => (
                                <Table.Th key={idx}>{header}</Table.Th>
                            ))}
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {table.rows.map((row, idx) => (
                            <Table.Tr key={idx}>
                                {table.headers.map((header, cellIdx) => {
                                    const cellValue = row[header.toLowerCase().replace(' ', '_')] || row[header];
                                    const status = row.status;

                                    return (
                                        <Table.Td key={cellIdx}>
                                            {cellIdx === table.headers.length - 1 && status ? (
                                                <Badge
                                                    variant="light"
                                                    color={
                                                        status === 'critical' ? 'red' :
                                                            status === 'warning' ? 'yellow' :
                                                                'green'
                                                    }
                                                >
                                                    {status}
                                                </Badge>
                                            ) : (
                                                cellValue
                                            )}
                                        </Table.Td>
                                    );
                                })}
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>
            </Stack>
        </Card>
    );
};

export default CoachVisualization;
