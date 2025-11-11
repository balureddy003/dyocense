import { Button, Container, Stack, Text, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
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
    const navigate = useNavigate()

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

    // Fetch connectors to check if user has data connected
    const { data: connectorsData = [] } = useQuery({
        queryKey: ['connectors', tenantId],
        queryFn: () => get(`/v1/tenants/${tenantId}/connectors`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000,
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

    // Derive metrics from health score breakdown if available
    const metrics = healthScoreData?.breakdown ? {
        revenue: {
            value: '$—',
            trend: Math.round((healthScoreData.breakdown.revenue - 50) / 5)
        },
        orders: {
            value: '—',
            trend: 0
        },
        fillRate: {
            value: '—%',
            trend: Math.round((healthScoreData.breakdown.operations - 50) / 5)
        },
        rating: {
            value: '—',
            trend: Math.round((healthScoreData.breakdown.customer - 50) / 5)
        },
    } : null

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

    // Check if user has any data connected
    const hasDataConnected = connectorsData && connectorsData.length > 0
    const hasCompletedOnboarding = typeof window !== 'undefined' && localStorage.getItem('hasCompletedOnboarding') === 'true'

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
                        Your AI Fitness Coach for Business Growth
                    </Text>
                </div>

                {/* Empty State - No Data Connected */}
                {!hasDataConnected && hasCompletedOnboarding && !isLoadingHealthScore ? (
                    <div className="rounded-3xl border-2 border-dashed border-brand-200 bg-gradient-to-br from-brand-50/30 to-violet-50/30 p-12 text-center">
                        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brand-100">
                            <span className="text-4xl">🏋️</span>
                        </div>
                        <Title order={2} mb="md" c="gray.9">
                            Ready to get your business in shape?
                        </Title>
                        <Text size="lg" c="gray.6" mb="xl" maw={600} mx="auto">
                            <strong>Dyocense is your AI Fitness Coach for business.</strong> Just like a fitness tracker monitors your health rings,
                            we track your Revenue, Operations, and Customer health in real-time.
                        </Text>
                        <Text size="md" c="gray.7" mb="xl" maw={560} mx="auto">
                            <strong>First step:</strong> Connect your data sources (ERP, POS, or CSV files) so we can calculate your Business Health Score
                            and create your personalized action plan.
                        </Text>
                        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                            <Button
                                size="lg"
                                leftSection={<span>🔗</span>}
                                onClick={() => navigate('/connectors')}
                                variant="gradient"
                                gradient={{ from: 'brand', to: 'violet', deg: 90 }}
                            >
                                Connect your first data source
                            </Button>
                            <Button
                                size="lg"
                                variant="light"
                                leftSection={<span>💡</span>}
                                onClick={() => navigate('/coach')}
                            >
                                Talk to your AI Coach
                            </Button>
                        </div>
                        <Text size="sm" c="gray.5" mt="xl">
                            💡 <strong>Pro tip:</strong> Start with a CSV export of your sales data to see instant insights
                        </Text>
                    </div>
                ) : (
                    <>
                        {/* Business Health Score - Apple Fitness Ring Style */}
                        <BusinessHealthScore
                            score={healthScore.score}
                            trend={healthScore.trend}
                            breakdown={healthScoreData?.breakdown}
                        />

                        {/* Daily Snapshot - Only show if we have metrics */}
                        {metrics && <DailySnapshot metrics={metrics} />}

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
                    </>
                )}
            </Stack>
        </Container>
    )
}
