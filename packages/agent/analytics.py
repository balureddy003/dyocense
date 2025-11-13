"""
Advanced Analytics Engine for Phase 4
Provides historical trend analysis, period comparisons, anomaly detection, and data export.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal, Tuple
from enum import Enum
import statistics


class TimeGranularity(str, Enum):
    """Time aggregation granularity."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ComparisonPeriod(str, Enum):
    """Period comparison types."""
    PREVIOUS_PERIOD = "previous_period"
    PREVIOUS_YEAR = "previous_year"
    AVERAGE = "average"


@dataclass
class TrendData:
    """Historical trend data for a metric."""
    metric_name: str
    data_points: List[Dict[str, Any]]  # [{date, value, label}]
    trend_direction: Literal["up", "down", "stable"]
    change_percentage: float
    moving_average_7d: Optional[float] = None
    moving_average_30d: Optional[float] = None
    seasonality_detected: bool = False
    forecast_next_period: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricComparison:
    """Comparison of metric across periods."""
    metric_name: str
    current_period: Dict[str, Any]  # {start_date, end_date, value}
    comparison_period: Dict[str, Any]
    absolute_change: float
    percentage_change: float
    is_improvement: bool
    context: str  # Human-readable explanation


@dataclass
class Anomaly:
    """Detected anomaly in metric."""
    metric_name: str
    detected_at: datetime
    value: float
    expected_value: float
    deviation_pct: float
    severity: Literal["low", "medium", "high"]
    explanation: str
    confidence: float


