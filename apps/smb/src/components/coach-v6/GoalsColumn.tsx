import { ActionIcon, Badge, Button, Card, Group, Progress, Stack, Text } from '@mantine/core';
import { IconChevronRight, IconPlus, IconTarget } from '@tabler/icons-react';
import type { GoalsColumnProps } from './types';

/**
 * Goals Column Component
 * 
 * Displays active goals with progress bars and due dates.
 * Part of the unified "Goals & Tasks" center panel.
 */
export function GoalsColumn({ goals, loading = false, onGoalClick, onCreateGoal }: GoalsColumnProps) {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'on_track':
                return 'green';
            case 'at_risk':
                return 'yellow';
            case 'off_track':
                return 'red';
            case 'completed':
                return 'blue';
            default:
                return 'gray';
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'on_track':
                return 'On Track';
            case 'at_risk':
                return 'At Risk';
            case 'off_track':
                return 'Off Track';
            case 'completed':
                return 'Completed';
            default:
                return status;
        }
    };

    const formatDueDate = (date: Date) => {
        const now = new Date();
        const diffTime = date.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays < 0) return 'Overdue';
        if (diffDays === 0) return 'Due today';
        if (diffDays === 1) return 'Due tomorrow';
        if (diffDays <= 7) return `Due in ${diffDays} days`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    return (
        <div>
            {/* Header */}
            <Group justify="space-between" align="center" mb="md">
                <Group gap="xs">
                    <IconTarget size={20} />
                    <Text size="sm" fw={600}>
                        Active Goals ({goals.length})
                    </Text>
                </Group>
                {onCreateGoal && (
                    <ActionIcon variant="light" size="sm" onClick={onCreateGoal}>
                        <IconPlus size={16} />
                    </ActionIcon>
                )}
            </Group>

            {/* Goals List */}
            <Stack gap="md">
                {loading ? (
                    <Text size="sm" c="dimmed">
                        Loading goals...
                    </Text>
                ) : goals.length === 0 ? (
                    <Card padding="lg" radius="md" withBorder>
                        <Stack gap="sm" align="center">
                            <Text size="sm" c="dimmed" ta="center">
                                No active goals yet.
                            </Text>
                            {onCreateGoal && (
                                <Button size="xs" variant="light" onClick={onCreateGoal}>
                                    Create Your First Goal
                                </Button>
                            )}
                        </Stack>
                    </Card>
                ) : (
                    goals.map((goal) => (
                        <Card
                            key={goal.id}
                            shadow="sm"
                            padding="md"
                            radius="md"
                            withBorder
                            onClick={() => onGoalClick?.(goal.id)}
                            style={{
                                cursor: onGoalClick ? 'pointer' : 'default',
                                transition: 'transform 0.2s',
                            }}
                            onMouseEnter={(e) => {
                                if (onGoalClick) {
                                    e.currentTarget.style.transform = 'translateX(2px)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (onGoalClick) {
                                    e.currentTarget.style.transform = 'translateX(0)';
                                }
                            }}
                        >
                            <Stack gap="sm">
                                {/* Header */}
                                <Group justify="space-between" align="flex-start">
                                    <div style={{ flex: 1 }}>
                                        <Text size="sm" fw={600} mb={4}>
                                            {goal.title}
                                        </Text>
                                        {goal.description && (
                                            <Text size="xs" c="dimmed" lineClamp={2}>
                                                {goal.description}
                                            </Text>
                                        )}
                                    </div>
                                    {onGoalClick && <IconChevronRight size={16} style={{ flexShrink: 0 }} />}
                                </Group>

                                {/* Progress */}
                                <div>
                                    <Group justify="space-between" mb={4}>
                                        <Text size="xs" c="dimmed">
                                            Progress
                                        </Text>
                                        <Text size="xs" fw={600}>
                                            {goal.currentValue} / {goal.targetValue}
                                        </Text>
                                    </Group>
                                    <Progress
                                        value={goal.progress}
                                        size="sm"
                                        radius="xl"
                                        color={getStatusColor(goal.status)}
                                    />
                                </div>

                                {/* Footer */}
                                <Group justify="space-between" align="center">
                                    <Badge size="xs" color={getStatusColor(goal.status)} variant="light">
                                        {getStatusLabel(goal.status)}
                                    </Badge>
                                    {goal.dueDate && (
                                        <Text size="xs" c="dimmed">
                                            {formatDueDate(goal.dueDate)}
                                        </Text>
                                    )}
                                </Group>
                            </Stack>
                        </Card>
                    ))
                )}
            </Stack>
        </div>
    );
}
