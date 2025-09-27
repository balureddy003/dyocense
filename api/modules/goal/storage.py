"""MongoDB storage for goals."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection


@dataclass(slots=True)
class GoalRecord:
    goal_id: str
    tenant_id: str
    name: str
    goaldsl: Dict[str, object]
    context: Dict[str, object]
    variants: List[Dict[str, object]]
    status: str
    approvals: List[Dict[str, object]]
    feedback: List[Dict[str, object]]
    created_at: datetime
    updated_at: datetime


DEFAULT_STATUS = "draft"


class GoalRepository:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection
        self._ensure_indexes()

    def create(
        self,
        tenant_id: str,
        name: str,
        goaldsl: Dict[str, object],
        context: Dict[str, object],
        variants: List[Dict[str, object]],
    ) -> GoalRecord:
        now = datetime.now(timezone.utc)
        document = {
            "goal_id": _uuid(),
            "tenant_id": tenant_id,
            "name": name,
            "goaldsl": goaldsl,
            "context": context,
            "variants": variants,
            "status": DEFAULT_STATUS,
            "approvals": [],
            "feedback": [],
            "created_at": now,
            "updated_at": now,
        }
        self._collection.insert_one(document)
        return _document_to_goal(document)

    def update(
        self,
        tenant_id: str,
        goal_id: str,
        *,
        name: Optional[str] = None,
        goaldsl: Optional[Dict[str, object]] = None,
        context: Optional[Dict[str, object]] = None,
    ) -> Optional[GoalRecord]:
        updates: Dict[str, object] = {}
        if name is not None:
            updates["name"] = name
        if goaldsl is not None:
            updates["goaldsl"] = goaldsl
        if context is not None:
            updates["context"] = context
        if not updates:
            return self.get(tenant_id, goal_id)
        updates["updated_at"] = datetime.now(timezone.utc)
        document = self._collection.find_one_and_update(
            {"tenant_id": tenant_id, "goal_id": goal_id},
            {"$set": updates},
            return_document=True,
        )
        return _document_to_goal(document) if document else None

    def add_variant(
        self,
        tenant_id: str,
        goal_id: str,
        variant: Dict[str, object],
    ) -> Optional[GoalRecord]:
        variant_with_id = {**variant, "variant_id": _uuid()}
        document = self._collection.find_one_and_update(
            {"tenant_id": tenant_id, "goal_id": goal_id},
            {
                "$push": {"variants": variant_with_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=True,
        )
        return _document_to_goal(document) if document else None

    def update_status(
        self,
        tenant_id: str,
        goal_id: str,
        status: str,
        note: Optional[str] = None,
    ) -> Optional[GoalRecord]:
        update_set: Dict[str, object] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        update_ops: Dict[str, Dict[str, object]] = {"$set": update_set}
        if note:
            update_ops["$push"] = {
                "approvals": {
                    "note": note,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc),
                }
            }
        document = self._collection.find_one_and_update(
            {"tenant_id": tenant_id, "goal_id": goal_id},
            update_ops,
            return_document=True,
        )
        return _document_to_goal(document) if document else None

    def add_feedback(
        self,
        tenant_id: str,
        goal_id: str,
        feedback: Dict[str, object],
    ) -> Optional[GoalRecord]:
        document = self._collection.find_one_and_update(
            {"tenant_id": tenant_id, "goal_id": goal_id},
            {
                "$push": {"feedback": {**feedback, "timestamp": datetime.now(timezone.utc)}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=True,
        )
        return _document_to_goal(document) if document else None

    def get(self, tenant_id: str, goal_id: str) -> Optional[GoalRecord]:
        document = self._collection.find_one({"tenant_id": tenant_id, "goal_id": goal_id})
        return _document_to_goal(document) if document else None

    def list(self, tenant_id: str) -> Iterable[GoalRecord]:
        cursor = self._collection.find({"tenant_id": tenant_id}).sort("updated_at", DESCENDING)
        return [_document_to_goal(doc) for doc in cursor]

    def _ensure_indexes(self) -> None:
        self._collection.create_index([("tenant_id", ASCENDING), ("goal_id", ASCENDING)], unique=True)
        self._collection.create_index([("tenant_id", ASCENDING), ("updated_at", DESCENDING)])


def _document_to_goal(document: Optional[Dict[str, object]]) -> Optional[GoalRecord]:
    if not document:
        return None
    created_at = _to_datetime(document.get("created_at"))
    updated_at = _to_datetime(document.get("updated_at"))
    return GoalRecord(
        goal_id=str(document.get("goal_id")),
        tenant_id=str(document.get("tenant_id")),
        name=str(document.get("name", "")),
        goaldsl=dict(document.get("goaldsl", {})),
        context=dict(document.get("context", {})),
        variants=list(document.get("variants", [])),
        status=str(document.get("status", DEFAULT_STATUS)),
        approvals=list(document.get("approvals", [])),
        feedback=list(document.get("feedback", [])),
        created_at=created_at,
        updated_at=updated_at,
    )


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


def _uuid() -> str:
    import uuid

    return str(uuid.uuid4())
