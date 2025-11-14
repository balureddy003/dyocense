"""
Forecasting service orchestration

Manages multiple forecasting models and provides unified interface.
Includes ensemble forecasting and automatic model selection.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import Forecast, BusinessMetric
from .arima import ARIMAForecaster, auto_arima
from .prophet import ProphetForecaster
from .xgboost_model import XGBoostForecaster

logger = logging.getLogger(__name__)

ModelType = Literal["auto", "arima", "prophet", "xgboost", "ensemble"]


class ForecastService:
    """
    Unified forecasting service.
    
    Provides:
    - Multi-model forecasting
    - Automatic model selection
    - Ensemble predictions
    - Model evaluation and comparison
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize forecast service."""
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def load_data(
        self,
        tenant_id: str,
        metric_name: str,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> pd.DataFrame:
        """
        Load historical metric data.
        
        Args:
            tenant_id: Tenant ID
            metric_name: Metric name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with datetime index
        """
        query = select(BusinessMetric).where(
            BusinessMetric.tenant_id == tenant_id,
            BusinessMetric.metric_name == metric_name
        )
        
        if start_date:
            query = query.where(BusinessMetric.timestamp >= start_date)
        if end_date:
            query = query.where(BusinessMetric.timestamp <= end_date)
        
        query = query.order_by(BusinessMetric.timestamp)
        
        result = await self.db.execute(query)
        metrics = result.scalars().all()
        
        if not metrics:
            raise ValueError(f"No data found for metric '{metric_name}'")
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "timestamp": m.timestamp,
                "value": m.value
            }
            for m in metrics
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        self.logger.info(f"Loaded {len(df)} observations for {metric_name}")
        
        return df
    
    def detect_data_characteristics(self, data: pd.Series) -> dict[str, Any]:
        """
        Analyze time series characteristics to recommend model.
        
        Args:
            data: Time series data
        
        Returns:
            Data characteristics and model recommendation
        """
        # Check for seasonality (using autocorrelation)
        from statsmodels.tsa.stattools import acf
        
        acf_vals = acf(data.dropna(), nlags=min(40, len(data) // 2))
        has_seasonality = any(abs(acf_vals[7:]) > 0.3)  # Check beyond weekly
        
        # Check for trend
        from scipy.stats import linregress
        x = np.arange(len(data))
        y = data.values
        slope, _, r_value, _, _ = linregress(x, y)
        has_trend = abs(r_value) > 0.3
        
        # Check data frequency
        freq = pd.infer_freq(data.index)
        
        # Recommend model
        if has_seasonality and has_trend:
            recommended = "prophet"
            reason = "Strong seasonality and trend detected"
        elif has_seasonality:
            recommended = "arima"
            reason = "Seasonality detected, SARIMA recommended"
        elif len(data) > 100:
            recommended = "xgboost"
            reason = "Large dataset, XGBoost can capture complex patterns"
        else:
            recommended = "arima"
            reason = "Default for simple time series"
        
        return {
            "has_seasonality": has_seasonality,
            "has_trend": has_trend,
            "trend_slope": round(slope, 4),
            "num_observations": len(data),
            "frequency": freq,
            "recommended_model": recommended,
            "recommendation_reason": reason
        }
    
    async def create_forecast(
        self,
        tenant_id: str,
        metric_name: str,
        model_type: ModelType = "auto",
        forecast_horizon: int = 30,
        confidence_level: float = 0.95
    ) -> dict[str, Any]:
        """
        Create forecast for a metric.
        
        Args:
            tenant_id: Tenant ID
            metric_name: Metric to forecast
            model_type: Model to use ('arima', 'prophet', 'xgboost', 'ensemble', 'auto')
            forecast_horizon: Number of periods to forecast
            confidence_level: Confidence level for intervals
        
        Returns:
            Forecast results
        """
        # Load data
        data = await self.load_data(tenant_id, metric_name)
        
        # Auto-detect model if requested
        if model_type == "auto":
            characteristics = self.detect_data_characteristics(data['value'])
            model_type = characteristics['recommended_model']
            self.logger.info(f"Auto-selected model: {model_type}")
        
        # Generate forecast based on model type
        if model_type == "ensemble":
            result = await self._forecast_ensemble(data, forecast_horizon, confidence_level)
        else:
            result = await self._forecast_single_model(
                data,
                model_type,
                forecast_horizon,
                confidence_level
            )
        
        # Save forecast to database
        forecast_record = Forecast(
            tenant_id=tenant_id,
            metric_name=metric_name,
            model_type=model_type,
            forecast_horizon=forecast_horizon,
            predictions=result['predictions'],
            confidence_intervals=result.get('confidence_intervals'),
            accuracy_metrics=result.get('accuracy_metrics'),
            extra_data=result.get('metadata', {})
        )
        
        self.db.add(forecast_record)
        await self.db.commit()
        await self.db.refresh(forecast_record)
        
        result['forecast_id'] = str(forecast_record.id)
        
        return result
    
    async def _forecast_single_model(
        self,
        data: pd.DataFrame,
        model_type: str,
        forecast_horizon: int,
        confidence_level: float
    ) -> dict[str, Any]:
        """Generate forecast using single model."""
        
        if model_type == "arima":
            # Prepare data for ARIMA (needs Series)
            series = data['value']
            
            # Auto-select ARIMA parameters
            forecaster = auto_arima(series, seasonal=True, seasonal_period=7)
            
            # Predict
            predictions = forecaster.predict(
                steps=forecast_horizon,
                return_conf_int=True,
                alpha=1 - confidence_level
            )
            
            return {
                "model_type": "arima",
                "predictions": predictions['predictions'],
                "dates": predictions['dates'],
                "confidence_intervals": predictions.get('confidence_intervals'),
                "metadata": {
                    "order": forecaster.order,
                    "seasonal_order": forecaster.seasonal_order
                }
            }
        
        elif model_type == "prophet":
            # Prepare data for Prophet
            df_prophet = data.reset_index().rename(columns={
                'timestamp': 'ds',
                'value': 'y'
            })
            
            # Fit Prophet
            forecaster = ProphetForecaster()
            forecaster.fit(df_prophet)
            
            # Predict
            predictions = forecaster.predict(periods=forecast_horizon)
            
            return {
                "model_type": "prophet",
                "predictions": predictions['predictions'],
                "dates": predictions['dates'],
                "confidence_intervals": {
                    "lower": predictions['lower_bound'],
                    "upper": predictions['upper_bound']
                },
                "metadata": {
                    "trend": predictions.get('trend'),
                    "seasonality": {
                        k: v for k, v in predictions.items()
                        if 'seasonality' in k
                    }
                }
            }
        
        elif model_type == "xgboost":
            # Prepare data for XGBoost
            df_xgb = data.copy()
            df_xgb.columns = ['y']
            
            # Fit XGBoost
            forecaster = XGBoostForecaster()
            fit_result = forecaster.fit(df_xgb)
            
            # Predict
            predictions = forecaster.predict(df_xgb, steps=forecast_horizon)
            
            return {
                "model_type": "xgboost",
                "predictions": predictions['predictions'],
                "dates": predictions['dates'],
                "metadata": {
                    "num_features": fit_result['num_features'],
                    "feature_importance": fit_result['feature_importance']
                }
            }
        
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    async def _forecast_ensemble(
        self,
        data: pd.DataFrame,
        forecast_horizon: int,
        confidence_level: float
    ) -> dict[str, Any]:
        """
        Generate ensemble forecast (average of multiple models).
        
        Args:
            data: Historical data
            forecast_horizon: Forecast periods
            confidence_level: Confidence level
        
        Returns:
            Ensemble forecast
        """
        self.logger.info("Generating ensemble forecast")
        
        # Generate forecasts from each model
        models = ["arima", "prophet", "xgboost"]
        all_predictions = []
        
        for model_type in models:
            try:
                result = await self._forecast_single_model(
                    data,
                    model_type,
                    forecast_horizon,
                    confidence_level
                )
                all_predictions.append(result['predictions'])
                self.logger.info(f"{model_type} forecast generated")
            except Exception as e:
                self.logger.warning(f"Failed to generate {model_type} forecast: {e}")
        
        if not all_predictions:
            raise RuntimeError("All ensemble models failed")
        
        # Average predictions
        predictions_array = np.array(all_predictions)
        ensemble_predictions = predictions_array.mean(axis=0).tolist()
        
        # Calculate ensemble confidence intervals (std across models)
        ensemble_std = predictions_array.std(axis=0)
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        
        lower_bound = (predictions_array.mean(axis=0) - z_score * ensemble_std).tolist()
        upper_bound = (predictions_array.mean(axis=0) + z_score * ensemble_std).tolist()
        
        # Use dates from first successful model
        dates = result['dates']
        
        return {
            "model_type": "ensemble",
            "predictions": ensemble_predictions,
            "dates": dates,
            "confidence_intervals": {
                "lower": lower_bound,
                "upper": upper_bound,
                "confidence_level": f"{confidence_level*100:.0f}%"
            },
            "metadata": {
                "models_used": models,
                "num_models": len(all_predictions)
            }
        }
    
    async def evaluate_forecast(
        self,
        forecast_id: str
    ) -> dict[str, Any]:
        """
        Evaluate forecast accuracy against actual data.
        
        Args:
            forecast_id: Forecast ID
        
        Returns:
            Accuracy metrics
        """
        # Load forecast
        result = await self.db.execute(
            select(Forecast).where(Forecast.id == forecast_id)
        )
        forecast = result.scalar_one_or_none()
        
        if not forecast:
            raise ValueError(f"Forecast {forecast_id} not found")
        
        # Load actual data for comparison period
        # (This would compare predictions to actual values if available)
        
        return {
            "forecast_id": forecast_id,
            "status": "evaluated",
            "message": "Evaluation requires actual data for forecast period"
        }


# Global instance creator
async def get_forecast_service(db: AsyncSession) -> ForecastService:
    """Get forecast service instance."""
    return ForecastService(db)
