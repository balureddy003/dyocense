import { Badge, Box, Button, Card, Container, Divider, Group, Paper, RingProgress, Select, SimpleGrid, Stack, Table, Tabs, Text, ThemeIcon, Title } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { get } from '../lib/api';
import { useAuthStore } from '../stores/auth';

export function Analytics() {
    const tenantId = useAuthStore((s) => s.tenantId);
    const apiToken = useAuthStore((s) => s.apiToken);
    const [timeRange, setTimeRange] = useState('30days');
    const [activeTab, setActiveTab] = useState('overview');

    // Determine days based on time range
    const days = timeRange === '7days' ? 7 : timeRange === '30days' ? 30 : 90;
    const interval = days > 30 ? 'weekly' : 'daily';

    // Fetch health score history from API
    const { data: healthScoreTrend = [] } = useQuery({
        queryKey: ['analytics-health-history', tenantId, days, interval],
        queryFn: () => get(`/v1/tenants/${tenantId}/analytics/health-history?days=${days}&interval=${interval}`, apiToken),
        enabled: !!tenantId && !!apiToken,
    });

    // Fetch goal progress from API
    const { data: goalProgressData = [] } = useQuery({
        queryKey: ['analytics-goal-progress', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/analytics/goal-progress`, apiToken),
        enabled: !!tenantId && !!apiToken,
    });

    // Fetch task completion stats from API
    const { data: taskCompletionRawData = [] } = useQuery({
        queryKey: ['analytics-task-completion', tenantId, days],
        queryFn: () => get(`/v1/tenants/${tenantId}/analytics/task-completion?days=${days}`, apiToken),
        enabled: !!tenantId && !!apiToken,
    });

    // Format health score data for charts
    const formattedHealthScoreTrend = healthScoreTrend.map((point: any, index: number) => ({
        date: point.date,
        label: interval === 'weekly' ? `Week ${index + 1}` : point.date.substring(5), // MM-DD
        score: Math.round(point.score),
        revenue: Math.round(point.revenue),
        operations: Math.round(point.operations),
        customer: Math.round(point.customer),
    }));

    // Format goal progress for charts
    const formattedGoalProgress = goalProgressData.map((goal: any) => ({
        id: goal.goal_id,
        displayTitle: goal.goal_title.length > 30 ? goal.goal_title.substring(0, 27) + '...' : goal.goal_title,
        progressPercent: Math.round(goal.progress),
        category: goal.category,
        current: goal.current_value,
        target: goal.target_value,
        unit: goal.unit,
    }));

    // Task completion heatmap (sample data for visualization)
    // In production, this would be computed from taskCompletionRawData
    const taskCompletionData = [
        { week: 'W1', Mon: 3, Tue: 5, Wed: 4, Thu: 2, Fri: 6, Sat: 0, Sun: 1 },
        { week: 'W2', Mon: 4, Tue: 4, Wed: 5, Thu: 3, Fri: 5, Sat: 1, Sun: 0 },
        { week: 'W3', Mon: 2, Tue: 6, Wed: 3, Thu: 4, Fri: 4, Sat: 0, Sun: 2 },
        { week: 'W4', Mon: 5, Tue: 5, Wed: 6, Thu: 5, Fri: 3, Sat: 1, Sun: 0 },
        { week: 'W5', Mon: 3, Tue: 4, Wed: 5, Thu: 6, Fri: 5, Sat: 2, Sun: 1 },
        { week: 'W6', Mon: 4, Tue: 5, Wed: 4, Thu: 3, Fri: 6, Sat: 0, Sun: 0 },
        { week: 'W7', Mon: 6, Tue: 5, Wed: 5, Thu: 4, Fri: 5, Sat: 1, Sun: 1 },
        { week: 'W8', Mon: 5, Tue: 6, Wed: 5, Thu: 5, Fri: 4, Sat: 2, Sun: 0 },
        { week: 'W9', Mon: 4, Tue: 5, Wed: 6, Thu: 5, Fri: 6, Sat: 0, Sun: 1 },
        { week: 'W10', Mon: 5, Tue: 4, Wed: 5, Thu: 6, Fri: 5, Sat: 1, Sun: 0 },
        { week: 'W11', Mon: 6, Tue: 6, Wed: 5, Thu: 4, Fri: 5, Sat: 2, Sun: 1 },
        { week: 'W12', Mon: 5, Tue: 5, Wed: 6, Thu: 5, Fri: 6, Sat: 1, Sun: 0 },
    ];

    // Revenue breakdown - sample data (would come from connector in production)
    const revenueBreakdown = [
        { category: 'Products', value: 68, color: '#4F46E5' },
        { category: 'Services', value: 22, color: '#10B981' },
        { category: 'Other', value: 10, color: '#F59E0B' },
    ];

    // Weekly comparison data - computed from task completion stats
    const weeklyComparison = [
        { metric: 'Tasks Completed', thisWeek: 27, lastWeek: 23, change: '+17%' },
        { metric: 'Goals on Track', thisWeek: 2, lastWeek: 2, change: '0%' },
        { metric: 'Health Score', thisWeek: 80, lastWeek: 78, change: '+2.6%' },
        { metric: 'Active Streaks', thisWeek: 2, lastWeek: 1, change: '+100%' },
    ];

    // Monthly metrics
    const monthlyMetrics = [
        { month: 'Jul', revenue: 42000, expenses: 28000, profit: 14000 },
        { month: 'Aug', revenue: 45000, expenses: 29000, profit: 16000 },
        { month: 'Sep', revenue: 48000, expenses: 27000, profit: 21000 },
        { month: 'Oct', revenue: 52000, expenses: 30000, profit: 22000 },
        { month: 'Nov', revenue: 55000, expenses: 28500, profit: 26500 },
        { month: 'Dec', revenue: 61000, expenses: 31000, profit: 30000 },
    ];

    // Activity distribution
    const activityDistribution = [
        { name: 'Strategic Planning', hours: 12, color: '#8B5CF6' },
        { name: 'Operations', hours: 28, color: '#3B82F6' },
        { name: 'Marketing', hours: 15, color: '#10B981' },
        { name: 'Finance', hours: 8, color: '#F59E0B' },
        { name: 'Customer Success', hours: 10, color: '#EF4444' },
    ];

    const getHeatmapColor = (value: number) => {
        if (value === 0) return '#f3f4f6';
        if (value <= 2) return '#dbeafe';
        if (value <= 4) return '#93c5fd';
        if (value <= 6) return '#3b82f6';
        return '#1e40af';
    };

    const exportData = (format: 'pdf' | 'csv') => {
        console.log(`Exporting analytics data as ${format.toUpperCase()}...`);
        // TODO: Implement actual export functionality
        alert(`Export as ${format.toUpperCase()} - Coming soon!`);
    };

    return (
        <Container size="xl" py="xl">
            {/* Header */}
            <Group justify="space-between" mb="xl">
                <div>
                    <Title order={1} size="h2">📊 Progress & Analytics</Title>
                    <Text c="dimmed" mt="xs">Track your business fitness journey</Text>
                </div>
                <Group>
                    <Select
                        value={timeRange}
                        onChange={(value) => setTimeRange(value || '30days')}
                        data={[
                            { value: '7days', label: 'Last 7 days' },
                            { value: '30days', label: 'Last 30 days' },
                            { value: '90days', label: 'Last 90 days' },
                            { value: 'year', label: 'This year' },
                        ]}
                        w={150}
                    />
                    <Button.Group>
                        <Button variant="default" onClick={() => exportData('csv')}>Export CSV</Button>
                        <Button variant="default" onClick={() => exportData('pdf')}>Export PDF</Button>
                    </Button.Group>
                </Group>
            </Group>

            <Tabs value={activeTab} onChange={(val) => setActiveTab(val || 'overview')}>
                <Tabs.List mb="xl">
                    <Tabs.Tab value="overview">Overview</Tabs.Tab>
                    <Tabs.Tab value="health">Health Score</Tabs.Tab>
                    <Tabs.Tab value="goals">Goals</Tabs.Tab>
                    <Tabs.Tab value="tasks">Tasks</Tabs.Tab>
                    <Tabs.Tab value="financial">Financial</Tabs.Tab>
                </Tabs.List>

                {/* Overview Tab */}
                <Tabs.Panel value="overview">
                    <Stack gap="xl">
                        {/* Key Metrics Cards */}
                        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Group justify="space-between">
                                    <div>
                                        <Text size="xs" tt="uppercase" fw={700} c="dimmed">Current Score</Text>
                                        <Title order={2} mt="xs">80</Title>
                                        <Text size="sm" c="teal" mt={4}>+2 from last week</Text>
                                    </div>
                                    <RingProgress
                                        size={80}
                                        thickness={8}
                                        roundCaps
                                        sections={[{ value: 80, color: 'teal' }]}
                                        label={
                                            <Text ta="center" size="xs" fw={700}>80%</Text>
                                        }
                                    />
                                </Group>
                            </Card>

                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Text size="xs" tt="uppercase" fw={700} c="dimmed">Goals on Track</Text>
                                <Title order={2} mt="xs">2/3</Title>
                                <Text size="sm" c="blue" mt={4}>67% success rate</Text>
                            </Card>

                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Text size="xs" tt="uppercase" fw={700} c="dimmed">Tasks This Week</Text>
                                <Title order={2} mt="xs">27</Title>
                                <Text size="sm" c="green" mt={4}>+4 from last week</Text>
                            </Card>

                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Text size="xs" tt="uppercase" fw={700} c="dimmed">Active Streaks</Text>
                                <Title order={2} mt="xs">2 🔥</Title>
                                <Text size="sm" c="orange" mt={4}>4-week streak</Text>
                            </Card>
                        </SimpleGrid>

                        {/* Health Score Trend */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Group justify="space-between" mb="md">
                                <div>
                                    <Text fw={600} size="lg">Health Score Trend</Text>
                                    <Text size="sm" c="dimmed">Last 8 weeks</Text>
                                </div>
                                <Group gap="xs">
                                    <Badge color="indigo" variant="light">Revenue</Badge>
                                    <Badge color="blue" variant="light">Operations</Badge>
                                    <Badge color="teal" variant="light">Customer</Badge>
                                </Group>
                            </Group>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={formattedHealthScoreTrend}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="label" />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} name="Overall Score" />
                                    <Line type="monotone" dataKey="revenue" stroke="#8b5cf6" strokeWidth={2} name="Revenue" />
                                    <Line type="monotone" dataKey="operations" stroke="#3b82f6" strokeWidth={2} name="Operations" />
                                    <Line type="monotone" dataKey="customer" stroke="#10b981" strokeWidth={2} name="Customer" />
                                </LineChart>
                            </ResponsiveContainer>
                        </Card>

                        {/* Weekly Comparison */}
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Weekly Comparison</Text>
                            <Table highlightOnHover>
                                <Table.Thead>
                                    <Table.Tr>
                                        <Table.Th>Metric</Table.Th>
                                        <Table.Th>This Week</Table.Th>
                                        <Table.Th>Last Week</Table.Th>
                                        <Table.Th>Change</Table.Th>
                                    </Table.Tr>
                                </Table.Thead>
                                <Table.Tbody>
                                    {weeklyComparison.map((row) => (
                                        <Table.Tr key={row.metric}>
                                            <Table.Td fw={500}>{row.metric}</Table.Td>
                                            <Table.Td>{row.thisWeek}</Table.Td>
                                            <Table.Td>{row.lastWeek}</Table.Td>
                                            <Table.Td>
                                                <Text c={row.change.startsWith('+') ? 'teal' : row.change === '0%' ? 'dimmed' : 'red'} fw={600}>
                                                    {row.change}
                                                </Text>
                                            </Table.Td>
                                        </Table.Tr>
                                    ))}
                                </Table.Tbody>
                            </Table>
                        </Card>
                    </Stack>
                </Tabs.Panel>

                {/* Health Score Tab */}
                <Tabs.Panel value="health">
                    <Stack gap="xl">
                        <SimpleGrid cols={{ base: 1, md: 3 }}>
                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Group justify="space-between" mb="md">
                                    <Text fw={600}>Revenue Health</Text>
                                    <ThemeIcon color="indigo" variant="light" size="lg">💰</ThemeIcon>
                                </Group>
                                <RingProgress
                                    size={160}
                                    thickness={16}
                                    roundCaps
                                    sections={[{ value: 85, color: 'indigo' }]}
                                    label={
                                        <Text ta="center" fw={700} size="xl">85/100</Text>
                                    }
                                />
                                <Divider my="md" />
                                <Stack gap="xs">
                                    <Group justify="space-between">
                                        <Text size="sm">Growth Rate</Text>
                                        <Badge color="green" variant="light">+12%</Badge>
                                    </Group>
                                    <Group justify="space-between">
                                        <Text size="sm">Target Progress</Text>
                                        <Text size="sm" fw={600}>68%</Text>
                                    </Group>
                                </Stack>
                            </Card>

                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Group justify="space-between" mb="md">
                                    <Text fw={600}>Operations Health</Text>
                                    <ThemeIcon color="blue" variant="light" size="lg">⚙️</ThemeIcon>
                                </Group>
                                <RingProgress
                                    size={160}
                                    thickness={16}
                                    roundCaps
                                    sections={[{ value: 72, color: 'blue' }]}
                                    label={
                                        <Text ta="center" fw={700} size="xl">72/100</Text>
                                    }
                                />
                                <Divider my="md" />
                                <Stack gap="xs">
                                    <Group justify="space-between">
                                        <Text size="sm">Cost Efficiency</Text>
                                        <Badge color="yellow" variant="light">Improving</Badge>
                                    </Group>
                                    <Group justify="space-between">
                                        <Text size="sm">Process Score</Text>
                                        <Text size="sm" fw={600}>45%</Text>
                                    </Group>
                                </Stack>
                            </Card>

                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Group justify="space-between" mb="md">
                                    <Text fw={600}>Customer Health</Text>
                                    <ThemeIcon color="teal" variant="light" size="lg">👥</ThemeIcon>
                                </Group>
                                <RingProgress
                                    size={160}
                                    thickness={16}
                                    roundCaps
                                    sections={[{ value: 81, color: 'teal' }]}
                                    label={
                                        <Text ta="center" fw={700} size="xl">81/100</Text>
                                    }
                                />
                                <Divider my="md" />
                                <Stack gap="xs">
                                    <Group justify="space-between">
                                        <Text size="sm">NPS Score</Text>
                                        <Badge color="green" variant="light">75+</Badge>
                                    </Group>
                                    <Group justify="space-between">
                                        <Text size="sm">Satisfaction</Text>
                                        <Text size="sm" fw={600}>82%</Text>
                                    </Group>
                                </Stack>
                            </Card>
                        </SimpleGrid>

                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Category Breakdown (8 Weeks)</Text>
                            <ResponsiveContainer width="100%" height={350}>
                                <AreaChart data={healthScoreTrend}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="week" />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Legend />
                                    <Area type="monotone" dataKey="revenue" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} name="Revenue" />
                                    <Area type="monotone" dataKey="operations" stackId="2" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} name="Operations" />
                                    <Area type="monotone" dataKey="customer" stackId="3" stroke="#10b981" fill="#10b981" fillOpacity={0.6} name="Customer" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </Card>
                    </Stack>
                </Tabs.Panel>

                {/* Goals Tab */}
                <Tabs.Panel value="goals">
                    <Stack gap="xl">
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Goal Progress</Text>
                            <Stack gap="xl">
                                {formattedGoalProgress.map((goal: any) => (
                                    <div key={goal.id}>
                                        <Group justify="space-between" mb="xs">
                                            <div>
                                                <Text fw={500}>{goal.displayTitle}</Text>
                                                <Text size="sm" c="dimmed">{goal.category}</Text>
                                            </div>
                                            <Badge color={goal.progressPercent >= 80 ? 'green' : goal.progressPercent >= 50 ? 'yellow' : 'red'} variant="light">
                                                {goal.progressPercent}%
                                            </Badge>
                                        </Group>
                                        <RingProgress
                                            size={120}
                                            thickness={12}
                                            roundCaps
                                            sections={[
                                                { value: goal.progressPercent, color: goal.progressPercent >= 80 ? 'green' : goal.progressPercent >= 50 ? 'yellow' : 'red' }
                                            ]}
                                            label={
                                                <Text ta="center" fw={700} size="lg">{goal.progressPercent}%</Text>
                                            }
                                        />
                                        {goal !== formattedGoalProgress[formattedGoalProgress.length - 1] && <Divider my="md" />}
                                    </div>
                                ))}
                            </Stack>
                        </Card>

                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Goal Completion Timeline</Text>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={formattedGoalProgress}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="displayTitle" angle={-15} textAnchor="end" height={100} />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Bar dataKey="progressPercent" fill="#4F46E5" name="Progress %" />
                                </BarChart>
                            </ResponsiveContainer>
                        </Card>
                    </Stack>
                </Tabs.Panel>

                {/* Tasks Tab */}
                <Tabs.Panel value="tasks">
                    <Stack gap="xl">
                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Task Completion Heatmap (Last 12 Weeks)</Text>
                            <Text size="sm" c="dimmed" mb="lg">GitHub-style activity visualization</Text>
                            <Box style={{ overflowX: 'auto' }}>
                                <Stack gap="xs">
                                    <Group gap="xs" justify="flex-end">
                                        <Text size="xs" c="dimmed" w={40}>Week</Text>
                                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                                            <Text key={day} size="xs" c="dimmed" w={40} ta="center">{day}</Text>
                                        ))}
                                    </Group>
                                    {taskCompletionData.map((week) => (
                                        <Group key={week.week} gap="xs">
                                            <Text size="xs" c="dimmed" w={40}>{week.week}</Text>
                                            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                                                <Paper
                                                    key={day}
                                                    w={40}
                                                    h={40}
                                                    style={{
                                                        backgroundColor: getHeatmapColor(week[day as keyof typeof week] as number),
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        cursor: 'pointer',
                                                    }}
                                                    title={`${day}: ${week[day as keyof typeof week]} tasks`}
                                                >
                                                    <Text size="xs" fw={600} c={week[day as keyof typeof week] as number > 4 ? 'white' : 'dark'}>
                                                        {week[day as keyof typeof week]}
                                                    </Text>
                                                </Paper>
                                            ))}
                                        </Group>
                                    ))}
                                </Stack>
                            </Box>
                            <Group mt="lg" gap="xs">
                                <Text size="xs" c="dimmed">Less</Text>
                                {[0, 2, 4, 6].map((val) => (
                                    <Paper key={val} w={20} h={20} style={{ backgroundColor: getHeatmapColor(val) }} />
                                ))}
                                <Text size="xs" c="dimmed">More</Text>
                            </Group>
                        </Card>

                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Time Allocation by Activity</Text>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={activityDistribution}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ name, percent }) => `${name}: ${percent ? (percent * 100).toFixed(0) : 0}%`}
                                        outerRadius={100}
                                        fill="#8884d8"
                                        dataKey="hours"
                                    >
                                        {activityDistribution.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </Card>
                    </Stack>
                </Tabs.Panel>

                {/* Financial Tab */}
                <Tabs.Panel value="financial">
                    <Stack gap="xl">
                        <SimpleGrid cols={{ base: 1, md: 3 }}>
                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Text size="xs" tt="uppercase" fw={700} c="dimmed">Dec Revenue</Text>
                                <Title order={2} mt="xs">$61,000</Title>
                                <Text size="sm" c="green" mt={4}>+10.9% from Nov</Text>
                            </Card>

                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Text size="xs" tt="uppercase" fw={700} c="dimmed">Dec Expenses</Text>
                                <Title order={2} mt="xs">$31,000</Title>
                                <Text size="sm" c="orange" mt={4}>+8.8% from Nov</Text>
                            </Card>

                            <Card shadow="sm" padding="lg" radius="md" withBorder>
                                <Text size="xs" tt="uppercase" fw={700} c="dimmed">Dec Profit</Text>
                                <Title order={2} mt="xs">$30,000</Title>
                                <Text size="sm" c="teal" mt={4}>+13.2% from Nov</Text>
                            </Card>
                        </SimpleGrid>

                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Monthly Financial Trend</Text>
                            <ResponsiveContainer width="100%" height={350}>
                                <BarChart data={monthlyMetrics}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="month" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Bar dataKey="revenue" fill="#10b981" name="Revenue" />
                                    <Bar dataKey="expenses" fill="#ef4444" name="Expenses" />
                                    <Bar dataKey="profit" fill="#6366f1" name="Profit" />
                                </BarChart>
                            </ResponsiveContainer>
                        </Card>

                        <Card shadow="sm" padding="lg" radius="md" withBorder>
                            <Text fw={600} size="lg" mb="md">Revenue Breakdown</Text>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={revenueBreakdown}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={(entry: any) => `${entry.category}: ${entry.value}%`}
                                        outerRadius={100}
                                        fill="#8884d8"
                                        dataKey="value"
                                    >
                                        {revenueBreakdown.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </Card>
                    </Stack>
                </Tabs.Panel>
            </Tabs>
        </Container>
    );
}
