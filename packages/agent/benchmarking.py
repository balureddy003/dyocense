"""
Peer Benchmarking System

Provides anonymized industry benchmarks for comparison:
- Aggregate metrics across similar businesses
- Percentile rankings (25th, 50th, 75th, 90th)
- "You vs peers" comparisons
- Industry-specific benchmarks by business type
- Regional adjustments (optional)

Privacy:
- All data is anonymized and aggregated
- Minimum sample size (10+ businesses) required
- No individual business identification
- Opt-in only for sharing data
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics


class BenchmarkMetric(str, Enum):
    """Metrics available for benchmarking"""
    # Financial
    REVENUE = "revenue"
    PROFIT_MARGIN = "profit_margin"
    REVENUE_GROWTH = "revenue_growth"
    
    # Restaurant
    FOOD_COST_PCT = "food_cost_pct"
    LABOR_COST_PCT = "labor_cost_pct"
    PRIME_COST_PCT = "prime_cost_pct"
    AVG_CHECK_SIZE = "avg_check_size"
    
    # Retail
    INVENTORY_TURNOVER = "inventory_turnover"
    GROSS_MARGIN = "gross_margin"
    CONVERSION_RATE = "conversion_rate"
    
    # Services
    UTILIZATION_RATE = "utilization_rate"
    REALIZATION_RATE = "realization_rate"
    PROJECT_MARGIN = "project_margin"
    
    # Contractor
    JOB_COMPLETION_RATE = "job_completion_rate"
    MATERIAL_COST_PCT = "material_cost_pct"
    LABOR_EFFICIENCY = "labor_efficiency"


@dataclass
class BenchmarkData:
    """Benchmark statistics for a metric"""
    metric: str
    business_type: str
    sample_size: int
    
    # Percentiles
    p25: float  # 25th percentile
    p50: float  # 50th percentile (median)
    p75: float  # 75th percentile
    p90: float  # 90th percentile
    
    # Additional stats
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    
    # Metadata
    period: str  # e.g., "30_days", "90_days"
    last_updated: str
    
    def get_percentile_rank(self, value: float) -> float:
        """
        Calculate what percentile a value falls into
        
        Returns:
            Percentile rank (0-100)
        """
        if value <= self.p25:
            return 25.0 * (value - self.min_value) / (self.p25 - self.min_value) if self.p25 > self.min_value else 0
        elif value <= self.p50:
            return 25.0 + 25.0 * (value - self.p25) / (self.p50 - self.p25)
        elif value <= self.p75:
            return 50.0 + 25.0 * (value - self.p50) / (self.p75 - self.p50)
        elif value <= self.p90:
            return 75.0 + 15.0 * (value - self.p75) / (self.p90 - self.p75)
        else:
            return min(100.0, 90.0 + 10.0 * (value - self.p90) / (self.max_value - self.p90)) if self.max_value > self.p90 else 100.0
    
    def get_performance_tier(self, value: float) -> str:
        """
        Get performance tier for a value
        
        Returns:
            "top" (>75th), "above_avg" (50-75th), "average" (25-50th), "below_avg" (<25th)
        """
        percentile = self.get_percentile_rank(value)
        
        if percentile >= 75:
            return "top"
        elif percentile >= 50:
            return "above_avg"
        elif percentile >= 25:
            return "average"
        else:
            return "below_avg"


@dataclass
class BenchmarkComparison:
    """Comparison of a business's metric to benchmarks"""
    metric: str
    your_value: float
    your_percentile: float
    performance_tier: str
    
    # Peer data
    peer_median: float
    peer_p75: float
    peer_p90: float
    
    # Insights
    vs_median_diff: float  # Percentage difference from median
    vs_top_quartile_diff: float  # Percentage difference from 75th percentile
    
    # Recommendations
    insight: str
    action_items: List[str]


