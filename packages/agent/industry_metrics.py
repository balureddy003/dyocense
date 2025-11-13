"""
Industry-Specific Metric Calculators

Calculates industry-relevant KPIs for personalized dashboards:

Restaurant/Food Service:
- Food cost % (COGS / Revenue)
- Labor cost % (Labor / Revenue)
- Prime cost % (Food + Labor / Revenue)
- Average check size
- Daily covers (customers served)
- Table turnover rate

Retail/E-commerce:
- Inventory turnover ratio
- Sell-through rate
- Gross margin return on investment (GMROI)
- Average basket size
- Conversion rate
- Same-store sales growth

Professional Services:
- Utilization rate (billable hours / total hours)
- Realization rate (actual revenue / potential revenue)
- Average hourly rate
- Project profitability
- Client acquisition cost

Contractor/Construction:
- Job completion rate
- Material cost %
- Labor efficiency ratio
- Change order percentage
- Safety incident rate
- Customer satisfaction score
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class MetricCategory(str, Enum):
    """Metric categories for organization"""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    EFFICIENCY = "efficiency"


@dataclass
class Metric:
    """Represents a single calculated metric"""
    id: str
    name: str
    value: Any
    formatted_value: str
    unit: str
    category: MetricCategory
    trend: Optional[str] = None  # 'up', 'down', 'stable'
    trend_value: Optional[float] = None
    benchmark: Optional[float] = None  # Industry benchmark
    status: Optional[str] = None  # 'good', 'warning', 'critical'
    tooltip: Optional[str] = None


class RestaurantMetrics:
    """Calculate restaurant-specific metrics"""
    
    @staticmethod
    def food_cost_percentage(
        cogs_food: float,
        revenue: float,
        period_days: int = 30,
    ) -> Metric:
        """
        Food Cost % = Food COGS / Revenue
        Target: 28-35% for full-service, 25-30% for QSR
        """
        percentage = (cogs_food / revenue * 100) if revenue > 0 else 0
        
        # Determine status
        if percentage < 25:
            status = "good"
        elif percentage < 38:
            status = "good" if percentage < 35 else "warning"
        else:
            status = "critical"
        
        return Metric(
            id="food_cost_pct",
            name="Food Cost %",
            value=percentage,
            formatted_value=f"{percentage:.1f}%",
            unit="percent",
            category=MetricCategory.FINANCIAL,
            benchmark=30.0,
            status=status,
            tooltip="Food & beverage cost as % of revenue. Target: 28-35%",
        )
    
    @staticmethod
    def labor_cost_percentage(
        labor_expenses: float,
        revenue: float,
    ) -> Metric:
        """
        Labor Cost % = Labor Expenses / Revenue
        Target: 25-35% depending on service level
        """
        percentage = (labor_expenses / revenue * 100) if revenue > 0 else 0
        
        if percentage < 25:
            status = "good"
        elif percentage < 38:
            status = "good" if percentage < 35 else "warning"
        else:
            status = "critical"
        
        return Metric(
            id="labor_cost_pct",
            name="Labor Cost %",
            value=percentage,
            formatted_value=f"{percentage:.1f}%",
            unit="percent",
            category=MetricCategory.FINANCIAL,
            benchmark=30.0,
            status=status,
            tooltip="Labor cost as % of revenue. Target: 25-35%",
        )
    
    @staticmethod
    def prime_cost_percentage(
        cogs_food: float,
        labor_expenses: float,
        revenue: float,
    ) -> Metric:
        """
        Prime Cost % = (Food COGS + Labor) / Revenue
        Target: <60% (excellent), 60-65% (acceptable), >65% (needs improvement)
        """
        prime_cost = cogs_food + labor_expenses
        percentage = (prime_cost / revenue * 100) if revenue > 0 else 0
        
        if percentage < 60:
            status = "good"
        elif percentage < 65:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="prime_cost_pct",
            name="Prime Cost %",
            value=percentage,
            formatted_value=f"{percentage:.1f}%",
            unit="percent",
            category=MetricCategory.FINANCIAL,
            benchmark=60.0,
            status=status,
            tooltip="Food + labor as % of revenue. Target: <60%",
        )
    
    @staticmethod
    def average_check_size(
        total_revenue: float,
        total_covers: int,
    ) -> Metric:
        """Average revenue per customer"""
        avg_check = total_revenue / total_covers if total_covers > 0 else 0
        
        return Metric(
            id="avg_check_size",
            name="Average Check",
            value=avg_check,
            formatted_value=f"${avg_check:.2f}",
            unit="currency",
            category=MetricCategory.CUSTOMER,
            tooltip="Average revenue per customer",
        )
    
    @staticmethod
    def daily_covers(
        total_covers: int,
        period_days: int,
    ) -> Metric:
        """Average customers served per day"""
        daily_avg = total_covers / period_days if period_days > 0 else 0
        
        return Metric(
            id="daily_covers",
            name="Daily Covers",
            value=daily_avg,
            formatted_value=f"{daily_avg:.0f}",
            unit="count",
            category=MetricCategory.OPERATIONAL,
            tooltip="Average customers served per day",
        )


class RetailMetrics:
    """Calculate retail-specific metrics"""
    
    @staticmethod
    def inventory_turnover(
        cogs: float,
        avg_inventory: float,
        period_days: int = 365,
    ) -> Metric:
        """
        Inventory Turnover = COGS / Average Inventory
        Higher is better (faster inventory movement)
        """
        turnover = cogs / avg_inventory if avg_inventory > 0 else 0
        
        # Industry benchmarks vary widely
        if turnover > 8:
            status = "good"
        elif turnover > 4:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="inventory_turnover",
            name="Inventory Turnover",
            value=turnover,
            formatted_value=f"{turnover:.1f}x",
            unit="ratio",
            category=MetricCategory.OPERATIONAL,
            benchmark=6.0,
            status=status,
            tooltip="How many times inventory sells in a year. Higher is better.",
        )
    
    @staticmethod
    def sell_through_rate(
        units_sold: int,
        beginning_inventory: int,
        period_days: int = 30,
    ) -> Metric:
        """
        Sell-Through Rate = Units Sold / Beginning Inventory
        Target: 70-80% monthly
        """
        rate = (units_sold / beginning_inventory * 100) if beginning_inventory > 0 else 0
        
        if rate > 70:
            status = "good"
        elif rate > 50:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="sell_through_rate",
            name="Sell-Through Rate",
            value=rate,
            formatted_value=f"{rate:.1f}%",
            unit="percent",
            category=MetricCategory.OPERATIONAL,
            benchmark=75.0,
            status=status,
            tooltip="% of inventory sold in period. Target: 70-80%",
        )
    
    @staticmethod
    def gmroi(
        gross_margin: float,
        avg_inventory_cost: float,
    ) -> Metric:
        """
        Gross Margin Return on Investment = Gross Margin / Avg Inventory Cost
        Target: >$3 return per $1 invested
        """
        gmroi_value = gross_margin / avg_inventory_cost if avg_inventory_cost > 0 else 0
        
        if gmroi_value > 3.0:
            status = "good"
        elif gmroi_value > 2.0:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="gmroi",
            name="GMROI",
            value=gmroi_value,
            formatted_value=f"${gmroi_value:.2f}",
            unit="ratio",
            category=MetricCategory.FINANCIAL,
            benchmark=3.0,
            status=status,
            tooltip="Return on inventory investment. Target: >$3 per $1 invested",
        )
    
    @staticmethod
    def average_basket_size(
        total_revenue: float,
        total_transactions: int,
    ) -> Metric:
        """Average transaction value"""
        avg_basket = total_revenue / total_transactions if total_transactions > 0 else 0
        
        return Metric(
            id="avg_basket_size",
            name="Average Basket",
            value=avg_basket,
            formatted_value=f"${avg_basket:.2f}",
            unit="currency",
            category=MetricCategory.CUSTOMER,
            tooltip="Average transaction value",
        )
    
    @staticmethod
    def conversion_rate(
        transactions: int,
        visitors: int,
    ) -> Metric:
        """
        Conversion Rate = Transactions / Visitors
        Target: 2-4% (e-commerce), 20-40% (brick & mortar)
        """
        rate = (transactions / visitors * 100) if visitors > 0 else 0
        
        return Metric(
            id="conversion_rate",
            name="Conversion Rate",
            value=rate,
            formatted_value=f"{rate:.1f}%",
            unit="percent",
            category=MetricCategory.CUSTOMER,
            tooltip="% of visitors who make a purchase",
        )


class ServicesMetrics:
    """Calculate professional services metrics"""
    
    @staticmethod
    def utilization_rate(
        billable_hours: float,
        total_hours: float,
    ) -> Metric:
        """
        Utilization Rate = Billable Hours / Total Hours
        Target: 70-80% (allows for admin, sales, training)
        """
        rate = (billable_hours / total_hours * 100) if total_hours > 0 else 0
        
        if rate > 70:
            status = "good"
        elif rate > 60:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="utilization_rate",
            name="Utilization Rate",
            value=rate,
            formatted_value=f"{rate:.1f}%",
            unit="percent",
            category=MetricCategory.EFFICIENCY,
            benchmark=75.0,
            status=status,
            tooltip="% of time spent on billable work. Target: 70-80%",
        )
    
    @staticmethod
    def realization_rate(
        actual_revenue: float,
        potential_revenue: float,
    ) -> Metric:
        """
        Realization Rate = Actual Revenue / (Billable Hours × Standard Rate)
        Target: 90%+ (accounts for discounts, write-offs)
        """
        rate = (actual_revenue / potential_revenue * 100) if potential_revenue > 0 else 0
        
        if rate > 90:
            status = "good"
        elif rate > 80:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="realization_rate",
            name="Realization Rate",
            value=rate,
            formatted_value=f"{rate:.1f}%",
            unit="percent",
            category=MetricCategory.FINANCIAL,
            benchmark=90.0,
            status=status,
            tooltip="% of potential revenue actually collected. Target: 90%+",
        )
    
    @staticmethod
    def average_hourly_rate(
        total_revenue: float,
        billable_hours: float,
    ) -> Metric:
        """Effective hourly rate"""
        rate = total_revenue / billable_hours if billable_hours > 0 else 0
        
        return Metric(
            id="avg_hourly_rate",
            name="Avg Hourly Rate",
            value=rate,
            formatted_value=f"${rate:.2f}",
            unit="currency",
            category=MetricCategory.FINANCIAL,
            tooltip="Effective billing rate per hour",
        )
    
    @staticmethod
    def project_profitability(
        project_revenue: float,
        project_costs: float,
    ) -> Metric:
        """
        Project Margin = (Revenue - Costs) / Revenue
        Target: 30-50% depending on service type
        """
        margin = ((project_revenue - project_costs) / project_revenue * 100) if project_revenue > 0 else 0
        
        if margin > 40:
            status = "good"
        elif margin > 25:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="project_margin",
            name="Project Margin",
            value=margin,
            formatted_value=f"{margin:.1f}%",
            unit="percent",
            category=MetricCategory.FINANCIAL,
            benchmark=35.0,
            status=status,
            tooltip="Profit margin on projects. Target: 30-50%",
        )


class ContractorMetrics:
    """Calculate contractor/construction metrics"""
    
    @staticmethod
    def job_completion_rate(
        completed_jobs: int,
        total_jobs: int,
        period_days: int = 30,
    ) -> Metric:
        """% of jobs completed on time"""
        rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        if rate > 85:
            status = "good"
        elif rate > 70:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="job_completion_rate",
            name="On-Time Completion",
            value=rate,
            formatted_value=f"{rate:.1f}%",
            unit="percent",
            category=MetricCategory.OPERATIONAL,
            benchmark=85.0,
            status=status,
            tooltip="% of jobs completed on schedule. Target: 85%+",
        )
    
    @staticmethod
    def material_cost_percentage(
        material_costs: float,
        total_job_cost: float,
    ) -> Metric:
        """
        Material Cost % = Materials / Total Job Cost
        Typical: 40-50% of total job cost
        """
        percentage = (material_costs / total_job_cost * 100) if total_job_cost > 0 else 0
        
        if 35 < percentage < 55:
            status = "good"
        elif 30 < percentage < 60:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="material_cost_pct",
            name="Material Cost %",
            value=percentage,
            formatted_value=f"{percentage:.1f}%",
            unit="percent",
            category=MetricCategory.FINANCIAL,
            benchmark=45.0,
            status=status,
            tooltip="Materials as % of total job cost. Typical: 40-50%",
        )
    
    @staticmethod
    def labor_efficiency_ratio(
        actual_labor_hours: float,
        estimated_labor_hours: float,
    ) -> Metric:
        """
        Labor Efficiency = Actual Hours / Estimated Hours
        Target: <1.0 (under estimate) or 1.0 (on estimate)
        """
        ratio = actual_labor_hours / estimated_labor_hours if estimated_labor_hours > 0 else 0
        
        if ratio < 1.05:
            status = "good"
        elif ratio < 1.20:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="labor_efficiency",
            name="Labor Efficiency",
            value=ratio,
            formatted_value=f"{ratio:.2f}x",
            unit="ratio",
            category=MetricCategory.EFFICIENCY,
            benchmark=1.0,
            status=status,
            tooltip="Actual vs estimated labor hours. Target: <1.05x",
        )
    
    @staticmethod
    def change_order_percentage(
        change_order_revenue: float,
        original_contract_value: float,
    ) -> Metric:
        """
        Change Orders = Change Order Revenue / Original Contract
        Track: Should be <10% ideally
        """
        percentage = (change_order_revenue / original_contract_value * 100) if original_contract_value > 0 else 0
        
        if percentage < 5:
            status = "good"
        elif percentage < 10:
            status = "warning"
        else:
            status = "critical"
        
        return Metric(
            id="change_order_pct",
            name="Change Orders",
            value=percentage,
            formatted_value=f"{percentage:.1f}%",
            unit="percent",
            category=MetricCategory.OPERATIONAL,
            benchmark=5.0,
            status=status,
            tooltip="Change orders as % of contract value. Target: <10%",
        )


# =============================================================================
# METRIC CALCULATOR FACTORY
# =============================================================================

class IndustryMetricCalculator:
    """Factory for calculating industry-specific metrics"""
    
    def __init__(self, business_type: str):
        self.business_type = business_type
        
        # Map business types to calculators
        self.calculators = {
            "restaurant": RestaurantMetrics,
            "retail": RetailMetrics,
            "services": ServicesMetrics,
            "contractor": ContractorMetrics,
        }
    
    async def calculate_metrics(
        self,
        tenant_data: Dict[str, Any],
        period_days: int = 30,
    ) -> List[Metric]:
        """
        Calculate all relevant metrics for this business type
        
        Returns:
            List of Metric objects with calculated values
        """
        calculator_class = self.calculators.get(self.business_type)
        if not calculator_class:
            return []
        
        metrics = []
        
        # Extract common data points
        revenue = tenant_data.get("revenue", 0)
        cogs = tenant_data.get("cogs", 0)
        expenses = tenant_data.get("expenses", {})
        
        # Calculate metrics based on business type
        if self.business_type == "restaurant":
            metrics.extend(self._calculate_restaurant_metrics(
                calculator_class,
                tenant_data,
                revenue,
                cogs,
                expenses,
                period_days,
            ))
        
        elif self.business_type == "retail":
            metrics.extend(self._calculate_retail_metrics(
                calculator_class,
                tenant_data,
                revenue,
                cogs,
                period_days,
            ))
        
        elif self.business_type == "services":
            metrics.extend(self._calculate_services_metrics(
                calculator_class,
                tenant_data,
                revenue,
                period_days,
            ))
        
        elif self.business_type == "contractor":
            metrics.extend(self._calculate_contractor_metrics(
                calculator_class,
                tenant_data,
                period_days,
            ))
        
        return metrics
    
    def _calculate_restaurant_metrics(
        self,
        calculator: RestaurantMetrics,
        data: Dict[str, Any],
        revenue: float,
        cogs: float,
        expenses: Dict[str, Any],
        period_days: int,
    ) -> List[Metric]:
        """Calculate restaurant-specific metrics"""
        metrics = []
        
        # Food cost %
        food_cogs = cogs  # Simplified; in reality would separate food from beverage
        metrics.append(calculator.food_cost_percentage(food_cogs, revenue, period_days))
        
        # Labor cost %
        labor = expenses.get("labor", expenses.get("payroll", 0))
        metrics.append(calculator.labor_cost_percentage(labor, revenue))
        
        # Prime cost %
        metrics.append(calculator.prime_cost_percentage(food_cogs, labor, revenue))
        
        # Average check & daily covers
        covers = data.get("total_covers", data.get("transactions", 0))
        if covers > 0:
            metrics.append(calculator.average_check_size(revenue, covers))
            metrics.append(calculator.daily_covers(covers, period_days))
        
        return metrics
    
    def _calculate_retail_metrics(
        self,
        calculator: RetailMetrics,
        data: Dict[str, Any],
        revenue: float,
        cogs: float,
        period_days: int,
    ) -> List[Metric]:
        """Calculate retail-specific metrics"""
        metrics = []
        
        # Inventory turnover
        avg_inventory = data.get("avg_inventory_value", data.get("inventory_value", 0))
        if avg_inventory > 0:
            # Annualize if period is not full year
            annualized_cogs = cogs * (365 / period_days)
            metrics.append(calculator.inventory_turnover(annualized_cogs, avg_inventory, 365))
        
        # Sell-through rate
        units_sold = data.get("units_sold", 0)
        beginning_inventory = data.get("beginning_inventory_units", 0)
        if beginning_inventory > 0:
            metrics.append(calculator.sell_through_rate(units_sold, beginning_inventory, period_days))
        
        # GMROI
        gross_margin = revenue - cogs
        if avg_inventory > 0:
            metrics.append(calculator.gmroi(gross_margin, avg_inventory))
        
        # Average basket size
        transactions = data.get("transactions", 0)
        if transactions > 0:
            metrics.append(calculator.average_basket_size(revenue, transactions))
        
        # Conversion rate (if visitor data available)
        visitors = data.get("visitors", 0)
        if visitors > 0:
            metrics.append(calculator.conversion_rate(transactions, visitors))
        
        return metrics
    
    def _calculate_services_metrics(
        self,
        calculator: ServicesMetrics,
        data: Dict[str, Any],
        revenue: float,
        period_days: int,
    ) -> List[Metric]:
        """Calculate professional services metrics"""
        metrics = []
        
        # Utilization rate
        billable_hours = data.get("billable_hours", 0)
        total_hours = data.get("total_hours", billable_hours * 1.4)  # Estimate if not provided
        if total_hours > 0:
            metrics.append(calculator.utilization_rate(billable_hours, total_hours))
        
        # Realization rate
        standard_rate = data.get("standard_hourly_rate", 0)
        potential_revenue = billable_hours * standard_rate if standard_rate > 0 else revenue * 1.1
        metrics.append(calculator.realization_rate(revenue, potential_revenue))
        
        # Average hourly rate
        if billable_hours > 0:
            metrics.append(calculator.average_hourly_rate(revenue, billable_hours))
        
        # Project profitability
        project_costs = data.get("project_costs", data.get("cogs", 0))
        metrics.append(calculator.project_profitability(revenue, project_costs))
        
        return metrics
    
    def _calculate_contractor_metrics(
        self,
        calculator: ContractorMetrics,
        data: Dict[str, Any],
        period_days: int,
    ) -> List[Metric]:
        """Calculate contractor-specific metrics"""
        metrics = []
        
        # Job completion rate
        completed = data.get("completed_jobs", 0)
        total_jobs = data.get("total_jobs", completed)
        if total_jobs > 0:
            metrics.append(calculator.job_completion_rate(completed, total_jobs, period_days))
        
        # Material cost %
        material_costs = data.get("material_costs", 0)
        total_job_cost = data.get("total_job_costs", material_costs * 2)
        if total_job_cost > 0:
            metrics.append(calculator.material_cost_percentage(material_costs, total_job_cost))
        
        # Labor efficiency
        actual_hours = data.get("actual_labor_hours", 0)
        estimated_hours = data.get("estimated_labor_hours", actual_hours)
        if estimated_hours > 0:
            metrics.append(calculator.labor_efficiency_ratio(actual_hours, estimated_hours))
        
        # Change orders
        change_orders = data.get("change_order_revenue", 0)
        contract_value = data.get("original_contract_value", 0)
        if contract_value > 0:
            metrics.append(calculator.change_order_percentage(change_orders, contract_value))
        
        return metrics


def create_metric_calculator(business_type: str) -> IndustryMetricCalculator:
    """Factory function for creating metric calculator"""
    return IndustryMetricCalculator(business_type)
