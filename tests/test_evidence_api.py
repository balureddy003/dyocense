"""
Integration tests for Evidence API endpoints

Tests cover:
- POST /api/v1/evidence/correlations
- POST /api/v1/evidence/granger
- POST /api/v1/evidence/explain
- POST /api/v1/evidence/what-if
- POST /api/v1/evidence/drivers
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


# =============================================================================
# CORRELATIONS ENDPOINT TESTS
# =============================================================================

def test_correlations_endpoint_basic():
    """Test basic correlation detection via API."""
    response = client.post(
        "/api/v1/evidence/correlations",
        json={
            "series": {
                "sales": [100.0, 120.0, 140.0, 160.0, 180.0],
                "revenue": [200.0, 240.0, 280.0, 320.0, 360.0],
                "cost": [50.0, 55.0, 60.0, 65.0, 70.0],
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    # Should find correlation between sales and revenue
    sales_revenue = next(
        (r for r in data["results"] if set([r["a"], r["b"]]) == {"sales", "revenue"}),
        None
    )
    assert sales_revenue is not None
    assert sales_revenue["corr"] > 0.95


def test_correlations_endpoint_empty_series():
    """Test correlations endpoint with empty series."""
    response = client.post(
        "/api/v1/evidence/correlations",
        json={"series": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


def test_correlations_endpoint_mismatched_lengths():
    """Test correlations endpoint with mismatched series lengths."""
    response = client.post(
        "/api/v1/evidence/correlations",
        json={
            "series": {
                "a": [1.0, 2.0, 3.0],
                "b": [1.0, 2.0, 3.0, 4.0, 5.0]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


def test_correlations_endpoint_invalid_payload():
    """Test correlations endpoint with invalid payload."""
    response = client.post(
        "/api/v1/evidence/correlations",
        json={"invalid": "data"}
    )
    assert response.status_code == 422  # Validation error


# =============================================================================
# GRANGER CAUSALITY ENDPOINT TESTS
# =============================================================================

def test_granger_endpoint_basic():
    """Test Granger causality via API."""
    response = client.post(
        "/api/v1/evidence/granger",
        json={
            "a_name": "marketing",
            "b_name": "sales",
            "a": [10.0, 12.0, 15.0, 18.0, 22.0, 25.0, 30.0, 35.0],
            "b": [100.0, 105.0, 110.0, 120.0, 130.0, 140.0, 155.0, 170.0],
            "max_lag": 2,
            "alpha": 0.05
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_granger_endpoint_insufficient_data():
    """Test Granger with insufficient data points."""
    response = client.post(
        "/api/v1/evidence/granger",
        json={
            "a_name": "x",
            "b_name": "y",
            "a": [1.0, 2.0],
            "b": [1.0, 2.0],
            "max_lag": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


def test_granger_endpoint_mismatched_lengths():
    """Test Granger with mismatched lengths."""
    response = client.post(
        "/api/v1/evidence/granger",
        json={
            "a_name": "x",
            "b_name": "y",
            "a": [1.0, 2.0, 3.0],
            "b": [1.0, 2.0, 3.0, 4.0]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


# =============================================================================
# EXPLAIN CHANGE ENDPOINT TESTS
# =============================================================================

def test_explain_endpoint_basic():
    """Test explain change endpoint."""
    response = client.post(
        "/api/v1/evidence/explain",
        json={
            "metric": "Revenue",
            "before": 10000.0,
            "after": 12000.0,
            "drivers": {
                "sales_volume": 1500.0,
                "price_increase": 500.0,
                "cost_reduction": 200.0
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "Revenue" in data["explanation"]
    assert "2000" in data["explanation"]  # Delta
    assert "sales_volume" in data["explanation"]  # Top driver


def test_explain_endpoint_no_drivers():
    """Test explain endpoint with no drivers."""
    response = client.post(
        "/api/v1/evidence/explain",
        json={
            "metric": "Profit",
            "before": 5000.0,
            "after": 6000.0,
            "drivers": {}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "No driver data" in data["explanation"]


def test_explain_endpoint_negative_change():
    """Test explain endpoint with negative change."""
    response = client.post(
        "/api/v1/evidence/explain",
        json={
            "metric": "Cost",
            "before": 8000.0,
            "after": 6500.0,
            "drivers": {
                "efficiency": -1000.0,
                "automation": -500.0
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "Cost" in data["explanation"]


# =============================================================================
# WHAT-IF ENDPOINT TESTS
# =============================================================================

def test_what_if_endpoint_basic():
    """Test what-if analysis endpoint."""
    response = client.post(
        "/api/v1/evidence/what-if",
        json={
            "cause_name": "marketing_spend",
            "effect_name": "sales",
            "cause": [1000.0, 1500.0, 2000.0, 2500.0, 3000.0],
            "effect": [10000.0, 15000.0, 20000.0, 25000.0, 30000.0],
            "delta_cause": 500.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_delta" in data
    assert "slope" in data
    assert "intercept" in data
    assert "r2" in data
    assert data["predicted_delta"] > 2000.0  # Should predict significant increase


def test_what_if_endpoint_negative_delta():
    """Test what-if with negative change."""
    response = client.post(
        "/api/v1/evidence/what-if",
        json={
            "cause_name": "price",
            "effect_name": "demand",
            "cause": [10.0, 12.0, 14.0, 16.0, 18.0],
            "effect": [1000.0, 900.0, 800.0, 700.0, 600.0],
            "delta_cause": -2.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_delta" in data
    # Price decrease should increase demand (positive delta)
    assert data["predicted_delta"] > 0


def test_what_if_endpoint_invalid_data():
    """Test what-if with invalid/empty data."""
    response = client.post(
        "/api/v1/evidence/what-if",
        json={
            "cause_name": "x",
            "effect_name": "y",
            "cause": [],
            "effect": [],
            "delta_cause": 1.0
        }
    )
    assert response.status_code == 400  # Should fail gracefully


def test_what_if_endpoint_mismatched_lengths():
    """Test what-if with mismatched array lengths."""
    response = client.post(
        "/api/v1/evidence/what-if",
        json={
            "cause_name": "x",
            "effect_name": "y",
            "cause": [1.0, 2.0, 3.0],
            "effect": [1.0, 2.0],
            "delta_cause": 1.0
        }
    )
    assert response.status_code == 400


# =============================================================================
# DRIVERS INFERENCE ENDPOINT TESTS
# =============================================================================

def test_drivers_endpoint_basic():
    """Test driver inference endpoint."""
    response = client.post(
        "/api/v1/evidence/drivers",
        json={
            "target_name": "revenue",
            "target": [10000.0, 12000.0, 15000.0, 18000.0, 22000.0],
            "drivers": {
                "sales_volume": [100.0, 120.0, 150.0, 180.0, 220.0],
                "avg_price": [100.0, 100.0, 100.0, 100.0, 100.0],
                "marketing": [500.0, 600.0, 700.0, 800.0, 900.0]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "drivers" in data
    assert isinstance(data["drivers"], list)
    assert len(data["drivers"]) > 0
    # Should identify sales_volume as top driver
    assert data["drivers"][0]["name"] in ["sales_volume", "marketing"]
    assert "beta" in data["drivers"][0]


def test_drivers_endpoint_empty_drivers():
    """Test drivers endpoint with no drivers."""
    response = client.post(
        "/api/v1/evidence/drivers",
        json={
            "target_name": "y",
            "target": [1.0, 2.0, 3.0],
            "drivers": {}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["drivers"] == []


def test_drivers_endpoint_mismatched_lengths():
    """Test drivers endpoint with mismatched lengths."""
    response = client.post(
        "/api/v1/evidence/drivers",
        json={
            "target_name": "y",
            "target": [1.0, 2.0, 3.0, 4.0],
            "drivers": {
                "x1": [1.0, 2.0, 3.0],  # Wrong length
                "x2": [1.0, 2.0, 3.0, 4.0]  # Correct length
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should only include x2 (matching length)
    assert len(data["drivers"]) == 1
    assert data["drivers"][0]["name"] == "x2"


def test_drivers_endpoint_sorted_by_importance():
    """Test that drivers are sorted by absolute beta."""
    response = client.post(
        "/api/v1/evidence/drivers",
        json={
            "target_name": "y",
            "target": [10.0, 20.0, 30.0, 40.0, 50.0],
            "drivers": {
                "strong": [1.0, 2.0, 3.0, 4.0, 5.0],
                "weak": [0.1, 0.2, 0.3, 0.4, 0.5]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["drivers"]) == 2
    # Should be sorted by importance
    betas = [abs(d["beta"]) for d in data["drivers"]]
    assert betas[0] >= betas[1]


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

def test_evidence_endpoints_validation_errors():
    """Test that endpoints properly validate request payloads."""
    endpoints = [
        "/api/v1/evidence/correlations",
        "/api/v1/evidence/granger",
        "/api/v1/evidence/explain",
        "/api/v1/evidence/what-if",
        "/api/v1/evidence/drivers"
    ]
    for endpoint in endpoints:
        response = client.post(endpoint, json={})
        assert response.status_code == 422  # Validation error


def test_evidence_endpoints_require_json():
    """Test that endpoints require JSON payloads."""
    response = client.post(
        "/api/v1/evidence/correlations",
        data="not json"
    )
    assert response.status_code == 422
