from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, HTTPException, status

from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging
from packages.knowledge import (
    InMemoryKnowledgeStore,
    KnowledgeDocument,
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResponse,
)

logger = configure_logging("knowledge-service")
store = InMemoryKnowledgeStore()


app = FastAPI(
    title="Dyocense Knowledge Service",
    version="0.1.0",
    description="Manages dataset ingestion and retrieval contexts for the compiler.",
)


@app.post("/v1/datasets/documents")
async def ingest_document(
    document: KnowledgeDocument,
    identity: dict = Depends(require_auth),
) -> dict:
    _ensure_tenant_access(document.tenant_id, identity)
    store.upsert(document)
    logger.info(
        "Ingested knowledge document %s for tenant=%s collection=%s",
        document.document_id,
        document.tenant_id,
        document.collection,
    )
    return {"document_id": document.document_id, "status": "stored"}


@app.post("/v1/datasets/batch")
async def ingest_batch(
    documents: List[KnowledgeDocument],
    identity: dict = Depends(require_auth),
) -> dict:
    count = 0
    for document in documents:
        _ensure_tenant_access(document.tenant_id, identity)
        store.upsert(document)
        count += 1
    logger.info("Batch ingested %s documents for tenant=%s", count, identity["tenant_id"])
    return {"count": count}


@app.post("/v1/retrieve", response_model=KnowledgeRetrievalResponse)
async def retrieve_context(
    request: KnowledgeRetrievalRequest,
    identity: dict = Depends(require_auth),
) -> KnowledgeRetrievalResponse:
    _ensure_tenant_access(request.tenant_id, identity)
    response = store.retrieve(request)
    logger.info(
        "Retrieved %s snippets for goal '%s' (tenant=%s)",
        len(response.snippets),
        request.goal,
        request.tenant_id,
    )
    return response


def _ensure_tenant_access(target_tenant: str, identity: dict) -> None:
    if target_tenant != identity["tenant_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant ingestion is not permitted.",
        )
