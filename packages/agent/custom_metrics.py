"""
Custom Metrics & KPI Builder

Allows users to define custom metrics with formulas, thresholds, and alerts.
Includes a library of pre-built KPI templates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import secrets
import re
import operator


class MetricType(str, Enum):
    """Types of custom metrics."""
    CALCULATED = "calculated"  # Formula-based
    AGGREGATED = "aggregated"  # Sum, avg, min, max
    RATIO = "ratio"  # Division of two metrics
    PERCENTAGE = "percentage"  # Ratio * 100
    CUSTOM = "custom"  # User-defined formula


class AggregationType(str, Enum):
    """Aggregation functions."""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"


class ThresholdComparison(str, Enum):
    """Threshold comparison operators."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricThreshold:
    """Threshold configuration for alerts."""
    comparison: ThresholdComparison
    value: float
    severity: AlertSeverity
    message: str


@dataclass
class CustomMetric:
    """User-defined custom metric."""
    id: str
    tenant_id: str
    name: str
    description: str
    metric_type: MetricType
    formula: str  # Mathematical expression or template
    unit: str  # e.g., "$", "%", "items"
    data_sources: List[str]  # List of source metrics
    thresholds: List[MetricThreshold] = field(default_factory=list)
    enabled: bool = True
    created_by: str = "user"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricCalculationResult:
    """Result of metric calculation."""
    metric_id: str
    metric_name: str
    value: float
    unit: str
    calculated_at: datetime
    triggered_thresholds: List[Dict[str, Any]] = field(default_factory=list)
    data_points: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MetricTemplate:
    """Pre-built KPI template."""
    id: str
    name: str
    description: str
    category: str  # financial, operational, marketing, sales
    formula: str
    unit: str
    data_sources: List[str]
    recommended_thresholds: List[Dict[str, Any]]
    industry: Optional[str] = None  # restaurant, retail, etc.


