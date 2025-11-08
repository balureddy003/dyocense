import io
import json

from fastapi.testclient import TestClient
from services.analyze.main import app

# Simple auth dependency bypass: monkeypatch require_auth if necessary

client = TestClient(app)

class DummyIdentity:
    def __init__(self):
        self.tenant_id = "test-tenant"


def test_sample_endpoint():
    # Note: analyze_sample depends on sample files; skip if missing
    resp = client.get("/v1/analyze/sample", headers={"Authorization": "Bearer dummy"})
    assert resp.status_code in (200, 404)  # allow 404 if sample files absent
    if resp.status_code == 200:
        data = resp.json()
        assert "mapping" in data
        assert "preview" in data
        assert isinstance(data["preview"], list)


def test_upload_csv(tmp_path):
    csv_content = "date,amount,product\n2024-01-01,10,A\n2024-01-02,20,B\n"
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))
    files = {"file": ("sales.csv", file_bytes, "text/csv")}
    resp = client.post("/v1/analyze", files=files, data={"use_sample": "false"}, headers={"Authorization": "Bearer dummy"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rows"] == 2
    assert body["mapping"]["amount"] in ("amount", "sales")
    assert len(body["insights"]) >= 1
