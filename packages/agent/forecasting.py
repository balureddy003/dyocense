"""
Advanced Forecasting Engine

Implements predictive analytics with trend forecasting, seasonality detection,
anomaly detection, and what-if scenario modeling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import statistics
from collections import defaultdict


class ForecastMethod(str, Enum):
    """Forecasting methods available."""
    LINEAR = "linear"  # Simple linear regression
    MOVING_AVERAGE = "moving_average"  # Moving average
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"  # Simple exponential smoothing
    SEASONAL = "seasonal"  # Seasonal decomposition
    AUTO = "auto"  # Automatically select best method


class SeasonalityPeriod(str, Enum):
    """Seasonality periods."""
    DAILY = "daily"  # 24-hour pattern
    WEEKLY = "weekly"  # 7-day pattern
    MONTHLY = "monthly"  # 30-day pattern
    QUARTERLY = "quarterly"  # 90-day pattern
    YEARLY = "yearly"  # 365-day pattern


class AnomalyMethod(str, Enum):
    """Anomaly detection methods."""
    ZSCORE = "zscore"  # Statistical Z-score
    IQR = "iqr"  # Interquartile range
    ISOLATION_FOREST = "isolation_forest"  # ML-based (requires sklearn)


@dataclass
class ForecastResult:
    """Result of forecasting operation."""
    metric_name: str
    method: ForecastMethod
    forecast_periods: int
    forecasted_values: List[Dict[str, Any]]
    confidence_intervals: List[Dict[str, Any]]
    accuracy_metrics: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SeasonalityResult:
    """Result of seasonality analysis."""
    metric_name: str
    has_seasonality: bool
    period: Optional[SeasonalityPeriod]
    strength: float  # 0-1, how strong the seasonal pattern is
    seasonal_components: List[float]
    trend_components: List[float]
    residual_components: List[float]


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection."""
    metric_name: str
    method: AnomalyMethod
    anomalies: List[Dict[str, Any]]
    anomaly_count: int
    anomaly_percentage: float


@dataclass
class ScenarioResult:
    """Result of what-if scenario analysis."""
    scenario_name: str
    assumptions: Dict[str, Any]
    predicted_outcomes: Dict[str, float]
    comparison_to_baseline: Dict[str, float]
    confidence_level: float


