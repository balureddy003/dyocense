from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from api.common import dto
from api.modules.plan.app import app, get_gateway, get_repository, get_chat_repository
from api.modules.plan.storage import ChatTranscriptRepository, PlanRepository

mongomock = pytest.importorskip("mongomock")


class StubGateway:
    def __init__(self, result: dto.KernelRunResult) -> None:
        self.result = result
        self.calls: Dict[str, Any] = {}
        self.call_history: List[Dict[str, Any]] = []

    def run_pipeline(self, payload: Dict[str, Any]) -> dto.KernelRunResult:
        self.calls = payload
        self.call_history.append(payload)
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

    chat_repository = ChatTranscriptRepository(mongo_client["unit-test"]["plan_chats"])

    app.dependency_overrides[get_gateway] = lambda: gateway
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_chat_repository] = lambda: chat_repository

    with TestClient(app) as test_client:
        test_client.gateway = gateway  # type: ignore[attr-defined]
        test_client.repository = repository  # type: ignore[attr-defined]
        test_client.chat_repository = chat_repository  # type: ignore[attr-defined]
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
    assert "llm_summary" in payload
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


def test_delta_and_counterfactual_plan(client: TestClient) -> None:
    create_resp = client.post(
        "/plans",
        json={"goal_id": "goal-1", "variant": "baseline", "kernel_payload": {"seed": 123}},
        headers={"Authorization": "Bearer tenant_demo"},
    )
    base_plan = create_resp.json()
    base_id = base_plan["plan_id"]

    delta_resp = client.post(
        f"/plans/{base_id}/delta",
        json={"variant_suffix": "tight-budget", "kernel_payload": {"constraints": {"budget_month": 8000}}},
        headers={"Authorization": "Bearer tenant_demo"},
    )
    assert delta_resp.status_code == 201, delta_resp.text
    delta_payload = delta_resp.json()
    assert delta_payload["parent_plan_id"] == base_id
    assert delta_payload["variant"] == "baseline-tight-budget"

    counter_resp = client.post(
        f"/plans/{base_id}/counterfactual",
        json={"variant_suffix": "no-sup1", "kernel_payload": {"context": {"remove_suppliers": {"SKU1": ["SUP1"]}}}},
        headers={"Authorization": "Bearer tenant_demo"},
    )
    assert counter_resp.status_code == 201
    counter_payload = counter_resp.json()
    assert counter_payload["parent_plan_id"] == base_id
    assert counter_payload["variant"] == "baseline-no-sup1"

    # Listing should return three plans for the tenant (baseline + two variants)
    list_resp = client.get("/plans", headers={"Authorization": "Bearer tenant_demo"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 3

    # Kernel payloads should include tenant info and overrides
    gateway = client.gateway  # type: ignore[attr-defined]
    assert gateway.call_history[-1]["tenant_id"] == "tenant_demo"
    assert gateway.call_history[-1]["mode"] == "counterfactual"


def test_chat_plan_endpoint(client: TestClient) -> None:
    response = client.post(
        "/chat/plan",
        json={"goal": "Reduce stockouts", "context": "SKU1", "tenant_id": "tenant_demo", "provider_id": "openai"},
        headers={"Authorization": "Bearer tenant_demo"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "accepted"
    assert "Reduce stockouts" in payload["summary"]
    assert payload["provider_id"] == "openai"
    assert payload["conversation_id"]
    assert payload.get("llm_response")
    repo = client.chat_repository  # type: ignore[attr-defined]
    transcripts = repo.list("tenant_demo")
    assert transcripts and transcripts[0].provider_id == "openai"
    assert transcripts[0].goal == "Reduce stockouts"
    assert len(transcripts[0].messages) >= 2
