from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from services.common import dto
from services.plan.app import app, get_gateway, get_repository
from services.plan.storage import PlanRepository

mongomock = pytest.importorskip("mongomock")


class StubGateway:
    def __init__(self, result: dto.KernelRunResult) -> None:
        self.result = result
        self.calls: Dict[str, Any] = {}

    def run_pipeline(self, payload: Dict[str, Any]) -> dto.KernelRunResult:
        self.calls = payload
        return self.result


@pytest.fixture
def client() -> TestClient:
    kernel_result_dict = {
        "evidence_ref": "evidence://stub",
        "solution": {
            "status": "FEASIBLE",
            "gap": 0.0,
            "kpis": {"total_cost": 100.0},
            "steps": [
                {
                    "sku": "SKU1",
                    "supplier": "SUP1",
                    "period": "t1",
                    "quantity": 50,
                    "price": 10.0,
                }
            ],
            "binding_constraints": ["budget"],
            "activities": {"budget": 100.0},
            "shadow_prices": {},
        },
        "diagnostics": {
            "reduction": {"original_count": 50, "reduced_count": 10},
            "simulation": {"runs": 5, "mean_service": 0.95},
        },
        "policy": {
            "allow": True,
            "policy_id": "policy.guard.v1",
            "reasons": [],
            "warnings": [],
            "controls": {"tier": "pro"},
        },
    }
    gateway = StubGateway(dto.KernelRunResult.from_dict(kernel_result_dict))
    mongo_client = mongomock.MongoClient()
    repository = PlanRepository(mongo_client["unit-test"]["plans"])

    app.dependency_overrides[get_gateway] = lambda: gateway
    app.dependency_overrides[get_repository] = lambda: repository

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_and_get_plan(client: TestClient) -> None:
    response = client.post(
        "/plans",
        json={
            "goal_id": "goal-123",
            "variant": "baseline",
            "kernel_payload": {"goaldsl": {"objective": {"cost": 1.0}}},
        },
        headers={"Authorization": "Bearer tenant_demo"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["goal_id"] == "goal-123"
    plan_id = payload["plan_id"]

    list_resp = client.get("/plans", headers={"Authorization": "Bearer tenant_demo"})
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["plan_id"] == plan_id

    get_resp = client.get(f"/plans/{plan_id}", headers={"Authorization": "Bearer tenant_demo"})
    assert get_resp.status_code == 200
    assert get_resp.json()["plan_id"] == plan_id

    steps_resp = client.get(
        f"/plans/{plan_id}/steps",
        headers={"Authorization": "Bearer tenant_demo"},
    )
    assert steps_resp.status_code == 200
    steps = steps_resp.json()["steps"]
    assert steps and steps[0]["sku"] == "SKU1"

    evidence_resp = client.get(
        f"/plans/{plan_id}/evidence",
        headers={"Authorization": "Bearer tenant_demo"},
    )
    assert evidence_resp.status_code == 200
    assert evidence_resp.json()["evidence_ref"] == "evidence://stub"
