from __future__ import annotations

from fastapi.testclient import TestClient

from services.compiler.main import app as compiler_app
from services.optimiser.main import app as optimiser_app
from services.forecast.main import app as forecast_app
from services.explainer.main import app as explainer_app
from services.policy.main import app as policy_app
from services.diagnostician.main import app as diagnostician_app
from services.evidence.main import app as evidence_app


def test_compile_returns_valid_ops():
    client = TestClient(compiler_app)
    response = client.post(
        "/v1/compile",
        json={"goal": "Plan inventory", "tenant_id": "demo-tenant", "project_id": "proj"},
        headers={"Authorization": "Bearer demo-tenant"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ops" in data
    assert "version_id" in data
    assert "goal_pack" in data
    metadata = data["ops"]["metadata"]
    goal_pack = data["goal_pack"]
    assert goal_pack["version_id"] == data["version_id"]
    assert goal_pack["tenant_id"] == "demo-tenant"
    assert metadata["tenant_id"] == "demo-tenant"
    assert metadata["project_id"] == "proj"
    assert data["ops"]["objective"]["sense"] == "min"


def test_end_to_end_flow():
    compiler_client = TestClient(compiler_app)
    optimiser_client = TestClient(optimiser_app)
    forecast_client = TestClient(forecast_app)
    explainer_client = TestClient(explainer_app)
    policy_client = TestClient(policy_app)
    diagnostician_client = TestClient(diagnostician_app)
    evidence_client = TestClient(evidence_app)

    headers = {"Authorization": "Bearer demo-tenant"}

    compile_response = compiler_client.post(
        "/v1/compile",
        json={"goal": "Reduce holding costs", "tenant_id": "demo-tenant", "project_id": "p1"},
        headers=headers,
    )
    compile_payload = compile_response.json()
    ops = compile_payload["ops"]
    version_id = compile_payload["version_id"]
    goal_pack = compile_payload["goal_pack"]
    assert goal_pack["version_id"] == version_id

    forecast_response = forecast_client.post(
        "/v1/forecast",
        json={
            "horizon": 2,
            "series": [
                {"name": "widget", "values": [100, 105, 110]},
                {"name": "gadget", "values": [75, 80, 90]},
            ],
        },
        headers=headers,
    )
    assert forecast_response.status_code == 200
    forecast_payload = forecast_response.json()

    policy_response = policy_client.post(
        "/v1/policy/evaluate",
        json={"tenant_id": "t1", "ops": ops},
        headers=headers,
    )
    assert policy_response.status_code == 200
    policy_payload = policy_response.json()
    assert policy_payload["verdict"] == "allow"

    optimise_response = optimiser_client.post(
        "/v1/optimise", json={"ops": ops}, headers=headers
    )
    assert optimise_response.status_code == 200
    solution = optimise_response.json()["solution"]

    solver_name = solution["metadata"]["solver"]
    assert solver_name in {"stub-optimiser", "cbc-mip"}
    assert solution["kpis"]["total_holding_cost"] >= 0
    assert solution["diagnostics"]["status"] in {"optimal", "feasible"}

    diagnose_response = diagnostician_client.post(
        "/v1/diagnose", json={"ops": ops, "solution": solution}, headers=headers
    )
    assert diagnose_response.status_code == 200
    diagnose_payload = diagnose_response.json()
    assert diagnose_payload["suggestions"]

    explain_response = explainer_client.post(
        "/v1/explain",
        json={
            "goal": "Reduce holding costs",
            "solution": solution,
            "forecasts": forecast_payload["forecasts"],
            "policy": policy_payload,
            "diagnostics": diagnose_payload,
        },
        headers=headers,
    )
    assert explain_response.status_code == 200
    explanation = explain_response.json()
    assert "summary" in explanation
    assert explanation["highlights"]

    evidence_response = evidence_client.post(
        "/v1/evidence/log",
        json={
            "run_id": solution["metadata"]["run_id"],
            "tenant_id": ops["metadata"].get("tenant_id", "unknown"),
            "ops": ops,
            "solution": solution,
            "explanation": explanation,
            "goal_pack": goal_pack,
            "facts": [
                {
                    "category": "policy",
                    "statement": "All constraints validated",
                    "status": "satisfied",
                    "source": "a1facts-stub",
                    "metadata": {"version_id": version_id},
                }
            ],
        },
        headers=headers,
    )
    assert evidence_response.status_code == 200
    stored = evidence_response.json()
    assert stored["run_id"] == solution["metadata"]["run_id"]

    evidence_fetch = evidence_client.get(
        f"/v1/evidence/{stored['run_id']}", headers=headers
    )
    assert evidence_fetch.status_code == 200
    fetched = evidence_fetch.json()
    assert fetched["run_id"] == stored["run_id"]
    assert fetched.get("goal_pack", {}).get("version_id") == version_id

    evidence_list = evidence_client.get(
        "/v1/evidence?limit=5", headers=headers
    )
    assert evidence_list.status_code == 200
    listed = evidence_list.json()
    assert listed["count"] >= 1

    facts_response = evidence_client.get(
        f"/v1/evidence/{solution['metadata']['run_id']}/facts", headers=headers
    )
    assert facts_response.status_code == 200
    facts_payload = facts_response.json()
    assert facts_payload["count"] == 1
