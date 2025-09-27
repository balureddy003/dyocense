"""Lightweight client for invoking an LLM router or provider."""
from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional

try:  # pragma: no cover - optional dependency to keep kernel lightweight
    import requests
except ImportError:  # pragma: no cover - gracefully degrade when unavailable
    requests = None  # type: ignore


@dataclass(slots=True)
class LLMProvider:
    provider_id: str
    name: str
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    streaming: bool = False


@dataclass(slots=True)
class LLMClientConfig:
    """Configuration for talking to multiple LLM providers."""

    providers: List[LLMProvider]
    default_provider_id: Optional[str] = None
    timeout: float = 15.0
    enable: bool = True

    @classmethod
    def from_env(cls) -> "LLMClientConfig":
        registry = os.getenv("LLM_PROVIDERS")
        providers: List[LLMProvider]
        if registry:
            try:
                data = json.loads(registry)
                providers = [LLMProvider(**item) for item in data]
            except json.JSONDecodeError:
                providers = cls._default_providers()
        else:
            providers = cls._default_providers()

        default_id = os.getenv("LLM_DEFAULT_PROVIDER") or (providers[0].provider_id if providers else None)
        timeout = float(os.getenv("LLM_TIMEOUT", "15"))
        enable = os.getenv("LLM_DISABLED", "false").lower() not in {"1", "true", "yes"}
        return cls(providers=providers, default_provider_id=default_id, timeout=timeout, enable=enable)

    @staticmethod
    def _default_providers() -> List[LLMProvider]:
        base_url = os.getenv("LLM_BASE_URL")
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        return [
            LLMProvider(
                provider_id="openai",
                name="OpenAI",
                model=model,
                base_url=base_url,
                api_key=api_key,
                streaming=True,
            )
        ]


class LLMInvocationError(RuntimeError):
    """Raised when the LLM provider cannot fulfil a request."""


