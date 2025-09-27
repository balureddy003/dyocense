"""Client for invoking the Plan service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass(slots=True)
class PlanClientConfig:
    base_url: str
    timeout: float = 10.0


class PlanClientError(RuntimeError):
    pass


class PlanClient:
    def __init__(self, config: PlanClientConfig, session: Optional[requests.Session] = None) -> None:
        self._config = config
        self._session = session or requests.Session()

    def create_plan(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        url = self._config.base_url.rstrip("/") + "/plans"
        headers = {"Authorization": f"Bearer {token}"}
        response = self._session.post(url, json=payload, headers=headers, timeout=self._config.timeout)
        if response.status_code >= 400:
            raise PlanClientError(f"Plan service error: {response.status_code}", response.text)
        return response.json()
