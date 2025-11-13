"""
Coach V6 Templates - AI-Powered Recommendation Generation

Comprehensive template system for generating contextual, natural-language
recommendations across 6 business domains:
- Cash Flow & Liquidity
- Inventory Management
- Revenue Growth
- Profitability
- Operations Efficiency
- Strategic Growth

Uses GPT-4 to generate recommendations with:
- Contextual awareness
- Data-driven insights
- Actionable steps
- Personalized tone
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import os


class RecommendationCategory(str, Enum):
    """Recommendation categories"""
    CASH_FLOW = "cash_flow"
    INVENTORY = "inventory"
    REVENUE = "revenue"
    PROFITABILITY = "profitability"
    OPERATIONS = "operations"
    GROWTH = "growth"


class TemplateTrigger(str, Enum):
    """Conditions that trigger recommendations"""
    # Cash Flow
    NEGATIVE_CASH_FLOW_PROJECTION = "negative_cash_flow_projection"
    LOW_CASH_BALANCE = "low_cash_balance"
    HIGH_BURN_RATE = "high_burn_rate"
    OVERDUE_RECEIVABLES = "overdue_receivables"
    PAYMENT_DELAYS = "payment_delays"
    
    # Inventory
    AGING_INVENTORY = "aging_inventory"
    STOCKOUT_RISK = "stockout_risk"
    OVERSTOCK = "overstock"
    SLOW_MOVING_ITEMS = "slow_moving_items"
    INVENTORY_TURNOVER_LOW = "inventory_turnover_low"
    
    # Revenue
    REVENUE_DECLINE = "revenue_decline"
    SEASONAL_OPPORTUNITY = "seasonal_opportunity"
    CUSTOMER_CHURN = "customer_churn"
    AVERAGE_ORDER_VALUE_DECLINE = "average_order_value_decline"
    NEW_CUSTOMER_ACQUISITION = "new_customer_acquisition"
    
    # Profitability
    MARGIN_EROSION = "margin_erosion"
    COST_SPIKE = "cost_spike"
    PRICING_OPPORTUNITY = "pricing_opportunity"
    EXPENSE_OPTIMIZATION = "expense_optimization"
    
    # Operations
    TASK_BACKLOG = "task_backlog"
    PROCESS_BOTTLENECK = "process_bottleneck"
    CAPACITY_CONSTRAINT = "capacity_constraint"
    WORKFLOW_INEFFICIENCY = "workflow_inefficiency"
    
    # Growth
    HIRING_OPPORTUNITY = "hiring_opportunity"
    EXPANSION_READY = "expansion_ready"
    PRODUCT_LINE_EXTENSION = "product_line_extension"
    PARTNERSHIP_OPPORTUNITY = "partnership_opportunity"


class RecommendationTemplate:
    """Template for generating recommendations"""
    
    def __init__(
        self,
        trigger: TemplateTrigger,
        category: RecommendationCategory,
        priority_logic: str,
        title_template: str,
        description_template: str,
        reasoning_template: str,
        actions: List[Dict[str, Any]],
        data_requirements: List[str],
    ):
        self.trigger = trigger
        self.category = category
        self.priority_logic = priority_logic
        self.title_template = title_template
        self.description_template = description_template
        self.reasoning_template = reasoning_template
        self.actions = actions
        self.data_requirements = data_requirements
    
    def should_trigger(self, data: Dict[str, Any]) -> bool:
        """Check if this template should be triggered"""
        # Evaluate priority logic as Python expression
        try:
            return eval(self.priority_logic, {"__builtins__": {}}, data)
        except Exception:
            return False
    
    def get_priority(self, data: Dict[str, Any]) -> str:
        """Determine priority level based on data"""
        # Extract severity from data
        if self.trigger in [
            TemplateTrigger.NEGATIVE_CASH_FLOW_PROJECTION,
            TemplateTrigger.LOW_CASH_BALANCE,
            TemplateTrigger.STOCKOUT_RISK,
        ]:
            if data.get("days_until_critical", 30) < 14:
                return "critical"
            elif data.get("days_until_critical", 30) < 30:
                return "important"
        
        if self.trigger in [
            TemplateTrigger.OVERDUE_RECEIVABLES,
            TemplateTrigger.AGING_INVENTORY,
            TemplateTrigger.MARGIN_EROSION,
        ]:
            if data.get("severity_score", 0) > 7:
                return "critical"
            elif data.get("severity_score", 0) > 4:
                return "important"
        
        return "suggestion"
    
    def format_template(self, template: str, data: Dict[str, Any]) -> str:
        """Format template string with data"""
        try:
            return template.format(**data)
        except KeyError:
            # Fallback if data is missing
            return template


# =============================================================================
# CASH FLOW & LIQUIDITY TEMPLATES
# =============================================================================

CASH_FLOW_TEMPLATES = [
    RecommendationTemplate(
        trigger=TemplateTrigger.NEGATIVE_CASH_FLOW_PROJECTION,
        category=RecommendationCategory.CASH_FLOW,
        priority_logic="data.get('days_until_negative', 100) < 21",
        title_template="Cash flow projected negative in {days_until_negative} days",
        description_template="Without intervention, your bank balance will drop to ${projected_balance:,.0f} by {critical_date}.",
        reasoning_template="Based on current burn rate of ${burn_rate:,.0f}/day and ${outstanding_receivables:,.0f} in outstanding receivables.",
        actions=[
            {
                "label": "Accelerate collections on {overdue_count} overdue invoices",
                "description": "Focus on invoices over 30 days (${overdue_amount:,.0f})",
                "buttonText": "View Invoices",
            },
            {
                "label": "Delay {deferrable_count} non-essential expenses",
                "description": "Postpone equipment purchases and subscriptions",
                "buttonText": "Review Expenses",
                "variant": "secondary",
            },
            {
                "label": "Explore short-term financing options",
                "description": "Line of credit or invoice factoring",
                "buttonText": "Get Quotes",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "days_until_negative",
            "projected_balance",
            "critical_date",
            "burn_rate",
            "outstanding_receivables",
            "overdue_count",
            "overdue_amount",
            "deferrable_count",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.LOW_CASH_BALANCE,
        category=RecommendationCategory.CASH_FLOW,
        priority_logic="data.get('cash_balance', 0) < data.get('min_safe_balance', 10000)",
        title_template="Cash balance below safe threshold",
        description_template="Your current balance of ${cash_balance:,.0f} is {percent_below}% below your recommended minimum of ${min_safe_balance:,.0f}.",
        reasoning_template="This leaves only {days_of_runway} days of operating runway based on average daily expenses.",
        actions=[
            {
                "label": "Transfer funds from savings",
                "description": "Move ${transfer_amount:,.0f} to operating account",
                "buttonText": "Initiate Transfer",
            },
            {
                "label": "Reduce discretionary spending",
                "description": "Cut back on non-essential expenses temporarily",
                "buttonText": "Review Budget",
            },
        ],
        data_requirements=[
            "cash_balance",
            "min_safe_balance",
            "percent_below",
            "days_of_runway",
            "transfer_amount",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.OVERDUE_RECEIVABLES,
        category=RecommendationCategory.CASH_FLOW,
        priority_logic="data.get('overdue_amount', 0) > 5000 and data.get('overdue_days_avg', 0) > 30",
        title_template="{overdue_count} invoices overdue by {overdue_days_avg} days",
        description_template="${overdue_amount:,.0f} in outstanding receivables is impacting your cash flow.",
        reasoning_template="If collected promptly, this would extend your cash runway by {additional_days} days.",
        actions=[
            {
                "label": "Send automated payment reminders",
                "description": "Email {overdue_count} customers with overdue balances",
                "buttonText": "Send Reminders",
            },
            {
                "label": "Offer early payment discount",
                "description": "2% discount for payment within 7 days",
                "buttonText": "Create Offer",
                "variant": "secondary",
            },
            {
                "label": "Call top {high_value_count} high-value customers",
                "description": "Accounts over ${high_value_threshold:,.0f}",
                "buttonText": "View List",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "overdue_count",
            "overdue_days_avg",
            "overdue_amount",
            "additional_days",
            "high_value_count",
            "high_value_threshold",
        ],
    ),
]


# =============================================================================
# INVENTORY MANAGEMENT TEMPLATES
# =============================================================================

INVENTORY_TEMPLATES = [
    RecommendationTemplate(
        trigger=TemplateTrigger.AGING_INVENTORY,
        category=RecommendationCategory.INVENTORY,
        priority_logic="data.get('aging_items_count', 0) > 10 and data.get('aging_days', 0) > 90",
        title_template="Inventory aging alert: {aging_items_count} items",
        description_template="{aging_items_count} items have been in stock for {aging_days}+ days, tying up ${capital_tied:,.0f}.",
        reasoning_template="Slow-moving inventory is reducing your inventory turnover ratio to {turnover_ratio}x (target: {target_turnover}x).",
        actions=[
            {
                "label": "Run clearance promotion",
                "description": "{discount_percent}% discount to move aging inventory",
                "buttonText": "Create Promotion",
            },
            {
                "label": "Bundle with popular items",
                "description": "Create package deals to increase velocity",
                "buttonText": "Create Bundles",
                "variant": "secondary",
            },
            {
                "label": "Donate or write off",
                "description": "Tax deduction for unsellable items",
                "buttonText": "Review Items",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "aging_items_count",
            "aging_days",
            "capital_tied",
            "turnover_ratio",
            "target_turnover",
            "discount_percent",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.STOCKOUT_RISK,
        category=RecommendationCategory.INVENTORY,
        priority_logic="data.get('at_risk_items_count', 0) > 0",
        title_template="Stockout risk: {at_risk_items_count} items below reorder point",
        description_template="Popular items will run out in {days_until_stockout} days if not reordered.",
        reasoning_template="These items account for {revenue_percent}% of your revenue. A stockout could cost ${lost_revenue:,.0f}/week.",
        actions=[
            {
                "label": "Place urgent reorder",
                "description": "Order {at_risk_items_count} items from suppliers",
                "buttonText": "Create PO",
            },
            {
                "label": "Enable backorder for customers",
                "description": "Accept orders with delayed fulfillment",
                "buttonText": "Enable Backorders",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "at_risk_items_count",
            "days_until_stockout",
            "revenue_percent",
            "lost_revenue",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.SLOW_MOVING_ITEMS,
        category=RecommendationCategory.INVENTORY,
        priority_logic="data.get('slow_moving_count', 0) > 5",
        title_template="Optimize inventory mix: {slow_moving_count} slow-moving items",
        description_template="Items with <{min_velocity} units/month velocity are taking up {percent_space}% of shelf space.",
        reasoning_template="Reallocating this space to faster-moving items could increase revenue by {potential_increase}%.",
        actions=[
            {
                "label": "Reduce reorder quantities",
                "description": "Lower par levels for slow movers",
                "buttonText": "Adjust Levels",
            },
            {
                "label": "Discontinue lowest performers",
                "description": "Remove bottom {discontinue_count} items",
                "buttonText": "Review Items",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "slow_moving_count",
            "min_velocity",
            "percent_space",
            "potential_increase",
            "discontinue_count",
        ],
    ),
]


# =============================================================================
# REVENUE GROWTH TEMPLATES
# =============================================================================

REVENUE_TEMPLATES = [
    RecommendationTemplate(
        trigger=TemplateTrigger.REVENUE_DECLINE,
        category=RecommendationCategory.REVENUE,
        priority_logic="data.get('revenue_change_percent', 0) < -10",
        title_template="Revenue declined {revenue_change_percent}% vs. {comparison_period}",
        description_template="From ${previous_revenue:,.0f} to ${current_revenue:,.0f} ({revenue_change:,.0f} decrease).",
        reasoning_template="Analysis shows decline driven by: {decline_factors}.",
        actions=[
            {
                "label": "Launch customer win-back campaign",
                "description": "Target {lapsed_customers} inactive customers",
                "buttonText": "Create Campaign",
            },
            {
                "label": "Analyze top {top_n} revenue loss sources",
                "description": "Identify root causes and opportunities",
                "buttonText": "View Analysis",
                "variant": "secondary",
            },
            {
                "label": "Offer limited-time promotion",
                "description": "{promo_percent}% off to drive immediate sales",
                "buttonText": "Create Promo",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "revenue_change_percent",
            "comparison_period",
            "previous_revenue",
            "current_revenue",
            "revenue_change",
            "decline_factors",
            "lapsed_customers",
            "top_n",
            "promo_percent",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.AVERAGE_ORDER_VALUE_DECLINE,
        category=RecommendationCategory.REVENUE,
        priority_logic="data.get('aov_change_percent', 0) < -5",
        title_template="Average order value down {aov_change_percent}%",
        description_template="From ${previous_aov:.2f} to ${current_aov:.2f} per transaction.",
        reasoning_template="Increasing AOV back to previous levels would add ${potential_revenue:,.0f}/month.",
        actions=[
            {
                "label": "Implement minimum order for free shipping",
                "description": "Set threshold at ${free_shipping_threshold:.0f}",
                "buttonText": "Configure",
            },
            {
                "label": "Create product bundles",
                "description": "Offer {bundle_count} curated packages",
                "buttonText": "Create Bundles",
                "variant": "secondary",
            },
            {
                "label": "Upsell at checkout",
                "description": "Suggest complementary items",
                "buttonText": "Enable Upsells",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "aov_change_percent",
            "previous_aov",
            "current_aov",
            "potential_revenue",
            "free_shipping_threshold",
            "bundle_count",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.SEASONAL_OPPORTUNITY,
        category=RecommendationCategory.REVENUE,
        priority_logic="data.get('seasonal_uplift_potential', 0) > 20",
        title_template="Capitalize on {season_name} season opportunity",
        description_template="Historical data shows {seasonal_uplift_potential}% revenue increase during this period.",
        reasoning_template="Last year, you generated ${last_year_seasonal:,.0f} in the {weeks_remaining} weeks before {peak_date}.",
        actions=[
            {
                "label": "Stock up on seasonal bestsellers",
                "description": "Increase inventory for top {top_seasonal_items} items",
                "buttonText": "Review Items",
            },
            {
                "label": "Launch seasonal marketing campaign",
                "description": "Email + social media promotion",
                "buttonText": "Create Campaign",
            },
            {
                "label": "Create seasonal bundles",
                "description": "Gift packages and themed collections",
                "buttonText": "Create Bundles",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "season_name",
            "seasonal_uplift_potential",
            "last_year_seasonal",
            "weeks_remaining",
            "peak_date",
            "top_seasonal_items",
        ],
    ),
]


# =============================================================================
# PROFITABILITY TEMPLATES
# =============================================================================

PROFITABILITY_TEMPLATES = [
    RecommendationTemplate(
        trigger=TemplateTrigger.MARGIN_EROSION,
        category=RecommendationCategory.PROFITABILITY,
        priority_logic="data.get('margin_change', 0) < -3",
        title_template="Gross margin declined to {current_margin}%",
        description_template="Down from {previous_margin}% last {period}, reducing profit by ${margin_impact:,.0f}.",
        reasoning_template="Analysis shows margin pressure from: {margin_factors}.",
        actions=[
            {
                "label": "Review supplier pricing",
                "description": "Negotiate with top {supplier_count} suppliers",
                "buttonText": "Contact Suppliers",
            },
            {
                "label": "Adjust pricing on {sku_count} low-margin SKUs",
                "description": "Increase prices by {price_increase_percent}%",
                "buttonText": "Review Pricing",
            },
            {
                "label": "Discontinue {unprofitable_count} unprofitable items",
                "description": "Focus on high-margin products",
                "buttonText": "View Items",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "current_margin",
            "previous_margin",
            "period",
            "margin_impact",
            "margin_factors",
            "supplier_count",
            "sku_count",
            "price_increase_percent",
            "unprofitable_count",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.COST_SPIKE,
        category=RecommendationCategory.PROFITABILITY,
        priority_logic="data.get('cost_increase_percent', 0) > 15",
        title_template="{cost_category} costs up {cost_increase_percent}%",
        description_template="Increased from ${previous_cost:,.0f} to ${current_cost:,.0f} this {period}.",
        reasoning_template="If sustained, this will reduce annual profit by ${annual_impact:,.0f}.",
        actions=[
            {
                "label": "Audit {cost_category} expenses",
                "description": "Identify cost reduction opportunities",
                "buttonText": "View Details",
            },
            {
                "label": "Negotiate better rates",
                "description": "Contact {vendor_count} vendors for discounts",
                "buttonText": "Contact Vendors",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "cost_category",
            "cost_increase_percent",
            "previous_cost",
            "current_cost",
            "period",
            "annual_impact",
            "vendor_count",
        ],
    ),
]


# =============================================================================
# OPERATIONS EFFICIENCY TEMPLATES
# =============================================================================

OPERATIONS_TEMPLATES = [
    RecommendationTemplate(
        trigger=TemplateTrigger.TASK_BACKLOG,
        category=RecommendationCategory.OPERATIONS,
        priority_logic="data.get('overdue_tasks', 0) > 10",
        title_template="{overdue_tasks} tasks overdue (avg {avg_days_overdue} days)",
        description_template="Task completion rate dropped to {completion_rate}% (target: {target_completion}%).",
        reasoning_template="Backlog is growing by {backlog_growth_rate} tasks/week, indicating capacity constraint.",
        actions=[
            {
                "label": "Prioritize critical tasks",
                "description": "Focus on {high_priority_count} high-impact items",
                "buttonText": "View Tasks",
            },
            {
                "label": "Delegate {delegatable_count} routine tasks",
                "description": "Assign to team members or contractors",
                "buttonText": "Delegate",
                "variant": "secondary",
            },
            {
                "label": "Automate repetitive workflows",
                "description": "Identify {automation_candidates} automation opportunities",
                "buttonText": "Explore Tools",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "overdue_tasks",
            "avg_days_overdue",
            "completion_rate",
            "target_completion",
            "backlog_growth_rate",
            "high_priority_count",
            "delegatable_count",
            "automation_candidates",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.CAPACITY_CONSTRAINT,
        category=RecommendationCategory.OPERATIONS,
        priority_logic="data.get('capacity_utilization', 0) > 90",
        title_template="Operating at {capacity_utilization}% capacity",
        description_template="You're {percent_over}% above optimal workload, risking burnout and quality issues.",
        reasoning_template="Peak demand times show {peak_utilization}% utilization, causing {bottleneck_count} bottlenecks.",
        actions=[
            {
                "label": "Hire part-time help",
                "description": "{hours_needed} hours/week for {role_description}",
                "buttonText": "Draft Job Post",
            },
            {
                "label": "Defer {deferrable_projects} non-critical projects",
                "description": "Focus resources on revenue-generating activities",
                "buttonText": "Review Projects",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "capacity_utilization",
            "percent_over",
            "peak_utilization",
            "bottleneck_count",
            "hours_needed",
            "role_description",
            "deferrable_projects",
        ],
    ),
]


# =============================================================================
# STRATEGIC GROWTH TEMPLATES
# =============================================================================

GROWTH_TEMPLATES = [
    RecommendationTemplate(
        trigger=TemplateTrigger.EXPANSION_READY,
        category=RecommendationCategory.GROWTH,
        priority_logic="data.get('growth_readiness_score', 0) > 75",
        title_template="Your business is ready for expansion",
        description_template="Financial health, operational efficiency, and market demand indicate expansion opportunity.",
        reasoning_template="You have {cash_runway} months runway, {margin}% margin, and growing demand in {growth_markets}.",
        actions=[
            {
                "label": "Explore new market opportunities",
                "description": "Research {target_markets} target markets",
                "buttonText": "View Analysis",
            },
            {
                "label": "Consider additional location or channel",
                "description": "Expand to {expansion_options}",
                "buttonText": "Explore Options",
                "variant": "secondary",
            },
            {
                "label": "Invest in marketing",
                "description": "Increase ad spend by ${marketing_investment:,.0f}",
                "buttonText": "Plan Campaign",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "growth_readiness_score",
            "cash_runway",
            "margin",
            "growth_markets",
            "target_markets",
            "expansion_options",
            "marketing_investment",
        ],
    ),
    
    RecommendationTemplate(
        trigger=TemplateTrigger.PRODUCT_LINE_EXTENSION,
        category=RecommendationCategory.GROWTH,
        priority_logic="data.get('product_opportunity_score', 0) > 60",
        title_template="Consider adding {product_category} to your lineup",
        description_template="Customer data shows {demand_percent}% of customers interested in {product_category}.",
        reasoning_template="Estimated additional revenue: ${revenue_potential:,.0f}/year with {margin_estimate}% margin.",
        actions=[
            {
                "label": "Survey customers on product preferences",
                "description": "Validate demand before investing",
                "buttonText": "Create Survey",
            },
            {
                "label": "Research {competitor_count} competitors offering {product_category}",
                "description": "Analyze pricing and positioning",
                "buttonText": "View Research",
                "variant": "secondary",
            },
            {
                "label": "Calculate ROI for product launch",
                "description": "Investment needed: ${investment_required:,.0f}",
                "buttonText": "View Model",
                "variant": "secondary",
            },
        ],
        data_requirements=[
            "product_category",
            "demand_percent",
            "revenue_potential",
            "margin_estimate",
            "competitor_count",
            "investment_required",
        ],
    ),
]


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

ALL_TEMPLATES = (
    CASH_FLOW_TEMPLATES +
    INVENTORY_TEMPLATES +
    REVENUE_TEMPLATES +
    PROFITABILITY_TEMPLATES +
    OPERATIONS_TEMPLATES +
    GROWTH_TEMPLATES
)


def get_template(trigger: TemplateTrigger) -> Optional[RecommendationTemplate]:
    """Get template by trigger"""
    for template in ALL_TEMPLATES:
        if template.trigger == trigger:
            return template
    return None


def get_templates_by_category(category: RecommendationCategory) -> List[RecommendationTemplate]:
    """Get all templates for a category"""
    return [t for t in ALL_TEMPLATES if t.category == category]


def get_triggered_templates(data: Dict[str, Any]) -> List[RecommendationTemplate]:
    """Get all templates that should trigger based on data"""
    return [t for t in ALL_TEMPLATES if t.should_trigger(data)]
