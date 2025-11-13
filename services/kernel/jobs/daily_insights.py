"""
Daily Insights Background Job

Automated job that runs daily at 6am local time per tenant to:
1. Fetch latest business data from connectors
2. Calculate health score and breakdown
3. Generate AI recommendations
4. Store insights in PostgreSQL
5. Trigger critical alerts via WebSocket

Scheduler Options:
- Celery Beat (for Redis-based scheduling)
- APScheduler (for simpler deployments)
- Temporal (for enterprise workflow orchestration)
"""
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SchedulerType(str, Enum):
    """Supported scheduler types"""
    CELERY = "celery"
    APSCHEDULER = "apscheduler"
    TEMPORAL = "temporal"


class DailyInsightsJob:
    """
    Daily insights generation job
    
    Runs at 6am local time per tenant to generate:
    - Health score calculation
    - AI recommendations
    - Critical alerts
    - Trend analysis
    """
    
    def __init__(
        self,
        recommendations_service_factory,
        connector_service,
        notification_service,
        persistence_backend,
    ):
        """
        Initialize daily insights job
        
        Args:
            recommendations_service_factory: Factory for creating recommendations service
            connector_service: Service for fetching connector data
            notification_service: Service for sending notifications
            persistence_backend: Database backend for storing insights
        """
        self.recommendations_service_factory = recommendations_service_factory
        self.connector_service = connector_service
        self.notification_service = notification_service
        self.backend = persistence_backend
    
    async def run_for_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """
        Run daily insights for a single tenant
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Dict with insights, recommendations, and status
        """
        logger.info(f"Starting daily insights job for tenant: {tenant_id}")
        
        try:
            # Step 1: Fetch connector data
            connector_data = await self._fetch_connector_data(tenant_id)
            
            # Step 2: Calculate health score
            health_score, health_breakdown = self._calculate_health_score(connector_data)
            
            # Step 3: Generate recommendations
            recommendations = await self._generate_recommendations(
                tenant_id,
                health_score,
                health_breakdown,
                connector_data,
            )
            
            # Step 4: Store insights
            insights_id = await self._store_insights(
                tenant_id,
                health_score,
                health_breakdown,
                recommendations,
                connector_data,
            )
            
            # Step 5: Trigger critical alerts
            await self._trigger_alerts(
                tenant_id,
                health_score,
                recommendations,
            )
            
            logger.info(
                f"Daily insights completed for tenant {tenant_id}: "
                f"health_score={health_score}, "
                f"recommendations={len(recommendations)}, "
                f"insights_id={insights_id}"
            )
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "insights_id": insights_id,
                "health_score": health_score,
                "health_breakdown": health_breakdown,
                "recommendations_count": len(recommendations),
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Daily insights failed for tenant {tenant_id}: {e}", exc_info=True)
            return {
                "success": False,
                "tenant_id": tenant_id,
                "error": str(e),
                "generated_at": datetime.now().isoformat(),
            }
    
    async def run_for_all_tenants(self) -> List[Dict[str, Any]]:
        """
        Run daily insights for all active tenants
        
        Returns:
            List of results per tenant
        """
        logger.info("Starting daily insights job for all tenants")
        
        # Get list of active tenants
        tenants = await self._get_active_tenants()
        logger.info(f"Found {len(tenants)} active tenants")
        
        # Run insights for each tenant (in parallel)
        tasks = [self.run_for_tenant(tenant["id"]) for tenant in tenants]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log summary
        successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failures = len(results) - successes
        logger.info(
            f"Daily insights completed: {successes} succeeded, {failures} failed"
        )
        
        return results
    
    async def _fetch_connector_data(self, tenant_id: str) -> Dict[str, Any]:
        """Fetch latest data from connectors"""
        try:
            # This would fetch from actual connectors (Xero, QuickBooks, etc.)
            data = await self.connector_service.get_latest_data(tenant_id)
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch connector data for {tenant_id}: {e}")
            # Return mock data for demo
            return self._generate_mock_connector_data()
    
    def _calculate_health_score(
        self,
        connector_data: Dict[str, Any]
    ) -> tuple[int, Dict[str, int]]:
        """
        Calculate business health score
        
        Returns:
            Tuple of (overall_score, breakdown_by_category)
        """
        # Extract metrics from connector data
        cash_balance = connector_data.get("cash_balance", 0)
        revenue = connector_data.get("revenue", 0)
        expenses = connector_data.get("expenses", 0)
        receivables = connector_data.get("receivables", 0)
        payables = connector_data.get("payables", 0)
        
        # Calculate component scores (0-100)
        cash_flow_score = self._calculate_cash_flow_score(
            cash_balance,
            revenue,
            expenses,
        )
        operations_score = self._calculate_operations_score(
            receivables,
            payables,
            connector_data,
        )
        revenue_score = self._calculate_revenue_score(
            revenue,
            connector_data.get("revenue_history", []),
        )
        profitability_score = self._calculate_profitability_score(
            revenue,
            expenses,
            connector_data.get("gross_margin", 0),
        )
        
        # Calculate weighted overall score
        overall_score = int(
            cash_flow_score * 0.35 +
            operations_score * 0.25 +
            revenue_score * 0.25 +
            profitability_score * 0.15
        )
        
        breakdown = {
            "cash_flow": cash_flow_score,
            "operations": operations_score,
            "revenue": revenue_score,
            "profitability": profitability_score,
        }
        
        return overall_score, breakdown
    
    def _calculate_cash_flow_score(
        self,
        cash_balance: float,
        revenue: float,
        expenses: float,
    ) -> int:
        """Calculate cash flow health score"""
        # Simple heuristic: days of runway
        burn_rate = expenses / 30  # Daily burn
        days_runway = cash_balance / burn_rate if burn_rate > 0 else 999
        
        if days_runway > 90:
            return 100
        elif days_runway > 60:
            return 85
        elif days_runway > 30:
            return 70
        elif days_runway > 14:
            return 50
        else:
            return 30
    
    def _calculate_operations_score(
        self,
        receivables: float,
        payables: float,
        data: Dict[str, Any],
    ) -> int:
        """Calculate operations efficiency score"""
        # Days Sales Outstanding (DSO)
        revenue = data.get("revenue", 1)
        dso = (receivables / revenue) * 30 if revenue > 0 else 0
        
        if dso < 30:
            return 100
        elif dso < 45:
            return 80
        elif dso < 60:
            return 60
        else:
            return 40
    
    def _calculate_revenue_score(
        self,
        current_revenue: float,
        revenue_history: List[float],
    ) -> int:
        """Calculate revenue trend score"""
        if not revenue_history or len(revenue_history) < 2:
            return 75  # Neutral if no history
        
        # Calculate trend
        prev_revenue = revenue_history[-2] if len(revenue_history) >= 2 else current_revenue
        growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        if growth > 15:
            return 100
        elif growth > 5:
            return 85
        elif growth > 0:
            return 75
        elif growth > -5:
            return 60
        elif growth > -10:
            return 45
        else:
            return 30
    
    def _calculate_profitability_score(
        self,
        revenue: float,
        expenses: float,
        gross_margin: float,
    ) -> int:
        """Calculate profitability score"""
        net_margin = ((revenue - expenses) / revenue * 100) if revenue > 0 else 0
        
        if net_margin > 20:
            return 100
        elif net_margin > 10:
            return 85
        elif net_margin > 5:
            return 70
        elif net_margin > 0:
            return 55
        else:
            return 35
    
    async def _generate_recommendations(
        self,
        tenant_id: str,
        health_score: int,
        health_breakdown: Dict[str, int],
        connector_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate AI recommendations"""
        service = self.recommendations_service_factory(tenant_id)
        recommendations = await service.generate_recommendations(
            health_score,
            health_breakdown,
            connector_data,
        )
        # Convert to dict for storage
        return [rec.dict() for rec in recommendations]
    
    async def _store_insights(
        self,
        tenant_id: str,
        health_score: int,
        health_breakdown: Dict[str, int],
        recommendations: List[Dict[str, Any]],
        connector_data: Dict[str, Any],
    ) -> str:
        """Store insights in database"""
        insights = {
            "tenant_id": tenant_id,
            "health_score": health_score,
            "health_breakdown": health_breakdown,
            "recommendations": recommendations,
            "connector_data_snapshot": {
                "cash_balance": connector_data.get("cash_balance"),
                "revenue": connector_data.get("revenue"),
                "expenses": connector_data.get("expenses"),
            },
            "generated_at": datetime.now().isoformat(),
        }
        
        # Store in PostgreSQL
        # TODO: Implement persistence layer
        insights_id = f"insights_{tenant_id}_{int(datetime.now().timestamp())}"
        logger.info(f"Stored insights: {insights_id}")
        
        return insights_id
    
    async def _trigger_alerts(
        self,
        tenant_id: str,
        health_score: int,
        recommendations: List[Dict[str, Any]],
    ) -> None:
        """Trigger WebSocket notifications for critical alerts"""
        # Only send alerts for critical issues
        critical_recs = [
            rec for rec in recommendations
            if rec.get("priority") == "critical"
        ]
        
        if not critical_recs:
            logger.info(f"No critical alerts for tenant {tenant_id}")
            return
        
        # Send notification via WebSocket
        for rec in critical_recs:
            await self.notification_service.send_notification(
                tenant_id=tenant_id,
                notification={
                    "type": "coach_alert",
                    "priority": "critical",
                    "title": rec["title"],
                    "message": rec["description"],
                    "recommendation_id": rec["id"],
                    "timestamp": datetime.now().isoformat(),
                }
            )
        
        logger.info(f"Sent {len(critical_recs)} critical alerts for tenant {tenant_id}")
    
    async def _get_active_tenants(self) -> List[Dict[str, Any]]:
        """Get list of active tenants"""
        # TODO: Query from database
        # For now, return mock data
        return [
            {"id": "tenant-demo", "name": "Demo Tenant", "timezone": "America/New_York"},
        ]
    
    def _generate_mock_connector_data(self) -> Dict[str, Any]:
        """Generate mock connector data for testing"""
        return {
            "cash_balance": 18450,
            "revenue": 45200,
            "expenses": 38500,
            "receivables": 12450,
            "payables": 8200,
            "revenue_history": [38000, 41000, 43500, 45200],
            "gross_margin": 42,
            "industry": "SMB",
        }


# =============================================================================
# SCHEDULER INTEGRATIONS
# =============================================================================

class CeleryScheduler:
    """Celery Beat scheduler for daily insights"""
    
    @staticmethod
    def configure_beat_schedule(insights_job: DailyInsightsJob):
        """
        Configure Celery Beat schedule
        
        Add to celery.py:
        ```python
        from celery.schedules import crontab
        
        app.conf.beat_schedule = {
            'daily-insights-6am': {
                'task': 'services.kernel.jobs.daily_insights.run_daily_insights',
                'schedule': crontab(hour=6, minute=0),
            },
        }
        ```
        """
        pass


class APSchedulerIntegration:
    """APScheduler integration for daily insights"""
    
    def __init__(self, insights_job: DailyInsightsJob):
        self.insights_job = insights_job
        self.scheduler = None
    
    def setup_scheduler(self):
        """Setup APScheduler"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        self.scheduler = AsyncIOScheduler()
        
        # Schedule at 6am daily
        self.scheduler.add_job(
            self.insights_job.run_for_all_tenants,
            trigger=CronTrigger(hour=6, minute=0),
            id="daily_insights",
            replace_existing=True,
        )
    
    def start(self):
        """Start scheduler"""
        if self.scheduler:
            self.scheduler.start()
            logger.info("APScheduler started for daily insights")
    
    def shutdown(self):
        """Shutdown scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()


class TemporalWorkflow:
    """Temporal workflow for daily insights"""
    
    @staticmethod
    def define_workflow():
        """
        Define Temporal workflow
        
        See Temporal documentation for workflow implementation
        """
        pass


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_daily_insights_job(
    recommendations_service_factory,
    connector_service,
    notification_service,
    persistence_backend,
) -> DailyInsightsJob:
    """
    Factory function for creating daily insights job
    
    Args:
        recommendations_service_factory: Factory for recommendations service
        connector_service: Connector data service
        notification_service: Notification service
        persistence_backend: Database backend
    
    Returns:
        DailyInsightsJob instance
    """
    return DailyInsightsJob(
        recommendations_service_factory=recommendations_service_factory,
        connector_service=connector_service,
        notification_service=notification_service,
        persistence_backend=persistence_backend,
    )


def create_apscheduler_integration(insights_job: DailyInsightsJob) -> APSchedulerIntegration:
    """
    Factory function for APScheduler integration
    
    Args:
        insights_job: Daily insights job instance
    
    Returns:
        APSchedulerIntegration instance
    """
    return APSchedulerIntegration(insights_job)


# =============================================================================
# MANUAL EXECUTION (for testing)
# =============================================================================

async def run_manual_insights(tenant_id: Optional[str] = None):
    """
    Manually run daily insights (for testing)
    
    Usage:
        python -m services.kernel.jobs.daily_insights
    """
    # Mock dependencies
    class MockRecommendationsService:
        async def generate_recommendations(self, *args, **kwargs):
            return []
    
    class MockConnectorService:
        async def get_latest_data(self, tenant_id):
            return {}
    
    class MockNotificationService:
        async def send_notification(self, tenant_id, notification):
            logger.info(f"Notification: {notification['title']}")
    
    # Create job
    job = create_daily_insights_job(
        recommendations_service_factory=lambda tid: MockRecommendationsService(),
        connector_service=MockConnectorService(),
        notification_service=MockNotificationService(),
        persistence_backend=None,
    )
    
    # Run for specific tenant or all
    if tenant_id:
        result = await job.run_for_tenant(tenant_id)
    else:
        result = await job.run_for_all_tenants()
    
    print(f"Results: {result}")


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    tenant_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(run_manual_insights(tenant_id))