class BenchmarkingEngine:
    """
    Calculates and provides benchmark data
    
    In production, this would query aggregated data from a data warehouse.
    For MVP, we use synthetic/estimated benchmarks.
    """
    
    # Synthetic benchmark data (in production, query from aggregated tenant data)
    SYNTHETIC_BENCHMARKS = {
        "restaurant": {
            "food_cost_pct": {
                "p25": 26.0, "p50": 30.0, "p75": 34.0, "p90": 38.0,
                "mean": 30.5, "std_dev": 4.2, "min_value": 20.0, "max_value": 45.0,
            },
            "labor_cost_pct": {
                "p25": 26.0, "p50": 30.0, "p75": 34.0, "p90": 38.0,
                "mean": 30.2, "std_dev": 4.5, "min_value": 20.0, "max_value": 42.0,
            },
            "prime_cost_pct": {
                "p25": 56.0, "p50": 60.0, "p75": 65.0, "p90": 70.0,
                "mean": 60.7, "std_dev": 5.1, "min_value": 48.0, "max_value": 78.0,
            },
            "avg_check_size": {
                "p25": 18.0, "p50": 25.0, "p75": 35.0, "p90": 50.0,
                "mean": 28.5, "std_dev": 12.3, "min_value": 10.0, "max_value": 75.0,
            },
        },
        "retail": {
            "inventory_turnover": {
                "p25": 4.0, "p50": 6.0, "p75": 8.5, "p90": 12.0,
                "mean": 6.8, "std_dev": 3.2, "min_value": 2.0, "max_value": 18.0,
            },
            "gross_margin": {
                "p25": 35.0, "p50": 42.0, "p75": 50.0, "p90": 58.0,
                "mean": 43.5, "std_dev": 8.7, "min_value": 25.0, "max_value": 65.0,
            },
            "conversion_rate": {
                "p25": 1.8, "p50": 2.5, "p75": 3.5, "p90": 5.0,
                "mean": 2.9, "std_dev": 1.3, "min_value": 0.8, "max_value": 7.0,
            },
        },
        "services": {
            "utilization_rate": {
                "p25": 65.0, "p50": 72.0, "p75": 78.0, "p90": 85.0,
                "mean": 72.8, "std_dev": 7.5, "min_value": 45.0, "max_value": 92.0,
            },
            "realization_rate": {
                "p25": 85.0, "p50": 90.0, "p75": 94.0, "p90": 97.0,
                "mean": 89.5, "std_dev": 5.2, "min_value": 70.0, "max_value": 99.0,
            },
            "project_margin": {
                "p25": 28.0, "p50": 35.0, "p75": 42.0, "p90": 50.0,
                "mean": 36.2, "std_dev": 8.9, "min_value": 15.0, "max_value": 60.0,
            },
        },
        "contractor": {
            "job_completion_rate": {
                "p25": 78.0, "p50": 85.0, "p75": 90.0, "p90": 95.0,
                "mean": 84.5, "std_dev": 6.8, "min_value": 60.0, "max_value": 98.0,
            },
            "material_cost_pct": {
                "p25": 40.0, "p50": 45.0, "p75": 50.0, "p90": 55.0,
                "mean": 45.8, "std_dev": 5.4, "min_value": 30.0, "max_value": 62.0,
            },
            "labor_efficiency": {
                "p25": 0.92, "p50": 1.0, "p75": 1.08, "p90": 1.15,
                "mean": 1.02, "std_dev": 0.12, "min_value": 0.75, "max_value": 1.30,
            },
        },
    }
    
    def __init__(self, business_type: str):
        self.business_type = business_type
    
    async def get_benchmark(
        self,
        metric: str,
        period: str = "30_days",
    ) -> Optional[BenchmarkData]:
        """
        Get benchmark data for a metric
        
        Args:
            metric: Metric name (e.g., "food_cost_pct")
            period: Time period for benchmark
        
        Returns:
            BenchmarkData or None if not available
        """
        from datetime import datetime
        
        benchmarks = self.SYNTHETIC_BENCHMARKS.get(self.business_type, {})
        metric_data = benchmarks.get(metric)
        
        if not metric_data:
            return None
        
        return BenchmarkData(
            metric=metric,
            business_type=self.business_type,
            sample_size=150,  # Synthetic sample size
            p25=metric_data["p25"],
            p50=metric_data["p50"],
            p75=metric_data["p75"],
            p90=metric_data["p90"],
            mean=metric_data["mean"],
            std_dev=metric_data["std_dev"],
            min_value=metric_data["min_value"],
            max_value=metric_data["max_value"],
            period=period,
            last_updated=datetime.utcnow().isoformat(),
        )
    
    async def compare_to_peers(
        self,
        metric: str,
        value: float,
    ) -> Optional[BenchmarkComparison]:
        """
        Compare a business's metric to peer benchmarks
        
        Args:
            metric: Metric name
            value: Business's metric value
        
        Returns:
            BenchmarkComparison with insights
        """
        benchmark = await self.get_benchmark(metric)
        if not benchmark:
            return None
        
        percentile = benchmark.get_percentile_rank(value)
        tier = benchmark.get_performance_tier(value)
        
        # Calculate differences
        vs_median = ((value - benchmark.p50) / benchmark.p50 * 100) if benchmark.p50 != 0 else 0
        vs_p75 = ((value - benchmark.p75) / benchmark.p75 * 100) if benchmark.p75 != 0 else 0
        
        # Generate insights and actions
        insight, actions = self._generate_insights(metric, value, benchmark, tier)
        
        return BenchmarkComparison(
            metric=metric,
            your_value=value,
            your_percentile=percentile,
            performance_tier=tier,
            peer_median=benchmark.p50,
            peer_p75=benchmark.p75,
            peer_p90=benchmark.p90,
            vs_median_diff=vs_median,
            vs_top_quartile_diff=vs_p75,
            insight=insight,
            action_items=actions,
        )
    
    def _generate_insights(
        self,
        metric: str,
        value: float,
        benchmark: BenchmarkData,
        tier: str,
    ) -> Tuple[str, List[str]]:
        """Generate insights and action items based on comparison"""
        
        # Determine if higher or lower is better
        lower_is_better = metric in [
            "food_cost_pct", "labor_cost_pct", "prime_cost_pct",
            "material_cost_pct", "labor_efficiency",
        ]
        
        if tier == "top":
            if lower_is_better:
                insight = f"Excellent! Your {metric.replace('_', ' ')} is in the top 25% (better than 75% of peers)."
                actions = [
                    "Maintain current practices",
                    "Document your processes to ensure consistency",
                    "Consider sharing best practices with team",
                ]
            else:
                insight = f"Outstanding! Your {metric.replace('_', ' ')} is in the top 25% (better than 75% of peers)."
                actions = [
                    "Keep up the great work",
                    "Scale successful strategies",
                    "Set even higher targets",
                ]
        
        elif tier == "above_avg":
            insight = f"Good! Your {metric.replace('_', ' ')} is above average (better than 50% of peers)."
            actions = [
                "Identify opportunities to reach top quartile",
                "Analyze what top performers do differently",
                f"Target: {benchmark.p75:.1f}",
            ]
        
        elif tier == "average":
            insight = f"Your {metric.replace('_', ' ')} is average. There's room for improvement."
            actions = [
                "Review industry best practices",
                "Identify inefficiencies in current processes",
                f"Target: {benchmark.p50:.1f} (peer median)",
            ]
        
        else:  # below_avg
            if lower_is_better:
                insight = f"Attention needed: Your {metric.replace('_', ' ')} is above peer average. This may be impacting profitability."
            else:
                insight = f"Attention needed: Your {metric.replace('_', ' ')} is below peer average."
            
            actions = [
                "Priority: Investigate root causes",
                "Benchmark against industry standards",
                f"Target: {benchmark.p50:.1f} (peer median)",
                "Consider consulting with industry experts",
            ]
        
        return insight, actions
    
    async def get_all_comparisons(
        self,
        metrics: Dict[str, float],
    ) -> List[BenchmarkComparison]:
        """
        Compare multiple metrics to peers
        
        Args:
            metrics: Dict of metric_name -> value
        
        Returns:
            List of BenchmarkComparison objects
        """
        comparisons = []
        
        for metric, value in metrics.items():
            comparison = await self.compare_to_peers(metric, value)
            if comparison:
                comparisons.append(comparison)
        
        return comparisons


def create_benchmarking_engine(business_type: str) -> BenchmarkingEngine:
    """Factory function for creating benchmarking engine"""
    return BenchmarkingEngine(business_type)
