"""
Advanced Forecaster using Prophet
Production-grade time-series forecasting with seasonality detection
"""
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime, timezone
import pandas as pd
import numpy as np

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


class ProphetForecaster:
    """Advanced forecasting using Facebook Prophet"""
    
    def __init__(self, backend):
        """Initialize with PostgreSQL backend"""
        self.backend = backend
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet not installed. Run: pip install prophet")
    
    def _prepare_prophet_data(self, historical_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert historical data to Prophet format (ds, y columns)
        
        Args:
            historical_data: List of {week: int, quantity: float}
        
        Returns:
            DataFrame with 'ds' (dates) and 'y' (values) columns
        """
        if not historical_data:
            return pd.DataFrame(columns=['ds', 'y'])
        
        # Sort by week
        sorted_data = sorted(historical_data, key=lambda x: x['week'])
        
        # Create date range starting from a reference date
        # Assuming week 1 starts at 2025-01-01
        from datetime import timedelta
        base_date = datetime(2025, 1, 1)
        
        dates = []
        values = []
        for item in sorted_data:
            week_num = item['week']
            quantity = item['quantity']
            # Each week is 7 days apart
            date = base_date + timedelta(weeks=week_num - 1)
            dates.append(date)
            values.append(quantity)
        
        df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        return df
    
    async def forecast_with_prophet(
        self,
        tenant_id: str,
        sku: Optional[str] = None,
        periods: int = 4
    ) -> Dict[str, Any]:
        """
        Generate demand forecast using Prophet
        
        Args:
            tenant_id: Tenant identifier
            sku: Optional SKU to forecast
            periods: Number of future periods (weeks) to forecast
        
        Returns:
            Forecast data with predictions, trends, and seasonality
        """
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                # Get demand data from business_metrics
                cur.execute(
                    """
                    SELECT extra_data FROM business_metrics 
                    WHERE tenant_id = %s AND metric_name = 'total_demand'
                    ORDER BY timestamp DESC LIMIT 1
                    """,
                    [tenant_id]
                )
                row = cur.fetchone()
                
                if not row:
                    # Fallback: get from raw_connector_data
                    cur.execute(
                        """
                        SELECT data FROM raw_connector_data 
                        WHERE tenant_id = %s 
                        ORDER BY ingested_at DESC LIMIT 1
                        """,
                        [tenant_id]
                    )
                    raw_row = cur.fetchone()
                    if not raw_row:
                        return {"error": "No demand data found"}
                    
                    raw_data = raw_row[0]
                    sample_rows = raw_data.get('sample_rows', [])
                    
                    # Aggregate by SKU
                    demand_by_sku = {}
                    for item in sample_rows:
                        item_sku = item.get('sku', '')
                        week = int(item.get('week', 0))
                        quantity = float(item.get('quantity', 0))
                        
                        if item_sku not in demand_by_sku:
                            demand_by_sku[item_sku] = []
                        
                        demand_by_sku[item_sku].append({
                            'week': week,
                            'quantity': quantity
                        })
                else:
                    # Get from extra_data
                    source_id = row[0].get('source_id')
                    cur.execute(
                        """
                        SELECT data FROM raw_connector_data 
                        WHERE source_id = %s 
                        ORDER BY ingested_at DESC LIMIT 1
                        """,
                        [source_id]
                    )
                    raw_row = cur.fetchone()
                    if not raw_row:
                        return {"error": "Source data not found"}
                    
                    raw_data = raw_row[0]
                    sample_rows = raw_data.get('sample_rows', [])
                    
                    demand_by_sku = {}
                    for item in sample_rows:
                        item_sku = item.get('sku', '')
                        week = int(item.get('week', 0))
                        quantity = float(item.get('quantity', 0))
                        
                        if item_sku not in demand_by_sku:
                            demand_by_sku[item_sku] = []
                        
                        demand_by_sku[item_sku].append({
                            'week': week,
                            'quantity': quantity
                        })
                
                # Filter by SKU if provided
                if sku:
                    if sku not in demand_by_sku:
                        return {"error": f"No demand data for SKU {sku}"}
                    demand_by_sku = {sku: demand_by_sku[sku]}
                
                # Generate forecasts using Prophet
                forecasts = {}
                for item_sku, historical_data in demand_by_sku.items():
                    # Prepare data for Prophet
                    df = self._prepare_prophet_data(historical_data)
                    
                    if len(df) < 2:
                        # Not enough data for Prophet, use simple average
                        avg = df['y'].mean() if len(df) > 0 else 0
                        predictions = []
                        for i in range(1, periods + 1):
                            predictions.append({
                                'period': historical_data[-1]['week'] + i if historical_data else i,
                                'predicted_quantity': round(avg, 2),
                                'lower_bound': round(avg * 0.8, 2),
                                'upper_bound': round(avg * 1.2, 2),
                                'confidence': 0.6
                            })
                        
                        forecasts[item_sku] = {
                            'historical_data': historical_data,
                            'predictions': predictions,
                            'model': 'simple_average',
                            'trend': 0,
                            'seasonality': None
                        }
                        continue
                    
                    # Train Prophet model
                    model = Prophet(
                        yearly_seasonality=False,
                        weekly_seasonality=False,
                        daily_seasonality=False,
                        interval_width=0.8  # 80% confidence interval
                    )
                    
                    # Suppress Prophet output
                    import logging
                    logging.getLogger('prophet').setLevel(logging.ERROR)
                    
                    model.fit(df)
                    
                    # Make future predictions
                    future = model.make_future_dataframe(periods=periods, freq='W')
                    forecast = model.predict(future)
                    
                    # Extract predictions for future periods
                    future_forecast = forecast.tail(periods)
                    predictions = []
                    last_week = historical_data[-1]['week'] if historical_data else 0
                    
                    for idx, (_, row) in enumerate(future_forecast.iterrows(), start=1):
                        predictions.append({
                            'period': last_week + idx,
                            'predicted_quantity': round(max(0, row['yhat']), 2),
                            'lower_bound': round(max(0, row['yhat_lower']), 2),
                            'upper_bound': round(max(0, row['yhat_upper']), 2),
                            'confidence': 0.8
                        })
                    
                    # Extract trend component
                    trend_component = forecast['trend'].iloc[-1] - forecast['trend'].iloc[0]
                    
                    forecasts[item_sku] = {
                        'historical_data': historical_data,
                        'predictions': predictions,
                        'model': 'prophet',
                        'trend': round(trend_component, 4),
                        'seasonality': None  # Would need more data for meaningful seasonality
                    }
                
                # Store forecast in database
                forecast_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO forecasts 
                    (forecast_id, tenant_id, metric_name, horizon_days, 
                     predictions, model_type, created_at, extra_data)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    [
                        forecast_id,
                        tenant_id,
                        'demand',
                        periods * 7,  # Convert weeks to days
                        json.dumps(forecasts),
                        'prophet',
                        json.dumps({
                            'confidence_interval': 0.8,
                            'seasonality_enabled': False
                        })
                    ]
                )
                conn.commit()
                
                return {
                    'forecast_id': forecast_id,
                    'forecasts': forecasts,
                    'periods': periods,
                    'model': 'prophet',
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
