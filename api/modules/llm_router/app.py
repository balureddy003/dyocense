"""LLM router endpoints inspired by LibreChat provider switching."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import ChatRequest, ChatResponse, ProviderResponse
from .service import router_service


router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/providers", response_model=list[ProviderResponse])
def list_providers() -> list[ProviderResponse]:
    return [
        ProviderResponse(
            provider_id=provider.provider_id,
            name=provider.name,
            model=provider.model,
            endpoint=provider.base_url,
            streaming=provider.streaming,
        )
        for provider in router_service.providers
    ]


@router.post("/chat", response_model=ChatResponse)
def chat_with_provider(request: ChatRequest) -> ChatResponse:
    try:
        payload = router_service.chat(provider_id=request.provider_id, prompt=request.prompt)
        return ChatResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/route/test", response_model=ChatResponse)
def test_route(request: ChatRequest) -> ChatResponse:
    """Alias for compatibility with LibreChat's test endpoint."""
    return chat_with_provider(request)
