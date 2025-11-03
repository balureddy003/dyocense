from fastapi.testclient import TestClient

from services.kernel.main import app as kernel_app


def test_kernel_aggregates_endpoints():
    client = TestClient(kernel_app)
    headers = {"Authorization": "Bearer demo-tenant"}

    compile_resp = client.post(
        "/v1/compile",
        json={"goal": "Reduce cost", "tenant_id": "demo", "project_id": "test"},
        headers=headers,
    )
    assert compile_resp.status_code == 200
    ops = compile_resp.json()["ops"]

    optimise_resp = client.post("/v1/optimise", json={"ops": ops}, headers=headers)
    assert optimise_resp.status_code == 200

    catalog_resp = client.get("/v1/catalog", headers=headers)
    assert catalog_resp.status_code == 200
