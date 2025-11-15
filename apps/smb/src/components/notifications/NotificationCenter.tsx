/**
 * NotificationCenter - Notification Panel and Toast Container
 * 
 * Features:
 * - Fixed position notification bell icon with badge
 * - Slide-out drawer panel with notification list
 * - Toast notifications that auto-dismiss
 * - Mark all as read
 * - Clear dismissed notifications
 */

import {
    ActionIcon,
    Badge,
    Box,
    Button,
    Drawer,
    Group,
    Indicator,
    ScrollArea,
    Stack,
    Text,
    Title,
} from '@mantine/core';
import { IconBell, IconBellOff, IconTrash } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNotificationStore } from '../../stores/notificationStore';
import { NotificationCard } from './NotificationCard';

interface NotificationCenterProps {
    /**
     * Position of the notification bell
     * @default 'top-right'
     */
    position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';

    /**
     * Show toast notifications for new notifications
     * @default true
     */
    showToasts?: boolean;

    /**
     * Max number of toast notifications to show simultaneously
     * @default 3
     */
    maxToasts?: number;
}

export function NotificationCenter({
    position = 'top-right',
    showToasts = true,
    maxToasts = 3,
}: NotificationCenterProps) {
    const {
        notifications,
        isPanelOpen,
        togglePanel,
        closePanel,
        markAllAsRead,
        clearDismissed,
        getUnreadCount,
        getActiveNotifications,
    } = useNotificationStore();

    const [toastIds, setToastIds] = useState<string[]>([]);

    const unreadCount = getUnreadCount();
    const activeNotifications = getActiveNotifications();

    // Position styles for the notification bell
    const positionStyles = getPositionStyles(position);

    // Show toast for new notifications
    useEffect(() => {
        if (!showToasts) return;

        // Find newest unread notification that's not already in toasts
        const newestNotification = notifications
            .filter((n) => !n.read && !n.dismissed && !toastIds.includes(n.id))
        [0];

        if (newestNotification) {
            setToastIds((prev) => {
                const newToasts = [newestNotification.id, ...prev].slice(0, maxToasts);
                return newToasts;
            });

            // Remove from toasts after auto-dismiss period (default 5s)
            const dismissMs = newestNotification.autoDismissMs || 5000;
            setTimeout(() => {
                setToastIds((prev) => prev.filter((id) => id !== newestNotification.id));
            }, dismissMs);
        }
    }, [notifications, showToasts, maxToasts, toastIds]);

    const handleMarkAllRead = () => {
        markAllAsRead();
    };

    const handleClearDismissed = () => {
        clearDismissed();
    };

    return (
        <>
            {/* Notification Bell Button */}
            <Box
                style={{
                    position: 'fixed',
                    zIndex: 1000,
                    ...positionStyles,
                }}
            >
                <Indicator
                    inline
                    label={unreadCount > 0 ? unreadCount : undefined}
                    size={16}
                    color="red"
                    disabled={unreadCount === 0}
                >
                    <ActionIcon
                        size="xl"
                        radius="xl"
                        variant="filled"
                        color={unreadCount > 0 ? 'blue' : 'gray'}
                        onClick={togglePanel}
                        aria-label="Open notifications"
                    >
                        {unreadCount > 0 ? (
                            <IconBell size={24} />
                        ) : (
                            <IconBellOff size={24} />
                        )}
                    </ActionIcon>
                </Indicator>
            </Box>

            {/* Toast Notifications */}
            {showToasts && (
                <Box
                    style={{
                        position: 'fixed',
                        right: 20,
                        top: 100,
                        zIndex: 1001,
                        maxWidth: 400,
                        width: '90vw',
                    }}
                >
                    <Stack gap="sm">
                        {toastIds.map((id) => {
                            const notification = notifications.find((n) => n.id === id);
                            if (!notification || notification.dismissed) return null;
                            return (
                                <NotificationCard
                                    key={id}
                                    notification={notification}
                                    isToast
                                />
                            );
                        })}
                    </Stack>
                </Box>
            )}

            {/* Notification Drawer Panel */}
            <Drawer
                opened={isPanelOpen}
                onClose={closePanel}
                position="right"
                title={
                    <Group justify="space-between" style={{ width: '100%' }}>
                        <Title order={4}>Notifications</Title>
                        {unreadCount > 0 && (
                            <Badge color="blue" variant="filled">
                                {unreadCount} new
                            </Badge>
                        )}
                    </Group>
                }
                padding="md"
                size="md"
            >
                <Stack gap="md" style={{ height: '100%' }}>
                    {/* Actions */}
                    <Group justify="space-between">
                        <Button
                            size="xs"
                            variant="subtle"
                            leftSection={<IconBellOff size={16} />}
                            onClick={handleMarkAllRead}
                            disabled={unreadCount === 0}
                        >
                            Mark all read
                        </Button>
                        <Button
                            size="xs"
                            variant="subtle"
                            color="red"
                            leftSection={<IconTrash size={16} />}
                            onClick={handleClearDismissed}
                        >
                            Clear dismissed
                        </Button>
                    </Group>

                    {/* Notification List */}
                    <ScrollArea style={{ flex: 1 }} type="auto">
                        {activeNotifications.length === 0 ? (
                            <Box style={{ textAlign: 'center', padding: '2rem' }}>
                                <IconBellOff size={48} color="gray" style={{ margin: '0 auto' }} />
                                <Text size="sm" c="dimmed" mt="md">
                                    No notifications
                                </Text>
                            </Box>
                        ) : (
                            <Stack gap="md">
                                {activeNotifications.map((notification) => (
                                    <NotificationCard
                                        key={notification.id}
                                        notification={notification}
                                    />
                                ))}
                            </Stack>
                        )}
                    </ScrollArea>
                </Stack>
            </Drawer>
        </>
    );
}

/**
 * Get CSS position styles based on position prop
 */
function getPositionStyles(position: NotificationCenterProps['position']) {
    switch (position) {
        case 'top-left':
            return { top: 20, left: 20 };
        case 'top-right':
            return { top: 20, right: 20 };
        case 'bottom-left':
            return { bottom: 20, left: 20 };
        case 'bottom-right':
            return { bottom: 20, right: 20 };
        default:
            return { top: 20, right: 20 };
    }
}
