# Copilot Instructions for Dyocense

## Project Overview
- **Dyocense** is a platform for translating SMB goals into optimized, auditable, and continuously improving plans.
- The architecture is layered: Experience (UI), API (FastAPI), Agent (LangGraph, LLMs), Decision Kernel (optimization, forecasting, evidence), and Data (Postgres, Redis, MinIO, Mongo, Neo4j).
- See `docs/architecture.md` for a full platform overview and Mermaid diagrams of data and control flow.

## Key Components & Patterns
- **API Layer:** Each service (goal, plan, evidence, feedback, etc.) has its own FastAPI contract. APIs are documented and versioned.
- **Agent Layer:** Orchestrated by LangGraph. Agents include GoalAgent, VoIAgent, EvidenceScribe, NegotiationAgent. LLM routing via LiteLLM/OpenRouter.
- **Decision Kernel:** Pipeline: Forecast → OptiGuide (GoalDSL compiler) → Optimizer (OR-Tools/Pyomo) → Evidence Graph (Neo4j). See `kernel/KernelDESIGN.md` for detailed flows and contracts.
- **Data Layer:** Uses Postgres (OLTP), Redis (cache/queue), MinIO (files), Mongo/Chroma/Qdrant (RAG/embeddings), Neo4j (evidence/provenance).
- **Service Boundaries:** Each service in `services/` has its own `DESIGN.md` and ADRs. Cross-service contracts are explicit and versioned.

## Developer Workflows
- **Local Dev:** Use Docker Compose for all services and dependencies. See `infra/DEPLOYMENT.md` for setup.
- **Testing:** (Not detailed in docs—add test commands here if/when available.)
- **Deployment:** Staging/prod via AKS/K3s, GitHub Actions, ArgoCD. See `infra/DEPLOYMENT.md`.
- **Telemetry:** OpenTelemetry, Prometheus/Grafana, Loki, Tempo for tracing/metrics/logs.

## Project Conventions
- **Design Docs:** Every major service and kernel module has a `DESIGN.md` and ADRs in `adrs/`.
- **ADR Index:** See `docs/architecture.md` for a summary of architectural decisions.
- **Naming:** Use clear, domain-driven names for services, agents, and APIs.
- **LLM Integration:** LLMs are routed via LiteLLM/OpenRouter, with local fallback to Ollama and cloud fallback to OpenAI/Anthropic.
- **Optimization:** Use OptiGuide for compiling GoalDSL, OR-Tools/Pyomo for solving, and persist evidence in Neo4j.

## Integration Points
- **External APIs:** POS (Shopify/Toast), ERP (Xero/QuickBooks), Supplier APIs, Email (SMTP/OAuth).
- **RAG:** Chroma/Qdrant for retrieval-augmented generation, integrated with LLM agents.
- **Policy/IAM:** OPA/OPAL for policy checks, Keycloak for auth.

## Examples
- For a full kernel pipeline, see `kernel/KernelDESIGN.md` (mermaid diagrams and sequence flows).
- For service boundaries and contracts, see `services/*/DESIGN.md` and `services/*/adrs/`.

---

**If you are an AI agent, always reference the above docs for architecture, flows, and conventions before generating or modifying code.**
