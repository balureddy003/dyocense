"""
Comprehensive tests for Evidence/Causal Engine

Tests cover:
- Correlation detection with p-values
- Granger causality tests
- Linear regression (what-if scenarios)
- Driver inference with multiple variables
- Edge cases: empty data, single values, NaN, mismatched lengths
"""
import math
import pytest
from backend.services.evidence.causal_engine import CausalEngine


# =============================================================================
# CORRELATION TESTS
# =============================================================================

def test_correlations_basic():
    """Test basic correlation detection with perfectly correlated data."""
    engine = CausalEngine()
    series = {
        "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        "y": [2.0, 4.0, 6.0, 8.0, 10.0],  # perfectly correlated with x
        "z": [1.0, -1.0, 1.0, -1.0, 1.0],
    }
    results = engine.detect_correlations(series)
    # Should contain x-y with correlation close to 1
    xy = next((r for r in results if (r["a"], r["b"]) in [("x", "y"), ("y", "x")]), None)
    assert xy is not None
    assert isinstance(xy["corr"], float)
    assert xy["corr"] > 0.99
    # p_value should be present (or None if scipy not available)
    assert "p_value" in xy


def test_correlations_negative():
    """Test detection of negative correlations."""
    engine = CausalEngine()
    series = {
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": [10.0, 8.0, 6.0, 4.0, 2.0],  # negative correlation
    }
    results = engine.detect_correlations(series)
    assert len(results) == 1
    assert results[0]["corr"] < -0.95


def test_correlations_empty_series():
    """Test correlation with empty input."""
    engine = CausalEngine()
    results = engine.detect_correlations({})
    assert results == []


def test_correlations_single_series():
    """Test correlation with only one series (no pairs to correlate)."""
    engine = CausalEngine()
    results = engine.detect_correlations({"x": [1.0, 2.0, 3.0]})
    assert results == []


def test_correlations_mismatched_lengths():
    """Test correlation with series of different lengths."""
    engine = CausalEngine()
    series = {
        "x": [1.0, 2.0, 3.0],
        "y": [1.0, 2.0, 3.0, 4.0, 5.0],  # different length
    }
    results = engine.detect_correlations(series)
    assert results == []  # Should return empty due to length mismatch


def test_correlations_with_nan():
    """Test correlation with NaN values (should skip)."""
    engine = CausalEngine()
    series = {
        "x": [1.0, 2.0, float('nan'), 4.0, 5.0],
        "y": [2.0, 4.0, 6.0, 8.0, 10.0],
    }
    results = engine.detect_correlations(series)
    # Should skip the pair with NaN
    xy = next((r for r in results if (r["a"], r["b"]) in [("x", "y"), ("y", "x")]), None)
    assert xy is None  # Should be filtered out


def test_correlations_zero_variance():
    """Test correlation with constant series (zero variance)."""
    engine = CausalEngine()
    series = {
        "constant": [5.0, 5.0, 5.0, 5.0, 5.0],
        "variable": [1.0, 2.0, 3.0, 4.0, 5.0],
    }
    results = engine.detect_correlations(series)
    # Correlation with constant is undefined/NaN - should handle gracefully
    assert isinstance(results, list)  # Should not crash


def test_correlations_sorted_by_magnitude():
    """Test that results are sorted by absolute correlation value."""
    engine = CausalEngine()
    series = {
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": [2.0, 4.0, 6.0, 8.0, 10.0],  # high correlation
        "c": [1.1, 2.2, 2.9, 4.1, 5.0],    # medium correlation
        "d": [5.0, 1.0, 3.0, 2.0, 4.0],    # low correlation
    }
    results = engine.detect_correlations(series)
    if len(results) > 1:
        # Check descending order by absolute value
        for i in range(len(results) - 1):
            assert abs(results[i]["corr"]) >= abs(results[i + 1]["corr"])


# =============================================================================
# GRANGER CAUSALITY TESTS
# =============================================================================

def test_granger_empty_series():
    """Test Granger causality with empty input."""
    engine = CausalEngine()
    results = engine.granger_causality({})
    assert results == []


def test_granger_wrong_number_of_series():
    """Test Granger causality with wrong number of series (needs exactly 2)."""
    engine = CausalEngine()
    # Only one series
    results = engine.granger_causality({"x": [1.0, 2.0, 3.0]})
    assert results == []
    # Three series
    results = engine.granger_causality({
        "x": [1.0, 2.0, 3.0],
        "y": [1.0, 2.0, 3.0],
        "z": [1.0, 2.0, 3.0],
    })
    assert results == []


def test_granger_mismatched_lengths():
    """Test Granger causality with series of different lengths."""
    engine = CausalEngine()
    results = engine.granger_causality({
        "x": [1.0, 2.0, 3.0],
        "y": [1.0, 2.0, 3.0, 4.0],
    })
    assert results == []


