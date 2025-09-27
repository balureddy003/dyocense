from base64 import urlsafe_b64decode

from fastapi.testclient import TestClient

from api.app import app


def test_issue_token_and_me() -> None:
    client = TestClient(app)
    response = client.post(
        "/auth/token",
        json={"username": "alice", "password": "secret", "tenant_id": "tenant_a"},
    )
    assert response.status_code == 200
    token_payload = response.json()
    token = token_payload["access_token"]
    decoded = urlsafe_b64decode(token.encode()).decode()
    assert decoded == "tenant_a:alice"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["username"] == "alice"
    assert data["tenant_id"] == "tenant_a"


def test_auth_token_requires_credentials() -> None:
    client = TestClient(app)
    response = client.post("/auth/token", json={"username": "", "password": ""})
    assert response.status_code == 400
