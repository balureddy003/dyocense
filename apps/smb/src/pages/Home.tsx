import { Container, Stack, Text, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import AICopilotInsights from '../components/AICopilotInsights'
import BusinessHealthScore from '../components/BusinessHealthScore'
import DailySnapshot from '../components/DailySnapshot'
import GoalProgress from '../components/GoalProgress'
import WeeklyPlan from '../components/WeeklyPlan'
import { useAuthStore } from '../stores/auth'
import { calculateHealthScore, getBusinessMetricsFromConnectors } from '../utils/healthScore'
import { generateMultiGoalWeeklyPlan, type Goal as PlanGoal } from '../utils/planGenerator'

export default function Home() {
    const user = useAuthStore((s) => s.user)
    const [healthScore, setHealthScore] = useState({ score: 0, trend: 0 })
    const [weeklyTasks, setWeeklyTasks] = useState<any[]>([])

    // Mock goals for CycloneRake.com
    const mockGoals: PlanGoal[] = [
        {
            id: '1',
            title: 'Seasonal Revenue Boost',
            description: 'Increase Q4 revenue by 25% through holiday promotions and new product launches',
            current: 78500,
            target: 100000,
            unit: 'USD',
            category: 'revenue',
            deadline: '2025-12-01',
        },
        {
            id: '2',
            title: 'Inventory Optimization',
            description: 'Improve inventory turnover rate to reduce holding costs and prevent stockouts',
            current: 87,
            target: 95,
            unit: '% Turnover',
            category: 'operations',
            deadline: '2025-12-10',
        },
        {
            id: '3',
            title: 'Customer Retention',
            description: 'Build loyalty program to increase repeat customer rate from 28% to 35%',
            current: 142,
            target: 200,
            unit: 'Repeat Customers',
            category: 'customer',
            deadline: '2025-11-24',
        },
    ]

    // Calculate real health score from connector data
    useEffect(() => {
        const loadHealthScore = async () => {
            const metrics = await getBusinessMetricsFromConnectors()
            const result = calculateHealthScore(metrics)
            setHealthScore({
                score: result.overallScore,
                trend: 5, // TODO: Calculate trend from historical data
            })
        }
        loadHealthScore()
    }, [])

    // Generate AI-powered weekly tasks from goals
    useEffect(() => {
        const plans = generateMultiGoalWeeklyPlan(mockGoals)
        const allTasks = plans.flatMap((plan) => plan.tasks)

        // Convert to WeeklyPlan component format
        const formattedTasks = allTasks.slice(0, 5).map((task) => ({
            id: task.id,
            title: task.title,
            category: task.category,
            completed: false,
        }))

        setWeeklyTasks(formattedTasks)
    }, [])

    const mockHealthScore = healthScore

    const mockMetrics = {
        revenue: { value: '$12,450', trend: 8 },
        orders: { value: '47', trend: 12 },
        fillRate: { value: '94%', trend: -2 },
        rating: { value: '4.8', trend: 3 },
    }

    // Convert goals to component format with days remaining
    const mockGoalsForDisplay = mockGoals.map((goal) => {
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

    const mockTasks = weeklyTasks.length > 0 ? weeklyTasks : [
        { id: '1', title: 'Review GrandNode abandoned carts', category: 'Sales', completed: true },
        { id: '2', title: 'Update Kennedy ERP inventory levels', category: 'Operations', completed: true },
        { id: '3', title: 'Analyze top-selling outdoor gear', category: 'Analytics', completed: false },
        { id: '4', title: 'Follow up with wholesale customers', category: 'Sales', completed: false },
        { id: '5', title: 'Optimize product recommendations', category: 'Marketing', completed: false },
    ]

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
                    <Text size="xs" c="neutral.600" fw={500} tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                        Business Fitness Dashboard
                    </Text>
                    <Title order={1} size="h2" c="neutral.900" mt={4}>
                        Welcome back, {user?.name || 'Business Owner'} 👋
                    </Title>
                    <Text size="sm" c="neutral.600" mt={4}>
                        CycloneRake.com • Outdoor Equipment E-commerce
                    </Text>
                </div>

                {/* Business Health Score - Apple Fitness Ring Style */}
                <BusinessHealthScore score={mockHealthScore.score} trend={mockHealthScore.trend} />

                {/* Daily Snapshot - 4 Metric Cards */}
                <DailySnapshot metrics={mockMetrics} />

                {/* Two Column Layout on Desktop */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Left Column */}
                    <Stack gap="xl">
                        {/* Active Goals */}
                        <GoalProgress goals={mockGoalsForDisplay} />

                        {/* Weekly Plan */}
                        <WeeklyPlan tasks={mockTasks} />
                    </Stack>

                    {/* Right Column */}
                    <Stack gap="xl">
                        {/* AI Copilot Insights */}
                        <AICopilotInsights insights={mockInsights} />
                    </Stack>
                </div>
            </Stack>
        </Container>
    )
}
