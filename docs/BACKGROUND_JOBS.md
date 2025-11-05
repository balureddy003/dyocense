# Background Jobs

The accounts service includes automated background jobs that run periodically without requiring external cron or task schedulers.

## Trial Enforcement Job

**Purpose:** Automatically downgrade silver trial tenants to free plan after 14 days.

**Schedule:** Runs every 24 hours

**What it does:**
1. Finds all tenants with:
   - `plan_tier: silver`
   - `status: trial`
   - `created_at` older than 14 days
2. Downgrades each tenant to free plan
3. Updates status to `active`
4. Logs results

**Configuration:**
- Trial period: 14 days (hardcoded, can be made configurable)
- Check interval: 24 hours (86400 seconds)

**Monitoring:**
- Health check: `GET /health` shows background job status
- Manual trigger: `POST /v1/trial/enforce-all` (admin only)
- Logs: Search for "Trial enforcement" in service logs

## How It Works

The background jobs use FastAPI's lifespan context manager and Python's asyncio:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create background task
    background_task = asyncio.create_task(trial_enforcement_job())
    yield
    # Shutdown: cancel task gracefully
    background_task.cancel()
```

**Benefits:**
- No external dependencies (no Redis, Celery, or cron needed)
- Runs in same process as API
- Automatic cleanup on service shutdown
- Simple to test and monitor

## Testing

### Check health endpoint:
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "accounts",
  "background_jobs": {
    "trial_enforcement": {
      "running": true,
      "enabled": true,
      "interval": "24 hours"
    }
  }
}
```

### Manual trial enforcement (admin only):
```bash
curl -X POST http://localhost:8001/v1/trial/enforce-all \
  -H "Authorization: Bearer <admin-token>"
```

### Test script:
```bash
python scripts/test_background_jobs.py
```

## Deployment Considerations

**Docker/Kubernetes:**
- Background jobs run automatically when the service starts
- Use `livenessProbe` pointing to `/health` endpoint
- Ensure only one replica runs trial enforcement (or make it idempotent)

**Scaling:**
- If running multiple replicas, consider:
  - Using a distributed lock (Redis) for trial enforcement
  - Or running trial enforcement in a separate singleton deployment
  - Or accepting duplicate checks (the enforce function is idempotent)

**Monitoring:**
- Set up alerts on `/health` endpoint
- Track trial enforcement logs
- Monitor MongoDB for trial status changes

## Future Enhancements

1. **Configurable intervals** - Environment variable for check frequency
2. **Email notifications** - Alert tenants before/after trial expiration
3. **Grace periods** - N-day warning before downgrade
4. **Multiple jobs** - Add more background tasks (cleanup, analytics, etc.)
5. **Admin dashboard** - Real-time view of background job status
6. **Distributed locks** - Prevent concurrent execution across replicas
