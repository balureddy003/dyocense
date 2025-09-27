from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from api.modules.goal.app import app, get_plan_client, get_repository
from api.modules.goal.storage import GoalRepository

mongomock = pytest.importorskip("mongomock")


class StubPlanClient:
    def __init__(self) -> None:
        self.calls: Dict[str, Any] = {}

    def create_plan(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        self.calls = {"payload": payload, "token": token}
        return {"plan_id": "plan_new"}


@pytest.fixture
def client() -> TestClient:
    mongo_client = mongomock.MongoClient()
    repository = GoalRepository(mongo_client["unit-test"]["goals"])
    plan_client = StubPlanClient()

    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_plan_client] = lambda: plan_client

    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        test_client.plan_client = plan_client  # type: ignore[attr-defined]
        yield test_client

    app.dependency_overrides.clear()


def _auth_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer tenant_demo"}


def test_goal_crud_and_plan_trigger(client: TestClient) -> None:
    create_resp = client.post(
        "/goals",
        json={"name": "Inventory", "goaldsl": {"objective": {"cost": 1.0}}},
        headers=_auth_headers(),
    )
    assert create_resp.status_code == 201
    goal = create_resp.json()
    goal_id = goal["goal_id"]

    list_resp = client.get("/goals", headers=_auth_headers())
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.patch(
        f"/goals/{goal_id}",
        json={"name": "Inventory Planning"},
        headers=_auth_headers(),
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Inventory Planning"

    variant_resp = client.post(
        f"/goals/{goal_id}/variants",
        json={"name": "high-service", "goaldsl": {"objective": {"service": 0.5}}},
        headers=_auth_headers(),
    )
    assert variant_resp.status_code == 200
    assert len(variant_resp.json()["variants"]) == 1

    status_resp = client.post(
        f"/goals/{goal_id}/status",
        json={"status": "READY_TO_PLAN"},
        headers=_auth_headers(),
    )
    assert status_resp.status_code == 200
    plan_client = client.plan_client  # type: ignore[attr-defined]
    assert plan_client.calls["token"] == "tenant_demo"

    feedback_resp = client.post(
        f"/goals/{goal_id}/feedback",
        json={"actuals": {"SKU1": 120}},
        headers=_auth_headers(),
    )
    assert feedback_resp.status_code == 200
    assert len(feedback_resp.json()["feedback"]) == 1
