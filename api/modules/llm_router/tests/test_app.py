from fastapi.testclient import TestClient

from api.app import app


def test_list_providers() -> None:
    client = TestClient(app)
    response = client.get("/llm/providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and data
    assert {"provider_id", "name", "model"}.issubset(data[0].keys())


def test_chat_with_provider() -> None:
    client = TestClient(app)
    response = client.post(
        "/llm/chat",
        json={"prompt": "Hello world", "provider_id": "openai"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_id"] == "openai"
    assert "Fallback summary" in payload["message"] or payload["message"]
    assert payload["tokens_estimated"] >= 0


def test_unknown_provider_returns_404() -> None:
    client = TestClient(app)
    response = client.post(
        "/llm/chat",
        json={"prompt": "Test", "provider_id": "missing"},
    )
    assert response.status_code == 404
