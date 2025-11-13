"""
Industry-Specific Dashboard Layout Configurations

Defines dashboard layouts for different business types:
- Which metrics to display
- Layout grid positioning
- Priority ordering
- Widget configurations
- Color schemes and theming
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field


class WidgetType(str, Enum):
    """Types of dashboard widgets"""
    METRIC_CARD = "metric_card"
    CHART = "chart"
    TABLE = "table"
    ALERT = "alert"
    GOAL_PROGRESS = "goal_progress"
    RECOMMENDATION = "recommendation"
    TIMELINE = "timeline"
    HEATMAP = "heatmap"


class ChartType(str, Enum):
    """Chart visualization types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SPARKLINE = "sparkline"
    GAUGE = "gauge"


@dataclass
class Widget:
    """Dashboard widget configuration"""
    id: str
    type: WidgetType
    title: str
    metric_id: Optional[str] = None  # Links to industry metrics
    chart_type: Optional[ChartType] = None
    
    # Grid layout (12-column grid)
    col_span: int = 3  # 1-12
    row_span: int = 1  # 1-N
    
    # Priority (1=highest, shown first on mobile)
    priority: int = 5
    
    # Visual styling
    color_scheme: Optional[str] = None  # e.g., "green", "red", "blue"
    show_trend: bool = True
    show_sparkline: bool = False
    
    # Data configuration
    data_source: Optional[str] = None
    refresh_interval: Optional[int] = None  # seconds
    
    # Conditional display
    min_confidence: Optional[float] = None  # Only show if business type confidence > threshold
    
    # Additional config
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardLayout:
    """Complete dashboard layout for a business type"""
    business_type: str
    display_name: str
    description: str
    
    # Primary metrics (always visible, top row)
    primary_metrics: List[Widget]
    
    # Secondary widgets (below primary metrics)
    secondary_widgets: List[Widget]
    
    # Optional widgets (shown based on data availability)
    optional_widgets: List[Widget] = field(default_factory=list)
    
    # Layout metadata
    theme_color: str = "blue"
    icon: str = "chart-bar"
    
    def get_all_widgets(self) -> List[Widget]:
        """Get all widgets in priority order"""
        all_widgets = self.primary_metrics + self.secondary_widgets + self.optional_widgets
        return sorted(all_widgets, key=lambda w: w.priority)


# =============================================================================
# RESTAURANT DASHBOARD LAYOUT
# =============================================================================

RESTAURANT_LAYOUT = DashboardLayout(
    business_type="restaurant",
    display_name="Restaurant Dashboard",
    description="Track food cost, labor, daily covers, and service efficiency",
    theme_color="orange",
    icon="utensils",
    
    primary_metrics=[
        Widget(
            id="prime_cost",
            type=WidgetType.METRIC_CARD,
            title="Prime Cost %",
            metric_id="prime_cost_pct",
            col_span=3,
            priority=1,
            color_scheme="red",
            show_trend=True,
            show_sparkline=True,
            config={
                "target": 60.0,
                "format": "percentage",
                "alert_threshold": 65.0,
                "description": "Food + Labor as % of revenue"
            }
        ),
        Widget(
            id="food_cost",
            type=WidgetType.METRIC_CARD,
            title="Food Cost %",
            metric_id="food_cost_pct",
            col_span=3,
            priority=2,
            color_scheme="orange",
            show_trend=True,
            config={
                "target": 30.0,
                "format": "percentage",
                "alert_threshold": 35.0,
            }
        ),
        Widget(
            id="labor_cost",
            type=WidgetType.METRIC_CARD,
            title="Labor Cost %",
            metric_id="labor_cost_pct",
            col_span=3,
            priority=3,
            color_scheme="blue",
            show_trend=True,
            config={
                "target": 30.0,
                "format": "percentage",
                "alert_threshold": 35.0,
            }
        ),
        Widget(
            id="daily_covers",
            type=WidgetType.METRIC_CARD,
            title="Daily Covers",
            metric_id="daily_covers",
            col_span=3,
            priority=4,
            color_scheme="green",
            show_trend=True,
            show_sparkline=True,
            config={
                "format": "number",
                "description": "Average customers per day"
            }
        ),
    ],
    
    secondary_widgets=[
        Widget(
            id="avg_check",
            type=WidgetType.METRIC_CARD,
            title="Average Check",
            metric_id="avg_check_size",
            col_span=3,
            priority=5,
            show_trend=True,
            config={"format": "currency"}
        ),
        Widget(
            id="covers_trend",
            type=WidgetType.CHART,
            title="Daily Covers Trend",
            chart_type=ChartType.LINE,
            col_span=6,
            row_span=2,
            priority=6,
            data_source="daily_covers_history",
            config={
                "period": "30_days",
                "show_weekday_patterns": True,
            }
        ),
        Widget(
            id="cost_breakdown",
            type=WidgetType.CHART,
            title="Cost Breakdown",
            chart_type=ChartType.PIE,
            col_span=3,
            row_span=2,
            priority=7,
            config={
                "categories": ["Food", "Labor", "Overhead", "Other"],
            }
        ),
    ],
    
    optional_widgets=[
        Widget(
            id="table_turnover",
            type=WidgetType.METRIC_CARD,
            title="Table Turnover",
            col_span=3,
            priority=10,
            min_confidence=0.8,  # Only show if we have high confidence data
        ),
        Widget(
            id="menu_performance",
            type=WidgetType.TABLE,
            title="Top Menu Items",
            col_span=6,
            priority=11,
            config={"limit": 10}
        ),
    ]
)


