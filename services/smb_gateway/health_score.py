"""
Health Score Service for SMB Gateway

Calculates business health score from connector data (orders, inventory, customers)
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthScoreBreakdown(BaseModel):
    """Detailed breakdown of health score components"""
    revenue: Optional[int] = Field(None, ge=0, le=100, description="Revenue health score")
    operations: Optional[int] = Field(None, ge=0, le=100, description="Operations health score")
    customer: Optional[int] = Field(None, ge=0, le=100, description="Customer health score")
    
    # Indicate which metrics are available
    revenue_available: bool = Field(default=False)
    operations_available: bool = Field(default=False)
    customer_available: bool = Field(default=False)
    
    # Data source information for transparency
    revenue_source: Optional[str] = Field(None, description="Source of revenue data (e.g., 'Shopify Integration', 'sales_data.csv')")
    operations_source: Optional[str] = Field(None, description="Source of operations data")
    customer_source: Optional[str] = Field(None, description="Source of customer data")
    revenue_record_count: Optional[int] = Field(None, description="Number of records used for revenue calculation")
    operations_record_count: Optional[int] = Field(None, description="Number of records used for operations calculation")
    customer_record_count: Optional[int] = Field(None, description="Number of records used for customer calculation")
    is_sample_data: bool = Field(default=False, description="Whether using sample/test data vs real integrations")


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
        
    def calculate_revenue_health(self) -> Optional[int]:
        """
        Calculate revenue health (0-100) based on:
        - Revenue growth rate
        - Sales velocity
        - Order value trends
        
        Returns None if no orders data available
        """
        orders = self.connector_data.get('orders', [])
        
        if not orders:
            return None  # No data available
        
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
    
    def calculate_operations_health(self) -> Optional[int]:
        """
        Calculate operations health (0-100) based on:
        - Inventory turnover
        - Stockout rate
        - Fulfillment efficiency
        
        Returns None if no inventory data available
        """
        inventory = self.connector_data.get('inventory', [])
        orders = self.connector_data.get('orders', [])
        
        if not inventory:
            return None  # No data available
        
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
    
    def calculate_customer_health(self) -> Optional[int]:
        """
        Calculate customer health (0-100) based on:
        - Repeat customer rate
        - Customer retention
        - Average order frequency
        
        Returns None if no customer/order data available
        """
        customers = self.connector_data.get('customers', [])
        orders = self.connector_data.get('orders', [])
        
        if not customers or not orders:
            return None  # No data available
        
        # Calculate repeat customer rate
        customer_order_counts = {}
        for order in orders:
            if self._is_recent(order.get('created_at'), 90):  # Last 90 days
                customer_id = order.get('customer_id')
                if customer_id:
                    customer_order_counts[customer_id] = customer_order_counts.get(customer_id, 0) + 1
        
        if not customer_order_counts:
            return None
        
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
        
        # Get data sources and counts
        orders = self.connector_data.get('orders', [])
        inventory = self.connector_data.get('inventory', [])
        customers = self.connector_data.get('customers', [])
        metadata = self.connector_data.get('metadata', {})
        is_sample = metadata.get('is_sample_data', False)
        
        # Determine data sources (from metadata or infer from data type)
        revenue_source = None
        operations_source = None
        customer_source = None
        
        if revenue_score is not None:
            revenue_source = metadata.get('orders_source', f'{len(orders)} orders' if not is_sample else 'Sample data')
        if operations_score is not None:
            operations_source = metadata.get('inventory_source', f'{len(inventory)} items' if not is_sample else 'Sample data')
        if customer_score is not None:
            customer_source = metadata.get('customers_source', f'{len(customers)} customers' if not is_sample else 'Sample data')
        
        # Collect available scores and their weights
        scores_and_weights = []
        if revenue_score is not None:
            scores_and_weights.append((revenue_score, 0.4))
        if operations_score is not None:
            scores_and_weights.append((operations_score, 0.3))
        if customer_score is not None:
            scores_and_weights.append((customer_score, 0.3))
        
        # Calculate weighted average only from available scores
        if scores_and_weights:
            total_weight = sum(weight for _, weight in scores_and_weights)
            overall_score = int(
                sum(score * weight for score, weight in scores_and_weights) / total_weight
            )
        else:
            # No data available at all
            overall_score = 0
        
        # Calculate trend (compare to previous period)
        # TODO: Store historical scores for accurate trend calculation
        # For now, estimate based on revenue growth
        trend = self._calculate_trend(orders)
        
        return HealthScoreResponse(
            score=overall_score,
            trend=trend,
            breakdown=HealthScoreBreakdown(
                revenue=revenue_score,
                operations=operations_score,
                customer=customer_score,
                revenue_available=revenue_score is not None,
                operations_available=operations_score is not None,
                customer_available=customer_score is not None,
                revenue_source=revenue_source,
                operations_source=operations_source,
                customer_source=customer_source,
                revenue_record_count=len(orders) if revenue_score is not None else None,
                operations_record_count=len(inventory) if operations_score is not None else None,
                customer_record_count=len(customers) if customer_score is not None else None,
                is_sample_data=is_sample,
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
