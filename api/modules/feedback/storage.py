"""Mongo storage for feedback events."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection


@dataclass(slots=True)
class FeedbackRecord:
    event_id: str
    tenant_id: str
    goal_id: Optional[str]
    plan_id: Optional[str]
    actuals: List[Dict[str, object]]
    created_at: datetime


class FeedbackRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._ensure_indexes()

    def insert_events(
        self,
        tenant_id: str,
        goal_id: Optional[str],
        plan_id: Optional[str],
        actuals: List[Dict[str, object]],
    ) -> FeedbackRecord:
        now = datetime.now(timezone.utc)
        document = {
            "event_id": _uuid(),
            "tenant_id": tenant_id,
            "goal_id": goal_id,
            "plan_id": plan_id,
            "actuals": actuals,
            "created_at": now,
        }
        self._collection.insert_one(document)
        return _document_to_record(document)

    def list_events(self, tenant_id: str, goal_id: Optional[str] = None) -> Iterable[FeedbackRecord]:
        query = {"tenant_id": tenant_id}
        if goal_id:
            query["goal_id"] = goal_id
        cursor = self._collection.find(query).sort("created_at", DESCENDING)
        return [_document_to_record(doc) for doc in cursor]

    def aggregate_drift(self, tenant_id: str, goal_id: Optional[str] = None) -> Dict[str, Dict[str, object]]:
        pipeline = [
            {"$match": {"tenant_id": tenant_id, **({"goal_id": goal_id} if goal_id else {})}},
            {"$unwind": "$actuals"},
            {
                "$group": {
                    "_id": "$actuals.sku",
                    "count": {"$sum": 1},
                    "avg_quantity": {"$avg": "$actuals.quantity"},
                    "last_event": {"$max": {"created_at": "$created_at", "period": "$actuals.period", "quantity": "$actuals.quantity"}},
                }
            },
        ]
        results = self._collection.aggregate(pipeline)
        aggregates: Dict[str, Dict[str, object]] = {}
        for row in results:
            data = row["last_event"]
            aggregates[row["_id"]] = {
                "count": row["count"],
                "avg_quantity": row["avg_quantity"],
                "last_period": data.get("period"),
                "last_quantity": data.get("quantity"),
            }
        return aggregates

    def _ensure_indexes(self) -> None:
        self._collection.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])
        self._collection.create_index([("tenant_id", ASCENDING), ("goal_id", ASCENDING)])


def _document_to_record(document: Dict[str, object]) -> FeedbackRecord:
    return FeedbackRecord(
        event_id=str(document.get("event_id")),
        tenant_id=str(document.get("tenant_id")),
        goal_id=document.get("goal_id"),
        plan_id=document.get("plan_id"),
        actuals=document.get("actuals", []),
        created_at=_to_datetime(document.get("created_at")),
    )


def _uuid() -> str:
    import uuid

    return str(uuid.uuid4())


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)