def test_granger_insufficient_data():
    """Test Granger causality with insufficient data points."""
    engine = CausalEngine()
    # Need enough data for max_lag
    results = engine.granger_causality({
        "x": [1.0, 2.0],
        "y": [1.0, 2.0],
    }, max_lag=3)
    assert results == []  # Should handle gracefully


# =============================================================================
# LINEAR REGRESSION TESTS
# =============================================================================

def test_fit_linear_basic():
    """Test basic linear regression fit."""
    engine = CausalEngine()
    x = [0.0, 1.0, 2.0, 3.0, 4.0]
    y = [1.0, 3.0, 5.0, 7.0, 9.0]  # y = 2x + 1
    result = engine.fit_linear(x, y)
    assert result is not None
    assert abs(result["slope"] - 2.0) < 0.01
    assert abs(result["intercept"] - 1.0) < 0.01
    assert result["r2"] > 0.99


def test_fit_linear_empty():
    """Test linear fit with empty data."""
    engine = CausalEngine()
    result = engine.fit_linear([], [])
    assert result is None


def test_fit_linear_single_point():
    """Test linear fit with single data point."""
    engine = CausalEngine()
    result = engine.fit_linear([1.0], [2.0])
    assert result is None  # Need at least 2 points


def test_fit_linear_mismatched_lengths():
    """Test linear fit with mismatched array lengths."""
    engine = CausalEngine()
    result = engine.fit_linear([1.0, 2.0, 3.0], [1.0, 2.0])
    assert result is None


def test_fit_linear_zero_variance():
    """Test linear fit with constant y values."""
    engine = CausalEngine()
    x = [1.0, 2.0, 3.0, 4.0]
    y = [5.0, 5.0, 5.0, 5.0]
    result = engine.fit_linear(x, y)
    assert result is not None
    assert abs(result["slope"]) < 1e-6  # Should be near zero
    assert result["r2"] >= 0.0  # R2 should be 0 for constant


def test_fit_linear_negative_slope():
    """Test linear fit with negative relationship."""
    engine = CausalEngine()
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [10.0, 8.0, 6.0, 4.0, 2.0]  # y = -2x + 12
    result = engine.fit_linear(x, y)
    assert result is not None
    assert result["slope"] < -1.9
    assert result["r2"] > 0.99


# =============================================================================
# WHAT-IF SCENARIO TESTS
# =============================================================================

def test_what_if_linear():
    """Test what-if analysis with linear relationship."""
    engine = CausalEngine()
    x = [0.0, 1.0, 2.0, 3.0, 4.0]
    y = [0.0, 2.0, 4.0, 6.0, 8.0]
    result = engine.what_if(x, y, delta_cause=1.0)
    assert result is not None
    assert math.isfinite(result["slope"]) and result["slope"] > 1.9
    assert math.isfinite(result["r2"]) and result["r2"] > 0.99
    # 1 unit increase in x should increase y by ~2 units
    assert abs(result["predicted_delta"] - 2.0) < 1e-6


def test_what_if_negative_delta():
    """Test what-if with negative change in cause."""
    engine = CausalEngine()
    x = [1.0, 2.0, 3.0, 4.0]
    y = [3.0, 5.0, 7.0, 9.0]  # y = 2x + 1
    result = engine.what_if(x, y, delta_cause=-1.0)
    assert result is not None
    assert result["predicted_delta"] < -1.9  # Should be approximately -2


def test_what_if_zero_delta():
    """Test what-if with zero change."""
    engine = CausalEngine()
    x = [1.0, 2.0, 3.0]
    y = [2.0, 4.0, 6.0]
    result = engine.what_if(x, y, delta_cause=0.0)
    assert result is not None
    assert abs(result["predicted_delta"]) < 1e-6


def test_what_if_invalid_data():
    """Test what-if with invalid input data."""
    engine = CausalEngine()
    result = engine.what_if([], [], delta_cause=1.0)
    assert result is None


# =============================================================================
# DRIVER INFERENCE TESTS
# =============================================================================

def test_infer_drivers():
    """Test driver inference with multiple drivers."""
    engine = CausalEngine()
    x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    y = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0]  # constant, should have low importance
    target = [2.0 * xi + 0.0 for xi in x]
    contribs = engine.infer_drivers(target, {"x": x, "y": y})
    assert contribs, "Expected non-empty driver contributions"
    # Top contributor should be x
    assert contribs[0]["name"] == "x"


def test_infer_drivers_empty():
    """Test driver inference with no drivers."""
    engine = CausalEngine()
    target = [1.0, 2.0, 3.0]
    result = engine.infer_drivers(target, {})
    assert result == []


