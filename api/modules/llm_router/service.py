"""LLM router service backed by kernel.llm.client."""
from __future__ import annotations

from typing import List

from kernel.llm.client import LLMClient, LLMClientConfig, LLMProvider

from .config import settings


class LLMRouterService:
    def __init__(self, client: LLMClient | None = None) -> None:
        providers = [
            LLMProvider(
                provider_id=provider.provider_id,
                name=provider.name,
                model=provider.model,
                base_url=provider.endpoint,
                streaming=provider.streaming,
            )
            for provider in settings.providers
        ]
        config = LLMClientConfig(
            providers=providers,
            default_provider_id=settings.providers[0].provider_id if settings.providers else None,
        )
        self._client = client or LLMClient(config)

    @property
    def providers(self) -> List[LLMProvider]:
        return self._client.list_providers()

    def chat(self, *, provider_id: str, prompt: str) -> dict[str, object]:
        provider_ids = {provider.provider_id for provider in self.providers}
        if provider_id not in provider_ids:
            raise ValueError(f"Unknown provider '{provider_id}'")
        result = self._client.chat(prompt, provider_id=provider_id)
        provider = self._client.get_provider(provider_id)
        completion = result.get("completion_tokens") or 0
        prompt_tokens = result.get("prompt_tokens") or 0
        return {
            "provider_id": provider.provider_id,
            "model": provider.model,
            "message": result.get("text", ""),
            "tokens_estimated": int(prompt_tokens or 0) + int(completion or 0),
            "streaming": provider.streaming,
        }

    def stream_chat(self, *, provider_id: str, prompt: str) -> List[str]:
        return list(self._client.stream_chat(prompt, provider_id=provider_id))


router_service = LLMRouterService()
