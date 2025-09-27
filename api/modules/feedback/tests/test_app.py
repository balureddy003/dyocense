from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from api.modules.feedback.app import (
    app,
    get_kernel_client,
    get_repository,
    get_scheduler_client,
)
from api.modules.feedback.storage import FeedbackRepository

mongomock = pytest.importorskip("mongomock")


class StubKernelClient:
    def __init__(self) -> None:
        self.payload: Dict[str, Any] = {}

    def send_forecast_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.payload = payload
        return {"status": "accepted"}


class StubSchedulerClient:
    def __init__(self) -> None:
        self.payload: Dict[str, Any] = {}
        self.token: str = ""

    def enqueue(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        self.payload = payload
        self.token = token
        return {"job_id": "job_123"}


@pytest.fixture
def client() -> TestClient:
    mongo_client = mongomock.MongoClient()
    collection = mongo_client["unit-test"]["feedback"]
    repository = FeedbackRepository(collection)
    kernel_client = StubKernelClient()
    scheduler_client = StubSchedulerClient()

    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_kernel_client] = lambda: kernel_client
    app.dependency_overrides[get_scheduler_client] = lambda: scheduler_client

    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        test_client.kernel_client = kernel_client  # type: ignore[attr-defined]
        test_client.scheduler_client = scheduler_client  # type: ignore[attr-defined]
        yield test_client

    app.dependency_overrides.clear()


def _headers() -> Dict[str, str]:
    return {"Authorization": "Bearer tenant_demo"}


def test_feedback_ingest_and_drift(client: TestClient) -> None:
    ingest_resp = client.post(
        "/feedback/ingest",
        json={
            "goal_id": "goal_1",
            "plan_id": "plan_1",
            "actuals": [
                {"sku": "SKU1", "period": "2025-09-01", "quantity": 120},
                {"sku": "SKU1", "period": "2025-09-02", "quantity": 130},
            ],
        },
        headers=_headers(),
    )
    assert ingest_resp.status_code == 200
    payload = ingest_resp.json()
    assert payload["count"] == 2
    assert payload["triggered_replan"] is True

    kernel_client = client.kernel_client  # type: ignore[attr-defined]
    assert kernel_client.payload["tenant_id"] == "tenant_demo"

    drift_resp = client.get("/feedback/kpi-drift", headers=_headers())
    assert drift_resp.status_code == 200
    drift_data = drift_resp.json()
    assert len(drift_data["items"]) == 1
    assert drift_data["items"][0]["sku"] == "SKU1"
