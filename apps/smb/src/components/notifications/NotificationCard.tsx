/**
 * NotificationCard - Slide-in Notification Component
 * 
 * Displays individual notifications with:
 * - Priority-based styling
 * - Action buttons
 * - Dismiss functionality
 * - Slide-in animation
 */

import { ActionIcon, Button, Card, Group, Stack, Text, ThemeIcon } from '@mantine/core';
import {
    IconAlertTriangle,
    IconCheck,
    IconInfoCircle,
    IconSparkles,
    IconTarget,
    IconX
} from '@tabler/icons-react';
import { useState } from 'react';
import { type Notification, useNotificationStore } from '../../stores/notificationStore';

interface NotificationCardProps {
    notification: Notification;
    /**
     * Whether this is a toast notification (floating, auto-dismiss)
     */
    isToast?: boolean;
}

/**
 * Get icon based on notification type
 */
function getNotificationIcon(type: Notification['type']) {
    switch (type) {
        case 'recommendation':
            return <IconSparkles size={20} />;
        case 'alert':
            return <IconAlertTriangle size={20} />;
        case 'task':
            return <IconCheck size={20} />;
        case 'goal':
            return <IconTarget size={20} />;
        case 'info':
        default:
            return <IconInfoCircle size={20} />;
    }
}

/**
 * Get color based on priority
 */
function getPriorityColor(priority: Notification['priority']): string {
    switch (priority) {
        case 'critical':
            return 'red';
        case 'important':
            return 'orange';
        case 'normal':
        default:
            return 'blue';
    }
}

export function NotificationCard({ notification, isToast = false }: NotificationCardProps) {
    const { markAsRead, dismissNotification } = useNotificationStore();
    const [isExiting, setIsExiting] = useState(false);

    const color = getPriorityColor(notification.priority);
    const icon = getNotificationIcon(notification.type);

    const handleDismiss = () => {
        setIsExiting(true);
        // Wait for animation to complete before dismissing
        setTimeout(() => {
            dismissNotification(notification.id);
        }, 300);
    };

    const handleAction = () => {
        if (notification.action?.onClick) {
            notification.action.onClick();
            // Mark as read and dismiss after action
            markAsRead(notification.id);
            handleDismiss();
        }
    };

    const handleCardClick = () => {
        if (!notification.read) {
            markAsRead(notification.id);
        }
    };

    return (
        <Card
            shadow="md"
            padding="md"
            radius="md"
            withBorder
            onClick={handleCardClick}
            style={{
                cursor: 'pointer',
                opacity: notification.read ? 0.7 : 1,
                animation: isExiting ? 'slideOut 0.3s ease-out' : 'slideIn 0.3s ease-out',
                borderColor: notification.read ? undefined : `var(--mantine-color-${color}-6)`,
                borderWidth: notification.read ? '1px' : '2px',
            }}
        >
            <Stack gap="sm">
                <Group justify="space-between" wrap="nowrap">
                    <Group gap="sm" wrap="nowrap">
                        <ThemeIcon color={color} variant="light" size="lg">
                            {icon}
                        </ThemeIcon>
                        <div style={{ flex: 1 }}>
                            <Text size="sm" fw={notification.read ? 400 : 600} lineClamp={1}>
                                {notification.title}
                            </Text>
                            <Text size="xs" c="dimmed">
                                {formatRelativeTime(notification.createdAt)}
                            </Text>
                        </div>
                    </Group>

                    <ActionIcon
                        variant="subtle"
                        color="gray"
                        size="sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            handleDismiss();
                        }}
                    >
                        <IconX size={16} />
                    </ActionIcon>
                </Group>

                <Text size="sm" c="dimmed">
                    {notification.message}
                </Text>

                {notification.action && (
                    <Group gap="xs">
                        <Button
                            size="xs"
                            color={color}
                            onClick={(e) => {
                                e.stopPropagation();
                                handleAction();
                            }}
                        >
                            {notification.action.label}
                        </Button>
                    </Group>
                )}
            </Stack>
        </Card>
    );
}

/**
 * Format relative time (e.g., "2 minutes ago", "1 hour ago")
 */
function formatRelativeTime(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - new Date(date).getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins}m ago`;
    } else if (diffHours < 24) {
        return `${diffHours}h ago`;
    } else if (diffDays < 7) {
        return `${diffDays}d ago`;
    } else {
        return new Date(date).toLocaleDateString();
    }
}

/**
 * CSS Keyframes for animations
 */
const styles = `
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
`;

// Inject styles
if (typeof document !== 'undefined') {
    const styleElement = document.createElement('style');
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
}
