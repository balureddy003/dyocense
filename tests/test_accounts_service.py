from fastapi.testclient import TestClient

from services.accounts.main import app


def test_tenant_registration_and_project_creation():
    client = TestClient(app)

    register_response = client.post(
        "/v1/tenants/register",
        json={"name": "Test Org", "owner_email": "ops@example.com", "plan_tier": "free"},
    )
    assert register_response.status_code == 201
    payload = register_response.json()
    assert payload["tenant_id"].startswith("test-org-")
    assert payload["api_token"].startswith("key-")

    headers = {"Authorization": f"Bearer {payload['api_token']}"}

    profile_response = client.get("/v1/tenants/me", headers=headers)
    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["tenant_id"] == payload["tenant_id"]
    assert profile["plan"]["tier"] == "free"

    project_response = client.post(
        "/v1/projects",
        json={"name": "Launchpad"},
        headers=headers,
    )
    assert project_response.status_code == 201
    project = project_response.json()
    assert project["project_id"].startswith("proj-")

    projects_list = client.get("/v1/projects", headers=headers)
    assert projects_list.status_code == 200
    projects = projects_list.json()
    assert len(projects) == 1
