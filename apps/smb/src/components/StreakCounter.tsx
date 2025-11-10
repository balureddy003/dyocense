import { Badge, Card, Group, RingProgress, Stack, Text, Tooltip } from '@mantine/core'
import { IconFlame, IconTrophy } from '@tabler/icons-react'
import { useEffect, useState } from 'react'

interface StreakData {
    currentStreak: number // Weeks in a row
    longestStreak: number
    totalWeeksCompleted: number
    lastCompletedWeek: string // ISO date
    weeklyCompletionRate: number // 0-100
}

interface StreakCounterProps {
    variant?: 'compact' | 'detailed'
    onStreakUpdate?: (streak: StreakData) => void
}

const STREAK_STORAGE_KEY = 'dyocense_streak_data'

/**
 * StreakCounter component - Gamified weekly task completion tracking
 * 
 * Persistence: localStorage
 * Update trigger: Weekly task completion (5/5 tasks)
 * Display: Flame icon + week count + ring progress
 */
export default function StreakCounter({ variant = 'detailed', onStreakUpdate }: StreakCounterProps) {
    const [streakData, setStreakData] = useState<StreakData>({
        currentStreak: 0,
        longestStreak: 0,
        totalWeeksCompleted: 0,
        lastCompletedWeek: '',
        weeklyCompletionRate: 0,
    })

    // Load streak data from localStorage
    useEffect(() => {
        const stored = localStorage.getItem(STREAK_STORAGE_KEY)
        if (stored) {
            try {
                const parsed = JSON.parse(stored)
                setStreakData(parsed)
            } catch (error) {
                console.error('Failed to parse streak data:', error)
            }
        }
    }, [])

    // Save streak data when it changes
    useEffect(() => {
        if (streakData.totalWeeksCompleted > 0) {
            localStorage.setItem(STREAK_STORAGE_KEY, JSON.stringify(streakData))
            onStreakUpdate?.(streakData)
        }
    }, [streakData, onStreakUpdate])

    const getStreakColor = (weeks: number) => {
        if (weeks >= 8) return 'orange.6' // 2 months
        if (weeks >= 4) return 'orange.5' // 1 month
        if (weeks >= 2) return 'orange.4'
        if (weeks >= 1) return 'orange.3'
        return 'gray.5'
    }

    const getStreakMessage = (weeks: number) => {
        if (weeks === 0) return 'Complete your first week!'
        if (weeks === 1) return 'Great start! Keep going!'
        if (weeks === 2) return 'Building momentum!'
        if (weeks === 4) return '1 month streak! 🎉'
        if (weeks === 8) return '2 months! Incredible!'
        if (weeks === 12) return '3 months! You\'re unstoppable!'
        return `${weeks} weeks strong!`
    }

    const getBadgeVariant = (weeks: number) => {
        if (weeks >= 12) return 'filled' // 3+ months
        if (weeks >= 8) return 'light' // 2+ months
        if (weeks >= 4) return 'outline' // 1+ month
        return 'subtle'
    }

    if (variant === 'compact') {
        return (
            <Tooltip label={getStreakMessage(streakData.currentStreak)} withArrow>
                <Group gap="xs">
                    <IconFlame
                        size={20}
                        color={streakData.currentStreak > 0 ? '#F76707' : '#ADB5BD'}
                        fill={streakData.currentStreak > 0 ? '#F76707' : 'none'}
                    />
                    <Text size="sm" fw={600} c={getStreakColor(streakData.currentStreak)}>
                        {streakData.currentStreak}
                    </Text>
                    <Text size="xs" c="dimmed">
                        {streakData.currentStreak === 1 ? 'week' : 'weeks'}
                    </Text>
                </Group>
            </Tooltip>
        )
    }

    return (
        <Card withBorder radius="md" p="lg">
            <Stack gap="md">
                <Group justify="space-between">
                    <Group gap="xs">
                        <IconFlame
                            size={24}
                            color={streakData.currentStreak > 0 ? '#F76707' : '#ADB5BD'}
                            fill={streakData.currentStreak > 0 ? '#F76707' : 'none'}
                        />
                        <div>
                            <Text size="sm" fw={600} c="neutral.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                                Current Streak
                            </Text>
                            <Text size="xs" c="dimmed">
                                Weeks completing your plan
                            </Text>
                        </div>
                    </Group>
                    {streakData.longestStreak > 0 && streakData.longestStreak > streakData.currentStreak && (
                        <Tooltip label={`Your record: ${streakData.longestStreak} weeks`}>
                            <Badge
                                leftSection={<IconTrophy size={14} />}
                                variant="light"
                                color="yellow"
                                size="sm"
                            >
                                Best: {streakData.longestStreak}
                            </Badge>
                        </Tooltip>
                    )}
                </Group>

                <Group gap="xl" align="center">
                    {/* Ring Progress */}
                    <RingProgress
                        size={120}
                        thickness={12}
                        sections={[
                            {
                                value: Math.min((streakData.currentStreak / 12) * 100, 100),
                                color: streakData.currentStreak >= 12 ? 'orange' : 'orange.4'
                            },
                        ]}
                        label={
                            <div style={{ textAlign: 'center' }}>
                                <Text size="xl" fw={700} c={getStreakColor(streakData.currentStreak)}>
                                    {streakData.currentStreak}
                                </Text>
                                <Text size="xs" c="dimmed">
                                    {streakData.currentStreak === 1 ? 'week' : 'weeks'}
                                </Text>
                            </div>
                        }
                    />

                    {/* Stats */}
                    <Stack gap="xs" style={{ flex: 1 }}>
                        <div>
                            <Text size="xs" c="dimmed">Status</Text>
                            <Badge
                                variant={getBadgeVariant(streakData.currentStreak)}
                                color="orange"
                                size="lg"
                                mt={4}
                            >
                                {getStreakMessage(streakData.currentStreak)}
                            </Badge>
                        </div>

                        <div>
                            <Text size="xs" c="dimmed">Total weeks completed</Text>
                            <Text size="sm" fw={600} c="neutral.9" mt={2}>
                                {streakData.totalWeeksCompleted}
                            </Text>
                        </div>

                        {streakData.weeklyCompletionRate > 0 && (
                            <div>
                                <Text size="xs" c="dimmed">Avg. completion rate</Text>
                                <Text size="sm" fw={600} c="teal.6" mt={2}>
                                    {Math.round(streakData.weeklyCompletionRate)}%
                                </Text>
                            </div>
                        )}
                    </Stack>
                </Group>

                {streakData.currentStreak === 0 && streakData.totalWeeksCompleted > 0 && (
                    <Text size="xs" c="orange.6" ta="center">
                        💪 You had a {streakData.longestStreak}-week streak! Start a new one this week.
                    </Text>
                )}
            </Stack>
        </Card>
    )
}

