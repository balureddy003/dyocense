"""Market intelligence ingestion API."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status

from api.common import BearerAuthMiddleware, context, get_mongo_collection, noop_decoder

from .config import get_settings
from .schemas import MarketIngestRequest, MarketIngestResponse, SupplierSnapshot
from .storage import MarketRepository

logger = logging.getLogger(__name__)

app = FastAPI(title="Dyocense Market Service", version="0.1.0")
app.add_middleware(BearerAuthMiddleware, decoder=noop_decoder)

_repository_singleton: Optional[MarketRepository] = None


def get_repository() -> MarketRepository:
    global _repository_singleton
    if _repository_singleton:
        return _repository_singleton
    settings = get_settings()
    if not settings.mongo_uri:
        raise RuntimeError("MARKET_MONGO_URI missing")
    collection = get_mongo_collection(settings.mongo_uri, settings.mongo_db, settings.collection)
    _repository_singleton = MarketRepository(collection)
    return _repository_singleton


@app.get("/health", tags=["health"])
def health() -> Dict[str, object]:
    settings = get_settings()
    return {"status": "ok", "mongo": settings.mongo_uri}


@app.post("/market/snapshots", response_model=MarketIngestResponse, tags=["market"])
async def ingest_market_data(
    request: MarketIngestRequest,
    repository: MarketRepository = Depends(get_repository),
) -> MarketIngestResponse:
    tenant = context.get_tenant()
    tenant_id = tenant.tenant_id if tenant else request.tenant_id
    records = repository.insert_snapshots(
        tenant_id=tenant_id,
        source=request.source,
        snapshots=[snapshot.dict() for snapshot in request.snapshots],
    )
    return MarketIngestResponse(count=len(records), ingested_at=datetime.now(timezone.utc))


@app.get("/market/snapshots", response_model=List[SupplierSnapshot], tags=["market"])
async def list_snapshots(repository: MarketRepository = Depends(get_repository)) -> List[SupplierSnapshot]:
    tenant = context.get_tenant()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing tenant context")
    records = repository.latest_snapshots(tenant.tenant_id)
    return [
        SupplierSnapshot(
            supplier_id=record.supplier_id,
            cost=record.cost,
            capacity=record.capacity,
            score=record.score,
            metadata=record.metadata,
        )
        for record in records
    ]
