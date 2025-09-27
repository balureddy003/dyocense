"""Schemas for LLM router endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProviderResponse(BaseModel):
    provider_id: str
    name: str
    model: str
    endpoint: Optional[str] = None
    streaming: bool = False


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="User prompt to send to the selected provider")
    provider_id: str = Field(..., description="Target provider identifier")
    model: Optional[str] = Field(default=None, description="Override default model")


class ChatResponse(BaseModel):
    provider_id: str
    model: str
    message: str
    tokens_estimated: int
    streaming: bool = False
