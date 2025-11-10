"""
Health Score Service for SMB Gateway

Calculates business health score from connector data (orders, inventory, customers)
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthScoreBreakdown(BaseModel):
    """Detailed breakdown of health score components"""
    revenue: int = Field(ge=0, le=100, description="Revenue health score")
    operations: int = Field(ge=0, le=100, description="Operations health score")
    customer: int = Field(ge=0, le=100, description="Customer health score")


class HealthScoreResponse(BaseModel):
    """Health score response"""
    score: int = Field(ge=0, le=100, description="Overall health score")
    trend: float = Field(description="Trend compared to previous period")
    breakdown: HealthScoreBreakdown
    last_updated: datetime
    period_days: int = Field(default=30, description="Period for calculation")


class HealthScoreCalculator:
    """Calculate business health score from various metrics"""
    
    def __init__(self, connector_data: Dict[str, Any]):
        self.connector_data = connector_data
        
    def calculate_revenue_health(self) -> int:
        """
        Calculate revenue health (0-100) based on:
        - Revenue growth rate
        - Sales velocity
        - Order value trends
        """
        orders = self.connector_data.get('orders', [])
        
        if not orders:
            return 50  # Neutral score if no data
        
        # Calculate current period vs previous period
        now = datetime.now()
        current_period_start = now - timedelta(days=30)
        previous_period_start = now - timedelta(days=60)
        
        current_revenue = sum(
            order.get('total_amount', 0) 
            for order in orders 
            if self._parse_date(order.get('created_at')) >= current_period_start
        )
        
        previous_revenue = sum(
            order.get('total_amount', 0) 
            for order in orders 
            if previous_period_start <= self._parse_date(order.get('created_at')) < current_period_start
        )
        
        # Calculate growth rate
        if previous_revenue > 0:
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
        else:
            growth_rate = 0 if current_revenue == 0 else 100
        
        # Score based on growth rate
        # -20% or worse = 0, 0% growth = 50, 20%+ growth = 100
        score = max(0, min(100, 50 + (growth_rate * 2.5)))
        
        return int(score)
    
    def calculate_operations_health(self) -> int:
        """
        Calculate operations health (0-100) based on:
        - Inventory turnover
        - Stockout rate
        - Fulfillment efficiency
        """
        inventory = self.connector_data.get('inventory', [])
        orders = self.connector_data.get('orders', [])
        
        if not inventory:
            return 50  # Neutral score if no data
        
        # Calculate inventory turnover (simplified)
        total_inventory_value = sum(item.get('value', 0) for item in inventory)
        total_sales_last_30_days = sum(
            order.get('total_amount', 0) 
            for order in orders 
            if self._is_recent(order.get('created_at'), 30)
        )
        
        # Inventory turnover rate = sales / avg inventory
        # Higher turnover is better (less capital tied up)
        if total_inventory_value > 0:
            turnover_rate = (total_sales_last_30_days * 12) / total_inventory_value  # Annualized
        else:
            turnover_rate = 0
        
        # Score based on turnover rate
        # 0 turnover = 0, 4 turnover = 50, 8+ turnover = 100
        score = min(100, (turnover_rate / 8) * 100)
        
        # Check for stockouts (items with 0 quantity)
        stockout_count = sum(1 for item in inventory if item.get('quantity', 0) == 0)
        stockout_penalty = min(30, stockout_count * 5)  # Max -30 points
        
        final_score = max(0, score - stockout_penalty)
        
        return int(final_score)
    
    def calculate_customer_health(self) -> int:
        """
        Calculate customer health (0-100) based on:
        - Repeat customer rate
        - Customer retention
        - Average order frequency
        """
        customers = self.connector_data.get('customers', [])
        orders = self.connector_data.get('orders', [])
        
        if not customers or not orders:
            return 50  # Neutral score if no data
        
        # Calculate repeat customer rate
        customer_order_counts = {}
        for order in orders:
            if self._is_recent(order.get('created_at'), 90):  # Last 90 days
                customer_id = order.get('customer_id')
                if customer_id:
                    customer_order_counts[customer_id] = customer_order_counts.get(customer_id, 0) + 1
        
        if not customer_order_counts:
            return 50
        
        repeat_customers = sum(1 for count in customer_order_counts.values() if count > 1)
        total_customers = len(customer_order_counts)
        
        repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
        
        # Score based on repeat rate
        # 0% repeat = 30, 25% repeat = 50, 50%+ repeat = 100
        score = 30 + min(70, repeat_rate * 1.4)
        
        return int(score)
    
    def calculate_overall_health(self) -> HealthScoreResponse:
        """Calculate overall health score with breakdown"""
        revenue_score = self.calculate_revenue_health()
        operations_score = self.calculate_operations_health()
        customer_score = self.calculate_customer_health()
        
        # Weighted average: Revenue 40%, Operations 30%, Customer 30%
        overall_score = int(
            (revenue_score * 0.4) + 
            (operations_score * 0.3) + 
            (customer_score * 0.3)
        )
        
        # Calculate trend (compare to previous period)
        # TODO: Store historical scores for accurate trend calculation
        # For now, estimate based on revenue growth
        orders = self.connector_data.get('orders', [])
        trend = self._calculate_trend(orders)
        
        return HealthScoreResponse(
            score=overall_score,
            trend=trend,
            breakdown=HealthScoreBreakdown(
                revenue=revenue_score,
                operations=operations_score,
                customer=customer_score
            ),
            last_updated=datetime.now(),
            period_days=30
        )
    
    def _calculate_trend(self, orders: list) -> float:
        """Calculate trend percentage from order data"""
        now = datetime.now()
        current_period = now - timedelta(days=30)
        previous_period = now - timedelta(days=60)
        
        current_orders = sum(
            1 for order in orders 
            if self._parse_date(order.get('created_at')) >= current_period
        )
        
        previous_orders = sum(
            1 for order in orders 
            if previous_period <= self._parse_date(order.get('created_at')) < current_period
        )
        
        if previous_orders > 0:
            trend = ((current_orders - previous_orders) / previous_orders) * 100
        else:
            trend = 0
        
        return round(trend, 1)
    
    def _is_recent(self, date_str: Optional[str], days: int) -> bool:
        """Check if date is within last N days"""
        if not date_str:
            return False
        
        try:
            date = self._parse_date(date_str)
            return date >= datetime.now() - timedelta(days=days)
        except:
            return False
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse date string to datetime"""
        if not date_str:
            return datetime.min
        
        try:
            # Handle ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Handle date-only format
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return datetime.min
