"""
Coach Recommendations Service for Coach V6

Generates proactive AI recommendations based on business health data.
Uses template system and GPT-4 for natural language generation.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import random
import sys
import os

# Add packages directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../packages"))

try:
    from agent.coach_templates import (
        get_triggered_templates,
        RecommendationTemplate,
        TemplateTrigger,
        RecommendationCategory,
    )
    from agent.gpt4_recommendations import (
        GPT4RecommendationGenerator,
        RecommendationEnricher,
    )
    TEMPLATES_AVAILABLE = True
except ImportError:
    print("Warning: Coach templates not available. Using simplified recommendations.")
    TEMPLATES_AVAILABLE = False


class RecommendationPriority(str, Enum):
    """Recommendation priority levels"""
    CRITICAL = "critical"
    IMPORTANT = "important"
    SUGGESTION = "suggestion"


class RecommendationAction(BaseModel):
    """Action within a recommendation"""
    id: str
    label: str
    description: Optional[str] = None
    button_text: str = Field(..., alias="buttonText")
    variant: str = "primary"
    completed: bool = False
    
    class Config:
        populate_by_name = True


class CoachRecommendation(BaseModel):
    """AI-generated coach recommendation"""
    id: str
    priority: RecommendationPriority
    title: str
    description: str
    reasoning: Optional[str] = None
    actions: List[RecommendationAction]
    dismissible: bool = True
    dismissed: bool = False
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    generated_at: datetime = Field(default_factory=datetime.now, alias="generatedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class Alert(BaseModel):
    """Critical alert for health score header"""
    id: str
    type: str = "critical"
    title: str
    description: str
    metric: Optional[str] = None
    value: Optional[Any] = None
    threshold: Optional[Any] = None


class Signal(BaseModel):
    """Positive signal for health score header"""
    id: str
    type: str = "positive"
    title: str
    description: str
    metric: Optional[str] = None
    value: Optional[Any] = None


class MetricSnapshot(BaseModel):
    """Key metric snapshot for metrics grid"""
    id: str
    label: str
    value: str
    change: float
    change_type: str = Field(..., alias="changeType")
    trend: str  # 'up' | 'down' | 'stable'
    sparkline_data: Optional[List[float]] = Field(None, alias="sparklineData")
    period: Optional[str] = None
    format: Optional[str] = None
    
    class Config:
        populate_by_name = True


class CoachRecommendationsService:
    """Service for generating coach recommendations"""
    
    def __init__(self, tenant_id: str, persistence_backend=None, use_gpt4: bool = False):
        self.tenant_id = tenant_id
        self.backend = persistence_backend
        self.use_gpt4 = use_gpt4
        
        # Initialize GPT-4 if available and requested
        if TEMPLATES_AVAILABLE and use_gpt4:
            self.gpt4_generator = GPT4RecommendationGenerator()
            self.enricher = RecommendationEnricher(self.gpt4_generator)
        else:
            self.gpt4_generator = None
            self.enricher = None
    
    async def generate_recommendations(
        self,
        health_score: int,
        health_breakdown: Dict[str, Any],
        connector_data: Dict[str, Any],
    ) -> List[CoachRecommendation]:
        """
        Generate AI recommendations based on health score and data.
        
        Uses template system and optional GPT-4 enhancement.
        """
        if TEMPLATES_AVAILABLE:
            return await self._generate_from_templates(
                health_score,
                health_breakdown,
                connector_data,
            )
        else:
            # Fallback to simplified logic
            return await self._generate_simplified(
                health_score,
                health_breakdown,
                connector_data,
            )
    
    async def _generate_from_templates(
        self,
        health_score: int,
        health_breakdown: Dict[str, Any],
        connector_data: Dict[str, Any],
    ) -> List[CoachRecommendation]:
        """Generate recommendations using template system"""
        recommendations = []
        
        # Prepare analysis data for template matching
        analysis_data = self._prepare_analysis_data(
            health_score,
            health_breakdown,
            connector_data,
        )
        
        # Get triggered templates
        triggered = get_triggered_templates(analysis_data)
        
        # Generate recommendations from templates (max 3-4 per request)
        for template in triggered[:4]:
            rec = self._build_recommendation_from_template(
                template,
                analysis_data,
            )
            
            # Optionally enrich with GPT-4
            if self.enricher:
                business_context = {
                    "tenant_id": self.tenant_id,
                    "health_score": health_score,
                    "industry": connector_data.get("industry", "SMB"),
                }
                rec_dict = rec.dict()
                enriched = self.enricher.enrich_recommendation(
                    rec_dict,
                    business_context,
                )
                # Update with enriched content
                rec.title = enriched.get("title", rec.title)
                rec.description = enriched.get("description", rec.description)
                rec.reasoning = enriched.get("reasoning", rec.reasoning)
            
            recommendations.append(rec)
        
        return recommendations
    
    def _prepare_analysis_data(
        self,
        health_score: int,
        health_breakdown: Dict[str, Any],
        connector_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare data for template matching"""
        # This would normally extract from real connector data
        # For now, use mock data that matches template requirements
        return {
            # Cash flow metrics
            "days_until_negative": 18 if health_score < 60 else 60,
            "cash_balance": connector_data.get("cash_balance", 18450),
            "burn_rate": connector_data.get("burn_rate", 1200),
            "min_safe_balance": 15000,
            "outstanding_receivables": 12450,
            "overdue_count": 3 if health_score < 70 else 0,
            "overdue_amount": 12450 if health_score < 70 else 0,
            "overdue_days_avg": 35 if health_score < 70 else 0,
            
            # Inventory metrics
            "aging_items_count": 18 if health_breakdown.get("operations", 100) < 70 else 5,
            "aging_days": 95 if health_breakdown.get("operations", 100) < 70 else 45,
            "capital_tied": 8500,
            "turnover_ratio": 2.3,
            "target_turnover": 4.0,
            "at_risk_items_count": 0,
            "slow_moving_count": 8,
            
            # Revenue metrics
            "revenue_change_percent": -12 if health_breakdown.get("revenue", 100) < 70 else 8,
            "current_revenue": 45200,
            "previous_revenue": 51400,
            "aov_change_percent": -5 if health_breakdown.get("revenue", 100) < 75 else 3,
            "seasonal_uplift_potential": 25,
            
            # Profitability metrics
            "current_margin": 38 if health_breakdown.get("profitability", 100) < 70 else 42,
            "previous_margin": 42,
            "margin_change": -4 if health_breakdown.get("profitability", 100) < 70 else 0,
            "cost_increase_percent": 12,
            
            # Operations metrics
            "overdue_tasks": 15 if health_breakdown.get("operations", 100) < 70 else 3,
            "completion_rate": 65 if health_breakdown.get("operations", 100) < 70 else 85,
            "target_completion": 90,
            "capacity_utilization": 92 if health_breakdown.get("operations", 100) < 75 else 75,
            
            # Growth metrics
            "growth_readiness_score": 78 if health_score > 75 else 45,
            "product_opportunity_score": 65 if health_score > 70 else 30,
            
            # Severity scores for prioritization
            "severity_score": 8 if health_score < 60 else (5 if health_score < 75 else 2),
            "days_until_critical": 18 if health_score < 60 else 45,
        }
    
    def _build_recommendation_from_template(
        self,
        template: "RecommendationTemplate",
        data: Dict[str, Any],
    ) -> CoachRecommendation:
        """Build recommendation from template"""
        rec_id = f"rec_{random.randint(1000, 9999)}"
        priority = template.get_priority(data)
        
        # Format text with data
        title = template.format_template(template.title_template, data)
        description = template.format_template(template.description_template, data)
        reasoning = template.format_template(template.reasoning_template, data)
        
        # Format actions
        actions = []
        for i, action_template in enumerate(template.actions):
            action = RecommendationAction(
                id=f"{rec_id}_action_{i}",
                label=template.format_template(action_template["label"], data),
                description=template.format_template(
                    action_template.get("description", ""),
                    data,
                ),
                buttonText=template.format_template(
                    action_template.get("buttonText", "Take Action"),
                    data,
                ),
                variant=action_template.get("variant", "primary"),
                completed=False,
            )
            actions.append(action)
        
        # Calculate expiration (7 days for critical, 14 for important, 30 for suggestions)
        expires_days = {"critical": 7, "important": 14, "suggestion": 30}
        expires_at = datetime.now() + timedelta(days=expires_days.get(priority, 14))
        
        return CoachRecommendation(
            id=rec_id,
            priority=RecommendationPriority(priority),
            title=title,
            description=description,
            reasoning=reasoning,
            actions=actions,
            dismissible=True,
            dismissed=False,
            expiresAt=expires_at,
            metadata={
                "template_trigger": template.trigger.value,
                "category": template.category.value,
            },
        )
    
    async def _generate_simplified(
        self,
        health_score: int,
        health_breakdown: Dict[str, Any],
        connector_data: Dict[str, Any],
    ) -> List[CoachRecommendation]:
        """Generate simplified recommendations (fallback)"""
        recommendations = []
        
        # Critical: Cash flow issues
        if health_score < 60:
            recommendations.append(self._create_cash_flow_recommendation(connector_data))
        
        # Important: Inventory issues
        if health_breakdown.get("operations", 100) < 70:
            recommendations.append(self._create_inventory_recommendation(connector_data))
        
        # Suggestion: Growth opportunities
        if health_breakdown.get("revenue", 100) > 75:
            recommendations.append(self._create_growth_recommendation(connector_data))
        
        return recommendations
    
    def _create_cash_flow_recommendation(self, data: Dict[str, Any]) -> CoachRecommendation:
        """Generate cash flow recommendation"""
        return CoachRecommendation(
            id=f"rec_{random.randint(1000, 9999)}",
            priority=RecommendationPriority.CRITICAL,
            title="Review cash flow projection",
            description="Your business is projected to have negative cash flow in 2 weeks.",
            reasoning="Based on current burn rate and outstanding receivables.",
            actions=[
                RecommendationAction(
                    id="action_1",
                    label="Call customers with overdue invoices",
                    description="Prioritize the invoices over 30 days",
                    buttonText="View Invoices",
                ),
                RecommendationAction(
                    id="action_2",
                    label="Delay non-essential expenses",
                    description="Postpone planned equipment purchases",
                    buttonText="Review Expenses",
                    variant="secondary",
                ),
            ],
            dismissible=True,
            dismissed=False,
            expiresAt=datetime.now() + timedelta(days=7),
        )
    
    def _create_inventory_recommendation(self, data: Dict[str, Any]) -> CoachRecommendation:
        """Generate inventory recommendation"""
        return CoachRecommendation(
            id=f"rec_{random.randint(1000, 9999)}",
            priority=RecommendationPriority.IMPORTANT,
            title="Inventory aging alert",
            description="18 items have been in stock for 90+ days.",
            reasoning="Slow-moving inventory is tying up working capital.",
            actions=[
                RecommendationAction(
                    id="action_1",
                    label="Run clearance promotion",
                    description="15% discount on aging items to free up cash",
                    buttonText="Create Promotion",
                ),
            ],
            dismissible=True,
            dismissed=False,
            expiresAt=datetime.now() + timedelta(days=14),
        )
    
    def _create_growth_recommendation(self, data: Dict[str, Any]) -> CoachRecommendation:
        """Generate growth recommendation"""
        return CoachRecommendation(
            id=f"rec_{random.randint(1000, 9999)}",
            priority=RecommendationPriority.SUGGESTION,
            title="Consider hiring part-time help",
            description="Your workload is 15% above optimal capacity.",
            reasoning="Task completion rate has dropped over the past 3 weeks.",
            actions=[
                RecommendationAction(
                    id="action_1",
                    label="Post job listing",
                    description="10-15 hours/week to handle order fulfillment",
                    buttonText="Draft Listing",
                ),
            ],
            dismissible=True,
            dismissed=False,
            expiresAt=datetime.now() + timedelta(days=30),
        )
    
    async def get_alerts(self, health_score: int, health_breakdown: Dict[str, Any]) -> List[Alert]:
        """Generate critical alerts for health score header"""
        alerts = []
        
        if health_score < 60:
            alerts.append(Alert(
                id="alert_1",
                type="critical",
                title="Cash flow projected negative in 14 days",
                description="Without intervention, bank balance will drop below $5,000",
                metric="cash_flow",
                value=-2400,
                threshold=0,
            ))
        
        if health_breakdown.get("operations", 100) < 70:
            alerts.append(Alert(
                id="alert_2",
                type="warning",
                title="3 invoices overdue by 30+ days",
                description="$12,450 in outstanding receivables",
                metric="receivables",
                value=12450,
                threshold=30,
            ))
        
        return alerts
    
    async def get_signals(self, health_score: int, health_breakdown: Dict[str, Any]) -> List[Signal]:
        """Generate positive signals for health score header"""
        signals = []
        
        if health_breakdown.get("revenue", 0) > 70:
            signals.append(Signal(
                id="signal_1",
                type="positive",
                title="Revenue up 12% vs. last month",
                description="$45,200 total revenue",
                metric="revenue",
                value=45200,
            ))
        
        if health_score > 75:
            signals.append(Signal(
                id="signal_2",
                type="positive",
                title="On track to hit Q1 sales goal",
                description="78% complete with 3 weeks remaining",
                metric="sales",
                value=78,
            ))
        
        return signals
    
    async def get_metrics_snapshot(self, connector_data: Dict[str, Any]) -> List[MetricSnapshot]:
        """Generate metrics snapshot for metrics grid"""
        # This would normally calculate from real connector data
        return [
            MetricSnapshot(
                id="metric_1",
                label="Revenue (MTD)",
                value="$45,200",
                change=12,
                changeType="percentage",
                trend="up",
                period="vs. last month",
                sparklineData=[32000, 35000, 38000, 42000, 45200],
            ),
            MetricSnapshot(
                id="metric_2",
                label="Cash Balance",
                value="$18,450",
                change=-8,
                changeType="percentage",
                trend="down",
                period="vs. last week",
                sparklineData=[22000, 21000, 20000, 19000, 18450],
            ),
            MetricSnapshot(
                id="metric_3",
                label="Gross Margin",
                value="42%",
                change=2,
                changeType="percentage",
                trend="up",
                period="vs. last quarter",
                sparklineData=[38, 39, 40, 41, 42],
            ),
            MetricSnapshot(
                id="metric_4",
                label="Active Orders",
                value="23",
                change=5,
                changeType="absolute",
                trend="up",
                period="vs. yesterday",
                sparklineData=[15, 18, 20, 18, 23],
            ),
        ]


def get_recommendations_service(tenant_id: str, persistence_backend=None) -> CoachRecommendationsService:
    """Factory function for recommendations service"""
    return CoachRecommendationsService(tenant_id, persistence_backend)
