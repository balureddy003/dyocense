"""
Chat Service - Conversational AI assistant for business planning and analysis.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
import time
import uuid
import os
import json
import logging
import sys

from packages.kernel_common.deps import require_auth

# Add packages to path for multi-agent imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chat Service",
    version="0.1.0",
    description="AI-powered chat assistant for business insights and planning.",
)

# Import multi-agent system
try:
    from packages.agents.multi_agent_system import OrchestratorAgent
    MULTI_AGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Multi-agent system not available: {e}")
    MULTI_AGENT_AVAILABLE = False
    OrchestratorAgent = None

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
    tenant_id = identity.get("tenant_id", "unknown")
    
    # Extract last user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    last_message = user_messages[-1].content if user_messages else ""
    
    # Simple intent-based routing (placeholder for actual LLM)
    reply = generate_response(last_message, request.context, tenant_id or "unknown")
    
    return ChatResponse(
        reply=reply,
        context=request.context
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
    # Function calling support
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of tools/functions for LLM to call")
    tool_choice: Optional[str] = Field(default=None, description="How to use tools: 'auto', 'none', or specific function")


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
    can integrate without custom adapters. It uses real LLM providers (OpenAI, Azure, Ollama)
    based on environment configuration.
    """
    tenant_id = identity.get("tenant_id", "unknown")
    
    # Try to use real LLM if configured
    reply_text = await invoke_llm_chat(body.messages, body.context or {}, tenant_id, body.tools)
    
    # Fallback to hardcoded responses if LLM unavailable
    if not reply_text:
        logger.warning("LLM unavailable, using fallback responses")
        last_user = next((m.content for m in reversed(body.messages) if m.role == "user"), "")
        reply_text = generate_response(last_user, body.context or {}, tenant_id or "unknown")

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


