# Data & Metadata Foundation

Phase 5 introduces a dedicated data foundation to back large-scale retrieval and version management.

## Components
- **MinIO** — object storage powering Apache Iceberg tables and artifact blobs.
- **Project Nessie** — metadata catalog used by Iceberg to manage table history.
- **Postgres (metadata)** — transactional store for OpenMetadata and auxiliary catalogs.
- **Qdrant** — vector database for dense retrieval aligned with OPS schema fields.
- **OpenMetadata** *(optional container)* — service catalog that tracks datasets, Iceberg tables, and fact registries.

Docker Compose now ships with MinIO, Nessie, Postgres, Qdrant, Mongo, and Neo4j. Start the stack via:

```bash
docker compose -f infra/docker-compose/docker-compose.yaml up -d minio nessie postgres-metadata qdrant
```

Want a slimmer footprint? `infra/docker-compose/docker-compose.override.yaml` introduces Compose profiles so optional services only start when requested:

```bash
# Core infra only (Mongo, Neo4j, MinIO)
docker compose -f infra/docker-compose/docker-compose.yaml up -d

# Add knowledge-plane services (Qdrant, Nessie, Postgres metadata)
docker compose --profile knowledge-plane up -d

# Bring kernel/orchestrator services when required
docker compose --profile kernel-services up -d
```

The compiler and knowledge services detect these endpoints through environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `NESSIE_ENDPOINT` | `http://localhost:19120/api/v1` | Iceberg catalog endpoint |
| `QDRANT_URL` | `http://localhost:6333` | Vector store API |
| `QDRANT_API_KEY` | *(optional)* | Auth token for managed clusters |
| `KNOWLEDGE_BACKEND` | `qdrant` or `memory` | Selects the knowledge store implementation |

Refer to `scripts/benchmark_compiler_retrieval.py` for an example that loads a large dataset into the knowledge plane and benchmarks compiler latency. The sample corpus lives in `examples/datasets/goal_context_large.jsonl`.
