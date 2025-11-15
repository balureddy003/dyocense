/**
 * ShowDetailsModal - Drill-down modal with data visualization
 * 
 * Shows:
 * - Recommendation reasoning with data
 * - Historical trends (charts)
 * - Key metrics and thresholds
 * - Related data points
 */

import {
    Badge,
    Card,
    Divider,
    Grid,
    Group,
    Modal,
    Progress,
    Stack,
    Table,
    Text,
} from '@mantine/core';
import {
    IconAlertTriangle,
    IconInfoCircle,
    IconTrendingDown,
    IconTrendingUp
} from '@tabler/icons-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { CoachRecommendation } from '../coach-v6/types';

interface ShowDetailsModalProps {
    opened: boolean;
    onClose: () => void;
    recommendation: CoachRecommendation | null;
}

/**
 * Mock data generator for demonstration
 * In production, this would fetch real data from the API
 */
function generateMockData(recommendationId: string) {
    // Historical trend data
    const trendData = [
        { date: '10/1', value: 45000, target: 50000 },
        { date: '10/8', value: 42000, target: 50000 },
        { date: '10/15', value: 38000, target: 50000 },
        { date: '10/22', value: 35000, target: 50000 },
        { date: '10/29', value: 32000, target: 50000 },
        { date: '11/5', value: 29000, target: 50000 },
        { date: '11/12', value: 28000, target: 50000 },
    ];

    // Breakdown data
    const breakdownData = [
        { category: 'Payables', amount: 12000, dueIn: 7 },
        { category: 'Receivables', amount: -8000, dueIn: 14 },
        { category: 'Operating Costs', amount: 5500, dueIn: 3 },
        { category: 'Inventory Purchase', amount: 3200, dueIn: 10 },
    ];

    // Key metrics
    const metrics = {
        cashBalance: 28000,
        burnRate: 8500,
        daysUntilCritical: 14,
        averageCollectionDays: 42,
        overdueInvoices: 3,
        overdueAmount: 12450,
    };

    return { trendData, breakdownData, metrics };
}

