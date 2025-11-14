import { ActionIcon, Badge, Button, Card, Center, Container, Grid, Group, Loader, Text as MantineText, Skeleton, Stack, Tabs, Tooltip } from '@mantine/core';
import { IconBulb, IconChevronDown, IconChevronUp, IconNote, IconTarget } from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Alert, CoachRecommendation, GoalWithProgress, MetricSnapshot, RecommendationAction, Signal, TaskWithPriority } from '../components/coach-v6';
import { GoalsColumn, HealthScoreHeader, MetricsGrid, ProactiveCoachCard, TasksColumn } from '../components/coach-v6';
import { NotificationCenter } from '../components/notifications';
import { useWebSocket } from '../hooks/useWebSocket';
import * as api from '../lib/api';
import { useAuthStore } from '../stores/auth';

export default function DashboardFixed() {
    const navigate = useNavigate();
    const { tenantId, apiToken: token } = useAuthStore();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [healthScore, setHealthScore] = useState(0);
    const [previousScore, setPreviousScore] = useState(0);
    const [healthData, setHealthData] = useState<any>(null); // Store full health object for context
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [signals, setSignals] = useState<Signal[]>([]);
    const [recommendations, setRecommendations] = useState<CoachRecommendation[]>([]);
    const [metrics, setMetrics] = useState<MetricSnapshot[]>([]);
    const [goals, setGoals] = useState<GoalWithProgress[]>([]);
    const [tasks, setTasks] = useState<TaskWithPriority[]>([]);
    const [recFilter, setRecFilter] = useState<'all' | 'critical' | 'important' | 'suggestion'>('all');
    const [showCoach, setShowCoach] = useState(false);
    const [showGoalsTasks, setShowGoalsTasks] = useState(true);

    const { isConnected: wsConnected, error: wsError } = useWebSocket({ tenantId: tenantId ?? '', token: token ?? '', enabled: !!tenantId && !!token });

    const narrativeText = useMemo(() => {
        const diff = healthScore - previousScore;
        const trendWord = diff > 0 ? 'up' : diff < 0 ? 'down' : 'flat';
        const critical = alerts.filter((a) => a.type === 'critical');
        const positives = signals.filter((s) => s.type === 'positive');
        const dueSoonGoals = goals.filter((g) => g.dueDate && Math.ceil(((g.dueDate as Date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)) <= 7);
        const pendingTasks = tasks.filter((t) => !t.completed);
        const attention = critical.slice(0, 2).map((a) => a.title).join('; ');
        const good = positives.slice(0, 2).map((s) => s.title).join('; ');
        return `Health score ${healthScore} (${trendWord} ${Math.abs(diff)}). ${critical.length ? 'Attention: ' + attention + '. ' : ''}${positives.length ? 'Positive: ' + good + '. ' : ''}${dueSoonGoals.length ? 'Goals due soon: ' + dueSoonGoals.length + '. ' : ''}Tasks pending: ${pendingTasks.length}.`;
    }, [healthScore, previousScore, alerts, signals, goals, tasks]);

    const fetchData = async () => {
        if (!tenantId) return;
        setLoading(true);
        setError(null);
        try {
            // Fetch tasks with defensive fallback in case horizon=today is unsupported
            const [health, alertsData, signalsData, metricsData, goalsData, recs] = await Promise.all([
                api.getHealthScore(tenantId, token),
                api.getHealthAlerts(tenantId, token),
                api.getHealthSignals(tenantId, token),
                api.getMetricsSnapshot(tenantId, token),
                api.getGoals(tenantId, token),
                api.getCoachRecommendations(tenantId, token),
            ]);

            let tasksData: any[] = [];
            try {
                tasksData = await api.getTasks(tenantId, token, 'daily');
            } catch (taskErr: any) {
                const msg = taskErr instanceof Error ? taskErr.message : String(taskErr);
                if (msg.includes('422')) {
                    // Fallback to default tasks fetch without horizon
                    tasksData = await api.getTasks(tenantId, token);
                } else {
                    throw taskErr;
                }
            }

            setHealthScore(health.score ?? 0);
            setPreviousScore((health.score ?? 0) - (health.trend ?? 0));
            setHealthData(health); // Store full health object
            setAlerts((alertsData ?? []).map((a: any) => ({
                ...a,
                // Normalize type to component union
                type: a.type === 'critical' ? 'critical' : a.type === 'warning' ? 'warning' : 'info',
            })) as any);
            setSignals((signalsData ?? []).map((s: any) => ({
                ...s,
                // Normalize type to component union
                type: s.type === 'positive' ? 'positive' : 'neutral',
            })) as any);
            setMetrics((metricsData ?? []).map((m: any) => ({
                ...m,
                format: (['currency', 'number', 'percentage'].includes(m.format) ? m.format : undefined) as 'currency' | 'number' | 'percentage' | undefined,
            })) as any);

            setGoals((goalsData ?? []).map((goal: any) => ({
                ...goal,
                status: goal.status || 'on_track',
                dueDate: goal.deadline ? new Date(goal.deadline) : undefined,
            })) as any);

            setTasks((tasksData ?? []).map((task: any) => ({
                ...task,
                completed: task.status === 'completed',
                dueDate: task.due_date ? new Date(task.due_date) : undefined,
            })) as any);

            setRecommendations((recs ?? []).map((r: any) => ({
                ...r,
                actions: (r.actions ?? []).map((action: any) => ({
                    id: action.id ?? action.label,
                    label: action.label,
                    description: action.description,
                    buttonText: action.buttonText ?? action.label,
                    variant: (['primary', 'secondary', 'tertiary'].includes(action.variant) ? action.variant : 'primary') as 'primary' | 'secondary' | 'tertiary',
                    completed: !!action.completed,
                    onClick: async () => {
                        // Default action: navigate to planner
                        navigate('/planner');
                    },
                })),
            })) as any);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [tenantId, token]);

    const handleViewReport = () => navigate('/reports');
    const handleAskCoach = () => {
        // Pass current context to coach so chat can start with situational awareness
        const context = {
            healthScore: healthData || { score: healthScore, trend: 0, breakdown: {} }, // Pass full object or construct minimal one
            previousScore,
            alerts: alerts.map(a => ({ id: a.id, type: a.type, title: a.title })),
            signals: signals.map(s => ({ id: s.id, type: s.type, title: s.title })),
            goals: goals.slice(0, 5).map(g => ({ id: g.id, title: g.title, status: g.status, dueDate: g.dueDate })),
            tasks: tasks.slice(0, 10).map(t => ({ id: t.id, title: t.title, status: t.status, priority: t.priority, dueDate: t.dueDate })),
        }
        navigate('/coach', { state: { context } })
    };
    const handleMetricClick = (metricId: string) => navigate(`/analytics?metric=${encodeURIComponent(metricId)}`);
    const handleGoalClick = (goalId: string) => navigate(`/goals?goalId=${encodeURIComponent(goalId)}`);
    const handleTaskClick = (taskId: string) => navigate(`/planner?taskId=${encodeURIComponent(taskId)}`);
    const handleToggleComplete = (taskId: string) => {
        setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, completed: !t.completed, status: t.completed ? 'todo' : 'completed' } : t)) as any);
    };
    const handleRetry = () => fetchData();
    const handleTakeAction = (action: RecommendationAction) => action.onClick();
    const handleDismissRecommendation = async (recommendationId: string) => {
        try {
            if (tenantId) await api.dismissRecommendation(tenantId, recommendationId, token);
        } catch (err) {
            console.error('Failed to dismiss recommendation', err);
        } finally {
            setRecommendations((prev) => prev.filter((r) => r.id !== recommendationId));
        }
    };

    if (!tenantId) {
        return (
            <Container size="xl" py="xl">
                <Stack align="center" gap="lg" style={{ marginTop: '100px' }}>
                    <MantineText size="xl" fw={600} c="red">No tenant ID found</MantineText>
                    <MantineText c="dimmed">Please log in to access your dashboard.</MantineText>
                </Stack>
            </Container>
        );
    }

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

    if (error) {
        return (
            <Container size="xl" py="md">
                <Center style={{ minHeight: '400px' }}>
                    <Stack align="center" gap="md">
                        <MantineText size="lg" fw={600} c="red">Unable to load dashboard</MantineText>
                        <MantineText c="dimmed">{error}</MantineText>
                        <Button variant="outline" onClick={handleRetry}>Retry</Button>
                    </Stack>
                </Center>
            </Container>
        );
    }

    return (
        <>
            <NotificationCenter position="top-right" showToasts maxToasts={3} />
            <Container size="xl" py="md">
                <Stack gap="lg">
                    <Tooltip label={wsError ? 'WebSocket error' : wsConnected ? 'Connected to live updates' : 'Offline; updates paused'}>
                        <Badge color={wsError ? 'red' : wsConnected ? 'green' : 'gray'} variant="light" size="sm">
                            {wsError ? 'Live updates error' : wsConnected ? 'Live updates connected' : 'Live updates offline'}
                        </Badge>
                    </Tooltip>

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

                    <MetricsGrid metrics={metrics} loading={loading} onMetricClick={handleMetricClick} />

                    <Card radius="md" withBorder>
                        <MantineText size="sm" c="dimmed">{narrativeText}</MantineText>
                    </Card>

                    <Group gap="sm">
                        <Button variant="light" leftSection={<IconBulb size={16} />} onClick={handleAskCoach}>Ask Coach</Button>
                        <Button variant="gradient" leftSection={<IconTarget size={16} />} onClick={() => navigate('/goals')}>Set a goal</Button>
                        <Button variant="default" leftSection={<IconNote size={16} />} onClick={() => navigate('/planner')}>Open Action Plan</Button>
                    </Group>

                    <Grid gutter="xl">
                        <Grid.Col span={{ base: 12, md: 4 }} id="recommendations-section">
                            <Group justify="space-between" align="center" mb="xs">
                                <MantineText fw={600}>Coach Insights</MantineText>
                                <ActionIcon variant="subtle" onClick={() => setShowCoach((s) => !s)}>
                                    {showCoach ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
                                </ActionIcon>
                            </Group>

                            {showCoach && recommendations.length > 0 && (
                                <Tabs value={recFilter} onChange={(v) => setRecFilter((v as any) ?? 'all')} variant="pills" radius="md" mb="md">
                                    <Tabs.List>
                                        <Tabs.Tab value="all">All <Badge ml="xs" size="xs" variant="light">{recommendations.length}</Badge></Tabs.Tab>
                                        <Tabs.Tab value="critical">Critical <Badge ml="xs" size="xs" color="red" variant="light">{recommendations.filter(r => r.priority === 'critical').length}</Badge></Tabs.Tab>
                                        <Tabs.Tab value="important">Important <Badge ml="xs" size="xs" color="yellow" variant="light">{recommendations.filter(r => r.priority === 'important').length}</Badge></Tabs.Tab>
                                        <Tabs.Tab value="suggestion">Suggested <Badge ml="xs" size="xs" color="blue" variant="light">{recommendations.filter(r => r.priority === 'suggestion').length}</Badge></Tabs.Tab>
                                    </Tabs.List>
                                </Tabs>
                            )}

                            {showCoach && (
                                <Stack gap="md">
                                    {loading ? (
                                        Array.from({ length: 3 }).map((_, i) => (
                                            <Card key={i} radius="md" withBorder>
                                                <Stack gap="xs" p="sm">
                                                    <Skeleton height={12} width="30%" />
                                                    <Skeleton height={10} width="80%" />
                                                    <Skeleton height={10} width="60%" />
                                                </Stack>
                                            </Card>
                                        ))
                                    ) : recommendations.length === 0 ? (
                                        <Card shadow="sm" radius="md" withBorder>
                                            <Stack gap="xs">
                                                <MantineText fw={600}>No recommendations</MantineText>
                                                <MantineText c="dimmed" size="sm">Recommendations appear here when new insights are available.</MantineText>
                                                <Button variant="light" onClick={handleAskCoach} leftSection={<IconBulb size={16} />}>Ask Coach</Button>
                                            </Stack>
                                        </Card>
                                    ) : (
                                        recommendations
                                            .filter((rec) => recFilter === 'all' ? true : rec.priority === recFilter)
                                            .map((rec) => (
                                                <ProactiveCoachCard
                                                    key={rec.id}
                                                    recommendation={rec}
                                                    onTakeAction={handleTakeAction}
                                                    onDismiss={handleDismissRecommendation}
                                                    loading={loading}
                                                />
                                            ))
                                    )}
                                </Stack>
                            )}
                        </Grid.Col>

                        <Grid.Col span={{ base: 12, md: 8 }}>
                            <Group justify="space-between" align="center" mb="xs">
                                <MantineText fw={600}>Goals & Tasks</MantineText>
                                <ActionIcon variant="subtle" onClick={() => setShowGoalsTasks((s) => !s)}>
                                    {showGoalsTasks ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
                                </ActionIcon>
                            </Group>

                            {showGoalsTasks && (
                                <Stack gap="xl">
                                    {(() => {
                                        const activeGoals = goals.filter((g) => g.status !== 'completed');
                                        const sortedGoals = activeGoals.sort((a, b) => {
                                            const statusRank = (s: string) => ({ at_risk: 0, off_track: 1, on_track: 2 } as any)[s] ?? 3;
                                            const srA = statusRank(a.status);
                                            const srB = statusRank(b.status);
                                            if (srA !== srB) return srA - srB;
                                            const da = a.dueDate?.getTime() ?? Number.MAX_SAFE_INTEGER;
                                            const db = b.dueDate?.getTime() ?? Number.MAX_SAFE_INTEGER;
                                            return da - db;
                                        });
                                        return (
                                            <GoalsColumn
                                                goals={sortedGoals}
                                                loading={loading}
                                                onGoalClick={handleGoalClick}
                                                onCreateGoal={() => navigate('/goals?create=true')}
                                            />
                                        );
                                    })()}

                                    {goals.length === 0 && !loading && (
                                        <Card shadow="sm" radius="md" withBorder>
                                            <Stack gap="xs">
                                                <MantineText fw={600}>No active goals</MantineText>
                                                <MantineText c="dimmed" size="sm">Create your first goal to start tracking progress.</MantineText>
                                                <Button variant="gradient" onClick={() => navigate('/goals')} leftSection={<IconTarget size={16} />}>Set a goal</Button>
                                            </Stack>
                                        </Card>
                                    )}

                                    {(() => {
                                        const priorityRank = (p: string) => ({ urgent: 0, high: 1, medium: 2, low: 3 } as any)[p] ?? 4;
                                        const sortedTasks = tasks.slice().sort((a, b) => {
                                            const ca = a.completed ? 1 : 0;
                                            const cb = b.completed ? 1 : 0;
                                            if (ca !== cb) return ca - cb;
                                            const pr = priorityRank(a.priority) - priorityRank(b.priority);
                                            if (pr !== 0) return pr;
                                            const ta = a.dueDate?.getTime() ?? Number.MAX_SAFE_INTEGER;
                                            const tb = b.dueDate?.getTime() ?? Number.MAX_SAFE_INTEGER;
                                            return ta - tb;
                                        });
                                        return (
                                            <TasksColumn
                                                tasks={sortedTasks}
                                                loading={loading}
                                                onTaskClick={handleTaskClick}
                                                onToggleComplete={handleToggleComplete}
                                            />
                                        );
                                    })()}

                                    {tasks.length === 0 && !loading && (
                                        <Card shadow="sm" radius="md" withBorder>
                                            <Stack gap="xs">
                                                <MantineText fw={600}>No tasks</MantineText>
                                                <MantineText c="dimmed" size="sm">Create an action plan to turn insights into progress.</MantineText>
                                                <Button variant="light" onClick={() => navigate('/planner')} leftSection={<IconNote size={16} />}>Open Action Plan</Button>
                                            </Stack>
                                        </Card>
                                    )}
                                </Stack>
                            )}
                        </Grid.Col>
                    </Grid>
                </Stack>
            </Container>
        </>
    );
}
