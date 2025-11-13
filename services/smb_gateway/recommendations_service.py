"""
Coach Recommendations Service for Coach V6

Generates proactive AI recommendations based on business health data.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import random


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
    
    def __init__(self, tenant_id: str, persistence_backend=None):
        self.tenant_id = tenant_id
        self.backend = persistence_backend
    
    async def generate_recommendations(
        self,
        health_score: int,
        health_breakdown: Dict[str, Any],
        connector_data: Dict[str, Any],
    ) -> List[CoachRecommendation]:
        """
        Generate AI recommendations based on health score and data.
        
        This is a simplified implementation. Full version would use GPT-4
        with templates for different scenarios.
        """
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
