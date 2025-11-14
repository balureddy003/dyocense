"""
AI Coach API Routes

Endpoints for conversational AI business coaching.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, CurrentUser
from backend.services.coach.service import get_coach_service

router = APIRouter()


# Request/Response Models
# =================================================================

class ChatRequest(BaseModel):
    """Chat request."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[UUID] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response."""
    session_id: str
    response: str
    provider: Optional[str] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None
    intent: Optional[str] = None


class GoalPlanResponse(BaseModel):
    """Goal planning response."""
    session_id: str
    response: str
    goals: list[dict]
    intent: str


# Endpoints
# =================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with AI business coach.
    
    The coach can:
    - Answer general business questions
    - Help set SMART goals
    - Analyze root causes of metric changes
    - Provide optimization recommendations
    
    Requests are routed to local (70%) or cloud (30%) LLM based on complexity.
    """
    coach = get_coach_service()
    
    try:
        result = await coach.chat(
            message=request.message,
            session_id=request.session_id,
            user_id=UUID(user["user_id"]),
            tenant_id=UUID(user["tenant_id"]),
            db=db,
            stream=request.stream
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/goals/plan", response_model=GoalPlanResponse)
async def plan_goals(
    request: ChatRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate SMART goals from high-level objective.
    
    Example:
    - Input: "I want to increase revenue"
    - Output: 3-5 SMART goals with specific metrics, targets, and deadlines
    """
    coach = get_coach_service()
    
    try:
        result = await coach.chat(
            message=request.message,
            session_id=request.session_id,
            user_id=UUID(user["user_id"]),
            tenant_id=UUID(user["tenant_id"]),
            db=db,
            stream=False
        )
        
        return GoalPlanResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Goal planning failed: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get coaching session history."""
    from backend.models import CoachingSession
    from sqlalchemy import select
    
    result = await db.execute(
        select(CoachingSession).where(
            CoachingSession.session_id == session_id,
            CoachingSession.tenant_id == UUID(user["tenant_id"])
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": str(session.session_id),
        "messages": session.messages,
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }


@router.get("/history")
async def get_history():
    """Get chat history"""
    return {"message": "Chat history - to be implemented"}
