/**
 * WebSocket Hook for Coach V6 Real-Time Updates
 * 
 * Manages WebSocket connection and handles real-time events:
 * - Health score updates
 * - New recommendations
 * - Task completion notifications
 * - Goal progress updates
 */

import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * WebSocket message types from server
 */
export type WebSocketMessageType =
    | 'connection_ack'
    | 'heartbeat'
    | 'pong'
    | 'health_score_update'
    | 'new_recommendation'
    | 'task_completed'
    | 'goal_progress_update'
    | 'subscription_ack';

/**
 * Base WebSocket message structure
 */
export interface WebSocketMessage<T = any> {
    type: WebSocketMessageType;
    tenant_id?: string;
    timestamp: string;
    data?: T;
}

/**
 * Health score update payload
 */
export interface HealthScoreUpdateData {
    score: number;
    previousScore: number;
    trend: 'up' | 'down' | 'stable';
    components: Record<string, number>;
    alerts: any[];
    signals: any[];
}

/**
 * New recommendation payload
 */
export interface NewRecommendationData {
    id: string;
    priority: 'critical' | 'important' | 'suggestion';
    title: string;
    description: string;
    actions: Array<{
        label: string;
        variant: 'primary' | 'secondary';
    }>;
    dismissible: boolean;
    createdAt: string;
}

/**
 * Task completed payload
 */
export interface TaskCompletedData {
    taskId: string;
    taskTitle: string;
    goalId?: string;
}

/**
 * Goal progress update payload
 */
export interface GoalProgressUpdateData {
    goalId: string;
    goalTitle: string;
    progress: number;
    status: string;
}

/**
 * WebSocket event handlers
 */
export interface WebSocketHandlers {
    onHealthScoreUpdate?: (data: HealthScoreUpdateData) => void;
    onNewRecommendation?: (data: NewRecommendationData) => void;
    onTaskCompleted?: (data: TaskCompletedData) => void;
    onGoalProgressUpdate?: (data: GoalProgressUpdateData) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onError?: (error: Event) => void;
}

/**
 * WebSocket hook options
 */
export interface UseWebSocketOptions {
    tenantId: string;
    token: string;
    baseUrl?: string;
    reconnectAttempts?: number;
    reconnectDelay?: number;
    enabled?: boolean;
}

/**
 * WebSocket hook return value
 */
export interface UseWebSocketReturn {
    isConnected: boolean;
    error: string | null;
    send: (message: any) => void;
    reconnect: () => void;
}

/**
 * Custom hook for managing WebSocket connection to Coach V6 backend
 * 
 * @param options - WebSocket configuration
 * @param handlers - Event handlers for different message types
 * @returns WebSocket connection state and controls
 * 
 * @example
 * ```tsx
 * const { isConnected, error } = useWebSocket(
 *   {
 *     tenantId: 'tenant-123',
 *     token: 'auth-token',
 *   },
 *   {
 *     onHealthScoreUpdate: (data) => {
 *       setHealthScore(data.score);
 *     },
 *     onNewRecommendation: (data) => {
 *       setRecommendations(prev => [data, ...prev]);
 *     },
 *   }
 * );
 * ```
 */
export function useWebSocket(
    options: UseWebSocketOptions,
    handlers: WebSocketHandlers = {}
): UseWebSocketReturn {
    const {
        tenantId,
        token,
        baseUrl = 'ws://localhost:8001',
        reconnectAttempts = 5,
        reconnectDelay = 3000,
        enabled = true,
    } = options;

    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectCountRef = useRef(0);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const handlersRef = useRef(handlers);

    // Keep handlers ref up to date
    useEffect(() => {
        handlersRef.current = handlers;
    }, [handlers]);

    /**
     * Handle incoming WebSocket messages
     */
    const handleMessage = useCallback((event: MessageEvent) => {
        try {
            const message: WebSocketMessage = JSON.parse(event.data);

            console.log('[WebSocket] Received:', message.type, message);

            switch (message.type) {
                case 'connection_ack':
                    console.log('[WebSocket] Connection acknowledged');
                    setIsConnected(true);
                    setError(null);
                    reconnectCountRef.current = 0;
                    handlersRef.current.onConnect?.();
                    break;

                case 'heartbeat':
                    // Server heartbeat - respond with ping to keep alive
                    wsRef.current?.send(JSON.stringify({ type: 'ping' }));
                    break;

                case 'pong':
                    // Server responded to our ping
                    break;

                case 'health_score_update':
                    handlersRef.current.onHealthScoreUpdate?.(message.data as HealthScoreUpdateData);
                    break;

                case 'new_recommendation':
                    handlersRef.current.onNewRecommendation?.(message.data as NewRecommendationData);
                    break;

                case 'task_completed':
                    handlersRef.current.onTaskCompleted?.(message.data as TaskCompletedData);
                    break;

                case 'goal_progress_update':
                    handlersRef.current.onGoalProgressUpdate?.(message.data as GoalProgressUpdateData);
                    break;

                case 'subscription_ack':
                    console.log('[WebSocket] Subscription acknowledged');
                    break;

                default:
                    console.warn('[WebSocket] Unknown message type:', message.type);
            }
        } catch (err) {
            console.error('[WebSocket] Failed to parse message:', err);
        }
    }, []);

    /**
     * Connect to WebSocket server
     */
    const connect = useCallback(() => {
        if (!enabled || !tenantId || !token) {
            console.log('[WebSocket] Not connecting - missing requirements');
            return;
        }

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            console.log('[WebSocket] Already connected');
            return;
        }

        try {
            const wsUrl = `${baseUrl}/v1/tenants/${tenantId}/ws`;
            console.log('[WebSocket] Connecting to:', wsUrl);

            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('[WebSocket] Connection opened');
                setIsConnected(true);
                setError(null);
                reconnectCountRef.current = 0;
            };

            ws.onmessage = handleMessage;

            ws.onerror = (event) => {
                console.error('[WebSocket] Error:', event);
                setError('WebSocket connection error');
                handlersRef.current.onError?.(event);
            };

            ws.onclose = () => {
                console.log('[WebSocket] Connection closed');
                setIsConnected(false);
                wsRef.current = null;
                handlersRef.current.onDisconnect?.();

                // Attempt reconnect if not at max attempts
                if (reconnectCountRef.current < reconnectAttempts) {
                    reconnectCountRef.current++;
                    console.log(
                        `[WebSocket] Reconnecting (${reconnectCountRef.current}/${reconnectAttempts}) in ${reconnectDelay}ms...`
                    );

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, reconnectDelay);
                } else {
                    setError(`Failed to connect after ${reconnectAttempts} attempts`);
                }
            };
        } catch (err) {
            console.error('[WebSocket] Failed to create connection:', err);
            setError(err instanceof Error ? err.message : 'Failed to connect');
        }
    }, [enabled, tenantId, token, baseUrl, reconnectAttempts, reconnectDelay, handleMessage]);

    /**
     * Disconnect from WebSocket
     */
    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (wsRef.current) {
            console.log('[WebSocket] Disconnecting...');
            wsRef.current.close();
            wsRef.current = null;
            setIsConnected(false);
        }
    }, []);

    /**
     * Send message to server
     */
    const send = useCallback((message: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.warn('[WebSocket] Cannot send - not connected');
        }
    }, []);

    /**
     * Manual reconnect
     */
    const reconnect = useCallback(() => {
        disconnect();
        reconnectCountRef.current = 0;
        connect();
    }, [disconnect, connect]);

    // Connect on mount, disconnect on unmount
    useEffect(() => {
        connect();

        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    return {
        isConnected,
        error,
        send,
        reconnect,
    };
}
