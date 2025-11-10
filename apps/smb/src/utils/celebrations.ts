import { notifications } from '@mantine/notifications'
import confetti from 'canvas-confetti'

/**
 * Celebration utilities for engaging business fitness coaching experience.
 * Uses Mantine notifications + canvas-confetti for visual feedback.
 */

// === GOAL MILESTONE CELEBRATIONS ===

export function celebrateGoalMilestone(goalTitle: string, percentage: number) {
    // Visual celebration with confetti
    confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#6366F1', '#818CF8', '#A5B4FC'],
    })

    // In-app notification
    const messages = {
        25: '🎯 Quarter way there! Keep the momentum going.',
        50: '🔥 Halfway! You\'re crushing it!',
        75: '💪 Almost there! Final push!',
        100: '🎉 GOAL CRUSHED! You did it!',
    }

    notifications.show({
        title: percentage === 100 ? '🏆 Goal Complete!' : `${percentage}% Complete!`,
        message: messages[percentage as keyof typeof messages] || `${goalTitle} is ${percentage}% done`,
        color: percentage === 100 ? 'green' : 'blue',
        autoClose: 5000,
    })
}

// === TASK COMPLETION CELEBRATIONS ===

export function celebrateTaskCompletion(tasksCompleted: number, totalTasks: number) {
    if (tasksCompleted === totalTasks) {
        // Week complete - big celebration
        confetti({
            particleCount: 150,
            spread: 90,
            origin: { y: 0.5 },
            colors: ['#6366F1', '#10B981', '#F59E0B'],
        })

        notifications.show({
            title: '🏆 Week Complete!',
            message: `You crushed all ${totalTasks} tasks this week. Amazing work!`,
            color: 'green',
            autoClose: 7000,
        })
    } else if (tasksCompleted > 0) {
        // Individual task completion
        notifications.show({
            title: '✅ Task Complete',
            message: `${tasksCompleted}/${totalTasks} tasks done this week`,
            color: 'teal',
            autoClose: 3000,
        })
    }
}

// === HEALTH SCORE IMPROVEMENTS ===

export function celebrateHealthScoreImprovement(oldScore: number, newScore: number) {
    const improvement = newScore - oldScore

    if (improvement >= 10) {
        // Big improvement
        confetti({
            particleCount: 120,
            spread: 80,
            origin: { y: 0.6 },
        })

        notifications.show({
            title: '📈 Major Improvement!',
            message: `Your health score jumped +${improvement} points! Keep it up!`,
            color: 'green',
            autoClose: 5000,
        })
    } else if (improvement >= 5) {
        // Moderate improvement
        notifications.show({
            title: '📊 Score Improved',
            message: `Health score +${improvement}. Great progress!`,
            color: 'blue',
            autoClose: 4000,
        })
    } else if (improvement > 0) {
        // Small improvement
        notifications.show({
            title: '✨ Moving Up',
            message: `Health score +${improvement}`,
            color: 'teal',
            autoClose: 3000,
        })
    }
}

// === STREAK TRACKING ===

export function celebrateStreak(weeks: number) {
    if (weeks === 1) {
        notifications.show({
            title: '🔥 Streak Started!',
            message: 'First week complete. Let\'s build momentum!',
            color: 'orange',
            autoClose: 4000,
        })
    } else if (weeks === 4) {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
        })

        notifications.show({
            title: '🔥 1 Month Streak!',
            message: 'You\'ve been crushing it for 4 weeks straight!',
            color: 'orange',
            autoClose: 5000,
        })
    } else if (weeks % 8 === 0) {
        // Every 2 months
        confetti({
            particleCount: 150,
            spread: 90,
            origin: { y: 0.5 },
        })

        notifications.show({
            title: `🔥 ${weeks} Week Streak!`,
            message: 'Incredible consistency! You\'re building something special.',
            color: 'orange',
            autoClose: 6000,
        })
    } else {
        notifications.show({
            title: `🔥 ${weeks} Week Streak`,
            message: 'Keep the momentum going!',
            color: 'orange',
            autoClose: 3000,
        })
    }
}

// === NUDGES & REMINDERS ===

export function nudgeInactiveUser(daysSinceLastLogin: number) {
    if (daysSinceLastLogin === 3) {
        notifications.show({
            title: '👋 We miss you!',
            message: 'It\'s been 3 days. Check your progress?',
            color: 'yellow',
            autoClose: false, // Keep open until user clicks
        })
    } else if (daysSinceLastLogin === 7) {
        notifications.show({
            title: '📉 Don\'t lose momentum',
            message: 'It\'s been a week. Your coach is waiting!',
            color: 'orange',
            autoClose: false,
        })
    }
}

export function remindDailyTask() {
    notifications.show({
        title: '📋 Daily Check-In',
        message: 'Good morning! Ready to tackle today\'s top task?',
        color: 'blue',
        autoClose: 5000,
    })
}

// === WEEKLY SUMMARY ===

export function showWeeklySummary(data: {
    tasksCompleted: number
    totalTasks: number
    healthScoreDelta: number
    goalsUpdated: number
}) {
    const { tasksCompleted, totalTasks, healthScoreDelta, goalsUpdated } = data
    const completionRate = Math.round((tasksCompleted / totalTasks) * 100)

    const summary = [
        `✅ ${tasksCompleted}/${totalTasks} tasks (${completionRate}%)`,
        healthScoreDelta > 0 ? `📈 Health score +${healthScoreDelta}` : `📊 Health score ${healthScoreDelta}`,
        goalsUpdated > 0 ? `🎯 ${goalsUpdated} goal${goalsUpdated > 1 ? 's' : ''} progressed` : '',
    ]
        .filter(Boolean)
        .join('\n')

    notifications.show({
        title: '📊 Your Week in Review',
        message: summary,
        color: completionRate >= 80 ? 'green' : completionRate >= 50 ? 'blue' : 'yellow',
        autoClose: 8000,
    })
}

// === ALERT NOTIFICATIONS ===

export function alertMetricDrop(metricName: string, dropPercentage: number) {
    notifications.show({
        title: '⚠️ Metric Alert',
        message: `${metricName} dropped ${dropPercentage}% this week. Check your plan for actions.`,
        color: 'red',
        autoClose: false,
    })
}

export function alertGoalOffTrack(goalTitle: string, daysRemaining: number) {
    notifications.show({
        title: '🚨 Goal Needs Attention',
        message: `${goalTitle} - ${daysRemaining} days left. Let's adjust the plan.`,
        color: 'orange',
        autoClose: false,
    })
}

// === MOTIVATIONAL MESSAGES ===

export function showMotivationalMessage() {
    const messages = [
        { title: '💪 You\'re building momentum', message: 'Every task completed compounds progress.' },
        { title: '🎯 Stay focused', message: 'Small wins lead to big achievements.' },
        { title: '🚀 Keep going', message: 'Progress isn\'t always linear, but it\'s always worth it.' },
        { title: '✨ Celebrate small wins', message: 'Each step forward is worth recognizing.' },
        { title: '🔥 Consistency beats intensity', message: 'Show up every week, results will follow.' },
    ]

    const random = messages[Math.floor(Math.random() * messages.length)]

    notifications.show({
        title: random.title,
        message: random.message,
        color: 'grape',
        autoClose: 5000,
    })
}
