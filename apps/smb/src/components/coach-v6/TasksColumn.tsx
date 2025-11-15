import { ActionIcon, Badge, Card, Checkbox, Group, Stack, Text } from '@mantine/core';
import { IconChevronRight, IconClock } from '@tabler/icons-react';
import type { TasksColumnProps } from './types';

/**
 * Tasks Column Component
 * 
 * Displays today's prioritized tasks with status indicators.
 * Part of the unified "Goals & Tasks" center panel.
 */
export function TasksColumn({ tasks, loading = false, onTaskClick, onToggleComplete }: TasksColumnProps) {
    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'urgent':
                return 'red';
            case 'high':
                return 'orange';
            case 'medium':
                return 'blue';
            case 'low':
                return 'gray';
            default:
                return 'gray';
        }
    };

    const getPriorityLabel = (priority: string) => {
        switch (priority) {
            case 'urgent':
                return 'Urgent';
            case 'high':
                return 'High';
            case 'medium':
                return 'Medium';
            case 'low':
                return 'Low';
            default:
                return priority;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'green';
            case 'in_progress':
                return 'blue';
            case 'blocked':
                return 'red';
            case 'pending':
                return 'gray';
            default:
                return 'gray';
        }
    };

    const formatDueTime = (date: Date) => {
        return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    };

    return (
        <div>
            {/* Header */}
            <Group justify="space-between" align="center" mb="md">
                <Group gap="xs">
                    <IconClock size={20} />
                    <Text size="sm" fw={600}>
                        Today's Tasks ({tasks.filter((t) => !t.completed).length})
                    </Text>
                </Group>
            </Group>

            {/* Tasks List */}
            <Stack gap="md">
                {loading ? (
                    <Text size="sm" c="dimmed">
                        Loading tasks...
                    </Text>
                ) : tasks.length === 0 ? (
                    <Card padding="lg" radius="md" withBorder>
                        <Text size="sm" c="dimmed" ta="center">
                            No tasks for today. Great job! 🎉
                        </Text>
                    </Card>
                ) : (
                    tasks.map((task) => (
                        <Card
                            key={task.id}
                            shadow="sm"
                            padding="md"
                            radius="md"
                            withBorder
                            style={{
                                opacity: task.completed ? 0.6 : 1,
                                transition: 'opacity 0.2s, transform 0.2s',
                            }}
                            onMouseEnter={(e) => {
                                if (onTaskClick) {
                                    e.currentTarget.style.transform = 'translateX(2px)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (onTaskClick) {
                                    e.currentTarget.style.transform = 'translateX(0)';
                                }
                            }}
                        >
                            <Group align="flex-start" gap="sm">
                                {/* Checkbox */}
                                {onToggleComplete && (
                                    <Checkbox
                                        checked={task.completed}
                                        onChange={() => onToggleComplete(task.id)}
                                        size="sm"
                                        style={{ marginTop: 2 }}
                                    />
                                )}

                                {/* Content */}
                                <div style={{ flex: 1 }}>
                                    <Group justify="space-between" align="flex-start" mb={4}>
                                        <Text
                                            size="sm"
                                            fw={600}
                                            style={{
                                                textDecoration: task.completed ? 'line-through' : 'none',
                                                flex: 1,
                                            }}
                                        >
                                            {task.title}
                                        </Text>
                                        {onTaskClick && (
                                            <ActionIcon
                                                variant="subtle"
                                                size="sm"
                                                onClick={() => onTaskClick(task.id)}
                                            >
                                                <IconChevronRight size={16} />
                                            </ActionIcon>
                                        )}
                                    </Group>

                                    {task.description && (
                                        <Text size="xs" c="dimmed" mb={8} lineClamp={2}>
                                            {task.description}
                                        </Text>
                                    )}

                                    {/* Footer */}
                                    <Group gap="xs">
                                        <Badge size="xs" color={getPriorityColor(task.priority)} variant="dot">
                                            {getPriorityLabel(task.priority)}
                                        </Badge>
                                        {task.status && task.status !== 'pending' && (
                                            <Badge size="xs" color={getStatusColor(task.status)} variant="light">
                                                {task.status.replace('_', ' ')}
                                            </Badge>
                                        )}
                                        {task.dueDate && (
                                            <Text size="xs" c="dimmed">
                                                {formatDueTime(task.dueDate)}
                                            </Text>
                                        )}
                                        {task.goalId && (
                                            <Badge size="xs" color="gray" variant="outline">
                                                Goal linked
                                            </Badge>
                                        )}
                                    </Group>
                                </div>
                            </Group>
                        </Card>
                    ))
                )}
            </Stack>
        </div>
    );
}
