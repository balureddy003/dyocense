# Dyocense — Architecture & Design Docs (v3)
Date: 2025-09-22

This bundle contains **fully populated** design documents and **ADRs for each service**.
See `docs/architecture.md` for the platform overview. Development setup instructions live in `docs/LOCAL_DEV.md`.

Repository layout:

- `kernel/` — decision kernel pipeline, modules, and tests
- `api/` — unified FastAPI backend (modules, shared helpers, docs)
- `client/` — Vite + React SPA (LibreChat-inspired UI)
- `docs/` — design and architecture references
- `scripts/` — sample payloads and HTTPie scripts

Reusable service helpers (kernel client, auth middleware, tracing) are documented in `api/common/README.md`. Service designs now live under `api/modules/*` (plan, goal, evidence, scheduler, feedback, market, policy, negotiation, auth, llm_router, questions).

## Quick Start (Docker)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

This launches MongoDB, Redis, Neo4j, the kernel (FastAPI on `:8080`), the unified API (`:8000`), and the React client (`:3000`). Visit <http://localhost:3000> to access the LibreChat-style UI.

Copy `.env.example` to `.env` and adjust provider credentials (Mongo, Neo4j, LLM router) before deploying to other environments. Docker Compose automatically loads `.env` values.
