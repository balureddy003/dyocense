import json
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_score_payload_shape():
    r = client.get("/v1/tenants/demo/health-score")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("score"), (int, float))
    assert isinstance(data.get("trend"), (int, float))
    assert isinstance(data.get("breakdown"), dict)
    bd = data["breakdown"]
    for k in ["revenue_available", "operations_available", "customer_available"]:
        assert k in bd
    for k in ["revenue", "operations", "customer"]:
        if k in bd:
            assert isinstance(bd[k], (int, float))
    assert "last_updated" in data
    assert "period_days" in data


def test_health_alerts_and_signals():
    alerts = client.get("/v1/tenants/demo/health-score/alerts")
    assert alerts.status_code == 200
    assert isinstance(alerts.json(), list)

    signals = client.get("/v1/tenants/demo/health-score/signals")
    assert signals.status_code == 200
    assert isinstance(signals.json(), list)


def test_metrics_snapshot():
    snap = client.get("/v1/tenants/demo/metrics/snapshot")
    assert snap.status_code == 200
    payload = snap.json()
    assert isinstance(payload, list)
    if payload:
        item = payload[0]
        assert {
            "id",
            "label",
            "value",
            "change",
            "changeType",
            "trend",
        }.issubset(item.keys())
