Microservices Design
Each service follows domain-driven design principles:

1. SMB Gateway Service
Responsibility: Main entry point for SMB users
Tech Stack: FastAPI, Pydantic, SQLAlchemy
APIs: Health score, business profiling, recommendations
2. Goal Service
Responsibility: SMART goal lifecycle management
Tech Stack: FastAPI, PostgreSQL, Temporal client
APIs: Create, update, track, evaluate goals
3. Coach Service (Multi-Agent)
Responsibility: Conversational AI coach
Tech Stack: LangGraph, LangChain, FastAPI Streaming
Agents: Goal Planner, Evidence Analyzer, Forecaster, Optimizer
4. Optimization Engine
Responsibility: Mathematical optimization (LP, MILP, constraint satisfaction)
Tech Stack: PuLP, OR-Tools, MiniZinc (via Python wrapper)
Use Cases: Inventory optimization, staffing, pricing, budget allocation
5. Forecasting Service
Responsibility: Time-series predictions with uncertainty quantification
Tech Stack: statsmodels (ARIMA), Prophet, XGBoost, scikit-learn
Models: Auto-ARIMA, seasonal decomposition, ensemble methods
6. Evidence Service
Responsibility: Causal inference and root cause analysis
Tech Stack: DoWhy, pgmpy (Bayesian networks), CausalNex
Methods: Granger causality, propensity score matching, DAG discovery
7. Connector Service
Responsibility: Data ingestion from external sources
Tech Stack: FastAPI, Requests, OAuth2 clients
Connectors: ERPNext, Salesforce, QuickBooks, Shopify, Stripe
8. Analytics Service
Responsibility: Query builder and aggregation engine
Tech Stack: FastAPI, PostgreSQL, DBT models
APIs: Flexible metric querying, custom dashboards
9. Notification Service
Responsibility: Multi-channel alerts (email, Slack, in-app)
Tech Stack: Celery, FastAPI, SMTP, Slack SDK
Channels: Email, Slack, webhooks, push notifications
Inter-Service Communication
Synchronous: REST APIs via internal service mesh
Asynchronous: PostgreSQL LISTEN/NOTIFY or Redis Streams
Workflow Orchestration: Temporal for durable, long-running workflows
Event Sourcing: Optional for audit trail (store all state changes)