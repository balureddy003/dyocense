"""
WebSocket Manager for Real-Time Coach V6 Updates

Manages WebSocket connections and broadcasts real-time updates for:
- Health score changes
- New recommendations
- Task completion notifications
- Goal progress updates
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from packages.kernel_common.logging import configure_logging

logger = configure_logging("websocket-manager")


class ConnectionManager:
    """
    Manages WebSocket connections per tenant.
    
    Architecture:
    - One WebSocket per browser tab
    - Multiple connections per tenant (multi-device support)
    - Automatic cleanup on disconnect
    - Heartbeat to detect dead connections
    """
    
    def __init__(self):
        # tenant_id -> set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        # WebSocket -> tenant_id mapping for quick lookup
        self.connection_to_tenant: Dict[WebSocket, str] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: Optional[str] = None):
        """
        Accept new WebSocket connection and register it for a tenant.
        
        Args:
            websocket: FastAPI WebSocket instance
            tenant_id: Tenant identifier
            user_id: Optional user identifier for multi-user tenants
        """
        await websocket.accept()
        
        self.active_connections[tenant_id].add(websocket)
        self.connection_to_tenant[websocket] = tenant_id
        self.connection_metadata[websocket] = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
        }
        
        logger.debug(f"WebSocket connected for tenant {tenant_id}. Active connections: {len(self.active_connections[tenant_id])}")
        
        # Send connection acknowledgment
        await self.send_personal_message(websocket, {
            "type": "connection_ack",
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection and clean up metadata.
        
        Args:
            websocket: FastAPI WebSocket instance to disconnect
        """
        tenant_id = self.connection_to_tenant.get(websocket)
        
        if tenant_id:
            self.active_connections[tenant_id].discard(websocket)
            
            # Clean up empty tenant entries
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
            
            logger.debug(f"WebSocket disconnected for tenant {tenant_id}. Remaining: {len(self.active_connections.get(tenant_id, []))}")
        
        # Clean up mappings
        self.connection_to_tenant.pop(websocket, None)
        self.connection_metadata.pop(websocket, None)
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send message to a specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection
            message: Message dictionary to send (will be JSON serialized)
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_tenant(self, tenant_id: str, message: Dict[str, Any]):
        """
        Broadcast message to all connections for a specific tenant.
        
        Args:
            tenant_id: Target tenant identifier
            message: Message dictionary to send (will be JSON serialized)
        """
        connections = self.active_connections.get(tenant_id, set())
        
        if not connections:
            logger.debug(f"No active connections for tenant {tenant_id}")
            return
        
        logger.info(f"Broadcasting to {len(connections)} connections for tenant {tenant_id}: {message.get('type', 'unknown')}")
        
        # Send to all connections, track failures
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to connection: {e}")
                disconnected.append(connection)
        
        # Clean up failed connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_health_score_update(
        self,
        tenant_id: str,
        score: int,
        previous_score: int,
        components: Dict[str, int],
        alerts: list,
        signals: list,
    ):
        """
        Broadcast health score update to all tenant connections.
        
        Args:
            tenant_id: Target tenant
            score: New health score (0-100)
            previous_score: Previous health score
            components: Component scores breakdown
            alerts: Critical alerts array
            signals: Positive signals array
        """
        message = {
            "type": "health_score_update",
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "score": score,
                "previousScore": previous_score,
                "trend": "up" if score > previous_score else "down" if score < previous_score else "stable",
                "components": components,
                "alerts": alerts,
                "signals": signals,
            },
        }
        await self.broadcast_to_tenant(tenant_id, message)
    
    async def broadcast_new_recommendation(
        self,
        tenant_id: str,
        recommendation: Dict[str, Any],
    ):
        """
        Broadcast new coach recommendation to all tenant connections.
        
        Args:
            tenant_id: Target tenant
            recommendation: Recommendation object with id, priority, title, actions, etc.
        """
        message = {
            "type": "new_recommendation",
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": recommendation,
        }
        await self.broadcast_to_tenant(tenant_id, message)
    
    async def broadcast_task_completed(
        self,
        tenant_id: str,
        task_id: str,
        task_title: str,
        goal_id: Optional[str] = None,
    ):
        """
        Broadcast task completion notification to all tenant connections.
        
        Args:
            tenant_id: Target tenant
            task_id: Completed task ID
            task_title: Task title for display
            goal_id: Associated goal ID if applicable
        """
        message = {
            "type": "task_completed",
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "taskId": task_id,
                "taskTitle": task_title,
                "goalId": goal_id,
            },
        }
        await self.broadcast_to_tenant(tenant_id, message)
    
    async def broadcast_goal_progress_update(
        self,
        tenant_id: str,
        goal_id: str,
        goal_title: str,
        progress: float,
        status: str,
    ):
        """
        Broadcast goal progress update to all tenant connections.
        
        Args:
            tenant_id: Target tenant
            goal_id: Goal identifier
            goal_title: Goal title for display
            progress: Progress percentage (0-100)
            status: Goal status (on_track, at_risk, blocked, etc.)
        """
        message = {
            "type": "goal_progress_update",
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "goalId": goal_id,
                "goalTitle": goal_title,
                "progress": progress,
                "status": status,
            },
        }
        await self.broadcast_to_tenant(tenant_id, message)
    
    async def send_heartbeat(self):
        """
        Send heartbeat ping to all connections to detect dead connections.
        Should be called periodically (e.g., every 30 seconds).
        """
        disconnected = []
        
        for tenant_id, connections in list(self.active_connections.items()):
            for connection in list(connections):
                try:
                    await connection.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    logger.error(f"Heartbeat failed for tenant {tenant_id}: {e}")
                    disconnected.append(connection)
        
        # Clean up dead connections
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_count(self, tenant_id: str) -> int:
        """
        Get number of active connections for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections.get(tenant_id, set()))
    
    def get_all_connection_counts(self) -> Dict[str, int]:
        """
        Get connection counts for all tenants.
        
        Returns:
            Dictionary mapping tenant_id to connection count
        """
        return {
            tenant_id: len(connections)
            for tenant_id, connections in self.active_connections.items()
        }


# Global singleton instance
manager = ConnectionManager()


async def start_heartbeat_task():
    """
    Background task that sends periodic heartbeats to detect dead connections.
    Should be started when the FastAPI app starts.
    """
    while True:
        await asyncio.sleep(30)  # Heartbeat every 30 seconds
        try:
            await manager.send_heartbeat()
        except Exception as e:
            logger.error(f"Heartbeat task error: {e}")