# =============================================================================
# RETAIL DASHBOARD LAYOUT
# =============================================================================

RETAIL_LAYOUT = DashboardLayout(
    business_type="retail",
    display_name="Retail Dashboard",
    description="Track inventory turnover, sales, conversion, and customer metrics",
    theme_color="purple",
    icon="shopping-bag",
    
    primary_metrics=[
        Widget(
            id="inventory_turnover",
            type=WidgetType.METRIC_CARD,
            title="Inventory Turnover",
            metric_id="inventory_turnover",
            col_span=3,
            priority=1,
            color_scheme="purple",
            show_trend=True,
            show_sparkline=True,
            config={
                "target": 6.0,
                "format": "ratio",
                "suffix": "x",
                "description": "Times inventory sold per year"
            }
        ),
        Widget(
            id="sell_through",
            type=WidgetType.METRIC_CARD,
            title="Sell-Through Rate",
            metric_id="sell_through_rate",
            col_span=3,
            priority=2,
            color_scheme="green",
            show_trend=True,
            config={
                "target": 75.0,
                "format": "percentage",
                "alert_threshold": 60.0,
            }
        ),
        Widget(
            id="avg_basket",
            type=WidgetType.METRIC_CARD,
            title="Avg Basket Size",
            metric_id="avg_basket_size",
            col_span=3,
            priority=3,
            color_scheme="blue",
            show_trend=True,
            config={"format": "currency"}
        ),
        Widget(
            id="gmroi",
            type=WidgetType.METRIC_CARD,
            title="GMROI",
            metric_id="gmroi",
            col_span=3,
            priority=4,
            color_scheme="orange",
            show_trend=True,
            config={
                "target": 3.0,
                "format": "ratio",
                "prefix": "$",
                "description": "Return per $1 invested"
            }
        ),
    ],
    
    secondary_widgets=[
        Widget(
            id="sales_trend",
            type=WidgetType.CHART,
            title="Sales Trend",
            chart_type=ChartType.AREA,
            col_span=8,
            row_span=2,
            priority=5,
            data_source="daily_sales",
            config={"period": "30_days"}
        ),
        Widget(
            id="category_performance",
            type=WidgetType.CHART,
            title="Category Performance",
            chart_type=ChartType.BAR,
            col_span=4,
            row_span=2,
            priority=6,
        ),
        Widget(
            id="conversion_rate",
            type=WidgetType.METRIC_CARD,
            title="Conversion Rate",
            metric_id="conversion_rate",
            col_span=3,
            priority=7,
            show_trend=True,
            config={"format": "percentage"}
        ),
    ],
    
    optional_widgets=[
        Widget(
            id="inventory_aging",
            type=WidgetType.HEATMAP,
            title="Inventory Aging",
            col_span=6,
            priority=10,
            min_confidence=0.7,
        ),
        Widget(
            id="top_products",
            type=WidgetType.TABLE,
            title="Best Sellers",
            col_span=6,
            priority=11,
        ),
    ]
)


# =============================================================================
# SERVICES DASHBOARD LAYOUT
# =============================================================================