/**
 * Utility function to update streak when a week is completed
 * Call this when user completes all weekly tasks (5/5)
 */
export function updateStreak(completedTasks: number, totalTasks: number) {
    if (completedTasks !== totalTasks) return // Only count 100% completion

    const stored = localStorage.getItem(STREAK_STORAGE_KEY)
    let streakData: StreakData = {
        currentStreak: 0,
        longestStreak: 0,
        totalWeeksCompleted: 0,
        lastCompletedWeek: '',
        weeklyCompletionRate: 0,
    }

    if (stored) {
        try {
            streakData = JSON.parse(stored)
        } catch (error) {
            console.error('Failed to parse streak data:', error)
        }
    }

    const now = new Date()
    const currentWeekStart = getWeekStart(now)
    const lastWeekStart = streakData.lastCompletedWeek ? new Date(streakData.lastCompletedWeek) : null

    // Check if this is a new week completion
    if (!lastWeekStart || currentWeekStart.getTime() !== lastWeekStart.getTime()) {
        const weeksSinceLastCompletion = lastWeekStart
            ? Math.floor((currentWeekStart.getTime() - lastWeekStart.getTime()) / (7 * 24 * 60 * 60 * 1000))
            : 0

        // If consecutive week, increment streak; otherwise reset to 1
        if (weeksSinceLastCompletion === 1) {
            streakData.currentStreak += 1
        } else if (weeksSinceLastCompletion > 1) {
            streakData.currentStreak = 1 // Reset streak
        } else {
            streakData.currentStreak = 1 // First time
        }

        // Update longest streak
        if (streakData.currentStreak > streakData.longestStreak) {
            streakData.longestStreak = streakData.currentStreak
        }

        streakData.totalWeeksCompleted += 1
        streakData.lastCompletedWeek = currentWeekStart.toISOString()

        // Calculate average completion rate (simplified - could track each week's rate)
        streakData.weeklyCompletionRate = 100 // Assume 100% since we only count full completions

        localStorage.setItem(STREAK_STORAGE_KEY, JSON.stringify(streakData))

        return streakData
    }

    return streakData
}

/**
 * Get the start of the current week (Monday)
 */
function getWeekStart(date: Date): Date {
    const d = new Date(date)
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1) // Adjust when day is Sunday
    return new Date(d.setDate(diff))
}

/**
 * Reset streak data (for testing or user request)
 */
export function resetStreak() {
    localStorage.removeItem(STREAK_STORAGE_KEY)
}
