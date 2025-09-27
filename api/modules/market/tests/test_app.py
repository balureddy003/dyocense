from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.modules.market.app import app, get_repository
from api.modules.market.storage import MarketRepository

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def client() -> TestClient:
    mongo_client = mongomock.MongoClient()
    collection = mongo_client["unit-test"]["market"]
    repository = MarketRepository(collection)

    app.dependency_overrides[get_repository] = lambda: repository

    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        yield test_client

    app.dependency_overrides.clear()


def _headers() -> dict[str, str]:
    return {"Authorization": "Bearer tenant_demo"}


def test_market_ingest_and_list(client: TestClient) -> None:
    ingest_resp = client.post(
        "/market/snapshots",
        json={
            "tenant_id": "tenant_demo",
            "source": "supplier_portal",
            "snapshots": [
                {"supplier_id": "SUP1", "cost": 1.2, "capacity": 100, "score": 0.8},
                {"supplier_id": "SUP2", "cost": 1.1, "capacity": 80, "score": 0.9},
            ],
        },
        headers=_headers(),
    )
    assert ingest_resp.status_code == 200
    payload = ingest_resp.json()
    assert payload["count"] == 2

    list_resp = client.get("/market/snapshots", headers=_headers())
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2
