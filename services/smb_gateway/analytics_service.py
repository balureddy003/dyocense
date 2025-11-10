"""
Analytics Service for SMB Gateway

Provides historical tracking and analytics for business metrics
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class HealthScoreHistoryPoint(BaseModel):
    """Historical health score data point"""
    date: str  # ISO date YYYY-MM-DD
    score: float
    revenue: float
    operations: float
    customer: float


class GoalProgressPoint(BaseModel):
    """Goal progress snapshot"""
    goal_id: str
    goal_title: str
    category: str
    progress: float  # Percentage 0-100
    current: float
    target: float
    unit: str


class TaskCompletionStats(BaseModel):
    """Task completion statistics"""
    date: str
    completed: int
    total: int
    completion_rate: float


class MetricDataPoint(BaseModel):
    """Generic metric data point for time series"""
    date: str
    value: float
    label: Optional[str] = None


class CategoryBreakdown(BaseModel):
    """Category breakdown for pie charts"""
    category: str
    value: float
    percentage: float


class AnalyticsService:
    """Service for analytics and historical tracking"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.health_score_history: Dict[str, List[HealthScoreHistoryPoint]] = {}  # {tenant_id: [points]}
        self.task_completions: Dict[str, List[TaskCompletionStats]] = {}  # {tenant_id: [stats]}
    
    def record_health_score(
        self,
        tenant_id: str,
        score: float,
        breakdown: Dict[str, float],
        date: Optional[str] = None,
    ) -> HealthScoreHistoryPoint:
        """
        Record a health score data point
        
        Args:
            tenant_id: Tenant identifier
            score: Overall health score
            breakdown: Category breakdown (revenue, operations, customer)
            date: ISO date string (defaults to today)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        point = HealthScoreHistoryPoint(
            date=date,
            score=score,
            revenue=breakdown.get('revenue', 0),
            operations=breakdown.get('operations', 0),
            customer=breakdown.get('customer', 0),
        )
        
        if tenant_id not in self.health_score_history:
            self.health_score_history[tenant_id] = []
        
        # Avoid duplicates for the same date
        existing = [p for p in self.health_score_history[tenant_id] if p.date == date]
        if existing:
            # Update existing point
            self.health_score_history[tenant_id] = [
                p for p in self.health_score_history[tenant_id] if p.date != date
            ]
        
        self.health_score_history[tenant_id].append(point)
        self.health_score_history[tenant_id].sort(key=lambda p: p.date)
        
        return point
    
    def get_health_score_history(
        self,
        tenant_id: str,
        days: int = 30,
        interval: str = 'daily',
    ) -> List[HealthScoreHistoryPoint]:
        """
        Get health score history
        
        Args:
            tenant_id: Tenant identifier
            days: Number of days to look back
            interval: 'daily' or 'weekly'
        """
        if tenant_id not in self.health_score_history:
            # Generate sample historical data for demo
            return self._generate_sample_health_history(days, interval)
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        history = [
            p for p in self.health_score_history[tenant_id]
            if p.date >= cutoff_date
        ]
        
        if interval == 'weekly':
            # Aggregate by week
            history = self._aggregate_by_week(history)
        
        return history
    
    def get_goal_progress_snapshot(
        self,
        goals: List[Dict[str, Any]]
    ) -> List[GoalProgressPoint]:
        """Get current progress snapshot for all goals"""
        progress_points = []
        
        for goal in goals:
            current = goal.get('current', 0)
            target = goal.get('target', 1)
            progress = (current / target * 100) if target > 0 else 0
            
            progress_points.append(GoalProgressPoint(
                goal_id=goal.get('id', ''),
                goal_title=goal.get('title', 'Untitled Goal'),
                category=goal.get('category', 'custom'),
                progress=min(progress, 100),  # Cap at 100%
                current=current,
                target=target,
                unit=goal.get('unit', 'units'),
            ))
        
        return progress_points
    
    def get_task_completion_stats(
        self,
        tenant_id: str,
        days: int = 30,
    ) -> List[TaskCompletionStats]:
        """Get task completion statistics over time"""
        if tenant_id not in self.task_completions:
            # Generate sample data
            return self._generate_sample_task_stats(days)
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return [
            s for s in self.task_completions[tenant_id]
            if s.date >= cutoff_date
        ]
    
    def record_task_completion(
        self,
        tenant_id: str,
        date: str,
        completed: int,
        total: int,
    ):
        """Record task completion stats for a date"""
        if tenant_id not in self.task_completions:
            self.task_completions[tenant_id] = []
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        stats = TaskCompletionStats(
            date=date,
            completed=completed,
            total=total,
            completion_rate=completion_rate,
        )
        
        # Remove existing entry for this date
        self.task_completions[tenant_id] = [
            s for s in self.task_completions[tenant_id] if s.date != date
        ]
        
        self.task_completions[tenant_id].append(stats)
        self.task_completions[tenant_id].sort(key=lambda s: s.date)
    
    def get_category_breakdown(
        self,
        items: List[Dict[str, Any]],
        category_field: str = 'category',
        value_field: Optional[str] = None,
    ) -> List[CategoryBreakdown]:
        """
        Get category breakdown for pie charts
        
        Args:
            items: List of items to analyze
            category_field: Field name for category
            value_field: Field name for value (if None, counts items)
        """
        category_totals = defaultdict(float)
        total = 0
        
        for item in items:
            category = item.get(category_field, 'other')
            
            if value_field:
                value = float(item.get(value_field, 0))
            else:
                value = 1  # Count items
            
            category_totals[category] += value
            total += value
        
        breakdowns = []
        for category, value in category_totals.items():
            percentage = (value / total * 100) if total > 0 else 0
            breakdowns.append(CategoryBreakdown(
                category=category,
                value=value,
                percentage=percentage,
            ))
        
        # Sort by value descending
        breakdowns.sort(key=lambda b: b.value, reverse=True)
        
        return breakdowns
    
    def _generate_sample_health_history(
        self,
        days: int,
        interval: str,
    ) -> List[HealthScoreHistoryPoint]:
        """Generate sample health score history for demo"""
        history = []
        
        # Determine number of points
        num_points = days if interval == 'daily' else min(days // 7, 12)
        
        # Generate trending data (slight upward trend with variance)
        base_score = 65
        
        for i in range(num_points):
            if interval == 'daily':
                date = (datetime.now() - timedelta(days=num_points - i - 1)).strftime('%Y-%m-%d')
            else:
                weeks_ago = num_points - i - 1
                date = (datetime.now() - timedelta(weeks=weeks_ago)).strftime('%Y-%m-%d')
            
            # Simulate growth with some variance
            trend = i * 1.5  # Gradual improvement
            variance = (i % 3) - 1  # Small fluctuations
            
            score = base_score + trend + variance
            revenue = score + (i % 5)
            operations = score - 3 + (i % 4)
            customer = score + 1 + (i % 3)
            
            history.append(HealthScoreHistoryPoint(
                date=date,
                score=min(score, 100),
                revenue=min(revenue, 100),
                operations=min(operations, 100),
                customer=min(customer, 100),
            ))
        
        return history
    
    def _generate_sample_task_stats(self, days: int) -> List[TaskCompletionStats]:
        """Generate sample task completion stats"""
        stats = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i - 1)).strftime('%Y-%m-%d')
            
            # Simulate realistic task completion patterns
            # Weekends: less tasks
            day_of_week = (datetime.now() - timedelta(days=days - i - 1)).weekday()
            if day_of_week >= 5:  # Weekend
                total = 2
                completed = total
            else:  # Weekday
                total = 5 + (i % 3)
                completed = int(total * 0.75)  # 75% completion rate
            
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            stats.append(TaskCompletionStats(
                date=date,
                completed=completed,
                total=total,
                completion_rate=completion_rate,
            ))
        
        return stats
    
    def _aggregate_by_week(
        self,
        history: List[HealthScoreHistoryPoint]
    ) -> List[HealthScoreHistoryPoint]:
        """Aggregate daily data into weekly averages"""
        weekly_data = defaultdict(list)
        
        for point in history:
            # Get week start (Monday)
            date_obj = datetime.strptime(point.date, '%Y-%m-%d')
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            weekly_data[week_key].append(point)
        
        # Calculate weekly averages
        aggregated = []
        for week_start, points in sorted(weekly_data.items()):
            avg_score = sum(p.score for p in points) / len(points)
            avg_revenue = sum(p.revenue for p in points) / len(points)
            avg_operations = sum(p.operations for p in points) / len(points)
            avg_customer = sum(p.customer for p in points) / len(points)
            
            aggregated.append(HealthScoreHistoryPoint(
                date=week_start,
                score=avg_score,
                revenue=avg_revenue,
                operations=avg_operations,
                customer=avg_customer,
            ))
        
        return aggregated


# Global instance
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