export function ShowDetailsModal({
    opened,
    onClose,
    recommendation,
}: ShowDetailsModalProps) {
    if (!recommendation) return null;

    // Generate mock data for visualization
    const { trendData, breakdownData, metrics } = generateMockData(recommendation.id);

    return (
        <Modal
            opened={opened}
            onClose={onClose}
            title="Recommendation Details"
            size="xl"
            padding="xl"
        >
            <Stack gap="lg">
                {/* Header with recommendation summary */}
                <Card withBorder padding="md" style={{ backgroundColor: 'var(--mantine-color-blue-0)' }}>
                    <Group justify="space-between" mb="xs">
                        <Text size="lg" fw={600}>{recommendation.title}</Text>
                        <Badge size="lg" color={
                            recommendation.priority === 'critical' ? 'red' :
                                recommendation.priority === 'important' ? 'orange' : 'blue'
                        }>
                            {recommendation.priority}
                        </Badge>
                    </Group>
                    <Text size="sm" c="dimmed">{recommendation.description}</Text>
                    {recommendation.reasoning && (
                        <>
                            <Divider my="sm" />
                            <Group gap="xs">
                                <IconInfoCircle size={16} />
                                <Text size="sm" fw={500}>Why this matters:</Text>
                            </Group>
                            <Text size="sm" mt="xs">{recommendation.reasoning}</Text>
                        </>
                    )}
                </Card>

                {/* Key Metrics Grid */}
                <div>
                    <Text size="md" fw={600} mb="md">Key Metrics</Text>
                    <Grid>
                        <Grid.Col span={6}>
                            <Card withBorder padding="md">
                                <Text size="xs" c="dimmed" mb={4}>Cash Balance</Text>
                                <Text size="xl" fw={700}>${metrics.cashBalance.toLocaleString()}</Text>
                                <Group gap={4} mt={4}>
                                    <IconTrendingDown size={16} color="red" />
                                    <Text size="xs" c="red">-15% vs. last month</Text>
                                </Group>
                            </Card>
                        </Grid.Col>
                        <Grid.Col span={6}>
                            <Card withBorder padding="md">
                                <Text size="xs" c="dimmed" mb={4}>Monthly Burn Rate</Text>
                                <Text size="xl" fw={700}>${metrics.burnRate.toLocaleString()}/mo</Text>
                                <Group gap={4} mt={4}>
                                    <IconAlertTriangle size={16} color="orange" />
                                    <Text size="xs" c="orange">Above average</Text>
                                </Group>
                            </Card>
                        </Grid.Col>
                        <Grid.Col span={6}>
                            <Card withBorder padding="md">
                                <Text size="xs" c="dimmed" mb={4}>Days Until Critical</Text>
                                <Text size="xl" fw={700}>{metrics.daysUntilCritical} days</Text>
                                <Progress value={(metrics.daysUntilCritical / 30) * 100} color="red" mt={4} />
                            </Card>
                        </Grid.Col>
                        <Grid.Col span={6}>
                            <Card withBorder padding="md">
                                <Text size="xs" c="dimmed" mb={4}>Overdue Invoices</Text>
                                <Text size="xl" fw={700}>{metrics.overdueInvoices}</Text>
                                <Text size="xs" c="dimmed" mt={4}>
                                    ${metrics.overdueAmount.toLocaleString()} total
                                </Text>
                            </Card>
                        </Grid.Col>
                    </Grid>
                </div>

                {/* Historical Trend Chart */}
                <div>
                    <Text size="md" fw={600} mb="md">Cash Flow Trend (Last 7 Weeks)</Text>
                    <Card withBorder padding="md">
                        <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={trendData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="date" />
                                <YAxis />
                                <Tooltip />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    stroke="#228be6"
                                    strokeWidth={2}
                                    name="Actual"
                                />
                                <Line
                                    type="monotone"
                                    dataKey="target"
                                    stroke="#82ca9d"
                                    strokeWidth={2}
                                    strokeDasharray="5 5"
                                    name="Target"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                        <Text size="xs" c="dimmed" ta="center" mt="xs">
                            Cash balance has declined 38% over the past 7 weeks
                        </Text>
                    </Card>
                </div>

                {/* Breakdown Table */}
                <div>
                    <Text size="md" fw={600} mb="md">Cash Flow Breakdown (Next 14 Days)</Text>
                    <Card withBorder padding={0}>
                        <Table>
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>Category</Table.Th>
                                    <Table.Th>Amount</Table.Th>
                                    <Table.Th>Due In</Table.Th>
                                    <Table.Th>Impact</Table.Th>
                                </Table.Tr>
                            </Table.Thead>
                            <Table.Tbody>
                                {breakdownData.map((item, index) => (
                                    <Table.Tr key={index}>
                                        <Table.Td>{item.category}</Table.Td>
                                        <Table.Td>
                                            <Text
                                                fw={600}
                                                c={item.amount > 0 ? 'red' : 'green'}
                                            >
                                                {item.amount > 0 ? '-' : '+'}$
                                                {Math.abs(item.amount).toLocaleString()}
                                            </Text>
                                        </Table.Td>
                                        <Table.Td>
                                            <Badge
                                                color={item.dueIn <= 7 ? 'red' : item.dueIn <= 14 ? 'orange' : 'gray'}
                                                variant="light"
                                            >
                                                {item.dueIn} days
                                            </Badge>
                                        </Table.Td>
                                        <Table.Td>
                                            {item.amount > 0 ? (
                                                <Group gap={4}>
                                                    <IconTrendingDown size={16} color="red" />
                                                    <Text size="xs">Outflow</Text>
                                                </Group>
                                            ) : (
                                                <Group gap={4}>
                                                    <IconTrendingUp size={16} color="green" />
                                                    <Text size="xs">Inflow</Text>
                                                </Group>
                                            )}
                                        </Table.Td>
                                    </Table.Tr>
                                ))}
                            </Table.Tbody>
                        </Table>
                    </Card>
                </div>

                {/* Actions Summary */}
                <Card withBorder padding="md" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                    <Text size="sm" fw={600} mb="xs">Recommended Actions</Text>
                    <Stack gap="xs">
                        {recommendation.actions.map((action, index) => (
                            <Group key={index} gap="xs">
                                <Badge size="sm" color="blue">{index + 1}</Badge>
                                <Text size="sm">{action.label}</Text>
                            </Group>
                        ))}
                    </Stack>
                </Card>
            </Stack>
        </Modal>
    );
}
