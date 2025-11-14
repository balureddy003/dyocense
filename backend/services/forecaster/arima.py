"""
ARIMA/SARIMA forecasting model

Uses statsmodels for ARIMA and SARIMA (Seasonal ARIMA) models.
Good for time series with trends and seasonality.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

logger = logging.getLogger(__name__)


class ARIMAForecaster:
    """
    ARIMA/SARIMA forecasting model.
    
    ARIMA(p,d,q):
    - p: Number of autoregressive terms
    - d: Number of differences (to make series stationary)
    - q: Number of moving average terms
    
    SARIMA(p,d,q)(P,D,Q,s):
    - Adds seasonal components with period s
    """
    
    def __init__(
        self,
        order: tuple[int, int, int] = (1, 1, 1),
        seasonal_order: tuple[int, int, int, int] | None = None,
        auto_detect_stationarity: bool = True
    ):
        """
        Initialize ARIMA forecaster.
        
        Args:
            order: ARIMA order (p, d, q)
            seasonal_order: Seasonal order (P, D, Q, s) or None for non-seasonal
            auto_detect_stationarity: Auto-detect if series needs differencing
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.auto_detect_stationarity = auto_detect_stationarity
        self.model = None
        self.fitted_model = None
        self.logger = logging.getLogger(__name__)
    
    def check_stationarity(self, series: pd.Series) -> dict[str, Any]:
        """
        Check if time series is stationary using Augmented Dickey-Fuller test.
        
        Args:
            series: Time series data
        
        Returns:
            Dict with test results and recommendation
        """
        # ADF test
        result = adfuller(series.dropna())
        
        adf_statistic = result[0]
        p_value = result[1]
        critical_values = result[4]
        
        is_stationary = p_value < 0.05
        
        self.logger.info(
            f"ADF Statistic: {adf_statistic:.4f}, p-value: {p_value:.4f}, "
            f"Stationary: {is_stationary}"
        )
        
        return {
            "is_stationary": is_stationary,
            "adf_statistic": round(adf_statistic, 4),
            "p_value": round(p_value, 4),
            "critical_values": {k: round(v, 4) for k, v in critical_values.items()},
            "recommendation": "Series is stationary" if is_stationary else "Apply differencing (d=1 or d=2)"
        }
    
    def fit(self, data: pd.Series) -> dict[str, Any]:
        """
        Fit ARIMA model to data.
        
        Args:
            data: Time series data (pd.Series with DatetimeIndex)
        
        Returns:
            Fit results and diagnostics
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have DatetimeIndex")
        
        # Check stationarity if auto-detect enabled
        if self.auto_detect_stationarity:
            stationarity = self.check_stationarity(data)
            if not stationarity['is_stationary'] and self.order[1] == 0:
                self.logger.warning(
                    "Series not stationary and d=0. Consider setting d=1 or d=2"
                )
        
        # Fit SARIMAX model
        self.logger.info(f"Fitting SARIMA{self.order}{self.seasonal_order or ''}")
        
        self.model = SARIMAX(
            data,
            order=self.order,
            seasonal_order=self.seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        
        self.fitted_model = self.model.fit(disp=False)
        
        # Extract diagnostics
        aic = self.fitted_model.aic
        bic = self.fitted_model.bic
        
        self.logger.info(f"Model fitted. AIC: {aic:.2f}, BIC: {bic:.2f}")
        
        return {
            "status": "success",
            "aic": round(aic, 2),
            "bic": round(bic, 2),
            "parameters": self.fitted_model.params.to_dict(),
            "converged": self.fitted_model.mle_retvals['converged']
        }
    
    def predict(
        self,
        steps: int,
        return_conf_int: bool = True,
        alpha: float = 0.05
    ) -> dict[str, Any]:
        """
        Generate forecast.
        
        Args:
            steps: Number of periods to forecast
            return_conf_int: Return confidence intervals
            alpha: Significance level for confidence intervals (0.05 = 95% CI)
        
        Returns:
            Forecast results with predictions and intervals
        """
        if self.fitted_model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        # Generate forecast
        forecast = self.fitted_model.get_forecast(steps=steps)
        
        predictions = forecast.predicted_mean
        
        result = {
            "predictions": predictions.tolist(),
            "dates": predictions.index.strftime('%Y-%m-%d').tolist()
        }
        
        if return_conf_int:
            conf_int = forecast.conf_int(alpha=alpha)
            result["confidence_intervals"] = {
                "lower": conf_int.iloc[:, 0].tolist(),
                "upper": conf_int.iloc[:, 1].tolist(),
                "alpha": alpha,
                "confidence_level": f"{(1-alpha)*100:.0f}%"
            }
        
        self.logger.info(f"Generated forecast for {steps} periods")
        
        return result
    
    def evaluate(self, actual: pd.Series, predicted: pd.Series) -> dict[str, Any]:
        """
        Evaluate forecast accuracy.
        
        Args:
            actual: Actual values
            predicted: Predicted values
        
        Returns:
            Accuracy metrics (MAE, RMSE, MAPE)
        """
        # Align series
        actual, predicted = actual.align(predicted, join='inner')
        
        # Calculate metrics
        mae = np.mean(np.abs(actual - predicted))
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # MAPE (avoid division by zero)
        mask = actual != 0
        mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100 if mask.any() else np.nan
        
        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape": round(mape, 2) if not np.isnan(mape) else None,
            "num_observations": len(actual)
        }


def auto_arima(
    data: pd.Series,
    seasonal: bool = True,
    seasonal_period: int = 12,
    max_p: int = 3,
    max_q: int = 3,
    max_d: int = 2
) -> ARIMAForecaster:
    """
    Automatically select best ARIMA parameters using grid search.
    
    Args:
        data: Time series data
        seasonal: Include seasonal component
        seasonal_period: Seasonal period (e.g., 12 for monthly data)
        max_p: Maximum p value to test
        max_q: Maximum q value to test
        max_d: Maximum d value to test
    
    Returns:
        Best fitted ARIMAForecaster
    """
    logger.info("Running auto ARIMA parameter selection")
    
    best_aic = float('inf')
    best_order = None
    best_seasonal_order = None
    
    # Grid search
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                try:
                    order = (p, d, q)
                    seasonal_order = (1, 1, 1, seasonal_period) if seasonal else None
                    
                    model = SARIMAX(
                        data,
                        order=order,
                        seasonal_order=seasonal_order,
                        enforce_stationarity=False,
                        enforce_invertibility=False
                    )
                    
                    fitted = model.fit(disp=False)
                    aic = fitted.aic
                    
                    if aic < best_aic:
                        best_aic = aic
                        best_order = order
                        best_seasonal_order = seasonal_order
                    
                except Exception as e:
                    logger.debug(f"Failed to fit ARIMA{order}: {e}")
                    continue
    
    logger.info(f"Best model: ARIMA{best_order} with AIC={best_aic:.2f}")
    
    # Create and fit best model
    forecaster = ARIMAForecaster(
        order=best_order,
        seasonal_order=best_seasonal_order
    )
    forecaster.fit(data)
    
    return forecaster
