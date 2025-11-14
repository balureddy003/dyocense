ETL/ELT Framework
Philosophy: ELT over ETL (load raw data, transform in PostgreSQL for flexibility)

Pipeline Stages
1. Ingestion Layer
Tool: Apache Airflow DAGs

Connectors:

API-Based: Poll REST APIs (Salesforce, Shopify) on schedule
Webhook-Based: Real-time ingestion via FastAPI webhooks
File-Based: CSV/Excel uploads to PostgreSQL via Pandas
Database-Based: Direct query from ERPNext, QuickBooks databases
Pattern: Extract → Load into raw_data schema → Trigger validation

2. Validation Layer
Tool: Great Expectations

Checks:

Schema Validation: Expected columns present, correct types
Range Checks: Revenue > 0, inventory >= 0
Consistency: Sum of line items = invoice total
Freshness: Data timestamp within expected window
Output: Data quality report (stored in PostgreSQL), alerts on failures

3. Transformation Layer
Tool: DBT (Data Build Tool)

Models:

Staging: Clean raw data, standardize formats
Intermediate: Join tables, calculate derived metrics
Marts: Final analytics-ready views (e.g., monthly_revenue_by_category)
Benefits:

Version Control: All transformations in Git
Testing: Built-in assertions (unique, not null, referential integrity)
Documentation: Auto-generated data lineage diagrams
4. Availability Layer
APIs:

GET /v1/metrics/{tenant_id}?metric_type=revenue&start_date=...&end_date=...
GET /v1/aggregations/{tenant_id}?group_by=category&time_grain=monthly
POST /v1/metrics/query (flexible query builder)
Streaming: Server-Sent Events (SSE) for real-time updates

Orchestration Strategy
Apache Airflow for batch pipelines:

DAG: connector_sync_{source_type}
Schedule: Hourly incremental, nightly full refresh
Retries: Exponential backoff (3 attempts)
Monitoring: Airflow UI + Prometheus metrics
Temporal for long-running workflows:

Workflow: goal_execution_lifecycle
Activities: Create tasks, send reminders, evaluate progress
Durability: Survives service restarts, replays from last checkpoint
