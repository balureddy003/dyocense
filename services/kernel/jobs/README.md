# Daily Insights Background Job

Automated job that runs daily at 6am local time per tenant to generate business health insights and AI recommendations.

## Overview

The Daily Insights Job performs the following steps:

1. **Fetch Data** - Retrieve latest business data from connectors (Xero, QuickBooks, etc.)
2. **Calculate Health** - Compute health score (0-100) and breakdown by category
3. **Generate Recommendations** - Use AI template system to create actionable recommendations
4. **Store Insights** - Persist results to PostgreSQL for historical analysis
5. **Trigger Alerts** - Send critical recommendations via WebSocket notifications

## Architecture

```
services/kernel/jobs/
├── daily_insights.py       # Main job implementation
├── __init__.py             # Package exports
└── README.md              # This file
```

## Components

### DailyInsightsJob

Main job class that orchestrates the daily insights generation:

```python
from services.kernel.jobs import create_daily_insights_job

job = create_daily_insights_job(
    recommendations_service_factory=lambda tid: get_recommendations_service(tid),
    connector_service=connector_service,
    notification_service=notification_service,
    persistence_backend=db,
)

# Run for single tenant
result = await job.run_for_tenant("tenant-123")

# Run for all tenants
results = await job.run_for_all_tenants()
```

### Health Score Calculation

Weighted scoring across 4 categories:

1. **Cash Flow (35%)** - Days of runway, burn rate
2. **Operations (25%)** - Days Sales Outstanding, process efficiency
3. **Revenue (25%)** - Growth trends, YoY comparison
4. **Profitability (15%)** - Net margin, gross margin

Formula:

```
overall_score = (
    cash_flow_score * 0.35 +
    operations_score * 0.25 +
    revenue_score * 0.25 +
    profitability_score * 0.15
)
```

### Scoring Heuristics

**Cash Flow Score:**

- 90+ days runway: 100
- 60-90 days: 85
- 30-60 days: 70
- 14-30 days: 50
- <14 days: 30 (critical)

**Operations Score (DSO):**

- <30 days: 100
- 30-45 days: 80
- 45-60 days: 60
- >60 days: 40

**Revenue Score (Growth):**
>
- >15% growth: 100
- 5-15%: 85
- 0-5%: 75
- 0 to -5%: 60
- -5 to -10%: 45
- <-10%: 30

**Profitability Score (Net Margin):**
>
- >20%: 100
- 10-20%: 85
- 5-10%: 70
- 0-5%: 55
- Negative: 35

## Scheduler Integration

### Option 1: APScheduler (Recommended for MVP)

Simple, in-process scheduler that doesn't require additional infrastructure:

```python
from services.kernel.jobs import create_daily_insights_job, create_apscheduler_integration

# Create job
insights_job = create_daily_insights_job(
    recommendations_service_factory=lambda tid: get_recommendations_service(tid),
    connector_service=connector_service,
    notification_service=notification_service,
    persistence_backend=db,
)

# Setup scheduler
scheduler_integration = create_apscheduler_integration(insights_job)
scheduler_integration.setup_scheduler()
scheduler_integration.start()

# In shutdown handler
scheduler_integration.shutdown()
```

**Add to `services/kernel/main.py`:**

```python
from contextlib import asynccontextmanager
from services.kernel.jobs import create_daily_insights_job, create_apscheduler_integration

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    insights_job = create_daily_insights_job(...)
    scheduler = create_apscheduler_integration(insights_job)
    scheduler.setup_scheduler()
    scheduler.start()
    
    yield
    
    # Shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

### Option 2: Celery Beat (For Production Scale)

Distributed task queue with Redis backend:

**1. Install dependencies:**

```bash
pip install celery redis
```

**2. Create `services/kernel/celery.py`:**

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('kernel', broker='redis://localhost:6379/0')

app.conf.beat_schedule = {
    'daily-insights-6am': {
        'task': 'services.kernel.tasks.run_daily_insights',
        'schedule': crontab(hour=6, minute=0),
    },
}
```

**3. Create `services/kernel/tasks.py`:**

```python
from services.kernel.celery import app
from services.kernel.jobs import create_daily_insights_job

@app.task
def run_daily_insights():
    job = create_daily_insights_job(...)
    asyncio.run(job.run_for_all_tenants())
```

**4. Run Celery worker and beat:**

```bash
celery -A services.kernel.celery worker --loglevel=info
celery -A services.kernel.celery beat --loglevel=info
```

### Option 3: Temporal (Enterprise)

Durable workflow orchestration with visibility:

```python
import temporalio
from temporalio import workflow, activity

@workflow.defn
class DailyInsightsWorkflow:
    @workflow.run
    async def run(self, tenant_id: str) -> dict:
        result = await workflow.execute_activity(
            generate_insights,
            tenant_id,
            start_to_close_timeout=timedelta(minutes=10),
        )
        return result

@activity.defn
async def generate_insights(tenant_id: str) -> dict:
    job = create_daily_insights_job(...)
    return await job.run_for_tenant(tenant_id)
```

## Tenant Timezone Handling

For multi-timezone support, schedule per tenant's local time:

