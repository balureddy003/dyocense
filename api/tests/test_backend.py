from fastapi.testclient import TestClient

from api.app import app


def test_health_lists_service_titles():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
    services = payload.get("services", [])
    assert "Dyocense Plan Service" in services
    assert "Dyocense Goal Service" in services
