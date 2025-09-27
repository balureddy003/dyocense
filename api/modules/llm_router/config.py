"""Configuration for LLM router providers."""
from __future__ import annotations

import json
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderConfig(BaseModel):
    name: str = Field(..., description="Human readable provider name")
    provider_id: str = Field(..., description="Unique identifier used by clients")
    model: str = Field(..., description="Default model name")
    endpoint: Optional[str] = Field(default=None, description="Base URL for the provider")
    streaming: bool = Field(default=False, description="Whether streaming responses are supported")


class LLMRouterSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", extra="allow")

    providers_raw: Optional[str] = Field(
        default=None,
        description="JSON encoded list of providers",
    )

    @property
    def providers(self) -> List[LLMProviderConfig]:
        if self.providers_raw:
            try:
                data = json.loads(self.providers_raw)
                return [LLMProviderConfig.model_validate(item) for item in data]
            except json.JSONDecodeError:
                pass
        # Default providers inspired by LibreChat multi-provider setup
        return [
            LLMProviderConfig(
                name="OpenAI",
                provider_id="openai",
                model="gpt-4o-mini",
                endpoint="https://api.openai.com/v1",
                streaming=True,
            ),
            LLMProviderConfig(
                name="Azure OpenAI",
                provider_id="azure-openai",
                model="gpt-4o",
                streaming=True,
            ),
            LLMProviderConfig(
                name="Local Ollama",
                provider_id="ollama",
                model="llama3",
                endpoint="http://ollama:11434",
                streaming=False,
            ),
        ]


settings = LLMRouterSettings()
