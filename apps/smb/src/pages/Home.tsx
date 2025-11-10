import { Container, Stack, Text, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import BusinessHealthScore from '../components/BusinessHealthScore'
import DailySnapshot from '../components/DailySnapshot'
import GoalProgress from '../components/GoalProgress'
import MultiHorizonPlanner from '../components/MultiHorizonPlanner'
import SmartInsights from '../components/SmartInsights'
import StreakCounter from '../components/StreakCounter'
import { get } from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { type Goal as PlanGoal } from '../utils/planGenerator'

export default function Home() {
    const user = useAuthStore((s) => s.user)
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)

    // Fetch real health score from backend
    const { data: healthScoreData, isLoading: isLoadingHealthScore } = useQuery({
        queryKey: ['health-score', tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const response = await get<{
                score: number
                trend: number
                breakdown: {
                    revenue: number
                    operations: number
                    customer: number
                }
            }>(`/v1/tenants/${encodeURIComponent(tenantId!)}/health-score`, apiToken)
            return response
        },
        retry: 1,
        staleTime: 5 * 60 * 1000, // 5 minutes
    })

    // Fetch goals from API
    const { data: goalsData = [] } = useQuery({
        queryKey: ['goals', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/goals?status=active`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000, // 30 seconds
    })

    // Convert API goals to PlanGoal format
    const goals: PlanGoal[] = goalsData.map((goal: any) => ({
        id: goal.id,
        title: goal.title,
        description: goal.description,
        current: goal.current,
        target: goal.target,
        unit: goal.unit,
        category: goal.category,
        deadline: goal.deadline,
    }))

    // Fetch tasks from API for different horizons
    const { data: dailyTasksData = [] } = useQuery({
        queryKey: ['tasks', 'daily', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/tasks?status=todo&horizon=daily&limit=5`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000,
    })

    const { data: weeklyTasksData = [] } = useQuery({
        queryKey: ['tasks', 'weekly', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/tasks?status=todo&horizon=weekly&limit=5`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000,
    })

    const { data: quarterlyTasksData = [] } = useQuery({
        queryKey: ['tasks', 'quarterly', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/tasks?status=todo&horizon=quarterly&limit=5`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000,
    })

    const { data: yearlyTasksData = [] } = useQuery({
        queryKey: ['tasks', 'yearly', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/tasks?status=todo&horizon=yearly&limit=5`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000,
    })

    // Use real health score data or default values while loading
    const healthScore = {
        score: healthScoreData?.score ?? 0,
        trend: healthScoreData?.trend ?? 0,
    }

    const mockMetrics = {
        revenue: { value: '$12,450', trend: healthScoreData?.breakdown?.revenue ? Math.round((healthScoreData.breakdown.revenue - 50) / 5) : 8 },
        orders: { value: '47', trend: 12 },
        fillRate: { value: '94%', trend: healthScoreData?.breakdown?.operations ? Math.round((healthScoreData.breakdown.operations - 50) / 5) : -2 },
        rating: { value: '4.8', trend: healthScoreData?.breakdown?.customer ? Math.round((healthScoreData.breakdown.customer - 50) / 5) : 3 },
    }

    // Convert goals to component format with days remaining
    const goalsForDisplay = goals.map((goal: PlanGoal) => {
        const deadline = new Date(goal.deadline)
        const today = new Date()
        const daysRemaining = Math.ceil((deadline.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

        return {
            id: goal.id,
            title: goal.title,
            current: goal.current,
            target: goal.target,
            unit: goal.unit,
            daysRemaining,
        }
    })

    // Convert API tasks to component format for each horizon
    const convertTasks = (tasksData: any[]) => tasksData.map((task: any) => ({
        id: task.id,
        title: task.title,
        category: task.category,
        completed: task.status === 'completed',
        due_date: task.due_date,
        priority: task.priority,
    }))

    const dailyTasks = convertTasks(dailyTasksData)
    const weeklyTasks = convertTasks(weeklyTasksData)
    const quarterlyTasks = convertTasks(quarterlyTasksData)
    const yearlyTasks = convertTasks(yearlyTasksData)

    const mockInsights = [
        {
            id: '1',
            message:
                'Cart abandonment rate is up 18% this week. Consider sending personalized follow-up emails to recover sales.',
            type: 'alert' as const,
            timestamp: '2 hours ago',
        },
        {
            id: '2',
            message:
                'Your best-selling camping gear (tents, sleeping bags) are running low. Reorder from supplier to avoid stockouts.',
            type: 'suggestion' as const,
            timestamp: '5 hours ago',
        },
    ]

    return (
        <Container size="xl" className="py-6">
            <Stack gap="xl">
                {/* Header */}
                <div>
                    <Text size="xs" c="gray.6" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                        Business Fitness Dashboard
                    </Text>
                    <Title order={1} size="h2" c="gray.9" mt={4}>
                        Welcome back, {user?.name || 'Business Owner'} 👋
                    </Title>
                    <Text size="sm" c="gray.6" mt={4}>
                        CycloneRake.com • Outdoor Equipment E-commerce
                    </Text>
                </div>

                {/* Business Health Score - Apple Fitness Ring Style */}
                <BusinessHealthScore
                    score={healthScore.score}
                    trend={healthScore.trend}
                    breakdown={healthScoreData?.breakdown}
                />

                {/* Daily Snapshot - 4 Metric Cards */}
                <DailySnapshot metrics={mockMetrics} />

                {/* Two Column Layout on Desktop */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Left Column */}
                    <Stack gap="xl">
                        {/* Active Goals */}
                        <GoalProgress goals={goalsForDisplay} />

                        {/* Multi-Horizon Planner */}
                        <MultiHorizonPlanner
                            dailyTasks={dailyTasks}
                            weeklyTasks={weeklyTasks}
                            quarterlyTasks={quarterlyTasks}
                            yearlyTasks={yearlyTasks}
                            defaultHorizon="weekly"
                        />
                    </Stack>

                    {/* Right Column */}
                    <Stack gap="xl">
                        {/* Streak Counter */}
                        <StreakCounter variant="detailed" />

                        {/* Smart AI Insights - Context-Aware */}
                        <SmartInsights />
                    </Stack>
                </div>
            </Stack>
        </Container>
    )
}
