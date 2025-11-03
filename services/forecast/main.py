from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    import pandas as pd
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    HAS_ADVANCED_FORECAST = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_ADVANCED_FORECAST = False
    np = None
    pd = None
    ExponentialSmoothing = None

try:
    _DEFAULT_SEASONAL_PERIOD = int(os.getenv("FORECAST_DEFAULT_SEASONAL_PERIOD", "0"))
except ValueError:
    _DEFAULT_SEASONAL_PERIOD = 0

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.data_ingest import load_series_from_sources
from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging

logger = configure_logging("forecast-service")

app = FastAPI(
    title="Dyocense Forecast Service",
    version="0.6.0",
    description="Forecast service powered by Holt-Winters smoothing with naive fallback.",
)


class ForecastSeries(BaseModel):
    name: str = Field(..., description="Identifier for the time series.")
    values: List[float] = Field(
        ..., description="Ordered history values (most recent last)."
    )
    seasonal_periods: int | None = Field(
        default=None,
        ge=2,
        description="Seasonal window for Holt-Winters (auto-detected when omitted).",
    )
    trend: str | None = Field(
        default=None,
        description="Trend component for Holt-Winters (add, mul).",
    )
    seasonal: str | None = Field(
        default=None,
        description="Seasonal component for Holt-Winters (add, mul).",
    )
    damped: bool = Field(
        default=False,
        description="Enable damped trend (only valid when trend component is set).",
    )


class ForecastRequest(BaseModel):
    horizon: int = Field(3, ge=1, le=12, description="Number of periods to forecast.")
    series: List[ForecastSeries] = Field(
        default_factory=list, description="Collection of named time series to forecast."
    )
    data_sources: List[Dict[str, Any]] | None = Field(
        default=None,
        description="Optional external data sources (CSV/MinIO/Sheets) to hydrate the series list.",
    )


class ForecastPoint(BaseModel):
    name: str
    timestamp: str
    point: float
    low: float
    high: float


class ForecastResponse(BaseModel):
    generated_at: str
    model: str
    horizon: int
    forecasts: List[ForecastPoint]


def compute_forecast(series: List[ForecastSeries], horizon: int) -> ForecastResponse:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    model_used = "holt-winters" if HAS_ADVANCED_FORECAST else "naive-last-value"
    forecasts: List[ForecastPoint] = []

    for entry in series:
        horizon_values = _forecast_series(entry, horizon)
        for step, (point, spread) in enumerate(horizon_values, start=1):
            forecasts.append(
                ForecastPoint(
                    name=f"{entry.name}-t+{step}",
                    timestamp=timestamp,
                    point=point,
                    low=point - spread,
                    high=point + spread,
                )
            )

    return ForecastResponse(
        generated_at=timestamp,
        model=model_used,
        horizon=horizon,
        forecasts=forecasts,
    )


@app.post("/v1/forecast", response_model=ForecastResponse)
def forecast(body: ForecastRequest, identity: dict = Depends(require_auth)) -> ForecastResponse:
    series_items = list(body.series)
    if body.data_sources:
        loaded = load_series_from_sources(body.data_sources)
        for entry in loaded:
            series_items.append(ForecastSeries(**entry))
    if not series_items:
        raise HTTPException(status_code=400, detail="No time series provided")

    logger.info(
        "Generating forecast for %d series (tenant=%s)",
        len(series_items),
        identity["tenant_id"],
    )
    return compute_forecast(series_items, body.horizon)

def _normalize_component(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"add", "additive"}:
        return "add"
    if normalized in {"mul", "multiplicative"}:
        return "mul"
    if normalized in {"none", ""}:
        return None
    raise ValueError(f"Unsupported Holt-Winters component '{value}'")


def _resolve_seasonal_period(entry: ForecastSeries, history_len: int, seasonal: Optional[str]) -> Optional[int]:
    if seasonal is None:
        return None
    if entry.seasonal_periods and entry.seasonal_periods >= 2:
        return entry.seasonal_periods
    candidates = [
        _DEFAULT_SEASONAL_PERIOD if _DEFAULT_SEASONAL_PERIOD >= 2 else None,
        12 if history_len >= 24 else None,
        7 if history_len >= 14 else None,
        4 if history_len >= 8 else None,
    ]
    for candidate in candidates:
        if candidate and history_len >= candidate * 2:
            return candidate
    return None


def _build_spreads(preds, sigma: float, history: List[float]) -> List[float]:
    spreads: List[float] = []
    base_spread = sigma * 1.96 if sigma > 0 else 0.05 * abs(history[-1])
    for pred in preds:
        fallback = max(0.01 * abs(float(pred)), 0.01)
        spreads.append(max(base_spread, fallback))
    return spreads


def _forecast_series(entry: ForecastSeries, horizon: int) -> List[tuple[float, float]]:
    history = entry.values
    if HAS_ADVANCED_FORECAST and len(history) >= 3:
        try:
            series = pd.Series(history, dtype="float64")
            trend = _normalize_component(entry.trend)
            seasonal = _normalize_component(entry.seasonal)
            seasonal_periods = _resolve_seasonal_period(entry, len(history), seasonal)
            damped_trend = entry.damped and trend is not None

            hw_kwargs: dict = {
                "trend": trend,
                "seasonal": seasonal,
                "initialization_method": "estimated",
            }
            if damped_trend:
                hw_kwargs["damped_trend"] = True
            if seasonal is not None:
                if seasonal_periods is None:
                    raise ValueError("Seasonal component requires seasonal_periods >= 2")
                hw_kwargs["seasonal_periods"] = seasonal_periods

            model = ExponentialSmoothing(series, **hw_kwargs)
            fit = model.fit(optimized=True)
            preds = fit.forecast(horizon)
            residuals = (series - fit.fittedvalues).dropna()
            sigma = float(residuals.std(ddof=1)) if len(residuals) else 0.0
            spreads = _build_spreads(preds, sigma, history)
            return list(zip([float(p) for p in preds], spreads))
        except Exception as exc:  # pragma: no cover - fallback
            logger.warning("Advanced forecast failed (%s). Falling back to naive.", exc)

    last_value = history[-1]
    delta = max(0.05 * abs(last_value), 0.01)
    return [(last_value, delta) for _ in range(horizon)]
