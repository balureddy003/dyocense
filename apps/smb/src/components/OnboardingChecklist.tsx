import { ActionIcon, Card, Progress, Stack, Text, ThemeIcon } from '@mantine/core'
import { IconCheck, IconChevronRight, IconX } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface OnboardingStep {
    id: string
    label: string
    description: string
    icon: string
    route: string
    checkComplete: () => boolean
}

const ONBOARDING_STORAGE_KEY = 'dyocense_onboarding_dismissed'

export function OnboardingChecklist() {
    const navigate = useNavigate()
    const [dismissed, setDismissed] = useState(() => {
        try {
            return localStorage.getItem(ONBOARDING_STORAGE_KEY) === 'true'
        } catch {
            return false
        }
    })

    const steps: OnboardingStep[] = [
        {
            id: 'connect_data',
            label: 'Connect your first data source',
            description: 'Link your tools to start tracking metrics',
            icon: '🔗',
            route: '/marketplace',
            checkComplete: () => {
                // Check if user has any connected data sources
                try {
                    const connectors = localStorage.getItem('hasConnectedData')
                    return connectors === 'true'
                } catch {
                    return false
                }
            },
        },
        {
            id: 'set_goal',
            label: 'Set your first business goal',
            description: 'Define what success looks like',
            icon: '🎯',
            route: '/goals',
            checkComplete: () => {
                try {
                    const goals = localStorage.getItem('hasCreatedGoal')
                    return goals === 'true'
                } catch {
                    return false
                }
            },
        },
        {
            id: 'check_health',
            label: 'Check your health score',
            description: 'See how your business is performing',
            icon: '📊',
            route: '/coach',
            checkComplete: () => {
                try {
                    const viewed = localStorage.getItem('hasViewedHealthScore')
                    return viewed === 'true'
                } catch {
                    return false
                }
            },
        },
        {
            id: 'ask_coach',
            label: 'Chat with your AI coach',
            description: 'Get personalized business advice',
            icon: '💡',
            route: '/coach-v5',
            checkComplete: () => {
                try {
                    const chatted = localStorage.getItem('hasUsedCoach')
                    return chatted === 'true'
                } catch {
                    return false
                }
            },
        },
    ]

    const [completionStatus, setCompletionStatus] = useState<Record<string, boolean>>({})

    useEffect(() => {
        // Check completion status
        const status: Record<string, boolean> = {}
        steps.forEach((step) => {
            status[step.id] = step.checkComplete()
        })
        setCompletionStatus(status)
    }, [])

    const completedCount = Object.values(completionStatus).filter(Boolean).length
    const totalCount = steps.length
    const progress = (completedCount / totalCount) * 100
    const allComplete = completedCount === totalCount

    const handleDismiss = () => {
        try {
            localStorage.setItem(ONBOARDING_STORAGE_KEY, 'true')
            setDismissed(true)
        } catch (e) {
            console.warn('Failed to save onboarding dismissal', e)
        }
    }

    // Auto-dismiss when all steps complete
    useEffect(() => {
        if (allComplete && !dismissed) {
            setTimeout(() => {
                handleDismiss()
            }, 3000) // Show completion state for 3 seconds
        }
    }, [allComplete, dismissed])

    if (dismissed) {
        return null
    }

    return (
        <Card shadow="sm" padding="lg" radius="md" withBorder style={{ marginBottom: '24px' }}>
            <Stack gap="md">
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Text size="lg" fw={600}>
                            {allComplete ? '🎉 Welcome setup complete!' : '🚀 Get Started with Dyocense'}
                        </Text>
                        <Text size="sm" c="dimmed">
                            {allComplete
                                ? "You're all set! This message will disappear soon."
                                : `${completedCount} of ${totalCount} steps completed`}
                        </Text>
                    </div>
                    <ActionIcon variant="subtle" color="gray" onClick={handleDismiss} aria-label="Dismiss onboarding">
                        <IconX size={18} />
                    </ActionIcon>
                </div>

                {/* Progress Bar */}
                <Progress value={progress} size="sm" radius="xl" color={allComplete ? 'green' : 'blue'} />

                {/* Steps */}
                <Stack gap="xs">
                    {steps.map((step) => {
                        const isComplete = completionStatus[step.id]
                        return (
                            <div
                                key={step.id}
                                onClick={() => !isComplete && navigate(step.route)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px',
                                    padding: '12px',
                                    borderRadius: '8px',
                                    cursor: isComplete ? 'default' : 'pointer',
                                    backgroundColor: isComplete ? 'var(--mantine-color-green-0)' : 'transparent',
                                    transition: 'background-color 0.2s',
                                }}
                                onMouseEnter={(e) => {
                                    if (!isComplete) {
                                        e.currentTarget.style.backgroundColor = 'var(--mantine-color-gray-0)'
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (!isComplete) {
                                        e.currentTarget.style.backgroundColor = 'transparent'
                                    }
                                }}
                            >
                                {/* Icon or Checkmark */}
                                {isComplete ? (
                                    <ThemeIcon color="green" size="lg" radius="xl" variant="light">
                                        <IconCheck size={18} />
                                    </ThemeIcon>
                                ) : (
                                    <div
                                        style={{
                                            fontSize: '24px',
                                            width: '40px',
                                            height: '40px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                        }}
                                    >
                                        {step.icon}
                                    </div>
                                )}

                                {/* Text */}
                                <div style={{ flex: 1 }}>
                                    <Text size="sm" fw={500} style={{ textDecoration: isComplete ? 'line-through' : 'none' }}>
                                        {step.label}
                                    </Text>
                                    <Text size="xs" c="dimmed">
                                        {step.description}
                                    </Text>
                                </div>

                                {/* Arrow */}
                                {!isComplete && <IconChevronRight size={18} color="var(--mantine-color-gray-6)" />}
                            </div>
                        )
                    })}
                </Stack>
            </Stack>
        </Card>
    )
}