async def invoke_llm_chat(
    messages: List[OAIMsg],
    context: Dict[str, Any],
    tenant_id: str,
    tools: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """
    Invoke LLM based on environment configuration.
    Supports OpenAI, Azure OpenAI, and Ollama.
    """
    provider = os.getenv("LLM_PROVIDER", "").lower()
    
    if provider == "openai":
        return await invoke_openai_chat(messages, context, tools)
    elif provider == "azure":
        return await invoke_azure_chat(messages, context, tools)
    elif provider == "ollama":
        return await invoke_ollama_chat(messages, context)
    else:
        logger.info("No LLM_PROVIDER configured, using fallback responses")
        return None


async def invoke_openai_chat(
    messages: List[OAIMsg],
    context: Dict[str, Any],
    tools: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """Call OpenAI API for chat completion."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not installed")
        return None

    try:
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Convert messages to OpenAI format
        oai_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        # Add context as a system message if provided
        if context:
            context_msg = f"Context: {json.dumps(context)}"
            oai_messages.insert(0, {"role": "system", "content": context_msg})
        
        # Prepare API call params
        params = {
            "model": model,
            "messages": oai_messages,
            "temperature": 0.2,
        }
        
        # Add tools if provided (function calling)
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        response = client.chat.completions.create(**params)
        
        # Handle function calling response
        if response.choices[0].message.tool_calls:
            # For now, return a formatted response indicating tools were called
            # In production, you'd execute the tools and continue the conversation
            tool_calls = response.choices[0].message.tool_calls
            formatted_response = response.choices[0].message.content or ""
            
            # Add markers for frontend to parse
            for tool_call in tool_calls:
                if tool_call.function.name == "show_connector_options":
                    args = json.loads(tool_call.function.arguments)
                    connectors = args.get("connectors", [])
                    formatted_response += f"\n\n[SHOW_CONNECTORS: {', '.join(connectors)}]"
                elif tool_call.function.name == "show_data_uploader":
                    args = json.loads(tool_call.function.arguments)
                    format_type = args.get("format", "csv")
                    formatted_response += f"\n\n[SHOW_UPLOADER: {format_type}]"
            
            return formatted_response or "I can help with that."
        
        return response.choices[0].message.content or ""
        
    except Exception as exc:
        logger.error(f"OpenAI API error: {exc}")
        return None


async def invoke_azure_chat(
    messages: List[OAIMsg],
    context: Dict[str, Any],
    tools: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """Call Azure OpenAI for chat completion."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    if not (endpoint and api_key and deployment):
        logger.warning("Azure OpenAI environment variables not fully configured")
        return None

    try:
        from openai import AzureOpenAI
    except ImportError:
        logger.warning("openai package not installed for Azure")
        return None

    try:
        client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-02-15-preview",
            azure_endpoint=endpoint
        )
        
        oai_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        if context:
            context_msg = f"Context: {json.dumps(context)}"
            oai_messages.insert(0, {"role": "system", "content": context_msg})
        
        params = {
            "model": deployment,
            "messages": oai_messages,
            "temperature": 0.2,
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        response = client.chat.completions.create(**params)
        
        # Handle function calling
        if response.choices[0].message.tool_calls:
            tool_calls = response.choices[0].message.tool_calls
            formatted_response = response.choices[0].message.content or ""
            
            for tool_call in tool_calls:
                if tool_call.function.name == "show_connector_options":
                    args = json.loads(tool_call.function.arguments)
                    connectors = args.get("connectors", [])
                    formatted_response += f"\n\n[SHOW_CONNECTORS: {', '.join(connectors)}]"
                elif tool_call.function.name == "show_data_uploader":
                    args = json.loads(tool_call.function.arguments)
                    format_type = args.get("format", "csv")
                    formatted_response += f"\n\n[SHOW_UPLOADER: {format_type}]"
            
            return formatted_response or "I can help with that."
        
        return response.choices[0].message.content or ""
        
    except Exception as exc:
        logger.error(f"Azure OpenAI API error: {exc}")
        return None


async def invoke_ollama_chat(
    messages: List[OAIMsg],
    context: Dict[str, Any]
) -> Optional[str]:
    """Call Ollama for chat completion."""
    import httpx
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    
    try:
        # Build a single prompt from messages
        prompt = "\n\n".join([f"{m.role}: {m.content}" for m in messages])
        
        if context:
            prompt = f"Context: {json.dumps(context)}\n\n{prompt}"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        timeout_cfg = httpx.Timeout(120.0, read=120.0, connect=30.0)
        
        response = httpx.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=timeout_cfg,
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("response") or "").strip()
        
    except Exception as exc:
        logger.error(f"Ollama API error: {exc}")
        return None


def generate_response(message: str, context: dict, tenant_id: str) -> str:
    """
    Generate a fallback response when LLM is unavailable.
    Simple intent-based routing (placeholder for actual LLM).
    """
    message_lower = message.lower()
    
    # Intent detection patterns
    if any(word in message_lower for word in ["inventory", "stock", "warehouse"]):
        return (
            "I can help you optimize inventory levels. To provide accurate recommendations, "
            "I'll need historical inventory data. [SHOW_UPLOADER: csv]"
        )
    
    if any(word in message_lower for word in ["forecast", "predict", "demand", "sales"]):
        return (
            "For accurate demand forecasting, I'll need historical sales data. "
            "Do you use a CRM system, or do you have sales data in spreadsheets? [SHOW_CONNECTORS: salesforce, hubspot, pipedrive]"
        )
    
    if any(word in message_lower for word in ["cost", "reduce", "save", "optimize"]):
        return (
            "I can help identify cost reduction opportunities. To analyze your costs, "
            "I'll need data from your accounting system. [SHOW_CONNECTORS: xero, quickbooks, sage]"
        )
    
    if any(word in message_lower for word in ["plan", "strategy", "goal"]):
        return (
            "Let's create a strategic plan together. To get started, I need to understand:\n"
            "- Your primary business objective\n"
            "- Time horizon (weeks, months, quarters)\n"
            "- Key constraints or limitations\n\n"
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


@app.post("/v1/chat/multi-agent", response_model=Dict[str, Any])
async def multi_agent_chat(
    request: Dict[str, Any],
    identity: dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Process complex business goals using multi-agent orchestration.
    
    Request format:
    {
        "goal": "Increase sales by 20% in Q2",
        "context": {
            "data_sources": [...],
            "constraints": {...}
        },
        "llm_config": {
            "provider": "azure",  // or "openai"
            "endpoint": "...",
            "api_key": "...",
            "deployment": "gpt-4o-mini"
        }
    }
    
    Returns:
    {
        "response": "Final business plan...",
        "goal_analysis": {...},
        "data_analysis": {...},
        "model_results": {...},
        "recommendations": {...},
        "conversation": [...]
    }
    """
    if not MULTI_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Multi-agent system not available. Install langgraph: pip install langgraph langchain-openai"
        )
    
    goal = request.get("goal")
    if not goal:
        raise HTTPException(status_code=400, detail="'goal' is required")
    
    context = request.get("context", {})
    llm_config = request.get("llm_config", {})
    
    # Get LLM configuration from env or request
    provider = llm_config.get("provider", os.getenv("LLM_PROVIDER", "azure"))
    
    # Create orchestrator
    if OrchestratorAgent is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-agent system module not properly loaded"
        )
    
    orchestrator = OrchestratorAgent()
    
    # Configure LLM
    if provider == "azure":
        orchestrator.configure_llm(
            provider="azure",
            azure_endpoint=llm_config.get("endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=llm_config.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY"),
            deployment_name=llm_config.get("deployment") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            api_version=llm_config.get("api_version", "2024-02-15-preview"),
            temperature=llm_config.get("temperature", 0.2)
        )
    else:
        orchestrator.configure_llm(
            provider="openai",
            api_key=llm_config.get("api_key") or os.getenv("OPENAI_API_KEY"),
            model=llm_config.get("model", "gpt-4o-mini"),
            temperature=llm_config.get("temperature", 0.2)
        )
    
    # Build the agent graph
    orchestrator.build_graph()
    
    # Process the goal
    try:
        result = await orchestrator.process_goal(goal, context)
        return result
    except Exception as e:
        logger.error(f"Multi-agent processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multi-agent processing failed: {str(e)}"
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
            {
                "id": "dyocense-multi-agent",
                "object": "model",
                "owned_by": "dyocense",
                "description": "Multi-agent orchestration for complex business goals"
            },
        ]
    }