class CustomMetricEngine:
    """Engine for creating and calculating custom metrics."""
    
    def __init__(self):
        """Initialize the custom metric engine."""
        self.metrics_cache: Dict[str, CustomMetric] = {}
        self.templates: Dict[str, MetricTemplate] = self._load_templates()
        
        # Safe operators for formula evaluation
        self.safe_operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '%': operator.mod,
            '**': operator.pow,
        }
    
    def _load_templates(self) -> Dict[str, MetricTemplate]:
        """Load pre-built KPI templates."""
        templates = {
            "gross_margin": MetricTemplate(
                id="gross_margin",
                name="Gross Margin",
                description="Percentage of revenue remaining after subtracting cost of goods sold",
                category="financial",
                formula="((revenue - cogs) / revenue) * 100",
                unit="%",
                data_sources=["revenue", "cogs"],
                recommended_thresholds=[
                    {"comparison": ">=", "value": 60, "severity": "info", "message": "Healthy gross margin"},
                    {"comparison": "<", "value": 40, "severity": "warning", "message": "Low gross margin - review pricing or costs"},
                    {"comparison": "<", "value": 30, "severity": "critical", "message": "Critical - margin too low for sustainability"}
                ],
                industry="restaurant"
            ),
            "inventory_turnover": MetricTemplate(
                id="inventory_turnover",
                name="Inventory Turnover Ratio",
                description="How many times inventory is sold and replaced over a period",
                category="operational",
                formula="cogs / average_inventory",
                unit="times",
                data_sources=["cogs", "average_inventory"],
                recommended_thresholds=[
                    {"comparison": ">=", "value": 4, "severity": "info", "message": "Good inventory turnover"},
                    {"comparison": "<", "value": 2, "severity": "warning", "message": "Slow inventory turnover - may indicate overstocking"}
                ],
                industry="restaurant"
            ),
            "labor_cost_percentage": MetricTemplate(
                id="labor_cost_percentage",
                name="Labor Cost Percentage",
                description="Labor costs as a percentage of revenue",
                category="operational",
                formula="(labor_cost / revenue) * 100",
                unit="%",
                data_sources=["labor_cost", "revenue"],
                recommended_thresholds=[
                    {"comparison": "<=", "value": 30, "severity": "info", "message": "Labor costs within healthy range"},
                    {"comparison": ">", "value": 35, "severity": "warning", "message": "Labor costs above optimal range"},
                    {"comparison": ">", "value": 40, "severity": "critical", "message": "Labor costs critically high"}
                ],
                industry="restaurant"
            ),
            "prime_cost": MetricTemplate(
                id="prime_cost",
                name="Prime Cost Percentage",
                description="Combined COGS and labor as percentage of revenue",
                category="operational",
                formula="((cogs + labor_cost) / revenue) * 100",
                unit="%",
                data_sources=["cogs", "labor_cost", "revenue"],
                recommended_thresholds=[
                    {"comparison": "<=", "value": 60, "severity": "info", "message": "Prime cost within excellent range"},
                    {"comparison": ">", "value": 65, "severity": "warning", "message": "Prime cost elevated - monitor closely"},
                    {"comparison": ">", "value": 70, "severity": "critical", "message": "Prime cost dangerously high"}
                ],
                industry="restaurant"
            ),
            "customer_acquisition_cost": MetricTemplate(
                id="customer_acquisition_cost",
                name="Customer Acquisition Cost (CAC)",
                description="Average cost to acquire a new customer",
                category="marketing",
                formula="marketing_spend / new_customers",
                unit="$",
                data_sources=["marketing_spend", "new_customers"],
                recommended_thresholds=[
                    {"comparison": "<=", "value": 100, "severity": "info", "message": "CAC is efficient"},
                    {"comparison": ">", "value": 200, "severity": "warning", "message": "CAC is high - review marketing efficiency"}
                ],
                industry=None
            ),
            "customer_lifetime_value": MetricTemplate(
                id="customer_lifetime_value",
                name="Customer Lifetime Value (CLV)",
                description="Average revenue from a customer over their lifetime",
                category="financial",
                formula="average_order_value * purchase_frequency * customer_lifespan",
                unit="$",
                data_sources=["average_order_value", "purchase_frequency", "customer_lifespan"],
                recommended_thresholds=[
                    {"comparison": ">=", "value": 1000, "severity": "info", "message": "Strong customer lifetime value"}
                ],
                industry=None
            ),
            "revenue_per_employee": MetricTemplate(
                id="revenue_per_employee",
                name="Revenue per Employee",
                description="Average revenue generated per employee",
                category="operational",
                formula="revenue / employee_count",
                unit="$",
                data_sources=["revenue", "employee_count"],
                recommended_thresholds=[
                    {"comparison": ">=", "value": 100000, "severity": "info", "message": "High productivity per employee"}
                ],
                industry=None
            ),
            "break_even_point": MetricTemplate(
                id="break_even_point",
                name="Break-Even Point",
                description="Revenue needed to cover all fixed and variable costs",
                category="financial",
                formula="fixed_costs / (1 - (variable_costs / revenue))",
                unit="$",
                data_sources=["fixed_costs", "variable_costs", "revenue"],
                recommended_thresholds=[],
                industry=None
            ),
            "cash_conversion_cycle": MetricTemplate(
                id="cash_conversion_cycle",
                name="Cash Conversion Cycle",
                description="Days between paying suppliers and receiving customer payments",
                category="financial",
                formula="days_inventory_outstanding + days_sales_outstanding - days_payable_outstanding",
                unit="days",
                data_sources=["days_inventory_outstanding", "days_sales_outstanding", "days_payable_outstanding"],
                recommended_thresholds=[
                    {"comparison": "<=", "value": 30, "severity": "info", "message": "Efficient cash conversion"},
                    {"comparison": ">", "value": 60, "severity": "warning", "message": "Cash conversion cycle is long"}
                ],
                industry=None
            ),
            "table_turnover_rate": MetricTemplate(
                id="table_turnover_rate",
                name="Table Turnover Rate",
                description="Average number of times a table is occupied per service period",
                category="operational",
                formula="total_covers / (table_count * service_periods)",
                unit="times",
                data_sources=["total_covers", "table_count", "service_periods"],
                recommended_thresholds=[
                    {"comparison": ">=", "value": 2, "severity": "info", "message": "Good table utilization"},
                    {"comparison": "<", "value": 1.5, "severity": "warning", "message": "Low table turnover"}
                ],
                industry="restaurant"
            ),
        }
        
        return templates
    
    async def create_metric(
        self,
        tenant_id: str,
        name: str,
        description: str,
        metric_type: MetricType,
        formula: str,
        unit: str,
        data_sources: List[str],
        thresholds: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "user"
    ) -> CustomMetric:
        """
        Create a new custom metric.
        
        Args:
            tenant_id: Tenant identifier
            name: Metric name
            description: Metric description
            metric_type: Type of metric
            formula: Mathematical formula or expression
            unit: Unit of measurement
            data_sources: List of required data sources
            thresholds: Optional threshold configurations
            created_by: User who created the metric
        
        Returns:
            Created CustomMetric object
        """
        # Validate formula
        validation_result = self._validate_formula(formula, data_sources)
        if not validation_result["valid"]:
            raise ValueError(f"Invalid formula: {validation_result['error']}")
        
        # Generate metric ID
        metric_id = f"metric_{secrets.token_hex(12)}"
        
        # Parse thresholds
        threshold_objects = []
        if thresholds:
            for t in thresholds:
                threshold_objects.append(MetricThreshold(
                    comparison=ThresholdComparison(t["comparison"]),
                    value=float(t["value"]),
                    severity=AlertSeverity(t["severity"]),
                    message=t["message"]
                ))
        
        # Create metric
        metric = CustomMetric(
            id=metric_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            metric_type=metric_type,
            formula=formula,
            unit=unit,
            data_sources=data_sources,
            thresholds=threshold_objects,
            created_by=created_by
        )
        
        # Store in cache
        self.metrics_cache[metric_id] = metric
        
        return metric
    
    def _validate_formula(
        self,
        formula: str,
        data_sources: List[str]
    ) -> Dict[str, Any]:
        """
        Validate a formula for safety and correctness.
        
        Args:
            formula: Formula to validate
            data_sources: Available data sources
        
        Returns:
            Validation result with 'valid' boolean and optional 'error' message
        """
        # Check for dangerous operations
        dangerous_keywords = ['import', 'exec', 'eval', '__', 'open', 'file']
        for keyword in dangerous_keywords:
            if keyword in formula.lower():
                return {"valid": False, "error": f"Forbidden keyword: {keyword}"}
        
        # Extract variables from formula
        # Match variable names (alphanumeric + underscore)
        variables = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula))
        
        # Remove known functions and operators
        known_functions = {'sum', 'avg', 'average', 'min', 'max', 'count', 'abs', 'round'}
        variables = variables - known_functions
        
        # Check if all variables are in data sources
        for var in variables:
            if var not in data_sources:
                return {
                    "valid": False,
                    "error": f"Variable '{var}' not in data sources. Available: {', '.join(data_sources)}"
                }
        
        return {"valid": True}
    
    async def calculate_metric(
        self,
        tenant_id: str,
        metric_id: str,
        data: Optional[Dict[str, float]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> MetricCalculationResult:
        """
        Calculate a custom metric value.
        
        Args:
            tenant_id: Tenant identifier
            metric_id: Metric to calculate
            data: Optional data values (if None, fetches from sources)
            start_date: Start date for data fetching
            end_date: End date for data fetching
        
        Returns:
            MetricCalculationResult with value and triggered alerts
        """
        metric = self.metrics_cache.get(metric_id)
        if not metric or metric.tenant_id != tenant_id:
            raise ValueError("Metric not found")
        
        # Get data values
        if data is None:
            data = await self._fetch_metric_data(
                tenant_id=tenant_id,
                data_sources=metric.data_sources,
                start_date=start_date,
                end_date=end_date
            )
        
        # Calculate value using formula
        try:
            value = self._evaluate_formula(metric.formula, data)
        except Exception as e:
            raise ValueError(f"Error calculating metric: {str(e)}")
        
        # Check thresholds
        triggered_thresholds = []
        for threshold in metric.thresholds:
            if self._check_threshold(value, threshold):
                triggered_thresholds.append({
                    "severity": threshold.severity,
                    "message": threshold.message,
                    "threshold_value": threshold.value,
                    "actual_value": value,
                    "comparison": threshold.comparison
                })
        
        # Create result
        result = MetricCalculationResult(
            metric_id=metric.id,
            metric_name=metric.name,
            value=round(value, 2),
            unit=metric.unit,
            calculated_at=datetime.utcnow(),
            triggered_thresholds=triggered_thresholds,
            data_points=[{"data_source": k, "value": v} for k, v in data.items()]
        )
        
        return result
    
    async def _fetch_metric_data(
        self,
        tenant_id: str,
        data_sources: List[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Fetch data from sources (MVP: sample data)."""
        # MVP: Return sample data
        data = {}
        
        sample_values = {
            "revenue": 50000,
            "cogs": 15000,
            "labor_cost": 12000,
            "marketing_spend": 5000,
            "new_customers": 50,
            "average_order_value": 45,
            "purchase_frequency": 2.5,
            "customer_lifespan": 24,
            "employee_count": 15,
            "average_inventory": 8000,
            "fixed_costs": 20000,
            "variable_costs": 25000,
            "days_inventory_outstanding": 15,
            "days_sales_outstanding": 30,
            "days_payable_outstanding": 20,
            "total_covers": 800,
            "table_count": 20,
            "service_periods": 2,
        }
        
        for source in data_sources:
            data[source] = sample_values.get(source, 100.0)
        
        return data
    
    def _evaluate_formula(
        self,
        formula: str,
        data: Dict[str, float]
    ) -> float:
        """
        Safely evaluate a formula with given data.
        
        Args:
            formula: Mathematical expression
            data: Variable values
        
        Returns:
            Calculated result
        """
        # Create safe namespace with data and basic functions
        namespace = {
            **data,
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'avg': lambda *args: sum(args) / len(args) if args else 0,
            'average': lambda *args: sum(args) / len(args) if args else 0,
        }
        
        # Use eval with restricted namespace
        # In production, use simpleeval or safer alternative
        try:
            result = eval(formula, {"__builtins__": {}}, namespace)
            return float(result)
        except ZeroDivisionError:
            return 0.0
        except Exception as e:
            raise ValueError(f"Formula evaluation error: {str(e)}")
    
    def _check_threshold(
        self,
        value: float,
        threshold: MetricThreshold
    ) -> bool:
        """Check if value triggers a threshold."""
        comparisons = {
            ThresholdComparison.GREATER_THAN: lambda v, t: v > t,
            ThresholdComparison.LESS_THAN: lambda v, t: v < t,
            ThresholdComparison.GREATER_EQUAL: lambda v, t: v >= t,
            ThresholdComparison.LESS_EQUAL: lambda v, t: v <= t,
            ThresholdComparison.EQUAL: lambda v, t: abs(v - t) < 0.01,
            ThresholdComparison.NOT_EQUAL: lambda v, t: abs(v - t) >= 0.01,
        }
        
        compare_fn = comparisons.get(threshold.comparison)
        if compare_fn:
            return compare_fn(value, threshold.value)
        
        return False
    
    async def list_metrics(
        self,
        tenant_id: str,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List all custom metrics for a tenant."""
        metrics = [
            {
                "id": metric.id,
                "name": metric.name,
                "description": metric.description,
                "metric_type": metric.metric_type,
                "formula": metric.formula,
                "unit": metric.unit,
                "data_sources": metric.data_sources,
                "thresholds_count": len(metric.thresholds),
                "enabled": metric.enabled,
                "created_at": metric.created_at.isoformat(),
                "created_by": metric.created_by
            }
            for metric in self.metrics_cache.values()
            if metric.tenant_id == tenant_id and (not enabled_only or metric.enabled)
        ]
        
        return metrics
    
    async def get_metric(
        self,
        tenant_id: str,
        metric_id: str
    ) -> Optional[CustomMetric]:
        """Get a specific custom metric."""
        metric = self.metrics_cache.get(metric_id)
        if metric and metric.tenant_id == tenant_id:
            return metric
        return None
    
    async def update_metric(
        self,
        tenant_id: str,
        metric_id: str,
        updates: Dict[str, Any]
    ) -> Optional[CustomMetric]:
        """Update an existing metric."""
        metric = self.metrics_cache.get(metric_id)
        if not metric or metric.tenant_id != tenant_id:
            return None
        
        # Validate formula if being updated
        if "formula" in updates:
            data_sources = updates.get("data_sources", metric.data_sources)
            validation_result = self._validate_formula(updates["formula"], data_sources)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid formula: {validation_result['error']}")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(metric, key) and key not in ["id", "tenant_id", "created_at", "created_by"]:
                setattr(metric, key, value)
        
        metric.updated_at = datetime.utcnow()
        
        return metric
    
    async def delete_metric(
        self,
        tenant_id: str,
        metric_id: str
    ) -> bool:
        """Delete a custom metric."""
        metric = self.metrics_cache.get(metric_id)
        if metric and metric.tenant_id == tenant_id:
            del self.metrics_cache[metric_id]
            return True
        return False
    
    async def get_templates(
        self,
        category: Optional[str] = None,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available metric templates."""
        templates = []
        
        for template in self.templates.values():
            # Filter by category and industry if specified
            if category and template.category != category:
                continue
            if industry and template.industry and template.industry != industry:
                continue
            
            templates.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "formula": template.formula,
                "unit": template.unit,
                "data_sources": template.data_sources,
                "recommended_thresholds": template.recommended_thresholds,
                "industry": template.industry
            })
        
        return templates
    
    async def create_from_template(
        self,
        tenant_id: str,
        template_id: str,
        custom_name: Optional[str] = None,
        created_by: str = "user"
    ) -> CustomMetric:
        """Create a custom metric from a template."""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Convert recommended thresholds to threshold objects
        thresholds = [
            MetricThreshold(
                comparison=ThresholdComparison(t["comparison"]),
                value=float(t["value"]),
                severity=AlertSeverity(t["severity"]),
                message=t["message"]
            )
            for t in template.recommended_thresholds
        ]
        
        # Create metric
        metric = await self.create_metric(
            tenant_id=tenant_id,
            name=custom_name or template.name,
            description=template.description,
            metric_type=MetricType.CALCULATED,
            formula=template.formula,
            unit=template.unit,
            data_sources=template.data_sources,
            thresholds=[
                {
                    "comparison": t.comparison.value,
                    "value": t.value,
                    "severity": t.severity.value,
                    "message": t.message
                }
                for t in thresholds
            ],
            created_by=created_by
        )
        
        return metric
    
    async def get_available_data_sources(
        self,
        tenant_id: str
    ) -> List[Dict[str, str]]:
        """Get list of available data sources for metric formulas."""
        # MVP: Return static list
        # Production: Query actual available metrics from tenant's data
        return [
            {"id": "revenue", "name": "Revenue", "unit": "$"},
            {"id": "cogs", "name": "Cost of Goods Sold", "unit": "$"},
            {"id": "labor_cost", "name": "Labor Cost", "unit": "$"},
            {"id": "marketing_spend", "name": "Marketing Spend", "unit": "$"},
            {"id": "new_customers", "name": "New Customers", "unit": "count"},
            {"id": "average_order_value", "name": "Average Order Value", "unit": "$"},
            {"id": "purchase_frequency", "name": "Purchase Frequency", "unit": "times"},
            {"id": "customer_lifespan", "name": "Customer Lifespan", "unit": "months"},
            {"id": "employee_count", "name": "Employee Count", "unit": "count"},
            {"id": "average_inventory", "name": "Average Inventory", "unit": "$"},
            {"id": "fixed_costs", "name": "Fixed Costs", "unit": "$"},
            {"id": "variable_costs", "name": "Variable Costs", "unit": "$"},
            {"id": "days_inventory_outstanding", "name": "Days Inventory Outstanding", "unit": "days"},
            {"id": "days_sales_outstanding", "name": "Days Sales Outstanding", "unit": "days"},
            {"id": "days_payable_outstanding", "name": "Days Payable Outstanding", "unit": "days"},
            {"id": "total_covers", "name": "Total Covers", "unit": "count"},
            {"id": "table_count", "name": "Table Count", "unit": "count"},
            {"id": "service_periods", "name": "Service Periods", "unit": "count"},
        ]


def create_custom_metric_engine() -> CustomMetricEngine:
    """Factory function to create CustomMetricEngine instance."""
    return CustomMetricEngine()
