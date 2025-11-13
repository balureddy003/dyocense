import { ActionIcon, Badge, Button, Card, Divider, Group, Stack, Text, ThemeIcon } from '@mantine/core';
import { IconAlertCircle, IconArrowRight, IconBulb, IconChartBar, IconCheck, IconClipboardList, IconInfoCircle, IconMessageCircle, IconSparkles, IconThumbUp, IconX } from '@tabler/icons-react';
import { useState } from 'react';
import * as api from '../../lib/api';
import { CreateActionPlanModal, ShowDetailsModal, TellMeMoreModal } from '../action-flows';
import { FeedbackModal } from '../feedback';
import type { ProactiveCoachCardProps } from './types';

/**
 * Proactive Coach Card Component
 * 
 * Displays AI-generated recommendations with actionable steps.
 * Priority-based styling (critical/important/suggestion).
 */
export function ProactiveCoachCard({
    recommendation,
    onTakeAction,
    onDismiss,
    loading = false,
}: ProactiveCoachCardProps) {
    const { id, priority, title, description, reasoning, actions, dismissible, generatedAt } = recommendation;

    // Modal state
    const [showActionPlan, setShowActionPlan] = useState(false);
    const [showDetails, setShowDetails] = useState(false);
    const [showChat, setShowChat] = useState(false);
    const [showFeedback, setShowFeedback] = useState(false);

    // Get tenant info for API calls
    const tenantId = localStorage.getItem('tenantId') || 'tenant-demo';
    const token = localStorage.getItem('token') || undefined;

    // Handle feedback submission
    const handleFeedbackSubmit = async (feedback: api.RecommendationFeedback) => {
        try {
            await api.submitRecommendationFeedback(tenantId, id, feedback, token);
            console.log('Feedback submitted successfully');
        } catch (error) {
            console.error('Failed to submit feedback:', error);
        }
    };

    // Priority styling
    const getPriorityColor = () => {
        switch (priority) {
            case 'critical':
                return 'red';
            case 'important':
                return 'yellow';
            case 'suggestion':
                return 'blue';
            default:
                return 'gray';
        }
    };

    const getPriorityIcon = () => {
        switch (priority) {
            case 'critical':
                return <IconAlertCircle size={20} />;
            case 'important':
                return <IconInfoCircle size={20} />;
            case 'suggestion':
                return <IconBulb size={20} />;
            default:
                return <IconSparkles size={20} />;
        }
    };

    const getPriorityLabel = () => {
        switch (priority) {
            case 'critical':
                return 'Urgent';
            case 'important':
                return 'Important';
            case 'suggestion':
                return 'Suggested';
            default:
                return 'Info';
        }
    };

    return (
        <Card
            shadow="sm"
            padding="lg"
            radius="md"
            withBorder
            style={{
                position: 'relative',
                borderLeft: priority === 'critical' ? '4px solid var(--mantine-color-red-6)' : undefined,
            }}
        >
            {/* Header */}
            <Group justify="space-between" align="flex-start" mb="md">
                <Group gap="xs" align="center">
                    <ThemeIcon color={getPriorityColor()} variant="light" size="md">
                        {getPriorityIcon()}
                    </ThemeIcon>
                    <div>
                        <Group gap={8}>
                            <Badge size="xs" color={getPriorityColor()} variant="light">
                                {getPriorityLabel()}
                            </Badge>
                            <Text size="xs" c="dimmed">
                                {new Date(generatedAt).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                            </Text>
                        </Group>
                    </div>
                </Group>

                {dismissible && (
                    <ActionIcon
                        variant="subtle"
                        color="gray"
                        size="sm"
                        onClick={() => onDismiss(id)}
                    >
                        <IconX size={14} />
                    </ActionIcon>
                )}
            </Group>

            {/* Content */}
            <Stack gap="md">
                <div>
                    <Text size="md" fw={600} mb={4}>
                        {title}
                    </Text>
                    <Text size="sm" c="dimmed">
                        {description}
                    </Text>
                </div>

                {reasoning && (
                    <Card padding="sm" bg="gray.0" radius="sm">
                        <Group gap={6} align="flex-start">
                            <IconSparkles size={14} style={{ marginTop: 2, flexShrink: 0 }} />
                            <Text size="xs" c="dimmed" style={{ flex: 1 }}>
                                {reasoning}
                            </Text>
                        </Group>
                    </Card>
                )}

                {/* Actions */}
                {actions.length > 0 && (
                    <Stack gap="xs">
                        <Text size="xs" fw={600} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.5px' }}>
                            Recommended Actions
                        </Text>
                        {actions.map((action, index) => (
                            <Card key={index} padding="sm" bg="blue.0" radius="sm" withBorder>
                                <Group justify="space-between" align="flex-start">
                                    <div style={{ flex: 1 }}>
                                        <Group gap={6} mb={4}>
                                            {action.completed && (
                                                <ThemeIcon color="green" size="xs" radius="xl">
                                                    <IconCheck size={10} />
                                                </ThemeIcon>
                                            )}
                                            <Text
                                                size="sm"
                                                fw={500}
                                                style={{ textDecoration: action.completed ? 'line-through' : 'none' }}
                                            >
                                                {action.label}
                                            </Text>
                                        </Group>
                                        {action.description && (
                                            <Text size="xs" c="dimmed" ml={action.completed ? 22 : 0}>
                                                {action.description}
                                            </Text>
                                        )}
                                    </div>
                                    <Button
                                        size="xs"
                                        variant="light"
                                        rightSection={<IconArrowRight size={12} />}
                                        onClick={() => onTakeAction(action)}
                                        disabled={action.completed}
                                    >
                                        {action.buttonText}
                                    </Button>
                                </Group>
                            </Card>
                        ))}
                    </Stack>
                )}

                {/* Action Flow Buttons */}
                <Group gap="xs" mt="md">
                    <Button
                        size="xs"
                        variant="default"
                        leftSection={<IconClipboardList size={14} />}
                        onClick={() => setShowActionPlan(true)}
                    >
                        Create Action Plan
                    </Button>
                    <Button
                        size="xs"
                        variant="default"
                        leftSection={<IconChartBar size={14} />}
                        onClick={() => setShowDetails(true)}
                    >
                        Show Details
                    </Button>
                    <Button
                        size="xs"
                        variant="default"
                        leftSection={<IconMessageCircle size={14} />}
                        onClick={() => setShowChat(true)}
                    >
                        Tell Me More
                    </Button>
                </Group>

                <Divider my="sm" />

                {/* Feedback Button */}
                <Group gap="xs">
                    <Button
                        size="xs"
                        variant="light"
                        color="gray"
                        leftSection={<IconThumbUp size={14} />}
                        onClick={() => setShowFeedback(true)}
                    >
                        Give Feedback
                    </Button>
                </Group>
            </Stack>

            {/* Action Flow Modals */}
            <CreateActionPlanModal
                opened={showActionPlan}
                onClose={() => setShowActionPlan(false)}
                recommendation={recommendation}
                onSubmit={(plan) => {
                    console.log('Action plan created:', plan);
                    // TODO: Send to API to create goals/tasks
                    setShowActionPlan(false);
                }}
            />

            <ShowDetailsModal
                opened={showDetails}
                onClose={() => setShowDetails(false)}
                recommendation={recommendation}
            />

            <TellMeMoreModal
                opened={showChat}
                onClose={() => setShowChat(false)}
                recommendation={recommendation}
            />

            <FeedbackModal
                opened={showFeedback}
                onClose={() => setShowFeedback(false)}
                recommendationId={id}
                recommendationTitle={title}
                onSubmit={(feedback) => {
                    handleFeedbackSubmit(feedback);
                    setShowFeedback(false);
                }}
            />
        </Card>
    );
}