def test_infer_drivers_mismatched_lengths():
    """Test driver inference with mismatched lengths."""
    engine = CausalEngine()
    target = [1.0, 2.0, 3.0, 4.0]
    drivers = {
        "x": [1.0, 2.0, 3.0],  # Wrong length
        "y": [1.0, 2.0, 3.0, 4.0],
    }
    result = engine.infer_drivers(target, drivers)
    # Should only include y (matching length)
    assert len(result) == 1
    assert result[0]["name"] == "y"


def test_infer_drivers_multiple_contributors():
    """Test driver inference with multiple contributing factors."""
    engine = CausalEngine()
    # target = 3*a + 2*b + 1*c
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [2.0, 4.0, 6.0, 8.0, 10.0]
    c = [1.0, 1.0, 1.0, 1.0, 1.0]
    target = [3*ai + 2*bi + 1*ci for ai, bi, ci in zip(a, b, c)]
    drivers = {"a": a, "b": b, "c": c}
    result = engine.infer_drivers(target, drivers)
    assert len(result) == 3
    # Results should be sorted by absolute beta
    betas = [r["beta"] for r in result]
    for i in range(len(betas) - 1):
        assert abs(betas[i]) >= abs(betas[i + 1])


def test_infer_drivers_sorted_by_importance():
    """Test that drivers are sorted by absolute beta coefficient."""
    engine = CausalEngine()
    # Create target with known coefficients
    x1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    x2 = [2.0, 4.0, 6.0, 8.0, 10.0]
    x3 = [0.5, 1.0, 1.5, 2.0, 2.5]
    target = [5*v1 + 1*v2 + 0.1*v3 for v1, v2, v3 in zip(x1, x2, x3)]
    result = engine.infer_drivers(target, {"x1": x1, "x2": x2, "x3": x3})
    assert len(result) >= 3
    # Should be sorted by importance
    assert abs(result[0]["beta"]) >= abs(result[1]["beta"])
    assert abs(result[1]["beta"]) >= abs(result[2]["beta"])


# =============================================================================
# EXPLANATION GENERATION TESTS
# =============================================================================

def test_explain_change_basic():
    """Test basic change explanation."""
    engine = CausalEngine()
    explanation = engine.explain_change(
        metric="Revenue",
        before=1000.0,
        after=1200.0,
        drivers={"sales": 150.0, "price": 50.0, "cost": -20.0}
    )
    assert "Revenue" in explanation
    assert "200" in explanation  # Delta
    assert "sales" in explanation  # Top driver


def test_explain_change_no_drivers():
    """Test explanation with no driver data."""
    engine = CausalEngine()
    explanation = engine.explain_change(
        metric="Profit",
        before=500.0,
        after=600.0,
        drivers={}
    )
    assert "Profit" in explanation
    assert "100" in explanation
    assert "No driver data" in explanation


def test_explain_change_negative():
    """Test explanation with negative change."""
    engine = CausalEngine()
    explanation = engine.explain_change(
        metric="Cost",
        before=1000.0,
        after=800.0,
        drivers={"efficiency": -150.0, "volume": -50.0}
    )
    assert "Cost" in explanation
    assert "-200" in explanation or "200" in explanation


def test_generate_explanation_correlations():
    """Test generating explanation from correlation results."""
    engine = CausalEngine()
    correlations = [
        {"a": "sales", "b": "revenue", "corr": 0.95, "p_value": 0.001},
        {"a": "cost", "b": "profit", "corr": -0.80, "p_value": 0.01},
    ]
    explanation = engine.generate_explanation(correlations, [])
    assert "sales" in explanation or "revenue" in explanation
    assert "0.95" in explanation
    assert "0.001" in explanation


def test_generate_explanation_granger():
    """Test generating explanation from Granger causality results."""
    engine = CausalEngine()
    granger = [
        {"cause": "marketing", "effect": "sales", "lag": 2, "p_value": 0.02}
    ]
    explanation = engine.generate_explanation([], granger)
    assert "marketing" in explanation
    assert "sales" in explanation
    assert "2" in explanation  # lag


def test_generate_explanation_empty():
    """Test generating explanation with no results."""
    engine = CausalEngine()
    explanation = engine.generate_explanation([], [])
    assert "No significant relationships" in explanation or "detected" in explanation


def test_generate_explanation_combined():
    """Test generating explanation with both correlation and Granger results."""
    engine = CausalEngine()
    correlations = [{"a": "x", "b": "y", "corr": 0.9, "p_value": 0.001}]
    granger = [{"cause": "a", "effect": "b", "lag": 1, "p_value": 0.03}]
    explanation = engine.generate_explanation(correlations, granger)
    assert len(explanation) > 0
    # Should contain elements from both
    assert "correlation" in explanation.lower() or "x" in explanation
    assert "causality" in explanation.lower() or "a" in explanation