class AdvancedAnalyticsEngine:
    """Advanced analytics and forecasting engine."""
    
    async def get_historical_trend(
        self,
        tenant_id: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity = TimeGranularity.DAILY
    ) -> TrendData:
        """
        Calculate historical trend with moving averages and seasonality.
        
        Steps:
        1. Fetch raw metric data from database
        2. Aggregate by granularity (daily/weekly/monthly)
        3. Calculate moving averages (7-day, 30-day)
        4. Detect seasonality using simple heuristics
        5. Forecast next period using simple linear regression
        6. Determine trend direction
        """
        # TODO: Fetch from actual database
        # For MVP, generate sample data
        data_points = self._generate_sample_data(
            metric_name, start_date, end_date, granularity
        )
        
        # Calculate moving averages
        values = [p["value"] for p in data_points]
        ma_7d = self._calculate_moving_average(values, 7) if len(values) >= 7 else None
        ma_30d = self._calculate_moving_average(values, 30) if len(values) >= 30 else None
        
        # Determine trend direction
        if len(values) < 2:
            trend_direction = "stable"
            change_pct = 0.0
        else:
            # Compare last 7 days to previous 7 days
            recent = values[-7:] if len(values) >= 7 else values[-len(values)//2:]
            earlier = values[-14:-7] if len(values) >= 14 else values[:len(values)//2]
            
            recent_avg = statistics.mean(recent) if recent else 0
            earlier_avg = statistics.mean(earlier) if earlier else 0
            
            if earlier_avg == 0:
                change_pct = 0.0
                trend_direction = "stable"
            else:
                change_pct = ((recent_avg - earlier_avg) / earlier_avg) * 100
                if change_pct > 5:
                    trend_direction = "up"
                elif change_pct < -5:
                    trend_direction = "down"
                else:
                    trend_direction = "stable"
        
        # Simple seasonality detection (check for weekly patterns)
        seasonality_detected = self._detect_seasonality(values, granularity)
        
        # Simple forecast (linear extrapolation)
        forecast = self._simple_forecast(values) if len(values) >= 3 else None
        
        return TrendData(
            metric_name=metric_name,
            data_points=data_points,
            trend_direction=trend_direction,
            change_percentage=round(change_pct, 2),
            moving_average_7d=ma_7d,
            moving_average_30d=ma_30d,
            seasonality_detected=seasonality_detected,
            forecast_next_period=forecast,
            metadata={
                "granularity": granularity,
                "data_points_count": len(data_points),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
    
    async def compare_periods(
        self,
        tenant_id: str,
        metric_name: str,
        current_start: datetime,
        current_end: datetime,
        comparison_type: ComparisonPeriod
    ) -> MetricComparison:
        """
        Compare metric across two time periods.
        
        Examples:
        - This week vs last week
        - This month vs same month last year
        - Current vs historical average
        """
        # Calculate current period value
        current_trend = await self.get_historical_trend(
            tenant_id, metric_name, current_start, current_end
        )
        current_value = statistics.mean([p["value"] for p in current_trend.data_points])
        
        # Determine comparison period dates
        period_length = (current_end - current_start).days
        
        if comparison_type == ComparisonPeriod.PREVIOUS_PERIOD:
            comp_start = current_start - timedelta(days=period_length)
            comp_end = current_start
        elif comparison_type == ComparisonPeriod.PREVIOUS_YEAR:
            comp_start = current_start - timedelta(days=365)
            comp_end = current_end - timedelta(days=365)
        else:  # AVERAGE
            # Compare to 90-day historical average
            comp_start = current_start - timedelta(days=90)
            comp_end = current_start
        
        # Calculate comparison period value
        comp_trend = await self.get_historical_trend(
            tenant_id, metric_name, comp_start, comp_end
        )
        comp_value = statistics.mean([p["value"] for p in comp_trend.data_points])
        
        # Calculate changes
        absolute_change = current_value - comp_value
        percentage_change = (absolute_change / comp_value * 100) if comp_value != 0 else 0.0
        
        # Determine if improvement (depends on metric type)
        # For now, assume higher is better
        is_improvement = absolute_change > 0
        
        # Generate context
        comp_type_label = {
            ComparisonPeriod.PREVIOUS_PERIOD: "previous period",
            ComparisonPeriod.PREVIOUS_YEAR: "same period last year",
            ComparisonPeriod.AVERAGE: "90-day average",
        }[comparison_type]
        
        direction = "up" if absolute_change > 0 else "down"
        context = f"{metric_name} is {direction} {abs(percentage_change):.1f}% vs {comp_type_label}"
        
        return MetricComparison(
            metric_name=metric_name,
            current_period={
                "start_date": current_start.isoformat(),
                "end_date": current_end.isoformat(),
                "value": round(current_value, 2),
            },
            comparison_period={
                "start_date": comp_start.isoformat(),
                "end_date": comp_end.isoformat(),
                "value": round(comp_value, 2),
            },
            absolute_change=round(absolute_change, 2),
            percentage_change=round(percentage_change, 2),
            is_improvement=is_improvement,
            context=context,
        )
    
    async def detect_anomalies(
        self,
        tenant_id: str,
        metric_name: str,
        threshold: float = 2.0  # Standard deviations
    ) -> List[Anomaly]:
        """
        Detect anomalies in metric time series using Z-score method.
        
        Flags data points > threshold standard deviations from mean.
        """
        # Fetch last 90 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        trend = await self.get_historical_trend(
            tenant_id, metric_name, start_date, end_date
        )
        
        values = [p["value"] for p in trend.data_points]
        dates = [datetime.fromisoformat(p["date"]) for p in trend.data_points]
        
        if len(values) < 10:
            return []  # Not enough data
        
        # Calculate mean and std dev
        mean = statistics.mean(values)
        try:
            std_dev = statistics.stdev(values)
        except statistics.StatisticsError:
            std_dev = 0
        
        if std_dev == 0:
            return []  # No variance
        
        # Detect anomalies
        anomalies = []
        for i, (value, date) in enumerate(zip(values, dates)):
            z_score = (value - mean) / std_dev
            
            if abs(z_score) > threshold:
                deviation_pct = ((value - mean) / mean) * 100
                
                # Determine severity
                if abs(z_score) > 3:
                    severity = "high"
                elif abs(z_score) > 2.5:
                    severity = "medium"
                else:
                    severity = "low"
                
                # Generate explanation
                direction = "higher" if value > mean else "lower"
                explanation = (
                    f"{metric_name} was {abs(deviation_pct):.1f}% {direction} than "
                    f"expected ({value:.1f} vs {mean:.1f} average)"
                )
                
                anomalies.append(Anomaly(
                    metric_name=metric_name,
                    detected_at=date,
                    value=value,
                    expected_value=mean,
                    deviation_pct=round(deviation_pct, 2),
                    severity=severity,
                    explanation=explanation,
                    confidence=min(abs(z_score) / 4, 0.95),  # Confidence based on z-score
                ))
        
        return anomalies
    
    async def calculate_cohort_metrics(
        self,
        tenant_id: str,
        cohort_definition: Dict[str, Any],  # e.g., {"business_type": "restaurant"}
        metrics: List[str],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate metrics for specific cohorts.
        
        Useful for:
        - Restaurant-specific analysis
        - Location-based analysis
        - Customer segment analysis
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        cohort_results = {
            "cohort": cohort_definition,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days,
            },
            "metrics": {}
        }
        
        # Calculate each requested metric
        for metric_name in metrics:
            trend = await self.get_historical_trend(
                tenant_id, metric_name, start_date, end_date
            )
            
            values = [p["value"] for p in trend.data_points]
            cohort_results["metrics"][metric_name] = {
                "average": round(statistics.mean(values), 2) if values else 0,
                "min": round(min(values), 2) if values else 0,
                "max": round(max(values), 2) if values else 0,
                "trend": trend.trend_direction,
                "change_percentage": trend.change_percentage,
            }
        
        return cohort_results
    
    async def export_to_csv(
        self,
        tenant_id: str,
        metrics: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> bytes:
        """Generate CSV export of analytics data."""
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow(["Date"] + metrics)
        
        # Fetch data for all metrics
        metric_data = {}
        for metric_name in metrics:
            trend = await self.get_historical_trend(
                tenant_id, metric_name, start_date, end_date
            )
            metric_data[metric_name] = {p["date"]: p["value"] for p in trend.data_points}
        
        # Find all unique dates
        all_dates = sorted(set(date for data in metric_data.values() for date in data.keys()))
        
        # Write data rows
        for date in all_dates:
            row = [date] + [metric_data[m].get(date, "") for m in metrics]
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    # Helper methods
    
    def _generate_sample_data(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity
    ) -> List[Dict[str, Any]]:
        """Generate sample data for testing."""
        import random
        
        data_points = []
        current = start_date
        
        # Determine time delta based on granularity
        if granularity == TimeGranularity.HOURLY:
            delta = timedelta(hours=1)
        elif granularity == TimeGranularity.DAILY:
            delta = timedelta(days=1)
        elif granularity == TimeGranularity.WEEKLY:
            delta = timedelta(weeks=1)
        elif granularity == TimeGranularity.MONTHLY:
            delta = timedelta(days=30)
        else:  # QUARTERLY
            delta = timedelta(days=90)
        
        # Base value depends on metric type
        base_value = {
            "revenue": 5000,
            "health_score": 75,
            "task_completion": 8,
            "profit_margin": 25,
        }.get(metric_name, 100)
        
        while current <= end_date:
            # Add some randomness and trend
            days_from_start = (current - start_date).days
            trend = days_from_start * 0.5  # Slight upward trend
            noise = random.uniform(-10, 10)
            value = max(0, base_value + trend + noise)
            
            data_points.append({
                "date": current.isoformat(),
                "value": round(value, 2),
                "label": current.strftime("%Y-%m-%d"),
            })
            
            current += delta
        
        return data_points
    
    def _calculate_moving_average(self, values: List[float], window: int) -> float:
        """Calculate moving average for the most recent window."""
        if len(values) < window:
            return statistics.mean(values) if values else 0
        return statistics.mean(values[-window:])
    
    def _detect_seasonality(
        self,
        values: List[float],
        granularity: TimeGranularity
    ) -> bool:
        """Simple seasonality detection using autocorrelation heuristic."""
        if len(values) < 14:
            return False
        
        # For daily data, check if there's a weekly pattern
        if granularity == TimeGranularity.DAILY and len(values) >= 28:
            # Compare alternating weeks
            week1 = values[:7]
            week3 = values[14:21]
            
            # If similar, likely seasonal
            if week1 and week3:
                diff = abs(statistics.mean(week1) - statistics.mean(week3))
                avg = (statistics.mean(week1) + statistics.mean(week3)) / 2
                return (diff / avg) < 0.2 if avg > 0 else False
        
        return False
    
    def _simple_forecast(self, values: List[float]) -> float:
        """Simple linear extrapolation for next period."""
        if len(values) < 3:
            return values[-1] if values else 0
        
        # Use last 7 points for trend
        recent = values[-7:] if len(values) >= 7 else values
        
        # Calculate simple linear trend
        n = len(recent)
        x = list(range(n))
        
        # Calculate slope (simple linear regression)
        x_mean = sum(x) / n
        y_mean = sum(recent) / n
        
        numerator = sum((x[i] - x_mean) * (recent[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return recent[-1]
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Forecast next point
        forecast = slope * n + intercept
        return round(max(0, forecast), 2)


def create_analytics_engine() -> AdvancedAnalyticsEngine:
    """Factory function to create analytics engine."""
    return AdvancedAnalyticsEngine()
