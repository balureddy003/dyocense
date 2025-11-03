# Knowledge Service

The knowledge service manages dataset ingestion and retrieval contexts that feed the compiler and explainability flows.

## Capabilities
- `POST /v1/datasets/documents` – ingest a single document chunk.
- `POST /v1/datasets/batch` – ingest multiple documents.
- `POST /v1/retrieve` – fetch ranked snippets for a goal/query.

All endpoints require bearer tokens (see `packages/kernel_common.deps.require_auth`).

## Configuration
- The default runtime keeps data in-process using `InMemoryKnowledgeStore`. Configure a remote store by injecting `KNOWLEDGE_SERVICE_URL` into clients (e.g., compiler) or swapping the store implementation.
- To enable vector search with Qdrant, set `KNOWLEDGE_BACKEND=qdrant` alongside `QDRANT_URL` (and optionally `QDRANT_API_KEY`/`QDRANT_COLLECTION`). The Docker Compose stack exposes Qdrant on `http://localhost:6333`.
- When Qdrant is active and Azure embeddings are configured (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_EMBED_DEPLOYMENT`), the knowledge store will automatically index text with Azure OpenAI embeddings instead of the default hash vectors.
- Future phases will connect to MinIO + Iceberg for raw datasets and Qdrant/Neo4j for vector/graph retrieval.

## Local Usage
1. Run the service: `uvicorn services.knowledge.main:app --reload --port 8086`.
2. Ingest a dataset: `scripts/ingest_dataset.py data/inventory.csv --tenant-id demo --project-id phase1 --collection ops_context`.
3. Compile goals with the compiler service; it will automatically retrieve snippets when `KNOWLEDGE_SERVICE_URL` points to this service.