SERVICES_LAYOUT = DashboardLayout(
    business_type="services",
    display_name="Professional Services Dashboard",
    description="Track utilization, billable hours, project profitability",
    theme_color="teal",
    icon="briefcase",
    
    primary_metrics=[
        Widget(
            id="utilization_rate",
            type=WidgetType.METRIC_CARD,
            title="Utilization Rate",
            metric_id="utilization_rate",
            col_span=3,
            priority=1,
            color_scheme="teal",
            show_trend=True,
            show_sparkline=True,
            config={
                "target": 75.0,
                "format": "percentage",
                "alert_threshold": 65.0,
                "description": "% of time on billable work"
            }
        ),
        Widget(
            id="realization_rate",
            type=WidgetType.METRIC_CARD,
            title="Realization Rate",
            metric_id="realization_rate",
            col_span=3,
            priority=2,
            color_scheme="green",
            show_trend=True,
            config={
                "target": 90.0,
                "format": "percentage",
                "description": "% of potential revenue collected"
            }
        ),
        Widget(
            id="avg_hourly_rate",
            type=WidgetType.METRIC_CARD,
            title="Avg Hourly Rate",
            metric_id="avg_hourly_rate",
            col_span=3,
            priority=3,
            color_scheme="blue",
            show_trend=True,
            config={"format": "currency"}
        ),
        Widget(
            id="project_margin",
            type=WidgetType.METRIC_CARD,
            title="Project Margin",
            metric_id="project_margin",
            col_span=3,
            priority=4,
            color_scheme="purple",
            show_trend=True,
            config={
                "target": 35.0,
                "format": "percentage",
            }
        ),
    ],
    
    secondary_widgets=[
        Widget(
            id="billable_hours_trend",
            type=WidgetType.CHART,
            title="Billable Hours",
            chart_type=ChartType.LINE,
            col_span=6,
            row_span=2,
            priority=5,
            data_source="weekly_hours",
        ),
        Widget(
            id="project_pipeline",
            type=WidgetType.CHART,
            title="Project Pipeline",
            chart_type=ChartType.BAR,
            col_span=6,
            row_span=2,
            priority=6,
            config={"group_by": "status"}
        ),
    ],
    
    optional_widgets=[
        Widget(
            id="client_retention",
            type=WidgetType.METRIC_CARD,
            title="Client Retention",
            col_span=3,
            priority=10,
            show_trend=True,
            config={"format": "percentage"}
        ),
        Widget(
            id="project_profitability",
            type=WidgetType.TABLE,
            title="Project Profitability",
            col_span=9,
            priority=11,
        ),
    ]
)


# =============================================================================
# CONTRACTOR DASHBOARD LAYOUT
# =============================================================================

CONTRACTOR_LAYOUT = DashboardLayout(
    business_type="contractor",
    display_name="Contractor Dashboard",
    description="Track job completion, material costs, labor efficiency",
    theme_color="yellow",
    icon="hammer",
    
    primary_metrics=[
        Widget(
            id="job_completion",
            type=WidgetType.METRIC_CARD,
            title="On-Time Completion",
            metric_id="job_completion_rate",
            col_span=3,
            priority=1,
            color_scheme="green",
            show_trend=True,
            config={
                "target": 85.0,
                "format": "percentage",
                "description": "% of jobs finished on schedule"
            }
        ),
        Widget(
            id="material_cost",
            type=WidgetType.METRIC_CARD,
            title="Material Cost %",
            metric_id="material_cost_pct",
            col_span=3,
            priority=2,
            color_scheme="orange",
            show_trend=True,
            config={
                "target": 45.0,
                "format": "percentage",
            }
        ),
        Widget(
            id="labor_efficiency",
            type=WidgetType.METRIC_CARD,
            title="Labor Efficiency",
            metric_id="labor_efficiency",
            col_span=3,
            priority=3,
            color_scheme="blue",
            show_trend=True,
            config={
                "target": 1.0,
                "format": "ratio",
                "suffix": "x",
                "description": "Actual vs estimated hours"
            }
        ),
        Widget(
            id="change_orders",
            type=WidgetType.METRIC_CARD,
            title="Change Orders",
            metric_id="change_order_pct",
            col_span=3,
            priority=4,
            color_scheme="red",
            show_trend=True,
            config={
                "target": 5.0,
                "format": "percentage",
                "alert_threshold": 10.0,
            }
        ),
    ],
    
    secondary_widgets=[
        Widget(
            id="active_jobs",
            type=WidgetType.CHART,
            title="Active Jobs Timeline",
            chart_type=ChartType.BAR,
            col_span=8,
            row_span=2,
            priority=5,
            config={"orientation": "horizontal"}
        ),
        Widget(
            id="cost_breakdown",
            type=WidgetType.CHART,
            title="Cost Breakdown",
            chart_type=ChartType.PIE,
            col_span=4,
            row_span=2,
            priority=6,
            config={
                "categories": ["Materials", "Labor", "Equipment", "Other"],
            }
        ),
    ],
    
    optional_widgets=[
        Widget(
            id="job_profitability",
            type=WidgetType.TABLE,
            title="Job Profitability",
            col_span=12,
            priority=10,
        ),
    ]
)


