"""
Chat Service - Conversational AI assistant for business planning and analysis.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
import time
import uuid

from packages.kernel_common.deps import require_auth

app = FastAPI(
    title="Chat Service",
    version="0.1.0",
    description="AI-powered chat assistant for business insights and planning.",
)

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: dict = {}

class ChatResponse(BaseModel):
    reply: str
    context: dict = {}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    identity: dict = Depends(require_auth)
) -> ChatResponse:
    """
    Process chat messages and return AI-generated response.
    
    TODO: Integrate with actual LLM service (OpenAI, Azure OpenAI, etc.)
    Currently returns a helpful placeholder response.
    """
    tenant_id = identity.get("tenant_id")
    
    # Extract last user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    last_message = user_messages[-1].content if user_messages else ""
    
    # Simple intent-based routing (placeholder for actual LLM)
    reply = generate_response(last_message, request.context, tenant_id)
    
    return ChatResponse(
        reply=reply,
        context=request.context
    )


def generate_response(message: str, context: dict, tenant_id: str = None) -> str:
    """
    Generate a response based on user message and context.
    
    TODO: Replace with actual LLM integration.
    """
    message_lower = message.lower()
    
    # Intent detection patterns
    if any(word in message_lower for word in ["inventory", "stock", "warehouse"]):
        return (
            "I can help you optimize inventory levels. Key factors to consider include:\n"
            "- Current stock levels and demand patterns\n"
            "- Lead times from suppliers\n"
            "- Storage costs and capacity\n"
            "- Seasonal variations\n\n"
            "Would you like me to analyze your inventory data or create an optimization plan?"
        )
    
    if any(word in message_lower for word in ["forecast", "predict", "demand"]):
        return (
            "For accurate demand forecasting, I'll need to analyze:\n"
            "- Historical sales data (at least 6-12 months)\n"
            "- Seasonal trends and patterns\n"
            "- External factors (promotions, market changes)\n\n"
            "Do you have sales data you'd like me to analyze?"
        )
    
    if any(word in message_lower for word in ["cost", "reduce", "save", "optimize"]):
        return (
            "I can help identify cost reduction opportunities. Common areas include:\n"
            "- Inventory carrying costs\n"
            "- Supply chain optimization\n"
            "- Process improvements\n"
            "- Resource allocation\n\n"
            "Which area would you like to focus on first?"
        )
    
    if any(word in message_lower for word in ["plan", "strategy", "goal"]):
        return (
            "Let's create a strategic plan together. To get started, I need to understand:\n"
            "- Your primary business objective\n"
            "- Time horizon (weeks, months, quarters)\n"
            "- Key constraints or limitations\n"
            "- Success metrics\n\n"
            "What's the main goal you're trying to achieve?"
        )
    
    # Default response
    return (
        "I'm here to help with:\n"
        "- Inventory optimization and planning\n"
        "- Demand forecasting\n"
        "- Cost reduction strategies\n"
        "- Business planning and analysis\n\n"
        "What would you like to work on?"
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "chat"}


# -----------------------------
# OpenAI-compatible endpoints
# -----------------------------

class OAIMsg(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class OAIChatCompletionsRequest(BaseModel):
    model: Optional[str] = Field(default="dyocense-chat-mini")
    messages: List[OAIMsg]
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: Optional[bool] = Field(default=False)
    user: Optional[str] = None
    # vendor extensions for context passthrough
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional app-specific context")


class OAIChatMessage(BaseModel):
    role: Literal["assistant"]
    content: str


class OAIChatChoice(BaseModel):
    index: int
    message: OAIChatMessage
    finish_reason: Literal["stop", "length"] = "stop"


class OAIUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OAIChatCompletionsResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[OAIChatChoice]
    usage: OAIUsage


@app.post("/v1/chat/completions", response_model=OAIChatCompletionsResponse)
async def chat_completions(
    body: OAIChatCompletionsRequest,
    identity: dict = Depends(require_auth),
) -> OAIChatCompletionsResponse:
    """OpenAI-compatible chat completions endpoint.

    This provides a minimal subset of the OpenAI Chat Completions API so clients
    can integrate without custom adapters. It maps requests to the same internal
    generator used by /v1/chat and returns an OpenAI-shaped response.
    """
    tenant_id = identity.get("tenant_id")
    last_user = next((m.content for m in reversed(body.messages) if m.role == "user"), "")

    # Reuse the internal generator
    reply_text = generate_response(last_user, body.context or {}, tenant_id)

    # naive token accounting (placeholder)
    prompt_tokens = sum(len(m.content.split()) for m in body.messages)
    completion_tokens = len(reply_text.split())
    created_ts = int(time.time())

    return OAIChatCompletionsResponse(
        id=f"chatcmpl_{uuid.uuid4().hex[:24]}",
        created=created_ts,
        model=body.model or "dyocense-chat-mini",
        choices=[
            OAIChatChoice(
                index=0,
                message=OAIChatMessage(role="assistant", content=reply_text),
                finish_reason="stop",
            )
        ],
        usage=OAIUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


@app.get("/v1/models")
def list_models(identity: dict = Depends(require_auth)) -> Dict[str, Any]:
    """Minimal OpenAI-compatible models listing."""
    return {
        "data": [
            {
                "id": "dyocense-chat-mini",
                "object": "model",
                "owned_by": "dyocense",
            },
        ]
    }
