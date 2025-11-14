"""
Forecasting services package

Provides multiple forecasting models:
- ARIMA/SARIMA (statsmodels)
- Prophet (Facebook Prophet)
- XGBoost (gradient boosting)
- Ensemble (combines multiple models)
"""

from .arima import ARIMAForecaster, auto_arima
from .prophet import ProphetForecaster
from .xgboost_model import XGBoostForecaster
from .service import ForecastService, get_forecast_service

__all__ = [
    "ARIMAForecaster",
    "auto_arima",
    "ProphetForecaster",
    "XGBoostForecaster",
    "ForecastService",
    "get_forecast_service",
]
