import { useQuery } from '@tanstack/react-query'
import React, { createContext, useContext, useMemo } from 'react'
import { get } from '../lib/api'
import { useAuthStore } from '../stores/auth'

export interface HealthScore {
    score: number
    trend: number
    breakdown: {
        revenue: number
        operations: number
        customer: number
    }
}

export interface Goal {
    id: string
    tenant_id: string
    title: string
    description: string
    current: number
    target: number
    unit: string
    category: 'revenue' | 'operations' | 'customer' | 'growth' | 'custom'
    status: 'active' | 'completed' | 'archived'
    deadline: string
    created_at: string
    updated_at: string
    auto_tracked: boolean
    connector_source?: string
    last_celebrated_milestone?: number
    progress?: number // Calculated
    daysRemaining?: number // Calculated
}

export interface Task {
    id: string
    title: string
    category: string
    status: 'todo' | 'in_progress' | 'completed'
    priority: 'low' | 'medium' | 'high' | 'urgent'
    due_date: string
    horizon: 'daily' | 'weekly' | 'quarterly' | 'yearly'
    goal_id?: string
}

export interface Insight {
    id: string
    type: 'alert' | 'suggestion' | 'success' | 'info'
    message: string
    timestamp: string
    priority: 'low' | 'medium' | 'high'
    actions?: {
        label: string
        path: string
        state?: any
    }[]
    relatedTo?: {
        type: 'goal' | 'task' | 'metric'
        id: string
    }
}

export interface DataSource {
    orders: number
    inventory: number
    customers: number
    hasRealData: boolean
}

export interface FocusArea {
    dimension: 'revenue' | 'operations' | 'customer'
    score: number
    label: string
    suggestions: string[]
}

export interface BusinessContextData {
    // Core Metrics
    healthScore: HealthScore | null
    dataSource: DataSource | null

    // Goals & Tasks
    activeGoals: Goal[]
    offTrackGoals: Goal[]
    completedGoals: Goal[]
    pendingTasks: Task[]
    overdueTasks: Task[]

    // Intelligence
    insights: Insight[]
    focusArea: FocusArea | null

    // Loading States
    isLoading: boolean
    isError: boolean
}

const BusinessContext = createContext<BusinessContextData | undefined>(undefined)