class LLMClient:
    """Thin wrapper around a chat-completions style endpoint.

    The client gracefully falls back to deterministic summaries when no LLM is
    configured or when the provider errors. This ensures the kernel pipeline can
    still complete while surfacing useful narrative context to end users.
    """

    def __init__(
        self,
        config: Optional[LLMClientConfig] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._config = config or LLMClientConfig.from_env()
        self._providers = {provider.provider_id: provider for provider in self._config.providers}
        self._default_provider_id = self._config.default_provider_id or next(iter(self._providers), None)
        if requests is not None:
            self._session = session or requests.Session()
        else:
            self._session = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def summarize_plan(
        self,
        *,
        context: Mapping[str, Any],
        solution: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
        policy: Optional[Mapping[str, Any]] = None,
        provider_id: Optional[str] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(context, solution, diagnostics, policy)
        if stream:
            # Collect streamed chunks into a single message for now.
            chunks = list(self.stream_chat(prompt, provider_id=provider_id))
            message = "".join(chunks) or "(empty response)"
            return {
                "text": message,
                "source": "llm-stream",
                "model": self._resolve_provider(provider_id).model,
                "prompt": prompt,
            }
        return self.chat(prompt, provider_id=provider_id)

    def chat(
        self,
        prompt: str,
        *,
        provider_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        functions: Optional[List[Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        provider = self._resolve_provider(provider_id)
        if self._can_call_provider(provider):
            try:
                return self._invoke_remote(prompt, provider, metadata, functions)
            except Exception as exc:  # pragma: no cover - network path
                return self._fallback_summary(prompt, {}, {}, error=str(exc), provider=provider)
        return self._fallback_summary(prompt, {}, {}, error=None, provider=provider)

    def stream_chat(
        self,
        prompt: str,
        *,
        provider_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        functions: Optional[List[Mapping[str, Any]]] = None,
    ) -> Iterator[str]:
        provider = self._resolve_provider(provider_id)
        if self._can_call_provider(provider) and provider.streaming and requests is not None:
            # Placeholder streaming: request completion then yield chunks.
            result = self._invoke_remote(prompt, provider, metadata, functions)
            text = result.get("text") or ""
            for chunk in self._chunk_text(text):
                yield chunk
        else:
            fallback = self._fallback_summary(prompt, {}, {}, error=None, provider=provider)
            for chunk in self._chunk_text(fallback.get("text", "")):
                yield chunk

    def list_providers(self) -> List[LLMProvider]:
        return list(self._providers.values())

    def get_provider(self, provider_id: Optional[str] = None) -> LLMProvider:
        return self._resolve_provider(provider_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_provider(self, provider_id: Optional[str]) -> LLMProvider:
        provider = self._providers.get(provider_id) if provider_id else None
        if provider is None and self._default_provider_id:
            provider = self._providers.get(self._default_provider_id)
        if provider is None and self._providers:
            provider = next(iter(self._providers.values()))
        if provider is None:
            # create fallback provider
            provider = LLMProvider(provider_id="fallback", name="Fallback", model="mock")
        return provider

    def _can_call_provider(self, provider: LLMProvider) -> bool:
        return bool(self._config.enable and provider.base_url)

    def _build_prompt(
        self,
        context: Mapping[str, Any],
        solution: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
        policy: Optional[Mapping[str, Any]],
    ) -> str:
        kpis = solution.get("kpis", {})
        primary_kpis = ", ".join(f"{key}: {value}" for key, value in sorted(kpis.items())) or "(none)"
        service_score = diagnostics.get("simulation", {}).get("mean_service")
        binding = ", ".join(solution.get("binding_constraints", [])) or "(none)"
        policy_txt = "allow" if not policy else ("allow" if policy.get("allow", True) else "deny")
        return (
            "You are a supply-chain planning analyst. Summarize the optimization output "
            "for business stakeholders. Highlight KPI performance, constraint drivers, "
            "and service-level implications."
            f"\nContext SKUs: {len(context.get('skus', []))}; periods: {len(context.get('periods', []))}."
            f"\nPrimary KPIs: {primary_kpis}."
            f"\nBinding constraints: {binding}."
            f"\nMean service in simulation: {service_score if service_score is not None else 'unknown'}."
            f"\nPolicy decision: {policy_txt}."
        )

    def _invoke_remote(
        self,
        prompt: str,
        provider: LLMProvider,
        metadata: Optional[Mapping[str, Any]],
        functions: Optional[List[Mapping[str, Any]]],
    ) -> Dict[str, Any]:  # pragma: no cover - network path
        if requests is None or provider.base_url is None:
            raise LLMInvocationError("requests library unavailable or provider missing base_url")
        url = provider.base_url.rstrip("/") + "/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if provider.api_key:
            headers["Authorization"] = f"Bearer {provider.api_key}"
        payload = {
            "model": provider.model,
            "messages": [
                {"role": "system", "content": "You are an expert supply-chain planning analyst."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if metadata:
            payload["metadata"] = dict(metadata)
        if functions:
            payload["tools"] = list(functions)
        session = self._session or requests.Session()
        response = session.post(url, json=payload, headers=headers, timeout=self._config.timeout)
        if response.status_code >= 400:
            raise LLMInvocationError(f"LLM router returned {response.status_code}: {response.text}")
        data = response.json()
        message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        return {
            "text": message.strip() or "(empty response)",
            "source": "llm",
            "model": data.get("model", provider.model),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        }

    def _fallback_summary(
        self,
        prompt: str,
        solution: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
        *,
        error: Optional[str],
        provider: Optional[LLMProvider] = None,
    ) -> Dict[str, Any]:
        steps = solution.get("steps", [])
        top_steps = "; ".join(
            f"{step.get('sku')}→{step.get('supplier')} {step.get('quantity')}@{step.get('period')}"
            for step in steps[:3]
        ) or "(no steps)"
        gap = solution.get("gap")
        service = diagnostics.get("simulation", {}).get("mean_service")
        text_lines = [
            "Fallback summary (LLM not configured).",
            f"Top actions: {top_steps}.",
            f"Objective gap: {gap if gap is not None else 'n/a'}.",
            f"Mean service: {service if service is not None else 'n/a'}.",
        ]
        if error:
            text_lines.append(f"LLM error: {error}")
        return {
            "text": "\n".join(text_lines),
            "source": "fallback",
            "model": provider.model if provider else None,
            "error": error,
            "prompt": prompt,
        }

    @staticmethod
    def _chunk_text(text: str, size: int = 60) -> Iterable[str]:
        if not text:
            yield ""
            return
        for index in range(0, len(text), size):
            yield text[index : index + size]
