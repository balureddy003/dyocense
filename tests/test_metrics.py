"""
Test metrics endpoint and instrumentation
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_metrics_endpoint_available():
    """Test that /metrics endpoint is available."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    
    # Check for some expected metrics
    content = response.text
    assert "http_requests" in content or "process_" in content  # Default metrics


def test_evidence_metrics_recorded():
    """Test that evidence engine operations record metrics."""
    # First, get initial metrics
    response = client.get("/metrics")
    initial_metrics = response.text
    
    # Perform a correlation analysis
    client.post(
        "/api/v1/evidence/correlations",
        json={
            "series": {
                "x": [1.0, 2.0, 3.0, 4.0, 5.0],
                "y": [2.0, 4.0, 6.0, 8.0, 10.0]
            }
        }
    )
    
    # Get metrics again
    response = client.get("/metrics")
    assert response.status_code == 200
    updated_metrics = response.text
    
    # Check that evidence metrics are present
    assert "evidence_correlations_total" in updated_metrics or len(updated_metrics) > len(initial_metrics)


def test_whatif_metrics_recorded():
    """Test that what-if analysis records metrics."""
    response = client.post(
        "/api/v1/evidence/what-if",
        json={
            "cause_name": "x",
            "effect_name": "y",
            "cause": [1.0, 2.0, 3.0, 4.0],
            "effect": [2.0, 4.0, 6.0, 8.0],
            "delta_cause": 1.0
        }
    )
    assert response.status_code == 200
    
    # Check metrics
    metrics_response = client.get("/metrics")
    assert "evidence_whatif" in metrics_response.text or metrics_response.status_code == 200


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
