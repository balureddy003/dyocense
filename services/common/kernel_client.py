"""HTTP client for interacting with the kernel services."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional

import requests
from requests import Response

from . import dto

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class KernelClientConfig:
    base_url: str
    timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    api_key: Optional[str] = None


class KernelClientError(RuntimeError):
    """Raised when the kernel client cannot fulfil a request."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class KernelClient:
    """Minimal synchronous client that wraps kernel REST endpoints with retry/backoff."""

    def __init__(self, config: KernelClientConfig, session: Optional[requests.Session] = None) -> None:
        self._config = config
        self._session = session or requests.Session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def forecast_scenarios(self, payload: Mapping[str, Any]) -> dto.ScenarioSet:
        result = self._request_json("POST", "/forecast/scenarios", json_payload=payload)
        return dto.ScenarioSet.from_dict(result)

    def compile_model(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        result = self._request_json("POST", "/optiguide/compile", json_payload=payload)
        # Caller may want both raw payload and typed hints; return raw map for flexibility.
        return result

    def solve_model(self, payload: Mapping[str, Any]) -> dto.KernelRunResult:
        result = self._request_json("POST", "/optimizer/solve", json_payload=payload)
        # Some deployments wrap the solution in {"solution": ...}. Support both shapes.
        if "solution" in result and "diagnostics" in result:
            envelope = result
        else:
            envelope = {"solution": result}
        return dto.KernelRunResult.from_dict({
            "evidence_ref": result.get("evidence_ref", ""),
            "solution": envelope.get("solution", {}),
            "diagnostics": envelope.get("diagnostics", {}),
            "policy": envelope.get("policy"),
        })

    def run_pipeline(self, payload: Mapping[str, Any]) -> dto.KernelRunResult:
        result = self._request_json("POST", "/kernel/pipeline/run", json_payload=payload)
        return dto.KernelRunResult.from_dict(result)

    def write_evidence(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return self._request_json("POST", "/evidence/write", json_payload=payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_payload: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        response = self._request(method, path, json_payload=json_payload, headers=headers)
        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive fallback
            raise KernelClientError("Kernel returned invalid JSON", status_code=response.status_code) from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_payload: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Response:
        url = self._config.base_url.rstrip("/") + path
        attempt = 0
        last_error: Optional[Exception] = None
        while attempt <= self._config.max_retries:
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=json_payload,
                    headers=self._build_headers(headers),
                    timeout=self._config.timeout,
                )
                if response.status_code >= 500 and attempt < self._config.max_retries:
                    self._sleep_backoff(attempt)
                    attempt += 1
                    continue
                if response.status_code >= 400:
                    raise KernelClientError(
                        f"Kernel request failed: {response.status_code}",
                        status_code=response.status_code,
                        payload=self._safe_json(response),
                    )
                return response
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = exc
                if attempt >= self._config.max_retries:
                    break
                self._sleep_backoff(attempt)
                attempt += 1
        raise KernelClientError("Kernel request failed", payload=repr(last_error))

    def _build_headers(self, headers: Optional[Mapping[str, str]]) -> Dict[str, str]:
        result: Dict[str, str] = {"Content-Type": "application/json"}
        if self._config.api_key:
            result["Authorization"] = f"Bearer {self._config.api_key}"
        if headers:
            result.update(headers)
        return result

    def _sleep_backoff(self, attempt: int) -> None:
        delay = self._config.backoff_factor * (2**attempt)
        logger.debug("Kernel client retry %s sleeping for %.2fs", attempt + 1, delay)
        time.sleep(delay)

    @staticmethod
    def _safe_json(response: Response) -> Optional[Any]:
        try:
            return response.json()
        except ValueError:
            return response.text
