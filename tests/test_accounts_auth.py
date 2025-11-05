from fastapi.testclient import TestClient

from services.accounts.main import app


def provision_tenant(client: TestClient) -> dict:
    response = client.post(
        "/v1/tenants/register",
        json={"name": "Auth Test", "owner_email": "owner@example.com", "plan_tier": "free"},
    )
    assert response.status_code == 201
    return response.json()


def test_user_registration_and_login_flow():
    client = TestClient(app)
    tenant = provision_tenant(client)

    register_response = client.post(
        "/v1/users/register",
        json={
            "tenant_id": tenant["tenant_id"],
            "email": "user@example.com",
            "full_name": "User Example",
            "password": "strong-password",
            "access_token": tenant["api_token"],
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/v1/users/login",
        json={
            "tenant_id": tenant["tenant_id"],
            "email": "user@example.com",
            "password": "strong-password",
        },
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["token"]

    headers = {"Authorization": f"Bearer {login_payload['token']}"}
    me_response = client.get("/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["email"] == "user@example.com"

    token_create = client.post("/v1/users/api-tokens", json={"name": "CLI"}, headers=headers)
    assert token_create.status_code == 201
    token_payload = token_create.json()
    assert token_payload["secret"].startswith("key-")

    tokens_list = client.get("/v1/users/api-tokens", headers=headers)
    assert tokens_list.status_code == 200
    assert any(item["token_id"] == token_payload["token_id"] for item in tokens_list.json())

    delete_resp = client.delete(f"/v1/users/api-tokens/{token_payload['token_id']}", headers=headers)
    assert delete_resp.status_code == 204
