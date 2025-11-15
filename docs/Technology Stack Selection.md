Core Technologies
Layer	Technology	Rationale
Database	PostgreSQL 16+	Single DB for all workloads, mature, portable
Time-Series	TimescaleDB	Native PostgreSQL extension, no separate DB
Vector Search	pgvector	Semantic search without separate vector DB
Graph Queries	Apache AGE	Cypher queries in PostgreSQL
API Framework	FastAPI	Async, auto-docs, Pydantic validation
Workflow Engine	Temporal	Durable workflows, fault-tolerant
Data Pipelines	Apache Airflow	Industry standard, rich ecosystem
ETL/ELT	DBT	SQL-based transformations, version control
Validation	Great Expectations	Data quality checks, alerts
LLM Orchestration	LangGraph	State machines for agents, streaming
Optimization	OR-Tools, PuLP	Industry-standard solvers
Forecasting	Prophet, XGBoost	Battle-tested, auto-tuning
Causal Inference	DoWhy, pgmpy	Research-backed libraries
Tracing	OpenTelemetry + Jaeger	Vendor-neutral, CNCF standard
Metrics	Prometheus + Grafana	De facto standard, rich ecosystem
Logging	Loki	Lightweight, integrates with Grafana
API Gateway	Kong or Tyk	Open-source, plugin ecosystem
Container Orchestration	Kubernetes	Industry standard, multi-cloud
CI/CD	GitHub Actions	Native to monorepo, free tier
Deployment Architecture
Development: Docker Compose (all services on local machine)

Staging: Kubernetes on single cloud provider (e.g., GKE, EKS, AKS)

Production: Multi-region Kubernetes with PostgreSQL replication

Disaster Recovery: Cross-cloud backup (PostgreSQL backups to S3-compatible storage)

Conclusion
This architecture balances innovation (hybrid AI + classical optimization) with pragmatism (PostgreSQL-first, open-source tools). By avoiding premature complexity (separate vector DB, graph DB, NoSQL), we reduce operational overhead while maintaining flexibility to scale.

The key architectural bets:

PostgreSQL as single source of truth → Simplifies ops, ACID guarantees
Hybrid AI architecture → Mathematically rigorous, patentable IP
Open-source first → No vendor lock-in, community-driven innovation
Orchestration over microservices chaos → Temporal for workflows, Airflow for data
