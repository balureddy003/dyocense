1. Distributed Tracing
Stack: OpenTelemetry + Jaeger (or Grafana Tempo)

Instrumentation:

Auto-instrument: FastAPI, SQLAlchemy, Requests
Manual spans: LLM calls, optimization solver runs
Trace Example:

Trace ID: abc123
├─ Span: POST /v1/goals/create [200ms]
│  ├─ Span: coach.generate_goal [150ms]
│  │  ├─ Span: llm.gpt4o.call [100ms] {tokens: 1500}
│  │  └─ Span: vector_search.retrieve_context [30ms]
│  └─ Span: postgres.insert_goal [20ms] {RU: 5}
2. Metrics Collection
Stack: Prometheus + Grafana

Business Metrics:

Goals created per day (counter)
Goal completion rate (gauge)
Average time to first goal (histogram)
Technical Metrics:

API latency (P50, P95, P99)
PostgreSQL query time
LLM token usage & cost
Dashboards:

AI Coach Health: Latency, error rate, token cost
Data Pipelines: Connector sync status, data freshness
Business KPIs: User engagement, goal metrics
3. Structured Logging
Stack: JSON logs + Loki (or ELK)

Log Format:

{
  "timestamp": "2024-11-14T10:30:00Z",
  "level": "INFO",
  "service": "coach-service",
  "tenant_id": "abc-123",
  "user_id": "user-456",
  "trace_id": "xyz-789",
  "message": "Goal created successfully",
  "metadata": {"goal_id": "goal-111", "type": "revenue_growth"}
}
Querying: LogQL (Loki) or Lucene (Elasticsearch)