```python
from zoneinfo import ZoneInfo
from datetime import datetime, time

async def schedule_tenant_insights():
    """Schedule insights based on tenant timezone"""
    tenants = await get_active_tenants()
    
    for tenant in tenants:
        # Get tenant's local timezone
        tz = ZoneInfo(tenant['timezone'])  # e.g., "America/New_York"
        
        # Calculate when 6am local = now UTC
        local_6am = datetime.now(tz).replace(hour=6, minute=0, second=0)
        utc_time = local_6am.astimezone(ZoneInfo("UTC"))
        
        # Schedule at this UTC time
        scheduler.add_job(
            job.run_for_tenant,
            args=[tenant['id']],
            trigger=CronTrigger(
                hour=utc_time.hour,
                minute=utc_time.minute,
            ),
        )
```

## Database Schema

### Insights Table

```sql
CREATE TABLE coach_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    health_score INT NOT NULL,
    health_breakdown JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    connector_data_snapshot JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_tenant_generated (tenant_id, generated_at DESC)
);
```

### Historical Tracking

Store daily insights for trend analysis:

```python
# Get last 30 days of insights
insights = await db.fetch_all(
    "SELECT * FROM coach_insights "
    "WHERE tenant_id = $1 AND generated_at >= NOW() - INTERVAL '30 days' "
    "ORDER BY generated_at DESC",
    [tenant_id]
)

# Calculate trends
health_scores = [i['health_score'] for i in insights]
avg_score = sum(health_scores) / len(health_scores)
trend = "improving" if health_scores[0] > health_scores[-1] else "declining"
```

## WebSocket Notification Integration

Critical alerts are sent via WebSocket to connected clients:

```python
# In daily_insights.py
await notification_service.send_notification(
    tenant_id=tenant_id,
    notification={
        "type": "coach_alert",
        "priority": "critical",
        "title": "Cash flow alert",
        "message": "Projected negative in 12 days",
        "recommendation_id": "rec_1234",
        "timestamp": datetime.now().isoformat(),
    }
)
```

**Frontend receives:**

```typescript
// In WebSocket handler
socket.on('notification', (notification) => {
  if (notification.type === 'coach_alert') {
    // Show toast
    showNotification({
      title: notification.title,
      message: notification.message,
      color: notification.priority === 'critical' ? 'red' : 'yellow',
    });
    
    // Add to notification drawer
    addNotification(notification);
  }
});
```

## Manual Execution (Testing)

Run insights manually for testing:

```bash
# Run for all tenants
python -m services.kernel.jobs.daily_insights

# Run for specific tenant
python -m services.kernel.jobs.daily_insights tenant-123
```

Or via Python:

```python
from services.kernel.jobs.daily_insights import run_manual_insights
import asyncio

asyncio.run(run_manual_insights("tenant-123"))
```

## Monitoring & Logging

The job logs key events:

```
INFO: Starting daily insights job for tenant: tenant-123
INFO: Stored insights: insights_tenant-123_1234567890
INFO: Sent 2 critical alerts for tenant tenant-123
INFO: Daily insights completed: health_score=65, recommendations=4
```

### Metrics to Track

- Job execution time per tenant
- Success/failure rate
- Number of recommendations generated
- Critical alerts sent
- Health score distribution

```python
# Add to job
import time

start = time.time()
result = await job.run_for_tenant(tenant_id)
duration = time.time() - start

logger.info(f"Job duration: {duration:.2f}s")
```

## Error Handling

The job handles failures gracefully:

1. **Connector Failure** - Falls back to mock data, logs warning
2. **Recommendation Generation Failure** - Returns empty list, continues
3. **Notification Failure** - Logs error, doesn't block insights storage
4. **Per-Tenant Isolation** - One tenant's failure doesn't affect others

```python
try:
    result = await job.run_for_tenant(tenant_id)
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
    # Continue with other tenants
```

## Configuration

Environment variables:

```bash
# Scheduler type (apscheduler, celery, temporal)
INSIGHTS_SCHEDULER=apscheduler

# Job execution time (hour in UTC)
INSIGHTS_HOUR=6

# Enable/disable job
INSIGHTS_ENABLED=true

# Notification settings
INSIGHTS_SEND_ALERTS=true
INSIGHTS_CRITICAL_ONLY=true
```

## Scaling Considerations

### Single Instance

- APScheduler in-process
- Good for <100 tenants
- Simple deployment

### Distributed

- Celery with Redis
- Horizontal scaling
- Good for 100-10,000 tenants

### Enterprise

- Temporal workflows
- Durable execution
- Good for >10,000 tenants
- Full observability

## Future Enhancements

1. **Adaptive Scheduling** - Adjust run time based on business hours
2. **Incremental Updates** - Run more frequently with delta updates
3. **Predictive Alerts** - Use ML to predict issues before they happen
4. **Trend Reports** - Weekly/monthly rollup emails
5. **Custom Schedules** - Per-tenant schedule configuration
6. **Historical Comparison** - "This time last year" insights

## Dependencies

```python
# Required
pydantic>=2.0.0
asyncio

# Optional (based on scheduler)
APScheduler>=3.10.0  # For apscheduler
celery>=5.3.0        # For celery
redis>=5.0.0         # For celery
temporal-sdk         # For temporal
```

Install:

```bash
pip install apscheduler  # For APScheduler integration
```

## Testing

Unit tests:

```python
import pytest
from services.kernel.jobs import DailyInsightsJob

@pytest.mark.asyncio
async def test_run_for_tenant():
    job = create_daily_insights_job(...)
    result = await job.run_for_tenant("tenant-test")
    
    assert result['success'] == True
    assert result['health_score'] > 0
    assert result['recommendations_count'] >= 0
```

Integration tests:

```bash
# Run with test tenant
python -m services.kernel.jobs.daily_insights tenant-test
```

## License

Part of Dyocense platform - Internal use only
