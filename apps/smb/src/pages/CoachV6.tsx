import { Center, Container, Loader, Text as MantineText, Stack } from '@mantine/core';
import { useEffect, useState } from 'react';
import type {
    Alert,
    CoachRecommendation,
    GoalWithProgress,
    MetricSnapshot,
    RecommendationAction,
    Signal,
    TaskWithPriority,
} from '../components/coach-v6';
import {
    GoalsColumn,
    HealthScoreHeader,
    MetricsGrid,
    ProactiveCoachCard,
    TasksColumn,
} from '../components/coach-v6';
import * as api from '../lib/api';
import { useWebSocket } from '../hooks/useWebSocket';

/**
 * Coach V6 - Fitness Dashboard Paradigm
 * 
 * "Business Health Coach" - Inspired by Whoop/Peloton fitness tracking
 * Mental model: "I'm checking my business health" not "I'm chatting with AI"
 * 
 * Design Principles:
 * - Dashboard-first (not chat-first)
 * - Persistent metrics (not hidden)
 * - Proactive coach (not reactive)
 * - Fitness metaphor (health score, progress tracking, coaching)
 */
export default function CoachV6() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [healthScore, setHealthScore] = useState(0);
    const [previousScore, setPreviousScore] = useState(0);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [signals, setSignals] = useState<Signal[]>([]);
    const [recommendations, setRecommendations] = useState<CoachRecommendation[]>([]);
    const [metrics, setMetrics] = useState<MetricSnapshot[]>([]);
    const [goals, setGoals] = useState<GoalWithProgress[]>([]);
    const [tasks, setTasks] = useState<TaskWithPriority[]>([]);

    // Get tenant and token from localStorage
    const tenantId = localStorage.getItem('tenantId') || 'tenant-demo';
    const token = localStorage.getItem('token') || undefined;

    // Initialize WebSocket connection for real-time updates
    const { isConnected: wsConnected, error: wsError } = useWebSocket(
        {
            tenantId,
            token: token || '',
            enabled: !!token, // Only connect if token exists
        },
        {
            onHealthScoreUpdate: (data) => {
                console.log('[Coach V6] Health score update:', data);
                setHealthScore(data.score);
                setPreviousScore(data.previousScore);
                setAlerts(data.alerts as any);
                setSignals(data.signals as any);
            },
            onNewRecommendation: (data) => {
                console.log('[Coach V6] New recommendation:', data);
                // Add new recommendation to top of list
                setRecommendations((prev) => [
                    {
                        ...data,
                        createdAt: new Date(data.createdAt),
                        generatedAt: new Date(data.createdAt),
                        reasoning: '',
                        dismissed: false,
                        actions: data.actions.map((action, idx) => ({
                            id: `${data.id}-action-${idx}`,
                            ...action,
                            description: '',
                            buttonText: action.label,
                            onClick: async () => console.log('Action:', action.label),
                        })),
                    },
                    ...prev,
                ]);
            },
            onTaskCompleted: (data) => {
                console.log('[Coach V6] Task completed:', data);
                // Update task status in state
                setTasks((prev) =>
                    prev.map((task) =>
                        task.id === data.taskId
                            ? { ...task, completed: true, status: 'completed' }
                            : task
                    )
                );
            },
            onGoalProgressUpdate: (data) => {
                console.log('[Coach V6] Goal progress update:', data);
                // Update goal progress in state
                setGoals((prev) =>
                    prev.map((goal) =>
                        goal.id === data.goalId
                            ? { ...goal, progress: data.progress, status: data.status }
                            : goal
                    )
                );
            },
            onConnect: () => {
                console.log('[Coach V6] WebSocket connected');
            },
            onDisconnect: () => {
                console.log('[Coach V6] WebSocket disconnected');
            },
            onError: (event) => {
                console.error('[Coach V6] WebSocket error:', event);
            },
        }
    );

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                // Fetch all data in parallel
                const [
                    healthScoreData,
                    recommendationsData,
                    alertsData,
                    signalsData,
                    metricsData,
                    goalsData,
                    tasksData,
                ] = await Promise.all([
                    api.getHealthScore(tenantId, token),
                    api.getCoachRecommendations(tenantId, token),
                    api.getHealthAlerts(tenantId, token),
                    api.getHealthSignals(tenantId, token),
                    api.getMetricsSnapshot(tenantId, token),
                    api.getGoals(tenantId, token),
                    api.getTasks(tenantId, token),
                ]);

                // Set health score
                setHealthScore(healthScoreData.score);
                setPreviousScore(healthScoreData.score - Math.round(healthScoreData.trend));

                // Set API data
                setAlerts(alertsData);
                setSignals(signalsData);
                setRecommendations(recommendationsData.map((rec: any) => ({
                    ...rec,
                    createdAt: new Date(rec.createdAt),
                    generatedAt: new Date(rec.generatedAt),
                    actions: rec.actions.map((action: any) => ({
                        ...action,
                        onClick: async () => console.log('Action:', action.label),
                    })),
                })));
                setMetrics(metricsData);

                // Transform goals data
                setGoals(goalsData.map((goal: any) => ({
                    ...goal,
                    targetValue: goal.target,
                    currentValue: goal.current,
                    status: goal.status || 'on_track',
                    dueDate: goal.deadline ? new Date(goal.deadline) : undefined,
                })));

                // Transform tasks data
                setTasks(tasksData.map((task: any) => ({
                    ...task,
                    completed: task.status === 'completed',
                    isOverdue: task.due_date && new Date(task.due_date) < new Date(),
                    dueDate: task.due_date ? new Date(task.due_date) : undefined,
                })));

                // FALLBACK: If no data, use mock data for demo
                if (alertsData.length === 0) {
                    setAlerts([
                        {
                            id: '1',
                            type: 'critical',
                            title: 'Cash flow projected negative in 14 days',
                            description: 'Without intervention, bank balance will drop below $5,000',
                            metric: 'cash_flow',
                            value: -2400,
                            threshold: 0,
                        },
                        {
                            id: '2',
                            type: 'warning',
                            title: '3 invoices overdue by 30+ days',
                            description: '$12,450 in outstanding receivables',
                            metric: 'receivables',
                            value: 12450,
                            threshold: 30,
                        },
                    ]);

                    // Mock signals
                    setSignals([
                        {
                            id: '1',
                            type: 'positive',
                            title: 'Revenue up 12% vs. last month',
                            description: '$45,200 total revenue',
                            metric: 'revenue',
                            value: 45200,
                        },
                        {
                            id: '2',
                            type: 'positive',
                            title: 'On track to hit Q1 sales goal',
                            description: '78% complete with 3 weeks remaining',
                            metric: 'sales',
                            value: 78,
                        },
                    ]);

                    // Mock recommendations
                    setRecommendations([
                        {
                            id: '1',
                            priority: 'critical',
                            title: 'Review cash flow projection',
                            description: 'Your business is projected to have negative cash flow in 2 weeks.',
                            reasoning:
                                'Based on current burn rate of $8,500/week and $32,000 outstanding receivables.',
                            actions: [
                                {
                                    id: '1',
                                    label: 'Call customers with overdue invoices',
                                    description: 'Prioritize the 3 invoices over 30 days ($12,450 total)',
                                    buttonText: 'View Invoices',
                                    variant: 'primary',
                                    onClick: async () => {
                                        console.log('Navigate to invoices');
                                    },
                                },
                                {
                                    id: '2',
                                    label: 'Delay non-essential expenses',
                                    description: 'Postpone $3,200 in planned equipment purchases',
                                    buttonText: 'Review Expenses',
                                    variant: 'secondary',
                                    onClick: async () => {
                                        console.log('Navigate to expenses');
                                    },
                                },
                            ],
                            dismissible: true,
                            dismissed: false,
                            createdAt: new Date(),
                            generatedAt: new Date(),
                        },
                        {
                            id: '2',
                            priority: 'important',
                            title: 'Inventory aging alert',
                            description: '18 items have been in stock for 90+ days.',
                            reasoning: '$6,200 in slow-moving inventory is tying up working capital.',
                            actions: [
                                {
                                    id: '1',
                                    label: 'Run clearance promotion',
                                    description: '15% discount on aging items to free up cash',
                                    buttonText: 'Create Promotion',
                                    variant: 'primary',
                                    onClick: async () => {
                                        console.log('Create promotion');
                                    },
                                },
                            ],
                            dismissible: true,
                            dismissed: false,
                            createdAt: new Date(),
                            generatedAt: new Date(),
                        },
                        {
                            id: '3',
                            priority: 'suggestion',
                            title: 'Consider hiring part-time help',
                            description: 'Your workload is 15% above optimal capacity.',
                            reasoning:
                                'Task completion rate has dropped from 85% to 68% over the past 3 weeks.',
                            actions: [
                                {
                                    id: '1',
                                    label: 'Post job listing',
                                    description: '10-15 hours/week to handle order fulfillment',
                                    buttonText: 'Draft Listing',
                                    variant: 'primary',
                                    onClick: async () => {
                                        console.log('Draft job listing');
                                    },
                                },
                            ],
                            dismissible: true,
                            dismissed: false,
                            createdAt: new Date(),
                            generatedAt: new Date(),
                        },
                    ]);

                    // Mock metrics
                    setMetrics([
                        {
                            id: '1',
                            label: 'Revenue (MTD)',
                            value: '$45,200',
                            change: 12,
                            changeType: 'percentage',
                            trend: 'up',
                            period: 'vs. last month',
                            sparklineData: [32000, 35000, 38000, 42000, 45200],
                        },
                        {
                            id: '2',
                            label: 'Cash Balance',
                            value: '$18,450',
                            change: -8,
                            changeType: 'percentage',
                            trend: 'down',
                            period: 'vs. last week',
                            sparklineData: [22000, 21000, 20000, 19000, 18450],
                        },
                        {
                            id: '3',
                            label: 'Gross Margin',
                            value: '42%',
                            change: 2,
                            changeType: 'percentage',
                            trend: 'up',
                            period: 'vs. last quarter',
                            sparklineData: [38, 39, 40, 41, 42],
                        },
                        {
                            id: '4',
                            label: 'Active Orders',
                            value: '23',
                            change: 5,
                            changeType: 'absolute',
                            trend: 'up',
                            period: 'vs. yesterday',
                            sparklineData: [15, 18, 20, 18, 23],
                        },
                    ]);

                    // Mock goals
                    setGoals([
                        {
                            id: '1',
                            title: 'Reach $150k in Q1 revenue',
                            description: 'Grow monthly recurring revenue to $50k/month',
                            target: 150000,
                            current: 117000,
                            targetValue: 150000,
                            currentValue: 117000,
                            progress: 78,
                            dueDate: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000), // 3 weeks
                            status: 'on_track',
                            priority: 'high',
                            category: 'Revenue',
                        },
                        {
                            id: '2',
                            title: 'Reduce operating costs by 10%',
                            description: 'Target $4,500/month in fixed costs',
                            target: 4500,
                            current: 4850,
                            targetValue: 4500,
                            currentValue: 4850,
                            progress: 30,
                            dueDate: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000), // 2 months
                            status: 'at_risk',
                            priority: 'medium',
                            category: 'Cost Reduction',
                        },
                    ]);

                    // Mock tasks
                    setTasks([
                        {
                            id: '1',
                            title: 'Follow up on 3 overdue invoices',
                            description: 'Customers: Acme Corp, BuildCo, TechStart',
                            status: 'todo',
                            priority: 'urgent',
                            dueDate: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours
                            isOverdue: false,
                            completed: false,
                            goalId: '1',
                        },
                        {
                            id: '2',
                            title: 'Review and approve vendor invoices',
                            status: 'in_progress',
                            priority: 'high',
                            dueDate: new Date(Date.now() + 5 * 60 * 60 * 1000), // 5 hours
                            isOverdue: false,
                            completed: false,
                        },
                        {
                            id: '3',
                            title: 'Update Q1 financial projections',
                            status: 'todo',
                            priority: 'medium',
                            dueDate: new Date(Date.now() + 8 * 60 * 60 * 1000), // end of day
                            isOverdue: false,
                            completed: false,
                        },
                        {
                            id: '4',
                            title: 'Schedule team meeting for next week',
                            status: 'completed',
                            priority: 'low',
                            isOverdue: false,
                            completed: true,
                        },
                    ]);
                }
            } catch (error) {
                console.error('Error fetching coach data:', error);
                setError(error instanceof Error ? error.message : 'Failed to load data');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [tenantId, token]);

    const handleViewReport = () => {
        console.log('Navigate to health score report');
        // TODO: Navigate to detailed health score breakdown
    };

    const handleAskCoach = () => {
        console.log('Open coach chat');
        // TODO: Open coach chat modal/drawer
    };

    const handleTakeAction = (action: RecommendationAction) => {
        console.log('Take action:', action);
        action.onClick();
    };

    const handleDismissRecommendation = (recommendationId: string) => {
        console.log('Dismiss recommendation:', recommendationId);
        // TODO: API call to dismiss recommendation
        setRecommendations((prev) => prev.filter((r) => r.id !== recommendationId));
    };

    const handleMetricClick = (metricId: string) => {
        console.log('View metric detail:', metricId);
        // TODO: Navigate to metric detail page
    };

    const handleGoalClick = (goalId: string) => {
        console.log('View goal detail:', goalId);
        // TODO: Navigate to goal detail page or open modal
    };

    const handleTaskClick = (taskId: string) => {
        console.log('View task detail:', taskId);
        // TODO: Navigate to task detail page or open modal
    };

    const handleToggleComplete = (taskId: string) => {
        console.log('Toggle task complete:', taskId);
        // TODO: API call to update task status
        setTasks((prev) =>
            prev.map((task) =>
                task.id === taskId ? { ...task, completed: !task.completed, status: task.completed ? 'todo' : 'completed' } : task
            )
        );
    };

    // Show loading state
    if (loading) {
        return (
            <Container size="xl" py="md">
                <Center style={{ minHeight: '400px' }}>
                    <Stack align="center" gap="md">
                        <Loader size="lg" />
                        <MantineText c="dimmed">Loading your business health dashboard...</MantineText>
                    </Stack>
                </Center>
            </Container>
        );
    }

    // Show error state
    if (error) {
        return (
            <Container size="xl" py="md">
                <Center style={{ minHeight: '400px' }}>
                    <Stack align="center" gap="md">
                        <MantineText size="lg" fw={600} c="red">Error Loading Dashboard</MantineText>
                        <MantineText c="dimmed">{error}</MantineText>
                        <MantineText size="sm" c="dimmed">Make sure the backend is running on port 8001</MantineText>
                    </Stack>
                </Center>
            </Container>
        );
    }

    return (
        <Container size="xl" py="md">
            <Stack gap="lg">
                {/* Health Score Header - Always visible, sticky */}
                <HealthScoreHeader
                    score={healthScore}
                    previousScore={previousScore}
                    trend={healthScore > previousScore ? 'up' : healthScore < previousScore ? 'down' : 'stable'}
                    changeAmount={Math.abs(healthScore - previousScore)}
                    criticalAlerts={alerts}
                    positiveSignals={signals}
                    onViewReport={handleViewReport}
                    onAskCoach={handleAskCoach}
                    loading={loading}
                />

                {/* Key Metrics Grid */}
                <MetricsGrid metrics={metrics} loading={loading} onMetricClick={handleMetricClick} />

                {/* Three-column layout: Coach | Goals & Tasks | Evidence */}
                <div
                    style={{
                        display: 'grid',
                        gridTemplateColumns: '360px 1fr 360px',
                        gap: '24px',
                    }}
                >
                    {/* Left: Proactive Coach */}
                    <div>
                        <Stack gap="md">
                            {recommendations.map((rec) => (
                                <ProactiveCoachCard
                                    key={rec.id}
                                    recommendation={rec}
                                    onTakeAction={handleTakeAction}
                                    onDismiss={handleDismissRecommendation}
                                    loading={loading}
                                />
                            ))}
                        </Stack>
                    </div>

                    {/* Center: Goals & Tasks */}
                    <div>
                        <Stack gap="xl">
                            <GoalsColumn goals={goals} loading={loading} onGoalClick={handleGoalClick} />
                            <TasksColumn
                                tasks={tasks}
                                loading={loading}
                                onTaskClick={handleTaskClick}
                                onToggleComplete={handleToggleComplete}
                            />
                        </Stack>
                    </div>

                    {/* Right: Evidence (TODO: Implement in Phase 2) */}
                    <div>
                        {/* Placeholder for evidence panel */}
                        {/* Will contain: Recent activity, data sources, insights history */}
                    </div>
                </div>
            </Stack>
        </Container>
    );
}
