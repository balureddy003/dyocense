"""
Forecaster Service
Simple demand forecasting using moving averages and linear regression
Production version should use ARIMA, Prophet, or XGBoost
"""
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime, timezone, timedelta


class ForecastService:
    """Simple forecasting service for demand prediction"""
    
    def __init__(self, backend):
        """Initialize with PostgreSQL backend"""
        self.backend = backend
    
    def _calculate_moving_average(self, values: List[float], window: int = 3) -> float:
        """Calculate simple moving average"""
        if len(values) < window:
            return sum(values) / len(values) if values else 0
        return sum(values[-window:]) / window
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend (slope)"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x_mean = (n - 1) / 2  # 0, 1, 2, ... n-1 average
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0
    
    async def forecast_demand(
        self, 
        tenant_id: str, 
        sku: Optional[str] = None, 
        periods: int = 4
    ) -> Dict[str, Any]:
        """
        Generate demand forecast for next N periods
        
        Args:
            tenant_id: Tenant identifier
            sku: Optional SKU to forecast (if None, forecast all SKUs)
            periods: Number of future periods to forecast
        
        Returns:
            Forecast data with predictions and confidence intervals
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
                    
                    # Parse raw data
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
                    metadata = row[0]
                    trends = metadata.get('trends', {})
                    
                    # Get detailed demand data from raw source
                    source_id = metadata.get('source_id')
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
                
                # Generate forecasts
                forecasts = {}
                for item_sku, historical_data in demand_by_sku.items():
                    # Sort by week
                    sorted_data = sorted(historical_data, key=lambda x: x['week'])
                    values = [d['quantity'] for d in sorted_data]
                    last_week = sorted_data[-1]['week'] if sorted_data else 0
                    
                    # Calculate trend and moving average
                    trend = self._calculate_trend(values)
                    ma = self._calculate_moving_average(values)
                    
                    # Generate predictions
                    predictions = []
                    for i in range(1, periods + 1):
                        # Simple forecast: MA + trend * period
                        forecast_value = ma + (trend * i)
                        forecast_value = max(0, forecast_value)  # No negative demand
                        
                        # Simple confidence interval (±20%)
                        predictions.append({
                            'period': last_week + i,
                            'predicted_quantity': round(forecast_value, 2),
                            'lower_bound': round(forecast_value * 0.8, 2),
                            'upper_bound': round(forecast_value * 1.2, 2),
                            'confidence': 0.8
                        })
                    
                    forecasts[item_sku] = {
                        'historical_data': sorted_data,
                        'trend': round(trend, 4),
                        'moving_average': round(ma, 2),
                        'predictions': predictions
                    }
                
                # Store forecast in database
                forecast_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO forecasts 
                    (forecast_id, tenant_id, metric_name, horizon_days, 
                     predictions, model_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """,
                    [
                        forecast_id,
                        tenant_id,
                        'demand',
                        periods * 7,  # Convert periods to days (assuming weekly)
                        json.dumps(forecasts),
                        'moving_average_trend'
                    ]
                )
                conn.commit()
                
                return {
                    'forecast_id': forecast_id,
                    'forecasts': forecasts,
                    'periods': periods,
                    'model': 'moving_average_trend',
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
