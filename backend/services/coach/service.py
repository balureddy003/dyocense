"""
AI Coach Service - Main Orchestration

Coordinates LLM router, agents, and streaming responses.
"""

from __future__ import annotations

import logging
import json
from typing import Any, AsyncIterator
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import CoachingSession, User
from backend.services.coach.llm_router import get_llm_router, LLMProvider
from backend.agents.goal_planner import get_goal_planner
from backend.agents.evidence_analyzer import get_evidence_analyzer

logger = logging.getLogger(__name__)


class CoachService:
    """
    AI Coach orchestration service.
    
    Features:
    - Chat with context from history
    - Goal planning and decomposition
    - Root cause analysis
    - Streaming responses (SSE)
    """
    
    def __init__(self):
        """Initialize coach service."""
        self.llm_router = get_llm_router()
        self.goal_planner = get_goal_planner()
        self.evidence_analyzer = get_evidence_analyzer()
    
    async def chat(
        self,
        message: str,
        session_id: UUID | None,
        user_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
        stream: bool = False
    ) -> dict[str, Any] | AsyncIterator[str]:
        """
        Chat with AI coach.
        
        Args:
            message: User message
            session_id: Existing session ID (or None for new)
            user_id: User ID
            tenant_id: Tenant ID
            db: Database session
            stream: Whether to stream response
        
        Returns:
            Response dict or SSE stream
        """
        logger.info(f"Coach chat: user={user_id}, session={session_id}")
        
        # Load or create session
        session = await self._get_or_create_session(
            session_id, user_id, tenant_id, db
        )
        
        # Check for special intents
        intent = self._detect_intent(message)
        
        if intent == "goal_planning":
            return await self._handle_goal_planning(message, session, db)
        elif intent == "root_cause":
            return await self._handle_root_cause(message, session, db)
        else:
            return await self._handle_general_chat(message, session, db, stream)
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message."""
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in ["goal", "achieve", "target", "objective"]):
            return "goal_planning"
        elif any(kw in message_lower for kw in ["why", "cause", "reason", "drop", "spike"]):
            return "root_cause"
        else:
            return "general"
    
    async def _get_or_create_session(
        self,
        session_id: UUID | None,
        user_id: UUID,
        tenant_id: UUID,
        db: AsyncSession
    ) -> CoachingSession:
        """Get existing session or create new one."""
        if session_id:
            result = await db.execute(
                select(CoachingSession).where(CoachingSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                return session
        
        # Create new session
        session = CoachingSession(
            session_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            messages=[],
            extra_data={}
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    
    async def _handle_goal_planning(
        self,
        message: str,
        session: CoachingSession,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Handle goal planning request."""
        logger.info("Handling goal planning request")
        
        # Use goal planner agent
        plan_result = await self.goal_planner.plan(
            user_goal=message,
            context={"tenant_id": str(session.tenant_id)}
        )
        
        # Format response
        response_text = self._format_goal_plan(plan_result)
        
        # Update session
        session.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.messages.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"intent": "goal_planning", "goals": plan_result["goals"]}
        })
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "session_id": str(session.session_id),
            "response": response_text,
            "goals": plan_result["goals"],
            "intent": "goal_planning"
        }
    
    async def _handle_root_cause(
        self,
        message: str,
        session: CoachingSession,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Handle root cause analysis request."""
        logger.info("Handling root cause analysis request")
        
        # Extract metric and date (simplified - should use NER)
        metric_name = "revenue"  # Default
        anomaly_date = datetime.utcnow()
        
        # Use evidence analyzer agent
        analysis = await self.evidence_analyzer.analyze_root_cause(
            metric_name=metric_name,
            anomaly_date=anomaly_date,
            tenant_id=str(session.tenant_id)
        )
        
        # Format response
        response_text = analysis["explanation"]
        
        # Update session
        session.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.messages.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"intent": "root_cause", "analysis": analysis}
        })
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "session_id": str(session.session_id),
            "response": response_text,
            "analysis": analysis,
            "intent": "root_cause"
        }
    
    async def _handle_general_chat(
        self,
        message: str,
        session: CoachingSession,
        db: AsyncSession,
        stream: bool = False
    ) -> dict[str, Any]:
        """Handle general chat request."""
        logger.info("Handling general chat request")
        
        # Build context from history
        history = session.messages[-10:] if session.messages else []
        
        # System prompt
        system_prompt = """You are an AI business coach for small and medium businesses (SMBs).

Your role:
- Help business owners make data-driven decisions
- Provide actionable insights from their metrics
- Suggest optimization opportunities
- Explain complex concepts simply

Be concise, practical, and encouraging."""
        
        # Generate response
        llm_response = await self.llm_router.generate(
            query=message,
            system_prompt=system_prompt,
            context={"history": history}
        )
        
        response_text = llm_response["text"]
        
        # Update session
        session.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.messages.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "provider": llm_response["provider"],
                "tokens": llm_response["tokens"],
                "cost": llm_response["cost"]
            }
        })
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "session_id": str(session.session_id),
            "response": response_text,
            "provider": llm_response["provider"],
            "tokens": llm_response["tokens"],
            "cost": llm_response["cost"]
        }
    
    def _format_goal_plan(self, plan_result: dict[str, Any]) -> str:
        """Format goal plan as natural language."""
        goals = plan_result.get("goals", [])
        
        response = f"I've created a plan with {len(goals)} SMART goals:\n\n"
        
        for i, goal in enumerate(goals, 1):
            response += f"{i}. **{goal['title']}**\n"
            response += f"   - Current: {goal['current_value']} {goal['unit']}\n"
            response += f"   - Target: {goal['target_value']} {goal['unit']}\n"
            response += f"   - Deadline: {goal['deadline'][:10]}\n"
            response += f"   - {goal['description']}\n\n"
        
        response += "Would you like me to break down any of these goals into smaller action steps?"
        
        return response


# Global service instance
_service: CoachService | None = None


def get_coach_service() -> CoachService:
    """Get or create global coach service."""
    global _service
    if _service is None:
        _service = CoachService()
    return _service