export function BusinessContextProvider({ children }: { children: React.ReactNode }) {
    const tenantId = useAuthStore((s) => s.tenantId)
    const apiToken = useAuthStore((s) => s.apiToken)

    // Fetch health score
    const { data: healthScoreData, isLoading: isLoadingHealth } = useQuery({
        queryKey: ['health-score', tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const response = await get<HealthScore>(`/v1/tenants/${encodeURIComponent(tenantId!)}/health-score`, apiToken)
            return response
        },
        retry: 1,
        staleTime: 5 * 60 * 1000, // 5 minutes
    })

    // Fetch data source info
    const { data: dataSourceData, isLoading: isLoadingDataSource } = useQuery({
        queryKey: ['data-source', tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const response = await get<DataSource>(`/v1/tenants/${encodeURIComponent(tenantId!)}/data-source`, apiToken)
            return response
        },
        retry: 1,
        staleTime: 5 * 60 * 1000,
    })

    // Fetch all active goals
    const { data: goalsData = [], isLoading: isLoadingGoals } = useQuery({
        queryKey: ['goals', tenantId],
        queryFn: () => get<Goal[]>(`/v1/tenants/${tenantId}/goals`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000,
    })

    // Fetch all tasks
    const { data: tasksData = [], isLoading: isLoadingTasks } = useQuery({
        queryKey: ['tasks', tenantId],
        queryFn: () => get<Task[]>(`/v1/tenants/${tenantId}/tasks`, apiToken),
        enabled: !!tenantId && !!apiToken,
        staleTime: 30 * 1000,
    })

    // Compute derived data
    const contextValue = useMemo<BusinessContextData>(() => {
        const now = new Date()

        // Calculate goal metrics
        const goalsWithMetrics = goalsData.map((goal: Goal) => {
            const deadline = new Date(goal.deadline)
            const daysRemaining = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
            const progress = Math.min((goal.current / goal.target) * 100, 100)
            return { ...goal, progress, daysRemaining }
        })

        const activeGoals = goalsWithMetrics.filter(g => g.status === 'active')
        const completedGoals = goalsWithMetrics.filter(g => g.status === 'completed')

        // Off-track goals: < 50% progress with < 30 days remaining
        const offTrackGoals = activeGoals.filter(g =>
            g.daysRemaining! < 30 && g.progress! < 50
        )

        // Task categorization
        const pendingTasks = tasksData.filter(t => t.status !== 'completed')
        const overdueTasks = pendingTasks.filter(t => {
            const dueDate = new Date(t.due_date)
            return dueDate < now
        })

        // Determine focus area (lowest health dimension)
        let focusArea: FocusArea | null = null
        if (healthScoreData?.breakdown) {
            const { revenue, operations, customer } = healthScoreData.breakdown
            const dimensions = [
                { dimension: 'revenue' as const, score: revenue, label: 'Revenue Growth' },
                { dimension: 'operations' as const, score: operations, label: 'Operational Excellence' },
                { dimension: 'customer' as const, score: customer, label: 'Customer Success' },
            ]
            const lowest = dimensions.reduce((min, d) => d.score < min.score ? d : min)

            focusArea = {
                ...lowest,
                suggestions: generateFocusSuggestions(lowest.dimension, lowest.score)
            }
        }

        // Generate insights
        const insights = generateInsights({
            healthScore: healthScoreData ?? null,
            activeGoals,
            offTrackGoals,
            overdueTasks,
            focusArea,
            dataSource: dataSourceData ?? null,
        })

        return {
            healthScore: healthScoreData ?? null,
            dataSource: dataSourceData ?? null,
            activeGoals,
            offTrackGoals,
            completedGoals,
            pendingTasks,
            overdueTasks,
            insights,
            focusArea,
            isLoading: isLoadingHealth || isLoadingGoals || isLoadingTasks || isLoadingDataSource,
            isError: false,
        }
    }, [healthScoreData, goalsData, tasksData, dataSourceData, isLoadingHealth, isLoadingGoals, isLoadingTasks, isLoadingDataSource])

    return <BusinessContext.Provider value={contextValue}>{children}</BusinessContext.Provider>
}

export function useBusinessContext() {
    const context = useContext(BusinessContext)
    if (context === undefined) {
        throw new Error('useBusinessContext must be used within a BusinessContextProvider')
    }
    return context
}

// Helper: Generate focus suggestions based on dimension
function generateFocusSuggestions(dimension: 'revenue' | 'operations' | 'customer', score: number): string[] {
    const suggestions: Record<string, string[]> = {
        revenue: [
            'Review pricing strategy and competitor analysis',
            'Identify top-performing products and upsell opportunities',
            'Analyze customer acquisition cost vs lifetime value',
            'Create promotional campaigns for slow-moving inventory',
        ],
        operations: [
            'Optimize inventory turnover and reduce stock-outs',
            'Streamline order fulfillment process',
            'Implement automated reorder points for key SKUs',
            'Reduce operational costs and improve efficiency',
        ],
        customer: [
            'Improve customer retention and repeat purchase rate',
            'Address negative reviews and customer complaints',
            'Create loyalty program to increase engagement',
            'Personalize customer experience and communication',
        ],
    }

    return suggestions[dimension] || []
}

// Helper: Generate contextual insights
function generateInsights(context: {
    healthScore: HealthScore | null
    activeGoals: Goal[]
    offTrackGoals: Goal[]
    overdueTasks: Task[]
    focusArea: FocusArea | null
    dataSource: DataSource | null
}): Insight[] {
    const insights: Insight[] = []
    let insightId = 1

    // 1. Focus area alert (if health score low)
    if (context.focusArea && context.focusArea.score < 75) {
        insights.push({
            id: `insight-${insightId++}`,
            type: 'alert',
            message: `${context.focusArea.label} needs attention (${context.focusArea.score}/100). This is currently your lowest health dimension.`,
            timestamp: new Date().toISOString(),
            priority: 'high',
            actions: [
                {
                    label: 'Ask AI Coach',
                    path: '/coach',
                    state: { question: `Why is my ${context.focusArea.dimension} health at ${context.focusArea.score}?` }
                },
                {
                    label: 'Set Improvement Goal',
                    path: '/goals',
                    state: { suggest: context.focusArea.dimension }
                },
                {
                    label: 'View Analytics',
                    path: '/analytics',
                    state: { focus: context.focusArea.dimension }
                }
            ],
            relatedTo: { type: 'metric', id: context.focusArea.dimension }
        })
    }

    // 2. Off-track goals alert
    if (context.offTrackGoals.length > 0) {
        const goal = context.offTrackGoals[0]
        insights.push({
            id: `insight-${insightId++}`,
            type: 'alert',
            message: `Goal "${goal.title}" may be off-track. ${Math.round(goal.progress!)}% complete with ${goal.daysRemaining} days remaining.`,
            timestamp: new Date().toISOString(),
            priority: 'high',
            actions: [
                {
                    label: 'Get Help from Coach',
                    path: '/coach',
                    state: { context: `goal-${goal.id}`, question: `How can I get my "${goal.title}" goal back on track?` }
                },
                {
                    label: 'Adjust Goal Timeline',
                    path: '/goals',
                    state: { editGoal: goal.id }
                }
            ],
            relatedTo: { type: 'goal', id: goal.id }
        })
    }

    // 3. Overdue tasks warning
    if (context.overdueTasks.length > 0) {
        const task = context.overdueTasks[0]
        insights.push({
            id: `insight-${insightId++}`,
            type: 'alert',
            message: `You have ${context.overdueTasks.length} overdue task${context.overdueTasks.length > 1 ? 's' : ''}. "${task.title}" needs attention.`,
            timestamp: new Date().toISOString(),
            priority: 'medium',
            actions: [
                {
                    label: 'Break Down Task',
                    path: '/coach',
                    state: { question: `Help me break down this task: "${task.title}"` }
                },
                {
                    label: 'View All Tasks',
                    path: '/',
                    state: { scrollTo: 'planner' }
                }
            ],
            relatedTo: { type: 'task', id: task.id }
        })
    }

    // 4. No goals suggestion
    if (context.activeGoals.length === 0 && context.focusArea) {
        insights.push({
            id: `insight-${insightId++}`,
            type: 'suggestion',
            message: `You don't have any active goals. Based on your ${context.focusArea.dimension} health (${context.focusArea.score}/100), consider setting improvement targets.`,
            timestamp: new Date().toISOString(),
            priority: 'medium',
            actions: [
                {
                    label: 'Create Your First Goal',
                    path: '/goals',
                    state: { suggest: context.focusArea.dimension }
                },
                {
                    label: 'Get Goal Ideas from Coach',
                    path: '/coach',
                    state: { question: 'What goals should I set for my business?' }
                }
            ]
        })
    }

    // 5. Data connection reminder (if using sample data)
    if (context.dataSource && !context.dataSource.hasRealData) {
        insights.push({
            id: `insight-${insightId++}`,
            type: 'info',
            message: `You're viewing sample data (${context.dataSource.orders} orders, ${context.dataSource.inventory} items). Connect your real data sources for personalized insights.`,
            timestamp: new Date().toISOString(),
            priority: 'low',
            actions: [
                {
                    label: 'Connect Data Sources',
                    path: '/connectors',
                },
                {
                    label: 'Learn More',
                    path: '/coach',
                    state: { question: 'What data sources can I connect?' }
                }
            ]
        })
    }

    // 6. Success/Progress celebration
    if (context.activeGoals.some(g => g.progress! >= 75)) {
        const highProgressGoals = context.activeGoals.filter(g => g.progress! >= 75)
        const goal = highProgressGoals[0]
        insights.push({
            id: `insight-${insightId++}`,
            type: 'success',
            message: `Great progress! "${goal.title}" is ${Math.round(goal.progress!)}% complete. Keep up the momentum! 🎉`,
            timestamp: new Date().toISOString(),
            priority: 'low',
            actions: [
                {
                    label: 'View Progress',
                    path: '/analytics',
                    state: { goalId: goal.id }
                },
                {
                    label: 'Plan Next Steps',
                    path: '/coach',
                    state: { question: `What should I focus on next for "${goal.title}"?` }
                }
            ],
            relatedTo: { type: 'goal', id: goal.id }
        })
    }

    return insights
}
