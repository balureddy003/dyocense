Version: 3.0
Last Updated: November 14, 2024
Status: Design Document

Table of Contents
System Architecture Overview
Data Architecture
Service Architecture
AI & Analytics Stack
Data Pipeline Architecture
External Data Integration
Multi-Agent System Design
Security & Multi-Tenancy
Observability Architecture
Technology Stack Selection
System Architecture Overview
High-Level Architecture Diagram
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  SMB Web UI (React)  │  Mobile App (React Native)  │  API Clients (SDK) │
└────────────┬─────────────────────────────┬──────────────────────────────┘
             │                             │
             ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Kong / Tyk (Open Source)                                               │
│  - Rate Limiting                                                         │
│  - Authentication (JWT)                                                  │
│  - Request Routing                                                       │
│  - Tenant Isolation                                                      │
└────────────┬────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER (Microservices)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ SMB Gateway  │  │ Goal Service │  │ Coach Service│                 │
│  │ (FastAPI)    │  │ (FastAPI)    │  │ (LangGraph)  │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Optimization │  │ Forecasting  │  │ Evidence     │                 │
│  │ Engine       │  │ Service      │  │ Service      │                 │
│  │ (OR-Tools)   │  │ (Prophet/XGB)│  │ (Causal AI)  │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Connector    │  │ Analytics    │  │ Notification │                 │
│  │ Service      │  │ Service      │  │ Service      │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                          │
└────────────┬────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐  ┌────────────────────┐                        │
│  │ Apache Airflow     │  │ Temporal           │                        │
│  │ (Data Pipelines)   │  │ (Goal Workflows)   │                        │
│  └────────────────────┘  └────────────────────┘                        │
└────────────┬────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (PostgreSQL)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PostgreSQL 16+ with Extensions:                                        │
│  ├─ TimescaleDB (Time-Series Metrics)                                  │
│  ├─ pgvector (Vector Search for RAG)                                   │
│  ├─ Apache AGE (Graph Queries for Evidence)                            │
│  ├─ pg_cron (Scheduled Jobs)                                           │
│  └─ PostGIS (Optional: Location-Based Analytics)                       │
│                                                                          │
│  Schemas:                                                               │
│  ├─ business_metrics (TimescaleDB hypertable)                          │
│  ├─ evidence_graph (AGE graph or JSONB)                                │
│  ├─ smart_goals (goal lifecycle tracking)                              │
│  ├─ coaching_sessions (conversation history + embeddings)              │
│  ├─ data_sources (connector configs)                                   │
│  ├─ external_benchmarks (industry/competitor data)                     │
│  └─ users, tenants, subscriptions                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SYSTEMS                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ├─ LLM Providers (OpenAI, Anthropic, local Llama)                     │
│  ├─ Data Sources (ERPNext, Salesforce, QuickBooks, Shopify)           │
│  ├─ Benchmark APIs (IBISWorld, FRED, Statista)                        │
│  └─ Observability (Prometheus, Jaeger, Grafana Cloud)                 │
└─────────────────────────────────────────────────────────────────────────┘

Design Principles
Single Database, Multiple Workloads: PostgreSQL with extensions eliminates operational complexity
Service Autonomy: Each microservice owns its domain logic but shares database
Event-Driven Communication: Services communicate via PostgreSQL LISTEN/NOTIFY or message queues
Idempotent Operations: All pipelines and workflows can safely retry
Tenant Isolation: Row-Level Security ensures data segregation at database level
Observability First: All services instrumented with OpenTelemetry from day one
