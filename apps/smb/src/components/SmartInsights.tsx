import { ActionIcon, Alert, Badge, Button, Card, Divider, Group, Stack, Text } from '@mantine/core'
import { IconArrowRight, IconBulb, IconCircleCheck, IconInfoCircle, IconSparkles, IconX } from '@tabler/icons-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBusinessContext } from '../contexts/BusinessContext'

export default function SmartInsights() {
    const navigate = useNavigate()
    const { insights, isLoading } = useBusinessContext()
    const [dismissedInsights, setDismissedInsights] = useState<Set<string>>(new Set())

    const visibleInsights = insights.filter(insight => !dismissedInsights.has(insight.id))

    const handleDismiss = (insightId: string) => {
        setDismissedInsights(prev => new Set(prev).add(insightId))
    }

    const handleAction = (path: string, state?: any) => {
        navigate(path, { state })
    }

    const getInsightIcon = (type: string) => {
        switch (type) {
            case 'alert':
                return <IconSparkles size={20} />
            case 'suggestion':
                return <IconBulb size={20} />
            case 'success':
                return <IconCircleCheck size={20} />
            case 'info':
                return <IconInfoCircle size={20} />
            default:
                return <IconSparkles size={20} />
        }
    }

    const getInsightColor = (type: string) => {
        switch (type) {
            case 'alert':
                return 'red'
            case 'suggestion':
                return 'blue'
            case 'success':
                return 'teal'
            case 'info':
                return 'gray'
            default:
                return 'blue'
        }
    }

    const getPriorityBadge = (priority: string) => {
        const colors = {
            high: 'red',
            medium: 'yellow',
            low: 'gray'
        }
        return (
            <Badge size="xs" color={colors[priority as keyof typeof colors] || 'gray'} variant="dot">
                {priority}
            </Badge>
        )
    }

    if (isLoading) {
        return (
            <Card withBorder radius="md" p="md">
                <Stack gap="sm">
                    <Group>
                        <IconSparkles size={20} />
                        <Text size="sm" fw={600}>AI Insights</Text>
                    </Group>
                    <Text size="xs" c="dimmed">Loading personalized insights...</Text>
                </Stack>
            </Card>
        )
    }

    if (visibleInsights.length === 0) {
        return (
            <Card withBorder radius="md" p="md">
                <Stack gap="sm">
                    <Group>
                        <IconCircleCheck size={20} color="var(--mantine-color-teal-6)" />
                        <Text size="sm" fw={600}>All Caught Up!</Text>
                    </Group>
                    <Text size="xs" c="dimmed">
                        No new insights at the moment. Keep up the great work! 🎉
                    </Text>
                </Stack>
            </Card>
        )
    }

    return (
        <Stack gap="xs">
            <Group justify="space-between">
                <Text size="sm" fw={600} c="gray.7" tt="uppercase" style={{ letterSpacing: '0.5px' }}>
                    AI Coach Insights
                </Text>
                {visibleInsights.length > 0 && (
                    <Badge size="sm" variant="filled" color="blue">
                        {visibleInsights.length}
                    </Badge>
                )}
            </Group>

            <Stack gap="sm">
                {visibleInsights.map((insight) => {
                    const color = getInsightColor(insight.type)
                    const icon = getInsightIcon(insight.type)

                    return (
                        <Alert
                            key={insight.id}
                            icon={icon}
                            color={color}
                            variant="light"
                            radius="md"
                            withCloseButton={false}
                            styles={{
                                root: {
                                    position: 'relative',
                                    paddingRight: '2.5rem',
                                }
                            }}
                        >
                            <Stack gap="xs">
                                <Group justify="space-between" align="flex-start">
                                    <Stack gap={4} style={{ flex: 1 }}>
                                        <Group gap="xs">
                                            {getPriorityBadge(insight.priority)}
                                            <Text size="xs" c="dimmed">
                                                {new Date(insight.timestamp).toLocaleTimeString('en-US', {
                                                    hour: 'numeric',
                                                    minute: '2-digit',
                                                    hour12: true
                                                })}
                                            </Text>
                                        </Group>
                                        <Text size="sm" fw={500}>
                                            {insight.message}
                                        </Text>
                                    </Stack>

                                    <ActionIcon
                                        variant="subtle"
                                        color="gray"
                                        size="sm"
                                        onClick={() => handleDismiss(insight.id)}
                                        style={{ position: 'absolute', top: '0.75rem', right: '0.75rem' }}
                                    >
                                        <IconX size={16} />
                                    </ActionIcon>
                                </Group>

                                {insight.actions && insight.actions.length > 0 && (
                                    <>
                                        <Divider my={4} />
                                        <Group gap="xs" wrap="wrap">
                                            {insight.actions.map((action, idx) => (
                                                <Button
                                                    key={idx}
                                                    size="xs"
                                                    variant={idx === 0 ? 'filled' : 'light'}
                                                    color={color}
                                                    rightSection={<IconArrowRight size={14} />}
                                                    onClick={() => handleAction(action.path, action.state)}
                                                >
                                                    {action.label}
                                                </Button>
                                            ))}
                                        </Group>
                                    </>
                                )}
                            </Stack>
                        </Alert>
                    )
                })}
            </Stack>
        </Stack>
    )
}
