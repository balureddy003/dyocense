/**import { Button, Card, Center, Container, Loader, Text as MantineText, Stack } from '@mantine/core';

 * Coach V6 - SMB-Optimized Chat Interfaceimport { useEffect, useState } from 'react';

 * import { useNavigate } from 'react-router-dom';

 * Design improvements:import type {

 * - Single-column layout (no three panes)    Alert,

 * - Plain language (no tech jargon)    CoachRecommendation,

 * - 8px spacing grid    GoalWithProgress,

 * - Mobile-first    MetricSnapshot,

 * - Clear visual hierarchy    RecommendationAction,

 */    Signal,

    TaskWithPriority,

import React, { useState, useRef, useEffect, useMemo } from 'react';} from '../components/coach-v6';

import {import {

    Container, GoalsColumn,

    Stack, HealthScoreHeader,

    Paper, MetricsGrid,

    TextInput, ProactiveCoachCard,

    ActionIcon, TasksColumn,

    ScrollArea,
} from '../components/coach-v6';

Group,import { NotificationCenter, useNotificationStore } from '../components/notifications';

Text,import { useWebSocket } from '../hooks/useWebSocket';

Button,import * as api from '../lib/api';

Box,import { useAuthStore } from '../stores/auth';

Avatar,

    Collapse,/**

    Divider, * Coach V6 - Fitness Dashboard Paradigm

} from '@mantine/core'; * 

import { * "Business Health Coach" - Inspired by Whoop/Peloton fitness tracking

    IconSend, * Mental model: "I'm checking my business health" not "I'm chatting with AI"

    IconChevronDown, * 

    IconChevronUp, * Design Principles:

} from '@tabler/icons-react'; * - Dashboard-first (not chat-first)

import { useQuery } from '@tanstack/react-query'; * - Persistent metrics (not hidden)

import { CoachVisualizationV2 } from '../components/CoachVisualizationV2'; * - Proactive coach (not reactive)

import { QuickActions, SimplifiedProgress, SPACING } from '../components/SimplifiedCoachLayout'; * - Fitness metaphor (health score, progress tracking, coaching)

 */

    interface Message {
        export default function CoachV6() {

            id: string; const navigate = useNavigate();

            role: 'user' | 'assistant'; const [loading, setLoading] = useState(true);

            content: string; const [error, setError] = useState<string | null>(null);

            timestamp: Date; const [healthScore, setHealthScore] = useState(0);

            visual_response ?: any; const [previousScore, setPreviousScore] = useState(0);

            metadata ?: {
                const [alerts, setAlerts] = useState<Alert[]>([]);

                phase?: string; const [signals, setSignals] = useState<Signal[]>([]);

                intent?: string; const [recommendations, setRecommendations] = useState<CoachRecommendation[]>([]);

                current_task?: number; const [metrics, setMetrics] = useState<MetricSnapshot[]>([]);

                total_tasks?: number; const [goals, setGoals] = useState<GoalWithProgress[]>([]);

            }; const [tasks, setTasks] = useState<TaskWithPriority[]>([]);

        }

    // Get tenant and token from auth store

    interface CoachV6Props {    const { tenantId, apiToken: token } = useAuthStore();

    tenantId: string;

    apiToken: string;    // Notification store for in-app notifications

    businessName ?: string; const { addNotification } = useNotificationStore();

}

// Log tenant ID and token status for debugging

export const CoachV6: React.FC<CoachV6Props> = ({ tenantId, apiToken, businessName }) => {
    console.log('[CoachV6] Tenant ID:', tenantId);

    // State    console.log('[CoachV6] Has token:', !!token);

    const [messages, setMessages] = useState<Message[]>([]);

    const [input, setInput] = useState('');    // If no tenant ID, show error

    const [isSending, setIsSending] = useState(false); if (!tenantId) {

        const [showEvidence, setShowEvidence] = useState<Record<string, boolean>>({}); return (

    const scrollRef = useRef<HTMLDivElement>(null); <Container size="xl" py="xl">

            const abortControllerRef = useRef<AbortController | null>(null);                <Stack align="center" gap="lg" style={{ marginTop: '100px' }}>

                <MantineText size="xl" fw={600} c="red">

    // Scroll to bottom on new messages                        No tenant ID found

    useEffect(() => {                    </MantineText>

                if (scrollRef.current) {<MantineText c="dimmed">

                    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;                        Please log in to access your dashboard.

        }                    </MantineText>

                }, [messages]);                </Stack>

        </Container>

        // Send message handler        );

        const handleSend = async () => { }

        if (!input.trim() || isSending) return;

        // Initialize WebSocket connection for real-time updates

        const userMessage: Message = {
            const { isConnected: wsConnected, error: wsError } = useWebSocket(

                id: Date.now().toString(), {

                role: 'user', tenantId,

                content: input.trim(), token: token || '',

                timestamp: new Date(), enabled: !!token, // Only connect if token exists

            };
        },

            {

                setMessages(prev => [...prev, userMessage]); onHealthScoreUpdate: (data) => {

                    setInput(''); console.log('[Coach V6] Health score update:', data);

                    setIsSending(true); setHealthScore(data.score);

                    setPreviousScore(data.previousScore);

                    try {
                        setAlerts(data.alerts as any);

                        // TODO: Implement SSE streaming to backend                setSignals(data.signals as any);

                        // For now, simulate assistant response

                        setTimeout(() => {                // Show notification for significant score changes

                            const assistantMessage: Message = {
                                const scoreDiff = data.score - data.previousScore;

                                id: (Date.now() + 1).toString(), if(Math.abs(scoreDiff) >= 5) {

                            role: 'assistant', addNotification({

                                content: 'Processing your request...', type: 'info',

                                timestamp: new Date(), priority: Math.abs(scoreDiff) >= 10 ? 'important' : 'normal',

                                metadata: {
                                    title: `Health Score ${scoreDiff > 0 ? 'Improved' : 'Declined'}`,

                                    phase: 'analyzing', message: `Your business health score ${scoreDiff > 0 ? 'increased' : 'decreased'} from ${data.previousScore} to ${data.score}`,

                                    current_task: 1, autoDismissMs: 5000,

                                    total_tasks: 3,
                                });

                        }
                    }

                };
    },

    setMessages(prev => [...prev, assistantMessage]); onNewRecommendation: (data) => {

        setIsSending(false); console.log('[Coach V6] New recommendation:', data);

    }, 1000);

} catch (error) {                // Add notification for new recommendation

    console.error('Error sending message:', error); addNotification({

        setIsSending(false);                    type: 'recommendation',

    }                    priority: data.priority === 'critical' ? 'critical' : data.priority === 'important' ? 'important' : 'normal',

    }; title: 'New Recommendation',

    message: data.title,

    const handleKeyPress = (e: React.KeyboardEvent) => {
    action: {

        if (e.key === 'Enter' && !e.shiftKey) {
            label: 'View',

                e.preventDefault(); onClick: () => {

                    handleSend();                            // Scroll to recommendations section

                }                            document.getElementById('recommendations-section')?.scrollIntoView({ behavior: 'smooth' });

        };
    },

},

const toggleEvidence = (messageId: string) => {
    autoDismissMs: data.priority === 'critical' ? 0 : 8000, // Critical stays until dismissed

        setShowEvidence(prev => ({
            metadata: { recommendationId: data.id },

            ...prev,
        });

    [messageId]: !prev[messageId]

}));                // Add new recommendation to top of list

    }; setRecommendations((prev) => [

    {

        return(...data,

        <Container size = "md" p = { 0} h = "100vh" style = {{ display: 'flex', flexDirection: 'column' }} > createdAt: new Date(data.createdAt),

    {/* Header */ }                        generatedAt: new Date(data.createdAt),

    <Paper p={SPACING.md} shadow="sm" style={{ borderRadius: 0 }}>                        reasoning: '',

        <Stack gap={SPACING.xs}>                        dismissed: false,

            <Group justify="space-between">                        actions: data.actions.map((action, idx) => ({

                <Text size="lg" fw={700}>                            id: `${data.id}-action-${idx}`,

                    👋 Hey {businessName || 'there'}                            ...action,

                </Text>                            description: '',

            </Group>                            buttonText: action.label,

            <Text size="sm" c="dimmed">                            onClick: async () => console.log('Action:', action.label),

                        I can help you understand your business and take action                        })),

            </Text>                    },

        </Stack>                    ...prev,

    </Paper>]);

            },

{/* Messages Area */ } onTaskCompleted: (data) => {

    <ScrollArea console.log('[Coach V6] Task completed:', data);

    ref = { scrollRef }

    style = {{ flex: 1 }
}                 // Show notification for task completion

p = { SPACING.md }                addNotification({

            > type: 'task',

    <Stack gap={SPACING.lg}>                    priority: 'normal',

        {/* Quick Actions - Show when no messages */}                    title: 'Task Completed! 🎉',

        {messages.length === 0 && (message: data.taskTitle,

        <Box mt={SPACING.xl}>                    autoDismissMs: 5000,

            <QuickActions />                });

        </Box>

                    )}                // Update task status in state

                setTasks((prev) =>

        {/* Messages */}                    prev.map((task) =>

        {messages.map((message) => (task.id === data.taskId

            < Box key = { message.id } >                            ? { ...task, completed: true, status: 'completed' }

                            {
                message.role === 'user' ? (                            : task

                    // User message - right aligned                    )

                    < Group justify="flex-end" >                );

        <Paper             },

                                        bg="blue.6"             onGoalProgressUpdate: (data) => {

            p = { SPACING.md }                 console.log('[Coach V6] Goal progress update:', data);

        radius="lg"

        maw="80%"                // Show notification for significant progress (milestone achieved)

        style={{ borderBottomRightRadius: 4 }}                if (data.progress >= 100) {

                                    > addNotification({

                                        < Text size = "sm" c = "white" > type: 'goal',

        {message.content}                        priority: 'important',

    </Text>                        title: 'Goal Achieved! 🏆',

                                    </Paper > message: data.goalTitle,

                                </Group > autoDismissMs: 10000,

) : (                    });

// Assistant message - left aligned                } else if (data.progress >= 50 && data.progress < 60) {

<Stack gap={SPACING.sm}>                    // Milestone: 50% complete

    <Group align="flex-start" gap={SPACING.sm}>                    addNotification({

        <Avatar color="violet" radius="xl" size="sm">                        type: 'goal',

            🤖                        priority: 'normal',

        </Avatar>                        title: 'Halfway There!',

        <Stack gap={SPACING.md} style={{ flex: 1 }}>                        message: `${data.goalTitle} is ${Math.round(data.progress)}% complete`,

            {/* Progress indicator */}                        autoDismissMs: 5000,

            {message.metadata?.phase && (                    });

            <SimplifiedProgress                }

            message={message.metadata.phase}

            current={message.metadata.current_task}                // Update goal progress in state

            total={message.metadata.total_tasks}                setGoals((prev) =>

                                                />                    prev.map((goal) =>

                                            )}                        goal.id === data.goalId

            ? {

                {/* Visual response */ }                                ...goal,

            {message.visual_response && (progress: data.progress,

            <CoachVisualizationV2 data={message.visual_response} />                                status: (['on_track', 'at_risk', 'off_track', 'completed'].includes(data.status)

                                            )}                                    ? data.status

            : 'on_track') as 'on_track' | 'at_risk' | 'off_track' | 'completed',

            {/* Text content */}                            }

            {message.content && (                            : goal

            <Paper                     )

            bg="gray.0"                 );

            p={SPACING.md}             },

                                                    radius="lg"            onConnect: () => {

                style = {{borderBottomLeftRadius: 4 }}                console.log('[Coach V6] WebSocket connected');

                                                >            },

            <Text size="sm">            onDisconnect: () => {

                { message.content }                console.log('[Coach V6] WebSocket disconnected');

            </Text>            },

        </Paper>            onError: (event) => {

                                            )}                console.error('[Coach V6] WebSocket error:', event);

            },

        {/* Evidence toggle (if available) */}        }

        {message.visual_response?.tables && message.visual_response.tables.length > 0 && (    );

        <>

            <Button useEffect(() => {

                variant = "subtle"        const fetchData = async () => {

                size = "xs"            setLoading(true);

            color="gray"            setError(null);

            onClick={() => toggleEvidence(message.id)}            try {

                rightSection = {                // Fetch all data in parallel

                    showEvidence[message.id]                 const [

                                                                ? <IconChevronUp size={16} />                     healthScoreData,

                                                                : <IconChevronDown size={16} />                    recommendationsData,

                                                        }                    alertsData,

                                                    >                    signalsData,

            {showEvidence[message.id] ? 'Hide' : 'Show'} evidence                    metricsData,

        </Button>                    goalsData,

        <Collapse in={showEvidence[message.id]}>                    tasksData,

            <Stack gap={SPACING.sm}>                ] = await Promise.all([

                {message.visual_response.tables.map((table: any, idx: number) => (api.getHealthScore(tenantId, token),

                    <Paper key={idx} p={SPACING.sm} bg="white" withBorder>                    api.getCoachRecommendations(tenantId, token),

                        <Text size="xs" fw={600} mb={SPACING.xs}>                    api.getHealthAlerts(tenantId, token),

                            {table.title}                    api.getHealthSignals(tenantId, token),

                        </Text>                    api.getMetricsSnapshot(tenantId, token),

                        {/* Table rendering would go here */}                    api.getGoals(tenantId, token),

                    </Paper>                    api.getTasks(tenantId, token),

                ))}                ]);

            </Stack>

        </Collapse>                // Set health score

    </>                setHealthScore(healthScoreData.score);

                                            )}                setPreviousScore(healthScoreData.score - Math.round(healthScoreData.trend));

</Stack>

                                    </Group >                // Set API data (normalize API types to component types)

                                </Stack > setAlerts(

)}                    alertsData.map((a: any) => ({

                        </Box> id: a.id,

))}                        type: (['critical', 'warning', 'info'].includes(a.type)

    ? a.type

                    {/* Typing indicator */ }                            : 'info') as 'critical' | 'warning' | 'info',

    { isSending && (title: a.title,

        <Group gap={SPACING.sm}>                        description: a.description,

            <Avatar color="violet" radius="xl" size="sm">                        metric: a.metric,

                🤖                        value: a.value,

            </Avatar>                        threshold: a.threshold,

            <Paper bg="gray.0" p={SPACING.md} radius="lg">                    }))

                <Text size="sm" c="dimmed">                );

                    Thinking...                setSignals(

                </Text>                    signalsData.map((s: any) => ({

                            </Paper>                        id: s.id,

        </Group>                        type: (['positive', 'neutral'].includes(s.type)

        )}                            ?s.type

                </Stack >                            : 'neutral') as 'positive' | 'neutral',

            </ScrollArea > title: s.title,

    description: s.description,

        {/* Input Area */ }                        metric: s.metric,

            <Paper p={SPACING.md} shadow="md" style={{ borderRadius: 0 }}>                        value: s.value,

                <Group gap={SPACING.sm} align="flex-end">                    }))

                    <TextInput                );

                    flex={1}                setRecommendations(

                        placeholder="Ask me anything about your business..."                    recommendationsData.map((rec: any) => ({

                        value = { input }                        ...rec,

                    onChange={(e) => setInput(e.target.value)}                        createdAt: new Date(rec.createdAt),

                    onKeyDown={handleKeyPress}                        generatedAt: new Date(rec.generatedAt),

                    disabled={isSending}                        actions: rec.actions.map((action: any) => ({

                        size = "md"                            id: action.id,

                    radius="xl"                            label: action.label,

                    styles={{
                        description: action.description,

                        input: {
                            buttonText: action.buttonText,

                            fontSize: '14px', variant: (['primary', 'secondary', 'tertiary'].includes(action.variant)

                                padding: `${SPACING.sm}px ${SPACING.md}px`,                                ? action.variant

                            }                                : 'primary') as 'primary' | 'secondary' | 'tertiary',

                        }}                            completed: action.completed,

                    />                            onClick: async () => console.log('Action:', action.label),

                    <ActionIcon                        })),

                    size={40}                    }))

                    radius="xl"                );

                    color="blue"                setMetrics(

                        variant="filled"                    metricsData.map((m: any) => ({

                        onClick = { handleSend }                        id: m.id,

                    disabled={!input.trim() || isSending}                        label: m.label,

                    >                        value: m.value,

                    <IconSend size={20} />                        change: m.change,

                </ActionIcon>                        changeType: m.changeType,

            </Group>                        trend: m.trend,

                <Text size="xs" c="dimmed" mt={SPACING.xs} ta="center">                        sparklineData: m.sparklineData,

                    Powered by your business data • Xero • Shopify                        period: m.period,

                </Text>                        format: (['currency', 'number', 'percentage'].includes(m.format)

            </Paper >                            ? m.format

        </Container >                            : undefined) as 'currency' | 'number' | 'percentage' | undefined,

    );                    }))

};                );



export default CoachV6;                // Transform goals data

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

                // No mock fallbacks. Display real backend data only.
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
    // Navigate to the Reports page
    navigate('/reports');
};

const handleAskCoach = () => {
    // Navigate to Coach (alias to CoachV5 conversational UI)
    navigate('/coach');
};

const handleTakeAction = (action: RecommendationAction) => {
    console.log('Take action:', action);
    action.onClick();
};

const handleDismissRecommendation = async (recommendationId: string) => {
    try {
        if (tenantId) {
            await api.dismissRecommendation(tenantId, recommendationId, token);
        }
    } catch (err) {
        console.error('Failed to dismiss recommendation', err);
    } finally {
        setRecommendations((prev) => prev.filter((r) => r.id !== recommendationId));
    }
};

const handleMetricClick = (metricId: string) => {
    navigate(`/analytics?metric=${encodeURIComponent(metricId)}`);
};

const handleGoalClick = (goalId: string) => {
    navigate(`/goals?goalId=${encodeURIComponent(goalId)}`);
};

const handleTaskClick = (taskId: string) => {
    navigate(`/planner?taskId=${encodeURIComponent(taskId)}`);
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
    <>
        {/* Notification Center - Fixed position bell icon + toast notifications */}
        <NotificationCenter position="top-right" showToasts maxToasts={3} />

        <Container size="xl" py="md">
            <Stack gap="lg">
                {wsError ? (
                    <MantineText size="xs" c="red">
                        Live updates error; reconnecting...
                    </MantineText>
                ) : (
                    <MantineText size="xs" c={wsConnected ? 'green' : 'gray'}>
                        {wsConnected ? 'Live updates connected' : 'Live updates offline; data may be delayed'}
                    </MantineText>
                )}
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
                    <div id="recommendations-section">
                        <Stack gap="md">
                            {recommendations.length === 0 ? (
                                <Card shadow="sm" radius="md" withBorder>
                                    <Stack gap="xs">
                                        <MantineText fw={600}>No coach tips yet</MantineText>
                                        <MantineText c="dimmed" size="sm">
                                            As we analyze your data, proactive tips will appear here.
                                        </MantineText>
                                        <Button variant="light" onClick={handleAskCoach} leftSection={<span>💡</span>}>
                                            Ask the coach now
                                        </Button>
                                    </Stack>
                                </Card>
                            ) : (
                                recommendations.map((rec) => (
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
                    </div>

                    {/* Center: Goals & Tasks */}
                    <div>
                        <Stack gap="xl">
                            <GoalsColumn goals={goals} loading={loading} onGoalClick={handleGoalClick} />
                            {goals.length === 0 && !loading && (
                                <Card shadow="sm" radius="md" withBorder>
                                    <Stack gap="xs">
                                        <MantineText fw={600}>No active goals</MantineText>
                                        <MantineText c="dimmed" size="sm">
                                            Set your first goal to track progress and get focused recommendations.
                                        </MantineText>
                                        <Button variant="gradient" onClick={() => navigate('/goals')} leftSection={<span>🎯</span>}>
                                            Set a goal
                                        </Button>
                                    </Stack>
                                </Card>
                            )}
                            <TasksColumn
                                tasks={tasks}
                                loading={loading}
                                onTaskClick={handleTaskClick}
                                onToggleComplete={handleToggleComplete}
                            />
                            {tasks.length === 0 && !loading && (
                                <Card shadow="sm" radius="md" withBorder>
                                    <Stack gap="xs">
                                        <MantineText fw={600}>No tasks for today</MantineText>
                                        <MantineText c="dimmed" size="sm">
                                            Create a plan to turn insights into action.
                                        </MantineText>
                                        <Button variant="light" onClick={() => navigate('/planner')} leftSection={<span>📝</span>}>
                                            Open Action Plan
                                        </Button>
                                    </Stack>
                                </Card>
                            )}
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
    </>
);
}
