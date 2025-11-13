/**
 * Type definitions for Coach V6 - Fitness Dashboard
 */

export interface HealthScore {
    score: number;
    previousScore: number;
    change: number;
    trend: 'up' | 'down' | 'stable';
    components: HealthScoreComponents;
    lastUpdated: Date;
}

export interface HealthScoreComponents {
    cashFlow: ComponentScore;
    revenue: ComponentScore;
    profitability: ComponentScore;
    operationalEfficiency: ComponentScore;
}

export interface ComponentScore {
    score: number;
    change: number;
    weight: number; // Percentage weight in overall score
}

export interface Alert {
    id: string;
    type: 'critical' | 'warning' | 'info';
    title: string;
    description: string;
    metric?: string;
    value?: number | string;
    threshold?: number | string;
    action?: AlertAction;
}

export interface AlertAction {
    label: string;
    onClick: () => void;
}

export interface Signal {
    id: string;
    type: 'positive' | 'neutral';
    title: string;
    description: string;
    metric?: string;
    value?: number | string;
    icon?: string;
}

export interface CoachRecommendation {
    id: string;
    priority: 'critical' | 'important' | 'suggestion';
    title: string;
    description: string;
    reasoning?: string;
    actions: RecommendationAction[];
    dismissible: boolean;
    dismissed: boolean;
    createdAt: Date;
    generatedAt: Date;
    expiresAt?: Date;
    metadata?: {
        relatedGoalId?: string;
        relatedTaskIds?: string[];
        dataSource?: string;
        confidence?: number;
    };
}

export interface RecommendationAction {
    id: string;
    label: string;
    description?: string;
    buttonText: string;
    variant: 'primary' | 'secondary' | 'tertiary';
    onClick: () => void | Promise<void>;
    loading?: boolean;
    completed?: boolean;
}

export interface MetricSnapshot {
    id: string;
    label: string;
    value: number | string;
    change: number;
    changeType: 'percentage' | 'absolute';
    trend: 'up' | 'down' | 'stable';
    sparklineData?: number[];
    period?: string;
    format?: 'currency' | 'number' | 'percentage';
}

export interface GoalWithProgress {
    id: string;
    title: string;
    description?: string;
    target: number;
    current: number;
    targetValue: number;
    currentValue: number;
    progress: number; // Percentage 0-100
    deadline?: Date;
    dueDate?: Date;
    daysRemaining?: number;
    status: 'on_track' | 'at_risk' | 'off_track' | 'completed';
    priority: 'high' | 'medium' | 'low';
    category?: string;
    sparklineData?: number[];
}

export interface TaskWithPriority {
    id: string;
    title: string;
    description?: string;
    status: 'pending' | 'todo' | 'in_progress' | 'completed' | 'blocked';
    priority: 'urgent' | 'high' | 'medium' | 'low';
    dueDate?: Date;
    isOverdue: boolean;
    completed: boolean;
    goalId?: string;
    goalTitle?: string;
    assignee?: string;
    tags?: string[];
    source?: 'user' | 'coach' | 'system';
    createdAt?: Date;
}

export interface HealthScoreHeaderProps {
    score: number;
    previousScore: number;
    trend: 'up' | 'down' | 'stable';
    changeAmount: number;
    criticalAlerts: Alert[];
    positiveSignals: Signal[];
    onViewReport: () => void;
    onAskCoach: () => void;
    loading?: boolean;
}

export interface ProactiveCoachCardProps {
    recommendation: CoachRecommendation;
    onTakeAction: (action: RecommendationAction) => void;
    onDismiss: (id: string) => void;
    loading?: boolean;
}

export interface MetricsGridProps {
    metrics: MetricSnapshot[];
    loading?: boolean;
    onMetricClick?: (metricId: string) => void;
}

export interface GoalsColumnProps {
    goals: GoalWithProgress[];
    loading?: boolean;
    onGoalClick?: (goalId: string) => void;
    onCreateGoal?: () => void;
}

export interface TasksColumnProps {
    tasks: TaskWithPriority[];
    loading?: boolean;
    onToggleComplete?: (taskId: string) => void;
    onTaskClick?: (taskId: string) => void;
    onCreateTask?: () => void;
}

// API Response Types
export interface HealthScoreTrendResponse {
    current_score: number;
    previous_score: number;
    change: number;
    trend_data: Array<{
        date: string;
        score: number;
    }>;
    components: {
        cash_flow: {
            score: number;
            change: number;
        };
        revenue: {
            score: number;
            change: number;
        };
        profitability: {
            score: number;
            change: number;
        };
        operational_efficiency: {
            score: number;
            change: number;
        };
    };
}

export interface CoachRecommendationsResponse {
    recommendations: Array<{
        id: string;
        priority: 'critical' | 'important' | 'suggestion';
        title: string;
        description: string;
        reasoning?: string;
        actions: Array<{
            id: string;
            label: string;
            type: string;
            params?: Record<string, any>;
        }>;
        created_at: string;
        expires_at?: string;
        metadata?: Record<string, any>;
    }>;
}

// View State Types
export type CenterView = 'overview' | 'action-steps' | 'tasks';
export type EvidenceView = 'sources' | 'reports' | 'graphs';

export interface CoachV6State {
    healthScore: HealthScore | null;
    recommendations: CoachRecommendation[];
    dismissedRecommendations: string[];
    metrics: MetricSnapshot[];
    goals: GoalWithProgress[];
    tasks: TaskWithPriority[];
    centerView: CenterView;
    evidenceView: EvidenceView;
    showLeftPlane: boolean;
    showRightPlane: boolean;
    loading: {
        healthScore: boolean;
        recommendations: boolean;
        metrics: boolean;
        goals: boolean;
        tasks: boolean;
    };
}
