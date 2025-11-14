# Observability Stack - Metrics Guide

## Custom Metrics Added (Week 3)

### Evidence Engine Metrics

**Correlation Analysis:**

- `evidence_correlations_total{tenant_id, num_series}` - Total analyses
- `evidence_correlation_duration_seconds{num_series}` - Latency histogram
- `evidence_correlation_strength` - Coefficient distribution

**What-If Analysis:**

- `evidence_whatif_total{tenant_id}` - Total analyses  
- `evidence_whatif_duration_seconds` - Latency histogram
- `evidence_model_r2` - Model quality (R²) distribution

**Driver Inference:**

- `evidence_drivers_total{tenant_id, num_drivers}` - Total operations
- `evidence_drivers_duration_seconds{num_drivers}` - Latency histogram

**Granger Causality:**

- `evidence_granger_total{tenant_id}` - Total tests
- `evidence_granger_duration_seconds` - Latency histogram

### Authentication Metrics

- `auth_login_attempts_total{tenant_id, status}` - Login attempts (status: success, invalid_credentials, user_not_found, account_disabled)
- `auth_login_duration_seconds` - Login latency histogram
- `auth_token_validations_total{status}` - JWT validations
- `auth_active_sessions` - Current active sessions

### Tenant Activity Metrics

- `tenant_api_requests_total{tenant_id, endpoint, method, status_code}` - API requests
- `tenant_api_duration_seconds{tenant_id, endpoint}` - API latency
- `tenant_database_queries_total{tenant_id, query_type}` - DB queries
- `tenant_users_total{tenant_id}` - User count per tenant
- `tenant_workspaces_total{tenant_id}` - Workspace count per tenant

## Grafana Dashboards

### Evidence Engine Analytics

**Path:** `infra/grafana/dashboards/evidence-engine.json`

Panels:

- Correlation analyses rate and latency (p50, p95)
- What-if model quality (R² distribution)
- Driver inference operations
- Granger causality tests
- Correlation coefficient heatmap

### Authentication & Security  

**Path:** `infra/grafana/dashboards/auth-security.json`

Panels:

- Login attempts by status (success/failure split)
- Login success rate by tenant
- Authentication latency (p50, p95, p99)
- Failed login alerts (potential attacks)
- Hourly stats (total, success rate, failures)

## Example Prometheus Queries

### Evidence Engine Performance

```promql
# Top tenants by evidence operations
topk(10, sum by (tenant_id) (
  rate(evidence_correlations_total[5m]) + 
  rate(evidence_whatif_total[5m]) + 
  rate(evidence_drivers_total[5m])
))

# Average correlation latency by number of series
avg by (num_series) (
  rate(evidence_correlation_duration_seconds_sum[5m]) / 
  rate(evidence_correlation_duration_seconds_count[5m])
)

# Model quality trend (p95 R²)
histogram_quantile(0.95, rate(evidence_model_r2_bucket[5m]))
```

### Authentication Monitoring

```promql
# Login success rate
sum(rate(auth_login_attempts_total{status="success"}[5m])) / 
sum(rate(auth_login_attempts_total[5m])) * 100

# Failed login spike detection (potential attacks)
sum by (tenant_id) (
  rate(auth_login_attempts_total{status!="success"}[5m])
) > 5

# p95 login latency
histogram_quantile(0.95, rate(auth_login_duration_seconds_bucket[5m]))
```

## Testing Metrics

```bash
# Verify metrics endpoint
curl http://localhost:8001/metrics | grep -E "(evidence|auth)_"

# Run all tests with metrics enabled
pytest tests/test_evidence*.py tests/test_metrics.py -v

# Check metrics in Python
python -c "
from backend.utils.metrics import METRICS_ENABLED
from prometheus_client import REGISTRY
print(f'Metrics enabled: {METRICS_ENABLED}')
print(f'Collectors: {len(list(REGISTRY._collector_to_names.keys()))}')
"
```

## Implementation Details

**Metrics Module:** `backend/utils/metrics.py`

- All custom metrics defined
- Helper functions for recording
- Graceful degradation if prometheus_client not installed

**Instrumented Routes:**

- `backend/routes/evidence.py` - All evidence endpoints
- `backend/routes/auth.py` - Login endpoint

**Main Integration:** `backend/main.py`

- Metrics endpoint mounted at `/metrics`
- setup_metrics() called on startup

## Next Steps

1. ✅ Metrics instrumentation complete
2. ⏳ Start observability stack: `docker-compose -f docker-compose.external.yml --profile monitoring up -d`
3. ⏳ Access Grafana at <http://localhost:3001>
4. ⏳ Import dashboards from `infra/grafana/dashboards/`
5. ⏳ Configure Loki for log aggregation
6. ⏳ Setup alerts in Prometheus
