# 📊 Observability Architecture

**Version:** 4.0 (Prometheus + Grafana Stack)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Distributed Tracing](#2-distributed-tracing)
3. [Metrics Collection](#3-metrics-collection)
4. [Structured Logging](#4-structured-logging)
5. [Alerting](#5-alerting)
6. [Cost Comparison](#6-cost-comparison)

---

## 🎯 1. Overview

### **Observability Pillars**

> **"You can't improve what you don't measure"**

**Three Pillars:**

1. **🔍 Traces** → Request flow through system (OpenTelemetry + Jaeger)
2. **📈 Metrics** → System health and business KPIs (Prometheus + Grafana)
3. **📝 Logs** → Event records for debugging (JSON logs + Loki)

---

### **Open Source vs. SaaS**

| Tool | Type | Cost (v3.0) | Cost (v4.0) | Savings |
|------|------|-------------|-------------|---------|
| **Datadog** | SaaS | $500/mo | ❌ Removed | **$6K/year** |
| **New Relic** | SaaS | $300/mo | ❌ Removed | **$3.6K/year** |
| **Prometheus** | Self-hosted | - | $0 | ✅ Free |
| **Grafana** | Self-hosted | - | $0 | ✅ Free |
| **Loki** | Self-hosted | - | $0 | ✅ Free |
| **Jaeger** | Self-hosted | - | $0 | ✅ Free |

**Total Savings:** $9.6K/year (switching from SaaS to open-source)

---

## 🔍 2. Distributed Tracing

### **Stack: OpenTelemetry + Jaeger**

**Why OpenTelemetry?**

- ✅ **Vendor-Neutral:** Switch from Jaeger to Tempo without changing code
- ✅ **Auto-Instrumentation:** FastAPI, SQLAlchemy, HTTP requests
- ✅ **Context Propagation:** Trace IDs flow through entire request

---

### **Instrumentation**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to Jaeger
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Auto-instrument SQLAlchemy
SQLAlchemyInstrumentor().instrument(engine=engine)
```

---

### **Manual Spans (for critical operations)**

```python
@router.post("/goals/create")
async def create_goal(goal_request: GoalRequest, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("create_goal") as span:
        # Add attributes
        span.set_attribute("tenant_id", goal_request.tenant_id)
        span.set_attribute("goal_type", goal_request.type)
        
        # LLM call (custom span)
        with tracer.start_as_current_span("llm.generate_smart_goal") as llm_span:
            smart_goal = await coach_service.generate_smart_goal(goal_request.description)
            llm_span.set_attribute("llm.model", "gpt-4o")
            llm_span.set_attribute("llm.tokens", smart_goal["token_count"])
            llm_span.set_attribute("llm.cost", smart_goal["cost_usd"])
        
        # Database insert
        with tracer.start_as_current_span("postgres.insert_goal"):
            goal = Goal(**smart_goal)
            db.add(goal)
            db.commit()
        
        return {"goal_id": goal.goal_id}
```

---

### **Trace Visualization**

**Example Trace in Jaeger:**

```
Trace ID: abc123 (Total: 250ms)
├─ POST /v1/goals/create [250ms]
│  ├─ create_goal [230ms]
│  │  ├─ llm.generate_smart_goal [180ms] ⚠️ Slow!
│  │  │  └─ http.post → api.openai.com [175ms]
│  │  ├─ postgres.insert_goal [30ms]
│  │  └─ vector_search.embed_goal [15ms]
│  └─ middleware.auth [5ms]
```

**Insights:**

- 🔴 **Bottleneck:** LLM call (180ms out of 250ms = 72%)
- ✅ **Optimization:** Cache embeddings, use local LLM for simple queries

---

## 📈 3. Metrics Collection

### **Stack: Prometheus + Grafana**

**Architecture:**

```
┌─────────────────┐
│  FastAPI App    │
│  (metrics       │
│   endpoint)     │
└────────┬────────┘
         │ :9090/metrics
         ▼
┌─────────────────┐
│  Prometheus     │
│  (scraper)      │
│  - 15s interval │
│  - 30 day retention
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Grafana        │
│  (dashboards)   │
└─────────────────┘
```

---

### **Exposing Metrics**

```python
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# Business metrics
goals_created = Counter("goals_created_total", "Total goals created", ["tenant_id", "goal_type"])
goal_completion_rate = Gauge("goal_completion_rate", "Percentage of goals completed", ["tenant_id"])

# Technical metrics
api_latency = Histogram("api_request_duration_seconds", "API latency", ["method", "endpoint"])
llm_tokens_used = Counter("llm_tokens_total", "LLM tokens consumed", ["model", "tenant_id"])
llm_cost = Counter("llm_cost_usd_total", "LLM cost in USD", ["model", "tenant_id"])

# PostgreSQL metrics
db_query_time = Histogram("postgres_query_duration_seconds", "Query latency", ["query_type"])

# Mount Prometheus /metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware to track API latency
@app.middleware("http")
async def track_latency(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    api_latency.labels(method=request.method, endpoint=request.url.path).observe(duration)
    return response

# Track goal creation
@router.post("/goals/create")
async def create_goal(goal: GoalRequest):
    goals_created.labels(tenant_id=goal.tenant_id, goal_type=goal.type).inc()
    # ... create goal logic
```

---

### **Prometheus Configuration**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'dyocense-api'
    static_configs:
      - targets: ['localhost:8000']  # FastAPI app
    metrics_path: /metrics
```

---

### **Grafana Dashboards**

**1. AI Coach Health Dashboard**

| Panel | Metric | Alert Threshold |
|-------|--------|-----------------|
| **API Latency** | `api_request_duration_seconds` (P95) | > 500ms |
| **Error Rate** | `api_errors_total / api_requests_total` | > 1% |
| **LLM Cost** | `llm_cost_usd_total` (daily sum) | > $50/day |
| **Token Usage** | `llm_tokens_total` (by model) | Monitor trends |

**PromQL Query:**

```promql
# P95 latency per endpoint
histogram_quantile(0.95, 
  sum(rate(api_request_duration_seconds_bucket[5m])) by (endpoint, le)
)
```

---

**2. Business KPIs Dashboard**

| Panel | Metric | Goal |
|-------|--------|------|
| **Goals Created** | `goals_created_total` (daily) | 100+/day |
| **Completion Rate** | `goal_completion_rate` | > 60% |
| **Active Tenants** | `active_tenants` (unique `tenant_id`) | Growing |
| **MRR** | `mrr_total` (sum of all tenants) | $10K+ |

---

**3. PostgreSQL Performance Dashboard**

| Panel | Metric | Alert |
|-------|--------|-------|
| **Query Time** | `postgres_query_duration_seconds` (P99) | > 200ms |
| **Connections** | `pg_stat_database{datname="dyocense"}.numbackends` | > 80% max |
| **Cache Hit Rate** | `pg_stat_database.blks_hit / (blks_hit + blks_read)` | < 95% |
| **Replication Lag** | `pg_stat_replication.replay_lag` | > 10s |

**Install PostgreSQL Exporter:**

```bash
docker run -d \
  --name postgres-exporter \
  -p 9187:9187 \
  -e DATA_SOURCE_NAME="postgresql://user:password@postgres:5432/dyocense?sslmode=disable" \
  prometheuscommunity/postgres-exporter
```

---

## 📝 4. Structured Logging

### **Stack: JSON Logs + Loki**

**Why Loki?**

- ✅ **Cost:** Free (vs. Elasticsearch $300/mo)
- ✅ **Grafana Integration:** Same UI as metrics
- ✅ **LogQL:** Prometheus-like query language

---

### **Log Format**

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
    
    def log(self, level: str, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service_name,
            "message": message,
            **kwargs  # tenant_id, user_id, trace_id, etc.
        }
        self.logger.info(json.dumps(log_entry))

# Usage
logger = StructuredLogger("coach-service")

logger.log("INFO", "Goal created", 
    tenant_id="abc-123",
    user_id="user-456",
    trace_id="xyz-789",
    goal_id="goal-111",
    goal_type="revenue_growth"
)
```

**Output:**

```json
{
  "timestamp": "2024-11-14T10:30:00Z",
  "level": "INFO",
  "service": "coach-service",
  "message": "Goal created",
  "tenant_id": "abc-123",
  "user_id": "user-456",
  "trace_id": "xyz-789",
  "goal_id": "goal-111",
  "goal_type": "revenue_growth"
}
```

---

### **Loki Configuration**

```yaml
# loki-config.yml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h  # 7 days
```

**Start Loki:**

```bash
docker run -d \
  --name loki \
  -p 3100:3100 \
  -v $(pwd)/loki-config.yml:/etc/loki/local-config.yaml \
  grafana/loki:latest
```

---

### **Promtail (Log Shipper)**

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: dyocense
    static_configs:
      - targets:
          - localhost
        labels:
          job: dyocense
          __path__: /var/log/dyocense/*.log  # JSON logs
```

---

### **LogQL Queries**

```logql
# All errors in last hour
{service="coach-service"} |= "ERROR" | json | level="ERROR"

# Goals created per tenant
{service="coach-service"} |= "Goal created" | json | tenant_id="abc-123"

# Slow queries (>500ms)
{service="postgres"} | json | duration > 500

# Trace correlation (find all logs for a trace)
{service=~".+"} | json | trace_id="xyz-789"
```

---

## 🚨 5. Alerting

### **Prometheus Alertmanager**

```yaml
# alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

### **Alert Rules**

```yaml
# alerts.yml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, api_request_duration_seconds_bucket) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          description: "API P95 latency is {{ $value }}s (threshold: 500ms)"
      
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) / rate(api_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          description: "Error rate is {{ $value }}% (threshold: 1%)"
      
      - alert: DatabaseDown
        expr: up{job="postgres-exporter"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          description: "PostgreSQL is down!"
      
      - alert: HighLLMCost
        expr: increase(llm_cost_usd_total[1d]) > 50
        labels:
          severity: warning
        annotations:
          description: "LLM cost is ${{ $value }}/day (budget: $50)"
```

---

## 💰 6. Cost Comparison

### **SaaS vs. Self-Hosted**

| Tool Stack | Monthly Cost | Annual Cost |
|-----------|--------------|-------------|
| **v3.0 (SaaS)** |  |  |
| Datadog (APM + Logs) | $500 | $6,000 |
| New Relic (Infra) | $300 | $3,600 |
| PagerDuty (Alerts) | $50 | $600 |
| **Total** | **$850/mo** | **$10,200/year** |
|  |  |  |
| **v4.0 (Self-Hosted)** |  |  |
| Prometheus (metrics) | $0 | $0 |
| Grafana (dashboards) | $0 | $0 |
| Loki (logs) | $0 | $0 |
| Jaeger (traces) | $0 | $0 |
| Slack (alerts) | $0 (free tier) | $0 |
| **Infrastructure** | $20 | $240 |
| **Total** | **$20/mo** | **$240/year** |

**Savings:** $10,000/year (98% cost reduction!)

---

## 🎯 Next Steps

1. **Review [Service Architecture](./Service-Architecture.md)** for deployment model
2. **Review [Security & Multi-Tenancy](./Security & Multi-Tenancy.md)** for audit logging
3. **Start Week 2** of [Implementation Roadmap](./Implementation-Roadmap.md)

**Observability = Confidence! 📊**