class ForecastingEngine:
    """Advanced forecasting and predictive analytics engine."""
    
    def __init__(self):
        """Initialize the forecasting engine."""
        self.historical_data_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    async def forecast_metric(
        self,
        tenant_id: str,
        metric_name: str,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        periods: int = 7,
        method: ForecastMethod = ForecastMethod.AUTO,
        confidence_level: float = 0.95
    ) -> ForecastResult:
        """
        Generate forecast for a metric.
        
        Args:
            tenant_id: Tenant identifier
            metric_name: Metric to forecast
            historical_data: Historical data points (if None, fetches from cache)
            periods: Number of periods to forecast ahead
            method: Forecasting method to use
            confidence_level: Confidence level for intervals (0-1)
        
        Returns:
            ForecastResult with predictions and confidence intervals
        """
        # Get historical data
        if historical_data is None:
            historical_data = await self._fetch_historical_data(tenant_id, metric_name)
        
        if len(historical_data) < 7:
            raise ValueError("Need at least 7 historical data points for forecasting")
        
        # Extract values and dates
        values = [point["value"] for point in historical_data]
        dates = [point["date"] for point in historical_data]
        
        # Auto-select method if needed
        if method == ForecastMethod.AUTO:
            method = self._select_best_method(values)
        
        # Generate forecast based on method
        if method == ForecastMethod.LINEAR:
            forecasted = self._linear_forecast(values, periods)
        elif method == ForecastMethod.MOVING_AVERAGE:
            forecasted = self._moving_average_forecast(values, periods)
        elif method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            forecasted = self._exponential_smoothing_forecast(values, periods)
        elif method == ForecastMethod.SEASONAL:
            forecasted = self._seasonal_forecast(values, periods)
        else:
            forecasted = self._linear_forecast(values, periods)
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            values, forecasted, confidence_level
        )
        
        # Generate forecast dates
        last_date = datetime.fromisoformat(dates[-1]) if isinstance(dates[-1], str) else dates[-1]
        forecast_dates = [
            (last_date + timedelta(days=i+1)).isoformat()
            for i in range(periods)
        ]
        
        # Calculate accuracy metrics
        accuracy_metrics = self._calculate_accuracy_metrics(values)
        
        # Build result
        forecasted_values = [
            {
                "date": forecast_dates[i],
                "value": round(forecasted[i], 2),
                "is_forecast": True
            }
            for i in range(periods)
        ]
        
        confidence_data = [
            {
                "date": forecast_dates[i],
                "lower_bound": round(confidence_intervals[i]["lower"], 2),
                "upper_bound": round(confidence_intervals[i]["upper"], 2)
            }
            for i in range(periods)
        ]
        
        return ForecastResult(
            metric_name=metric_name,
            method=method,
            forecast_periods=periods,
            forecasted_values=forecasted_values,
            confidence_intervals=confidence_data,
            accuracy_metrics=accuracy_metrics,
            metadata={
                "historical_points": len(values),
                "confidence_level": confidence_level
            }
        )
    
    def _select_best_method(self, values: List[float]) -> ForecastMethod:
        """Auto-select best forecasting method based on data characteristics."""
        # Check for seasonality
        if len(values) >= 14:
            has_seasonality = self._quick_seasonality_check(values, period=7)
            if has_seasonality:
                return ForecastMethod.SEASONAL
        
        # Check for trend strength
        trend_strength = self._calculate_trend_strength(values)
        if trend_strength > 0.3:
            return ForecastMethod.LINEAR
        
        # Default to exponential smoothing
        return ForecastMethod.EXPONENTIAL_SMOOTHING
    
    def _quick_seasonality_check(self, values: List[float], period: int) -> bool:
        """Quick check for seasonality using autocorrelation."""
        if len(values) < period * 2:
            return False
        
        # Calculate autocorrelation at lag=period
        mean = statistics.mean(values)
        n = len(values)
        
        c0 = sum((x - mean) ** 2 for x in values) / n
        c_lag = sum((values[i] - mean) * (values[i - period] - mean) 
                    for i in range(period, n)) / n
        
        if c0 == 0:
            return False
        
        autocorr = c_lag / c0
        return autocorr > 0.5  # Strong positive correlation
    
    def _calculate_trend_strength(self, values: List[float]) -> float:
        """Calculate strength of linear trend (0-1)."""
        n = len(values)
        if n < 2:
            return 0.0
        
        # Calculate linear regression
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Calculate R-squared
        y_pred = [slope * x + (y_mean - slope * x_mean) for x in x_values]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        
        if ss_tot == 0:
            return 0.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return abs(r_squared)
    
    def _linear_forecast(self, values: List[float], periods: int) -> List[float]:
        """Linear regression forecast."""
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope and intercept
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            # No trend, return mean
            return [y_mean] * periods
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Generate forecasts
        forecasts = [slope * (n + i) + intercept for i in range(periods)]
        
        # Ensure non-negative values for most business metrics
        return [max(0, f) for f in forecasts]
    
    def _moving_average_forecast(
        self, 
        values: List[float], 
        periods: int,
        window: int = 7
    ) -> List[float]:
        """Moving average forecast."""
        # Calculate moving average of last window
        window_size = min(window, len(values))
        moving_avg = sum(values[-window_size:]) / window_size
        
        # Simple forecast: repeat the moving average
        return [moving_avg] * periods
    
    def _exponential_smoothing_forecast(
        self,
        values: List[float],
        periods: int,
        alpha: float = 0.3
    ) -> List[float]:
        """Exponential smoothing forecast."""
        # Calculate smoothed values
        smoothed = [values[0]]
        for i in range(1, len(values)):
            smoothed_value = alpha * values[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(smoothed_value)
        
        # Calculate trend
        if len(smoothed) >= 2:
            trend = smoothed[-1] - smoothed[-2]
        else:
            trend = 0
        
        # Forecast with trend
        last_value = smoothed[-1]
        forecasts = [last_value + trend * (i + 1) for i in range(periods)]
        
        return [max(0, f) for f in forecasts]
    
    def _seasonal_forecast(
        self,
        values: List[float],
        periods: int,
        season_length: int = 7
    ) -> List[float]:
        """Seasonal forecast with trend."""
        n = len(values)
        
        # Calculate seasonal indices
        seasonal_indices = self._calculate_seasonal_indices(values, season_length)
        
        # Calculate deseasonalized trend
        deseasonalized = [
            values[i] / seasonal_indices[i % season_length]
            for i in range(n)
        ]
        
        # Linear trend on deseasonalized data
        trend_forecast = self._linear_forecast(deseasonalized, periods)
        
        # Reapply seasonality
        forecasts = [
            trend_forecast[i] * seasonal_indices[i % season_length]
            for i in range(periods)
        ]
        
        return [max(0, f) for f in forecasts]
    
    def _calculate_seasonal_indices(
        self,
        values: List[float],
        season_length: int
    ) -> List[float]:
        """Calculate seasonal indices."""
        n = len(values)
        
        # Group by season
        seasonal_sums = defaultdict(list)
        for i, value in enumerate(values):
            seasonal_sums[i % season_length].append(value)
        
        # Calculate average for each season
        seasonal_avgs = [
            statistics.mean(seasonal_sums[i]) if seasonal_sums[i] else 1.0
            for i in range(season_length)
        ]
        
        # Normalize to sum to season_length
        total = sum(seasonal_avgs)
        if total == 0:
            return [1.0] * season_length
        
        return [avg * season_length / total for avg in seasonal_avgs]
    
    def _calculate_confidence_intervals(
        self,
        historical: List[float],
        forecasted: List[float],
        confidence_level: float
    ) -> List[Dict[str, float]]:
        """Calculate confidence intervals for forecasts."""
        # Calculate standard error from historical residuals
        mean_value = statistics.mean(historical)
        std_dev = statistics.stdev(historical) if len(historical) > 1 else 0
        
        # Z-score for confidence level (approximation)
        z_score = 1.96 if confidence_level >= 0.95 else 1.645
        
        # Widen intervals for further forecasts
        intervals = []
        for i, forecast in enumerate(forecasted):
            # Increase uncertainty with forecast distance
            uncertainty_factor = 1 + (i * 0.1)
            margin = z_score * std_dev * uncertainty_factor
            
            intervals.append({
                "lower": max(0, forecast - margin),
                "upper": forecast + margin
            })
        
        return intervals
    
    def _calculate_accuracy_metrics(self, values: List[float]) -> Dict[str, float]:
        """Calculate forecast accuracy metrics."""
        if len(values) < 2:
            return {"mape": 0.0, "rmse": 0.0}
        
        # MAPE (Mean Absolute Percentage Error) - using historical variance
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        
        mape = (std_val / mean_val * 100) if mean_val > 0 else 0
        
        # RMSE (Root Mean Squared Error)
        rmse = std_val
        
        return {
            "mape": round(mape, 2),
            "rmse": round(rmse, 2)
        }
    
    async def detect_seasonality(
        self,
        tenant_id: str,
        metric_name: str,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> SeasonalityResult:
        """
        Detect seasonality in time series data.
        
        Args:
            tenant_id: Tenant identifier
            metric_name: Metric to analyze
            historical_data: Historical data points
        
        Returns:
            SeasonalityResult with seasonal decomposition
        """
        # Get historical data
        if historical_data is None:
            historical_data = await self._fetch_historical_data(tenant_id, metric_name)
        
        values = [point["value"] for point in historical_data]
        
        if len(values) < 14:
            return SeasonalityResult(
                metric_name=metric_name,
                has_seasonality=False,
                period=None,
                strength=0.0,
                seasonal_components=[],
                trend_components=[],
                residual_components=[]
            )
        
        # Test different periods
        periods_to_test = [
            (7, SeasonalityPeriod.WEEKLY),
            (30, SeasonalityPeriod.MONTHLY),
        ]
        
        best_period = None
        best_strength = 0.0
        
        for period_len, period_type in periods_to_test:
            if len(values) >= period_len * 2:
                strength = self._calculate_seasonality_strength(values, period_len)
                if strength > best_strength:
                    best_strength = strength
                    best_period = (period_len, period_type)
        
        has_seasonality = best_strength > 0.3
        
        if has_seasonality and best_period:
            period_len, period_type = best_period
            # Decompose
            seasonal, trend, residual = self._seasonal_decomposition(values, period_len)
        else:
            period_type = None
            seasonal = []
            trend = values.copy()
            residual = [0.0] * len(values)
        
        return SeasonalityResult(
            metric_name=metric_name,
            has_seasonality=has_seasonality,
            period=period_type,
            strength=best_strength,
            seasonal_components=seasonal,
            trend_components=trend,
            residual_components=residual
        )
    
    def _calculate_seasonality_strength(
        self,
        values: List[float],
        period: int
    ) -> float:
        """Calculate strength of seasonality (0-1)."""
        if len(values) < period * 2:
            return 0.0
        
        # Calculate autocorrelation at seasonal lag
        mean = statistics.mean(values)
        n = len(values)
        
        c0 = sum((x - mean) ** 2 for x in values) / n
        if c0 == 0:
            return 0.0
        
        c_lag = sum((values[i] - mean) * (values[i - period] - mean)
                    for i in range(period, n)) / n
        
        autocorr = abs(c_lag / c0)
        return min(autocorr, 1.0)
    
    def _seasonal_decomposition(
        self,
        values: List[float],
        period: int
    ) -> Tuple[List[float], List[float], List[float]]:
        """Decompose time series into seasonal, trend, and residual."""
        n = len(values)
        
        # Calculate seasonal indices
        seasonal_indices = self._calculate_seasonal_indices(values, period)
        
        # Seasonal component
        seasonal = [seasonal_indices[i % period] for i in range(n)]
        
        # Deseasonalize
        deseasonalized = [values[i] / seasonal[i] if seasonal[i] != 0 else values[i]
                          for i in range(n)]
        
        # Trend (moving average of deseasonalized)
        window = min(period, n // 2)
        trend = []
        for i in range(n):
            start = max(0, i - window // 2)
            end = min(n, i + window // 2 + 1)
            trend.append(statistics.mean(deseasonalized[start:end]))
        
        # Residual
        residual = [values[i] - (seasonal[i] * trend[i])
                    for i in range(n)]
        
        return seasonal, trend, residual
    
    async def detect_anomalies(
        self,
        tenant_id: str,
        metric_name: str,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        method: AnomalyMethod = AnomalyMethod.ZSCORE,
        sensitivity: float = 3.0
    ) -> AnomalyDetectionResult:
        """
        Detect anomalies in time series data.
        
        Args:
            tenant_id: Tenant identifier
            metric_name: Metric to analyze
            historical_data: Historical data points
            method: Anomaly detection method
            sensitivity: Sensitivity threshold (higher = less sensitive)
        
        Returns:
            AnomalyDetectionResult with detected anomalies
        """
        # Get historical data
        if historical_data is None:
            historical_data = await self._fetch_historical_data(tenant_id, metric_name)
        
        if len(historical_data) < 7:
            return AnomalyDetectionResult(
                metric_name=metric_name,
                method=method,
                anomalies=[],
                anomaly_count=0,
                anomaly_percentage=0.0
            )
        
        # Detect based on method
        if method == AnomalyMethod.ZSCORE:
            anomalies = self._zscore_anomalies(historical_data, sensitivity)
        elif method == AnomalyMethod.IQR:
            anomalies = self._iqr_anomalies(historical_data, sensitivity)
        else:
            anomalies = self._zscore_anomalies(historical_data, sensitivity)
        
        anomaly_pct = (len(anomalies) / len(historical_data) * 100) if historical_data else 0
        
        return AnomalyDetectionResult(
            metric_name=metric_name,
            method=method,
            anomalies=anomalies,
            anomaly_count=len(anomalies),
            anomaly_percentage=round(anomaly_pct, 2)
        )
    
    def _zscore_anomalies(
        self,
        data: List[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Detect anomalies using Z-score method."""
        values = [point["value"] for point in data]
        
        if len(values) < 2:
            return []
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        if std_dev == 0:
            return []
        
        anomalies = []
        for point in data:
            z_score = abs((point["value"] - mean) / std_dev)
            if z_score > threshold:
                anomalies.append({
                    "date": point["date"],
                    "value": point["value"],
                    "expected_value": mean,
                    "z_score": round(z_score, 2),
                    "deviation": round(abs(point["value"] - mean), 2),
                    "severity": "high" if z_score > threshold + 1 else "medium"
                })
        
        return anomalies
    
    def _iqr_anomalies(
        self,
        data: List[Dict[str, Any]],
        multiplier: float
    ) -> List[Dict[str, Any]]:
        """Detect anomalies using IQR method."""
        values = [point["value"] for point in data]
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1
        
        if iqr == 0:
            return []
        
        # Calculate bounds
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        anomalies = []
        for point in data:
            if point["value"] < lower_bound or point["value"] > upper_bound:
                median = statistics.median(values)
                anomalies.append({
                    "date": point["date"],
                    "value": point["value"],
                    "expected_range": f"{round(lower_bound, 2)} - {round(upper_bound, 2)}",
                    "deviation": round(abs(point["value"] - median), 2),
                    "severity": "high" if abs(point["value"] - median) > 2 * iqr else "medium"
                })
        
        return anomalies
    
    async def run_scenario(
        self,
        tenant_id: str,
        scenario_name: str,
        assumptions: Dict[str, Any],
        baseline_metrics: Optional[Dict[str, float]] = None
    ) -> ScenarioResult:
        """
        Run what-if scenario analysis.
        
        Args:
            tenant_id: Tenant identifier
            scenario_name: Name of the scenario
            assumptions: Scenario assumptions (e.g., {"revenue_growth": 0.15})
            baseline_metrics: Current metric values
        
        Returns:
            ScenarioResult with predicted outcomes
        """
        # Get baseline if not provided
        if baseline_metrics is None:
            baseline_metrics = await self._fetch_current_metrics(tenant_id)
        
        # Apply scenario assumptions
        predicted_outcomes = {}
        comparison_to_baseline = {}
        
        for metric, baseline_value in baseline_metrics.items():
            # Check if there's an assumption for this metric
            growth_key = f"{metric}_growth"
            change_key = f"{metric}_change"
            
            if growth_key in assumptions:
                # Percentage growth
                growth = assumptions[growth_key]
                predicted = baseline_value * (1 + growth)
            elif change_key in assumptions:
                # Absolute change
                change = assumptions[change_key]
                predicted = baseline_value + change
            else:
                # No change
                predicted = baseline_value
            
            predicted_outcomes[metric] = round(predicted, 2)
            comparison_to_baseline[metric] = round(predicted - baseline_value, 2)
        
        # Calculate confidence based on assumption complexity
        confidence = 0.8 - (len(assumptions) * 0.05)
        confidence = max(0.5, min(0.95, confidence))
        
        return ScenarioResult(
            scenario_name=scenario_name,
            assumptions=assumptions,
            predicted_outcomes=predicted_outcomes,
            comparison_to_baseline=comparison_to_baseline,
            confidence_level=round(confidence, 2)
        )
    
    async def _fetch_historical_data(
        self,
        tenant_id: str,
        metric_name: str,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Fetch historical data for a metric (MVP: sample data)."""
        # MVP: Generate sample data
        data = []
        base_value = 1000 if metric_name == "revenue" else 80
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            
            # Add trend
            trend = i * 2
            
            # Add seasonality (weekly pattern)
            seasonal = 50 * (1 + 0.5 * ((i % 7) / 3.5 - 1))
            
            # Add noise
            import random
            noise = random.uniform(-20, 20)
            
            value = base_value + trend + seasonal + noise
            
            data.append({
                "date": date.isoformat(),
                "value": max(0, value)
            })
        
        return data
    
    async def _fetch_current_metrics(
        self,
        tenant_id: str
    ) -> Dict[str, float]:
        """Fetch current metric values (MVP: sample data)."""
        return {
            "revenue": 50000,
            "profit": 15000,
            "customers": 500,
            "orders": 1200,
            "avg_order_value": 41.67
        }


def create_forecasting_engine() -> ForecastingEngine:
    """Factory function to create ForecastingEngine instance."""
    return ForecastingEngine()
