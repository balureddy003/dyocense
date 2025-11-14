"""
Prophet forecasting model

Uses Facebook Prophet for time series forecasting with seasonality.
Good for data with strong seasonal patterns and holidays.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from prophet import Prophet

logger = logging.getLogger(__name__)


class ProphetForecaster:
    """
    Facebook Prophet forecasting model.
    
    Handles:
    - Daily, weekly, yearly seasonality
    - Holidays and special events
    - Missing data
    - Trend changes
    """
    
    def __init__(
        self,
        seasonality_mode: str = 'additive',
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        changepoint_prior_scale: float = 0.05
    ):
        """
        Initialize Prophet forecaster.
        
        Args:
            seasonality_mode: 'additive' or 'multiplicative'
            yearly_seasonality: Include yearly seasonality
            weekly_seasonality: Include weekly seasonality
            daily_seasonality: Include daily seasonality
            changepoint_prior_scale: Flexibility of trend (higher = more flexible)
        """
        self.seasonality_mode = seasonality_mode
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.changepoint_prior_scale = changepoint_prior_scale
        
        self.model = None
        self.logger = logging.getLogger(__name__)
    
    def fit(self, data: pd.DataFrame) -> dict[str, Any]:
        """
        Fit Prophet model to data.
        
        Args:
            data: DataFrame with columns:
                - ds: Date (datetime)
                - y: Value to forecast
        
        Returns:
            Fit results
        """
        if 'ds' not in data.columns or 'y' not in data.columns:
            raise ValueError("Data must have 'ds' and 'y' columns")
        
        self.logger.info(f"Fitting Prophet model with {len(data)} observations")
        
        # Create and configure model
        self.model = Prophet(
            seasonality_mode=self.seasonality_mode,
            yearly_seasonality=self.yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=self.daily_seasonality,
            changepoint_prior_scale=self.changepoint_prior_scale
        )
        
        # Fit model
        self.model.fit(data)
        
        self.logger.info("Prophet model fitted successfully")
        
        return {
            "status": "success",
            "num_observations": len(data),
            "seasonality_mode": self.seasonality_mode,
            "changepoints": len(self.model.changepoints)
        }
    
    def predict(
        self,
        periods: int,
        freq: str = 'D',
        include_history: bool = False
    ) -> dict[str, Any]:
        """
        Generate forecast.
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D'=daily, 'W'=weekly, 'M'=monthly)
            include_history: Include historical fitted values
        
        Returns:
            Forecast results with predictions and components
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(
            periods=periods,
            freq=freq,
            include_history=include_history
        )
        
        # Generate forecast
        forecast = self.model.predict(future)
        
        # Extract predictions (future only, not history)
        if include_history:
            predictions = forecast.tail(periods)
        else:
            predictions = forecast
        
        result = {
            "predictions": predictions['yhat'].tolist(),
            "dates": predictions['ds'].dt.strftime('%Y-%m-%d').tolist(),
            "lower_bound": predictions['yhat_lower'].tolist(),
            "upper_bound": predictions['yhat_upper'].tolist(),
            "trend": predictions['trend'].tolist()
        }
        
        # Add seasonal components if available
        if 'yearly' in predictions.columns:
            result["yearly_seasonality"] = predictions['yearly'].tolist()
        if 'weekly' in predictions.columns:
            result["weekly_seasonality"] = predictions['weekly'].tolist()
        if 'daily' in predictions.columns:
            result["daily_seasonality"] = predictions['daily'].tolist()
        
        self.logger.info(f"Generated forecast for {periods} periods")
        
        return result
    
    def evaluate(
        self,
        data: pd.DataFrame,
        horizon: str = '30 days',
        period: str = '90 days',
        initial: str = '180 days'
    ) -> dict[str, Any]:
        """
        Evaluate model using cross-validation.
        
        Args:
            data: Training data with 'ds' and 'y' columns
            horizon: Forecast horizon for evaluation
            period: Spacing between cutoff dates
            initial: Initial training period
        
        Returns:
            Cross-validation metrics
        """
        from prophet.diagnostics import cross_validation, performance_metrics
        
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        self.logger.info("Running cross-validation")
        
        # Cross-validation
        df_cv = cross_validation(
            self.model,
            initial=initial,
            period=period,
            horizon=horizon
        )
        
        # Calculate metrics
        df_metrics = performance_metrics(df_cv)
        
        # Average metrics
        avg_metrics = {
            "mae": round(df_metrics['mae'].mean(), 4),
            "rmse": round(df_metrics['rmse'].mean(), 4),
            "mape": round(df_metrics['mape'].mean(), 4),
            "coverage": round(df_metrics['coverage'].mean(), 4)
        }
        
        self.logger.info(f"CV Metrics - MAE: {avg_metrics['mae']}, RMSE: {avg_metrics['rmse']}")
        
        return avg_metrics
    
    def detect_anomalies(
        self,
        data: pd.DataFrame,
        threshold: float = 0.05
    ) -> dict[str, Any]:
        """
        Detect anomalies in time series.
        
        Args:
            data: Data with 'ds' and 'y' columns
            threshold: Anomaly threshold (percentile)
        
        Returns:
            Anomaly detection results
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        # Generate predictions
        forecast = self.model.predict(data)
        
        # Calculate residuals
        residuals = data['y'] - forecast['yhat']
        
        # Detect anomalies (outside prediction intervals)
        is_anomaly = (
            (data['y'] < forecast['yhat_lower']) |
            (data['y'] > forecast['yhat_upper'])
        )
        
        anomalies = data[is_anomaly].copy()
        anomalies['residual'] = residuals[is_anomaly]
        anomalies['yhat'] = forecast.loc[is_anomaly.index, 'yhat']
        
        self.logger.info(f"Detected {len(anomalies)} anomalies")
        
        return {
            "num_anomalies": len(anomalies),
            "anomaly_rate": round(len(anomalies) / len(data), 4),
            "anomalies": anomalies.to_dict('records')
        }
    
    def get_trend_changepoints(self) -> dict[str, Any]:
        """
        Get detected trend changepoints.
        
        Returns:
            Changepoint dates and magnitudes
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        # Get significant changepoints
        changepoints = self.model.changepoints
        deltas = self.model.params['delta'].mean(axis=0)
        
        # Filter significant changes (>5% of trend)
        threshold = np.abs(deltas).max() * 0.05
        significant_idx = np.abs(deltas) > threshold
        
        significant_changepoints = changepoints[significant_idx]
        significant_deltas = deltas[significant_idx]
        
        return {
            "num_changepoints": len(significant_changepoints),
            "changepoints": [
                {
                    "date": cp.strftime('%Y-%m-%d'),
                    "delta": float(delta)
                }
                for cp, delta in zip(significant_changepoints, significant_deltas)
            ]
        }
