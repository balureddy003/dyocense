/**
 * Coach Visualization V2 - SMB-Optimized Design
 * 
 * Improvements:
 * - 8px spacing grid for consistency
 * - Clear visual hierarchy 
 * - Plain language (no jargon)
 * - Mobile-friendly
 * - Critical actions stand out
 */
import {
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
} from '@mantine/core';
import {
    IconMinus,
    IconTrendingDown,
    IconTrendingUp,
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
    trend?: 'up' | 'down' | 'neutral';
    change?: string;
    icon?: string;
}

interface Chart {
    type: 'radialBar' | 'line' | 'bar';
    title: string;
    data: any;
    color?: string;
}

interface DataTable {
    title: string;
    headers: string[];
    rows: Array<(string | number)[]>;
    highlight_rows?: number[];
}

interface ActionCard {
    priority: 'critical' | 'high' | 'medium' | 'low';
    icon: string;
    title: string;
    deadline: string;
    why: string;
    clients?: Array<{ name: string; amount: number; days_overdue: number }>;
    products?: Array<{ name: string; current: number; min: number }>;
}

interface Insight {
    type: 'alert' | 'info' | 'success';
    icon: string;
    title: string;
    message: string;
    metric?: string;
}

interface CoachVisualizationProps {
    data: VisualResponse;
}

// ============================================================================
// KPI Widget - Simplified
// ============================================================================

const KPIWidget: React.FC<{ kpi: KPI }> = ({ kpi }) => {
    const getTrendIcon = () => {
        if (kpi.trend === 'up') return <IconTrendingUp size={18} color="#37b24d" />;
        if (kpi.trend === 'down') return <IconTrendingDown size={18} color="#f03e3e" />;
        return <IconMinus size={18} color="#868e96" />;
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
                        {kpi.value}
                    </Text>
                    {kpi.change && (
                        <Group gap={4}>
                            {getTrendIcon()}
                            <Text size="sm" fw={600} c={kpi.trend === 'up' ? 'green' : kpi.trend === 'down' ? 'red' : 'gray'}>
                                {kpi.change}
                            </Text>
                        </Group>
                    )}
                </Group>
            </Stack>
        </Card>
    );
};

// ============================================================================
// Chart Widget - Simplified
// ============================================================================

const ChartWidget: React.FC<{ chart: Chart }> = ({ chart }) => {
    const renderChart = () => {
        if (chart.type === 'radialBar') {
            const value = chart.data?.value || 0;
            return (
                <Box style={{ display: 'flex', justifyContent: 'center' }}>
                    <RingProgress
                        size={120}
                        thickness={12}
                        sections={[{ value, color: chart.color || 'blue' }]}
                        label={
                            <Text size="lg" fw={700} ta="center">
                                {value}%
                            </Text>
                        }
                    />
                </Box>
            );
        }

        if (chart.type === 'bar') {
            return (
                <Stack gap={SPACING.xs}>
                    {chart.data?.categories?.map((category: string, idx: number) => (
                        <Box key={idx}>
                            <Group justify="apart" mb={4}>
                                <Text size="xs" fw={500}>{category}</Text>
                                <Text size="xs" c="dimmed">{chart.data.values[idx]}</Text>
                            </Group>
                            <Progress value={(chart.data.values[idx] / Math.max(...chart.data.values)) * 100} color={chart.color || 'blue'} />
                        </Box>
                    ))}
                </Stack>
            );
        }

        return <Text size="sm" c="dimmed">Chart type not supported</Text>;
    };

    return (
        <Card shadow="sm" padding={SPACING.md} radius="lg" withBorder>
            <Stack gap={SPACING.md}>
                <Text size="sm" fw={700}>{chart.title}</Text>
                {renderChart()}
            </Stack>
        </Card>
    );
};

// ============================================================================
// Table Widget - Cleaned Up
// ============================================================================

