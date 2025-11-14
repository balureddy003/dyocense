"""
Forecasting Routes

Time series forecasting using multiple models (ARIMA, Prophet, XGBoost).
"""

from __future__ import annotations

from typing import Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.forecaster import get_forecast_service
from backend.dependencies import get_current_user, get_db

router = APIRouter()


# --- Request Models ---

class ForecastRequest(BaseModel):
    """Create forecast request"""
    metric_name: str = Field(..., description="Name of metric to forecast")
    model_type: Literal["auto", "arima", "prophet", "xgboost", "ensemble"] = Field(
        "auto",
        description="Forecasting model ('auto' selects best model)"
    )
    forecast_horizon: int = Field(30, gt=0, le=365, description="Number of periods to forecast")
    confidence_level: float = Field(0.95, ge=0.80, le=0.99, description="Confidence level for intervals")
    start_date: str | None = Field(None, description="Start date for training data (YYYY-MM-DD)")
    end_date: str | None = Field(None, description="End date for training data (YYYY-MM-DD)")


class DataCharacteristicsRequest(BaseModel):
    """Analyze data characteristics request"""
    metric_name: str = Field(..., description="Metric to analyze")
    start_date: str | None = None
    end_date: str | None = None


# --- Response Models ---

class ForecastResponse(BaseModel):
    """Forecast response"""
    forecast_id: str
    model_type: str
    predictions: list[float]
    dates: list[str]
    confidence_intervals: dict | None = None
    metadata: dict | None = None


# --- Routes ---

@router.post("/create", response_model=ForecastResponse)
async def create_forecast(
    request: ForecastRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create forecast for a business metric.
    
    Supports multiple models:
    - **auto**: Automatically selects best model based on data characteristics
    - **arima**: ARIMA/SARIMA for time series with trends/seasonality
    - **prophet**: Facebook Prophet for strong seasonal patterns
    - **xgboost**: XGBoost for complex patterns with feature engineering
    - **ensemble**: Combines multiple models for robust predictions
    
    Returns forecast with predictions and confidence intervals.
    """
    try:
        service = await get_forecast_service(db)
        
        result = await service.create_forecast(
            tenant_id=current_user['tenant_id'],
            metric_name=request.metric_name,
            model_type=request.model_type,
            forecast_horizon=request.forecast_horizon,
            confidence_level=request.confidence_level
        )
        
        return ForecastResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")


@router.get("/{forecast_id}")
async def get_forecast(
    forecast_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve forecast by ID.
    
    Returns the stored forecast with all details.
    """
    from backend.models import Forecast
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(Forecast).where(
                Forecast.id == forecast_id,
                Forecast.tenant_id == current_user['tenant_id']
            )
        )
        forecast = result.scalar_one_or_none()
        
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")
        
        return {
            "forecast_id": str(forecast.id),
            "metric_name": forecast.metric_name,
            "model_type": forecast.model_type,
            "forecast_horizon": forecast.forecast_horizon,
            "predictions": forecast.predictions,
            "confidence_intervals": forecast.confidence_intervals,
            "accuracy_metrics": forecast.accuracy_metrics,
            "created_at": forecast.created_at.isoformat(),
            "metadata": forecast.extra_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-data")
async def analyze_data_characteristics(
    request: DataCharacteristicsRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze time series data characteristics.
    
    Detects:
    - Seasonality
    - Trend
    - Data frequency
    - Recommends best forecasting model
    
    Useful for understanding your data before forecasting.
    """
    try:
        service = await get_forecast_service(db)
        
        # Load data
        data = await service.load_data(
            tenant_id=current_user['tenant_id'],
            metric_name=request.metric_name,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Analyze characteristics
        characteristics = service.detect_data_characteristics(data['value'])
        
        return {
            "metric_name": request.metric_name,
            "num_observations": len(data),
            "date_range": {
                "start": data.index.min().strftime('%Y-%m-%d'),
                "end": data.index.max().strftime('%Y-%m-%d')
            },
            **characteristics
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/")
async def list_forecasts(
    metric_name: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all forecasts for the tenant.
    
    Optionally filter by metric name.
    """
    from backend.models import Forecast
    from sqlalchemy import select
    
    try:
        query = select(Forecast).where(Forecast.tenant_id == current_user['tenant_id'])
        
        if metric_name:
            query = query.where(Forecast.metric_name == metric_name)
        
        query = query.order_by(Forecast.created_at.desc())
        
        result = await db.execute(query)
        forecasts = result.scalars().all()
        
        return {
            "forecasts": [
                {
                    "forecast_id": str(f.id),
                    "metric_name": f.metric_name,
                    "model_type": f.model_type,
                    "forecast_horizon": f.forecast_horizon,
                    "created_at": f.created_at.isoformat()
                }
                for f in forecasts
            ],
            "total": len(forecasts)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{forecast_id}/evaluate")
async def evaluate_forecast(
    forecast_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate forecast accuracy against actual data.
    
    Compares forecast predictions to actual values (if available).
    Returns accuracy metrics (MAE, RMSE, MAPE).
    """
    try:
        service = await get_forecast_service(db)
        result = await service.evaluate_forecast(forecast_id)
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
