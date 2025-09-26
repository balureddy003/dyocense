"""Gateways for invoking the decision kernel."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from services.common import KernelClient, KernelClientConfig, KernelClientError, dto

from .config import get_settings


class KernelGateway:
    """High-level wrapper around the kernel client."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.kernel_base_url:
            raise RuntimeError(
                "PLAN_KERNEL_BASE_URL is not configured. "
                "Run the kernel service and set the environment variable."
            )
        config = KernelClientConfig(
            base_url=str(settings.kernel_base_url),
            timeout=settings.kernel_timeout,
            api_key=settings.kernel_api_key,
        )
        self._client = KernelClient(config)

    def run_pipeline(self, payload: Mapping[str, Any]) -> dto.KernelRunResult:
        try:
            return self._client.run_pipeline(payload)
        except KernelClientError as exc:  # pragma: no cover - simple pass-through
            raise