const TableWidget: React.FC<{ table: DataTable }> = ({ table }) => {
    return (
        <Card shadow="sm" padding={SPACING.md} radius="lg" withBorder>
            <Stack gap={SPACING.sm}>
                <Text size="sm" fw={700}>{table.title}</Text>
                <Table striped highlightOnHover>
                    <Table.Thead>
                        <Table.Tr>
                            {table.headers.map((header, idx) => (
                                <Table.Th key={idx}>
                                    <Text size="xs" fw={600}>{header}</Text>
                                </Table.Th>
                            ))}
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {table.rows.map((row, rowIdx) => (
                            <Table.Tr
                                key={rowIdx}
                                bg={table.highlight_rows?.includes(rowIdx) ? 'red.0' : undefined}
                            >
                                {row.map((cell, cellIdx) => (
                                    <Table.Td key={cellIdx}>
                                        <Text size="xs">{cell}</Text>
                                    </Table.Td>
                                ))}
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>
            </Stack>
        </Card>
    );
};

// ============================================================================
// Action Card - Using Simplified Component
// ============================================================================

const ActionCardWidget: React.FC<{ action: ActionCard }> = ({ action }) => {
    // Use new simplified component for critical/high priority
    if (action.priority === 'critical' || action.priority === 'high') {
        return (
            <CriticalActionCard
                icon={action.icon || '⚠️'}
                title={action.title}
                deadline={action.deadline}
                why={action.why}
                clients={action.clients}
                products={action.products}
            />
        );
    }

    // Simple card for lower priority
    const getColor = () => {
        if (action.priority === 'medium') return 'orange';
        return 'blue';
    };

    return (
        <Card shadow="sm" padding={SPACING.md} radius="lg" withBorder>
            <Stack gap={SPACING.sm}>
                <Group gap={SPACING.xs}>
                    {action.icon && <Text size="lg">{action.icon}</Text>}
                    <Badge variant="light" color={getColor()} size="sm">
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
};

// ============================================================================
// Insight Card - Simplified
// ============================================================================

const InsightCard: React.FC<{ insight: Insight }> = ({ insight }) => {
    const getColor = () => {
        if (insight.type === 'alert') return 'red';
        if (insight.type === 'success') return 'green';
        return 'blue';
    };

    return (
        <Paper p={SPACING.md} radius="lg" bg={`${getColor()}.0`} withBorder style={{ borderColor: `var(--mantine-color-${getColor()}-3)` }}>
            <Group gap={SPACING.sm} align="flex-start">
                <Text size="xl">{insight.icon}</Text>
                <Stack gap={4} style={{ flex: 1 }}>
                    <Text size="sm" fw={700} c={`${getColor()}.9`}>
                        {insight.title}
                    </Text>
                    <Text size="sm" c={`${getColor()}.8`}>
                        {insight.message}
                    </Text>
                    {insight.metric && (
                        <Badge color={getColor()} size="sm" mt={4}>
                            {insight.metric}
                        </Badge>
                    )}
                </Stack>
            </Group>
        </Paper>
    );
};

// ============================================================================
// Main Visualization Component
// ============================================================================

export const CoachVisualizationV2: React.FC<CoachVisualizationProps> = ({ data }) => {
    if (!data) return null;

    return (
        <Stack gap={SPACING.lg}>
            {/* Health Score - If Available */}
            {data.metadata?.health_score !== undefined && (
                <SimplifiedHealthScore score={data.metadata.health_score} />
            )}

            {/* Summary */}
            {data.summary && (
                <Paper p={SPACING.md} radius="lg" bg="blue.0">
                    <Text size="sm" fw={600} c="blue.9">
                        {data.summary}
                    </Text>
                </Paper>
            )}

            {/* KPIs */}
            {data.kpis && data.kpis.length > 0 && (
                <Grid gutter={SPACING.md}>
                    {data.kpis.map((kpi, idx) => (
                        <Grid.Col key={idx} span={{ base: 12, xs: 6, md: 3 }}>
                            <KPIWidget kpi={kpi} />
                        </Grid.Col>
                    ))}
                </Grid>
            )}

            {/* Critical Actions */}
            {data.actions && data.actions.length > 0 && (
                <Stack gap={SPACING.md}>
                    <Text size="md" fw={700}>What needs your attention:</Text>
                    {data.actions.map((action, idx) => (
                        <ActionCardWidget key={idx} action={action} />
                    ))}
                </Stack>
            )}

            {/* Insights */}
            {data.insights && data.insights.length > 0 && (
                <Stack gap={SPACING.sm}>
                    <Text size="md" fw={700}>Key insights:</Text>
                    {data.insights.map((insight, idx) => (
                        <InsightCard key={idx} insight={insight} />
                    ))}
                </Stack>
            )}

            {/* Charts */}
            {data.charts && data.charts.length > 0 && (
                <Grid gutter={SPACING.md}>
                    {data.charts.map((chart, idx) => (
                        <Grid.Col key={idx} span={{ base: 12, md: 6 }}>
                            <ChartWidget chart={chart} />
                        </Grid.Col>
                    ))}
                </Grid>
            )}

            {/* Tables */}
            {data.tables && data.tables.length > 0 && (
                <Stack gap={SPACING.md}>
                    <Text size="md" fw={700}>Evidence:</Text>
                    {data.tables.map((table, idx) => (
                        <TableWidget key={idx} table={table} />
                    ))}
                </Stack>
            )}
        </Stack>
    );
};

export default CoachVisualizationV2;
