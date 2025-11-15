/**
 * Notification Store - Zustand State Management for In-App Notifications
 * 
 * Manages notification state for Coach V6:
 * - New recommendations
 * - Critical alerts
 * - Task completions
 * - Goal updates
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type NotificationType = 'recommendation' | 'alert' | 'task' | 'goal' | 'info';
export type NotificationPriority = 'critical' | 'important' | 'normal';

export interface Notification {
    id: string;
    type: NotificationType;
    priority: NotificationPriority;
    title: string;
    message: string;
    /**
     * Action button configuration
     */
    action?: {
        label: string;
        onClick: () => void;
    };
    /**
     * Timestamp when notification was created
     */
    createdAt: Date;
    /**
     * Whether notification has been read
     */
    read: boolean;
    /**
     * Whether notification has been dismissed
     */
    dismissed: boolean;
    /**
     * Auto-dismiss timeout in ms (0 = never auto-dismiss)
     */
    autoDismissMs?: number;
    /**
     * Icon to display (defaults based on type)
     */
    icon?: string;
    /**
     * Optional metadata for tracking/analytics
     */
    metadata?: Record<string, any>;
}

interface NotificationStore {
    /**
     * All notifications (including dismissed)
     */
    notifications: Notification[];

    /**
     * Whether notification panel is open
     */
    isPanelOpen: boolean;

    /**
     * Add new notification
     */
    addNotification: (notification: Omit<Notification, 'id' | 'createdAt' | 'read' | 'dismissed'>) => void;

    /**
     * Mark notification as read
     */
    markAsRead: (id: string) => void;

    /**
     * Dismiss notification (removes from active list)
     */
    dismissNotification: (id: string) => void;

    /**
     * Mark all notifications as read
     */
    markAllAsRead: () => void;

    /**
     * Clear all dismissed notifications
     */
    clearDismissed: () => void;

    /**
     * Toggle notification panel open/closed
     */
    togglePanel: () => void;

    /**
     * Open notification panel
     */
    openPanel: () => void;

    /**
     * Close notification panel
     */
    closePanel: () => void;

    /**
     * Get unread count
     */
    getUnreadCount: () => number;

    /**
     * Get active notifications (not dismissed)
     */
    getActiveNotifications: () => Notification[];
}

export const useNotificationStore = create<NotificationStore>()(
    persist(
        (set, get) => ({
            notifications: [],
            isPanelOpen: false,

            addNotification: (notification) => {
                const newNotification: Notification = {
                    ...notification,
                    id: `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                    createdAt: new Date(),
                    read: false,
                    dismissed: false,
                };

                set((state) => ({
                    notifications: [newNotification, ...state.notifications],
                }));

                // Auto-dismiss if configured
                if (newNotification.autoDismissMs && newNotification.autoDismissMs > 0) {
                    setTimeout(() => {
                        get().dismissNotification(newNotification.id);
                    }, newNotification.autoDismissMs);
                }
            },

            markAsRead: (id) => {
                set((state) => ({
                    notifications: state.notifications.map((n) =>
                        n.id === id ? { ...n, read: true } : n
                    ),
                }));
            },

            dismissNotification: (id) => {
                set((state) => ({
                    notifications: state.notifications.map((n) =>
                        n.id === id ? { ...n, dismissed: true } : n
                    ),
                }));
            },

            markAllAsRead: () => {
                set((state) => ({
                    notifications: state.notifications.map((n) => ({ ...n, read: true })),
                }));
            },

            clearDismissed: () => {
                set((state) => ({
                    notifications: state.notifications.filter((n) => !n.dismissed),
                }));
            },

            togglePanel: () => {
                set((state) => ({ isPanelOpen: !state.isPanelOpen }));
            },

            openPanel: () => {
                set({ isPanelOpen: true });
            },

            closePanel: () => {
                set({ isPanelOpen: false });
            },

            getUnreadCount: () => {
                return get().notifications.filter((n) => !n.read && !n.dismissed).length;
            },

            getActiveNotifications: () => {
                return get().notifications.filter((n) => !n.dismissed);
            },
        }),
        {
            name: 'coach-v6-notifications',
            // Don't persist panel open state or action callbacks
            partialize: (state) => ({
                notifications: state.notifications.map((n) => ({
                    ...n,
                    action: undefined, // Don't persist callbacks
                })),
            }),
        }
    )
);