# =============================================================================
# DEFAULT/OTHER DASHBOARD LAYOUT
# =============================================================================

DEFAULT_LAYOUT = DashboardLayout(
    business_type="other",
    display_name="Business Dashboard",
    description="General business metrics and performance indicators",
    theme_color="blue",
    icon="chart-line",
    
    primary_metrics=[
        Widget(
            id="revenue",
            type=WidgetType.METRIC_CARD,
            title="Revenue",
            col_span=3,
            priority=1,
            color_scheme="green",
            show_trend=True,
            show_sparkline=True,
            config={"format": "currency"}
        ),
        Widget(
            id="profit_margin",
            type=WidgetType.METRIC_CARD,
            title="Profit Margin",
            col_span=3,
            priority=2,
            color_scheme="blue",
            show_trend=True,
            config={"format": "percentage"}
        ),
        Widget(
            id="cash_flow",
            type=WidgetType.METRIC_CARD,
            title="Cash Flow",
            col_span=3,
            priority=3,
            color_scheme="teal",
            show_trend=True,
            config={"format": "currency"}
        ),
        Widget(
            id="transactions",
            type=WidgetType.METRIC_CARD,
            title="Transactions",
            col_span=3,
            priority=4,
            show_trend=True,
            config={"format": "number"}
        ),
    ],
    
    secondary_widgets=[
        Widget(
            id="revenue_trend",
            type=WidgetType.CHART,
            title="Revenue Trend",
            chart_type=ChartType.LINE,
            col_span=6,
            row_span=2,
            priority=5,
        ),
        Widget(
            id="expense_breakdown",
            type=WidgetType.CHART,
            title="Expense Breakdown",
            chart_type=ChartType.PIE,
            col_span=6,
            row_span=2,
            priority=6,
        ),
    ],
)


# =============================================================================
# LAYOUT REGISTRY
# =============================================================================

LAYOUT_REGISTRY: Dict[str, DashboardLayout] = {
    "restaurant": RESTAURANT_LAYOUT,
    "retail": RETAIL_LAYOUT,
    "services": SERVICES_LAYOUT,
    "contractor": CONTRACTOR_LAYOUT,
    "healthcare": SERVICES_LAYOUT,  # Reuse services layout
    "manufacturing": DEFAULT_LAYOUT,  # Use default for now
    "wholesale": RETAIL_LAYOUT,  # Similar to retail
    "other": DEFAULT_LAYOUT,
}


def get_dashboard_layout(business_type: str) -> DashboardLayout:
    """Get dashboard layout for business type"""
    return LAYOUT_REGISTRY.get(business_type, DEFAULT_LAYOUT)


def get_layout_config(business_type: str) -> Dict[str, Any]:
    """
    Get dashboard layout as JSON-serializable dict
    
    Returns:
        {
            "business_type": "restaurant",
            "display_name": "Restaurant Dashboard",
            "description": "...",
            "theme_color": "orange",
            "icon": "utensils",
            "widgets": [
                {
                    "id": "prime_cost",
                    "type": "metric_card",
                    "title": "Prime Cost %",
                    "col_span": 3,
                    "priority": 1,
                    ...
                },
                ...
            ]
        }
    """
    layout = get_dashboard_layout(business_type)
    
    all_widgets = layout.get_all_widgets()
    
    return {
        "business_type": layout.business_type,
        "display_name": layout.display_name,
        "description": layout.description,
        "theme_color": layout.theme_color,
        "icon": layout.icon,
        "widgets": [
            {
                "id": w.id,
                "type": w.type.value,
                "title": w.title,
                "metric_id": w.metric_id,
                "chart_type": w.chart_type.value if w.chart_type else None,
                "col_span": w.col_span,
                "row_span": w.row_span,
                "priority": w.priority,
                "color_scheme": w.color_scheme,
                "show_trend": w.show_trend,
                "show_sparkline": w.show_sparkline,
                "data_source": w.data_source,
                "refresh_interval": w.refresh_interval,
                "min_confidence": w.min_confidence,
                "config": w.config,
            }
            for w in all_widgets
        ]
    }
