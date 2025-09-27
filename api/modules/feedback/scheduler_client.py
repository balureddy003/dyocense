"""Client to enqueue jobs on Scheduler service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass(slots=True)
class SchedulerClientConfig:
    base_url: str
    timeout: float = 10.0


class SchedulerClientError(RuntimeError):
    pass


class SchedulerClient:
    def __init__(self, config: SchedulerClientConfig, session: Optional[requests.Session] = None) -> None:
        self._config = config
        self._session = session or requests.Session()

    def enqueue(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        url = self._config.base_url.rstrip("/") + "/queue/enqueue"
        headers = {"Authorization": f"Bearer {token}"}
        response = self._session.post(url, json=payload, headers=headers, timeout=self._config.timeout)
        if response.status_code >= 400:
            raise SchedulerClientError(f"Scheduler error: {response.status_code}", response.text)
        return response.json()
