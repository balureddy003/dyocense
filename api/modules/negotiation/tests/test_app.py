from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.modules.negotiation.app import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_proposal_requires_auth(client: TestClient) -> None:
    resp = client.post(
        "/negotiation/proposals",
        json={"plan_id": "plan_1", "supplier_id": "SUP1", "adjustments": {"price": -0.05}, "rationale": "Better deal"},
    )
    assert resp.status_code == 401
