from fastapi.testclient import TestClient

from services.compiler.main import app as compiler_app
from services.scenario.main import app as scenario_app


def test_create_scenario_from_version():
    compiler_client = TestClient(compiler_app)
    headers = {"Authorization": "Bearer demo-tenant"}
    compile_resp = compiler_client.post(
        "/v1/compile",
        json={"goal": "Baseline inventory", "tenant_id": "demo-tenant", "project_id": "proj-x"},
        headers=headers,
    )
    version_id = compile_resp.json()["version_id"]

    scenario_client = TestClient(scenario_app)
    request_payload = {
        "base_version_id": version_id,
        "label": "What-if demand spike",
        "parameter_overrides": {"demand": {"widget": 999}},
        "recompute": False,
    }

    response = scenario_client.post(
        "/v1/scenarios",
        json=request_payload,
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["base_version_id"] == version_id
    assert data["label"] == "What-if demand spike"
    assert any(item["before"] != item["after"] for item in data["diff"])
