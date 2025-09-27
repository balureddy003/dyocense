"""Mongo storage for market intelligence snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection


@dataclass(slots=True)
class MarketRecord:
    tenant_id: str
    supplier_id: str
    source: str
    cost: float
    capacity: float
    score: float
    metadata: Dict[str, object]
    ingested_at: datetime


class MarketRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._ensure_indexes()

    def insert_snapshots(
        self,
        tenant_id: str,
        source: str,
        snapshots: List[Dict[str, object]],
    ) -> List[MarketRecord]:
        now = datetime.now(timezone.utc)
        documents = []
        for snapshot in snapshots:
            document = {
                "tenant_id": tenant_id,
                "supplier_id": snapshot["supplier_id"],
                "source": source,
                "cost": snapshot["cost"],
                "capacity": snapshot["capacity"],
                "score": snapshot["score"],
                "metadata": snapshot.get("metadata", {}),
                "ingested_at": now,
            }
            documents.append(document)
        if documents:
            self._collection.insert_many(documents)
        return [_document_to_record(doc) for doc in documents]

    def latest_snapshots(self, tenant_id: str) -> Iterable[MarketRecord]:
        cursor = self._collection.find({"tenant_id": tenant_id}).sort("ingested_at", DESCENDING)
        return [_document_to_record(doc) for doc in cursor]

    def _ensure_indexes(self) -> None:
        self._collection.create_index([("tenant_id", ASCENDING), ("supplier_id", ASCENDING), ("ingested_at", DESCENDING)])


def _document_to_record(document: Dict[str, object]) -> MarketRecord:
    return MarketRecord(
        tenant_id=str(document.get("tenant_id")),
        supplier_id=str(document.get("supplier_id")),
        source=str(document.get("source", "")),
        cost=float(document.get("cost", 0.0)),
        capacity=float(document.get("capacity", 0.0)),
        score=float(document.get("score", 0.0)),
        metadata=dict(document.get("metadata", {})),
        ingested_at=document.get("ingested_at", datetime.now(timezone.utc)),
    )
