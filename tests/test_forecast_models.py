from __future__ import annotations

import pytest

from services.forecast.main import ForecastSeries, compute_forecast, HAS_ADVANCED_FORECAST
from services.forecast.main import app as forecast_app
from fastapi.testclient import TestClient


@pytest.mark.skipif(not HAS_ADVANCED_FORECAST, reason="statsmodels not installed")
def test_holt_winters_with_seasonality():
    history = [10, 12, 9, 11, 13, 15, 12, 14, 11, 13, 16, 18]
    series = [
        ForecastSeries(
            name="inventory",
            values=history,
            seasonal="add",
            seasonal_periods=4,
            trend="add",
            damped=True,
        )
    ]
    response = compute_forecast(series, horizon=3)

    assert response.model == "holt-winters"
    assert len(response.forecasts) == 3
    for point in response.forecasts:
        assert point.low < point.point < point.high


def test_data_sources_csv(tmp_path):
    csv_path = tmp_path / "widget.csv"
    csv_path.write_text("value\n1\n2\n3\n")

    client = TestClient(forecast_app)
    payload = {
        "horizon": 1,
        "data_sources": [
            {"type": "csv", "path": str(csv_path), "name": "widget"}
        ],
    }
    response = client.post(
        "/v1/forecast",
        json=payload,
        headers={"Authorization": "Bearer demo-tenant"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] in {"holt-winters", "naive-last-value"}
    assert data["forecasts"]
